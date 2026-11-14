# Bring-up order

Bring-up proceeds in stages. Each stage has a visible result and a log line. Isolate one stage at a time.

For repeated builds, save paths in [unixnu.local.toml](/reference/configuration#local-build-inputs). After changing boot arguments, rebuild the payload and boot image using the [argument workflow](/xnu/boot-arguments#apply-arguments). Follow the [green-bar diagnosis](/guide/debugging#green-bar) for a stall at loader handoff.

Before enabling a peripheral, complete its [adaptation procedure](/porting/drivers). Build the image with [Building](/building), then use these checkpoints in order. After each failure, keep the image and the last log before changing inputs. A macOS image follows the same stages with the [macOS checkpoints](/porting/macos#bring-up).

## Stage 0: Stock boot baseline

Before testing a replacement firmware, verify that a matching official stock
system boots normally and the host detects the device in Fastboot. If restoring
Android, use the device's appropriate official package and retain its unlocked
bootloader. Record the actual stock system version separately from the firmware
inputs selected by the device repository. One complete successful stock start
and Fastboot detection satisfy this baseline. The sheng baseline was checked
with three successful ordinary Android reboots.

If temporary boot rejects the stock boot image too, investigate that boot
method before assigning the failure to UEFI. A successful build or a Fastboot
`OKAY` response is not a firmware execution checkpoint.

## Stage 1: UEFI

Goal: the firmware reaches a UEFI shell, a boot menu or the UniXNU application.

Checks:

- The firmware volume size matches `[uefi_fd] size`.
- The boot image header matches the bootloader requirement.
- `fastboot boot boot.img` starts the firmware without a reset.
- The framebuffer shows output, or the serial port shows UEFI output.
- A firmware-only probe stays in its interface without starting an OS. One
  complete successful run is sufficient: at least 300 visible one-second
  heartbeat ticks, a matching build ID, real key response and a demonstrated
  return to Fastboot. Save the image hash with the observations.

For sheng, use the device repository's independent **UEFI probe** workflow or
`scripts/build-uefi-probe.py`. It embeds a standalone interface and removes
DarwinBoot in isolated source copies. It uses the board's existing pinned stock
archive and needs no kernel, IPSW, payload, installation seed or userdata image.
Its early DEBUG markers use the inherited framebuffer; they are not physical
UART output. BootShim execution and an invisible display cannot be distinguished
by a black screen alone. The probe's ordinary restart does not guarantee
Fastboot entry; use the hardware recovery key combination for this check.

A sheng device comparison kept BootShim, the FD, gzip payload and DTB unchanged:
switching the Android boot header from v0 to v4 produced a visible UEFI probe
with responsive volume keys. The user confirmed the matching build ID, at least
300 advancing heartbeats without a reset and return to Fastboot with the
hardware keys. Stage 1 passed this complete run. The user waived three cold-boot
repetitions; they were not performed and are not a pending action. The independent
builder applies the v4 override to its isolated board configuration; it leaves
the original `board.toml` firmware pins unchanged.

Block devices and the payload volume are checked when adding the payload in
stage 3. For a Mu-Silicium initrd payload, check `UniXNURamDiskDxe`, DiskIoDxe
and FAT using the [firmware integration guide](/porting/uefi-firmware#required-integration).

Tools:

```sh
fastboot boot out/<device>/<os_profile>/<config>/boot/boot.img
```

If firmware stops responding, reset into the device's bootloader, confirm `fastboot devices`, and capture the last firmware output before retrying.

## Stage 2: UniXNU

Goal: the menu appears and the configuration is parsed.

The sheng `--stage menu` fixture embeds a read-only FAT volume in firmware,
containing a build-linked configuration and HelloPayload EFI file. It needs no
boot ramdisk or `vendor_boot` write. Physical confirmation selects an expected
missing-file error or the file-loaded Hello, which returns to the menu after
15 seconds. The isolated research firmware permits this test EFI and skips
automatic key enrollment; the stock bootloader and board firmware pins remain
unchanged. Device observations must establish configuration, error and file
execution separately before continuing to XNU.
The owner confirmed the matching menu, physical navigation, visible Not Found
error and Hello returning to the menu on sheng build `e48871c4a505`; this
single complete run passed the menu/file fixture stage.

The next sheng trial reuses the existing complete kernel at the owner's
request. Its v4 repack disables persistent Data and native UFS log/export
writes and removes installation. The first device attempt displayed four
fallback entries instead of its two configured entries, then a failure and
power-off; XNU execution was not observed. The `full` firmware variant reports
the incoming initrd and verifies the exact FAT volume behind any vendor prefix
before offering a manually confirmed DarwinBoot handoff. Keep payload discovery,
loader handoff, kernel entry and platform initialization as separate evidence.
Run native host checks before downloading the large firmware inputs. The
kernel-probe fixture uses explicit 16-bit string reads: an optimized macOS
mock reported an incorrect UTF-16 length. Keep these host simulation failures
separate from firmware or device results.

Checks:

- Serial lines start with `UNIXNU:`.
- The log reports the entry, driver, patch, ACPI, slice and kit counts.
- The menu lists the expected entries.
- Driver failures show a count and the first failure reason.

Minimal test: an empty ramdisk. UniXNU falls back to its built-in configuration and lists removable loaders.

```sh
./unixnu bootimg --uefi /path/to/Mu-Silicium --dtb board.dtb --ramdisk none
```

Before continuing, [scan the firmware log](/porting/log-capture#qr-logs) from
**Tools → Advanced Logger**. Prepare the platform logger and plugin with the
[integration steps](/porting/log-capture#firmware-setup).

## Stage 3: Payload

Goal: UniXNU reads `unixnu.toml` and the payload files.

Checks:

- The log reports the configuration path.
- The `xnu` entry is present.
- The payload report hashes match the files in the volume.
- The ADT sidecar is next to the kernel.

A payload error is visible before DarwinBoot starts.

## Stage 4: DarwinBoot

Goal: DarwinBoot validates the kernel, the ADT and the trust cache, then exits boot services.

Checks:

- Serial lines start with `DARWINBOOT:`.
- The loader prints the virtual base, physical base, arguments address and entry address.
- The printed output shows the framebuffer base, width, height and depth.
- The exception level is EL1.
- The bootstrap page table path reaches the kernel entry.

A refusal prints `DARWINBOOT: boot refused: <status>; firmware retained`. The firmware stays in control, so the device returns to the menu.

## Stage 5: Kernel entry

Goal: XNU starts and reaches the platform expert.

Checks:

- The kernel prints its version and boot arguments.
- The bootstrap page tables map the kernel window.
- The platform expert matches the ADT root.
- `/cpus`, `/arm-io`, `/defaults`, `/options` and the NVRAM proxy are present.

With the entry probe enabled, color bars mark early kernel checkpoints. See [Color bars](/guide/debugging#color-bars).

A missing platform provider produces a panic that names the provider. Add the driver or correct the ADT.

## Stage 6: Storage and root

Goal: the block driver publishes the userdata partition, the volumes appear, and XNU mounts the root.

Checks:

- The storage driver logs the link speed and the command queue.
- The partition scheme publishes `OS` and `SystemOS`.
- The root volume UUID matches `root_match_volume_uuid`.
- The kernel mounts the root and starts `launchd`.

A root match failure leaves the kernel without a root device. Check the UUID, the window offsets and the partition capacity.

Once storage works, [adapt persistent capture](/porting/log-capture#persistent-logs)
with a kernel writer and a Linux or recovery reader. Complete one manual retrieval before
enabling timed reset and the automated cycle.

## Stage 7: Userland

Goal: `launchd` runs and the first user process reaches a visible state.

Checks:

- `launchd` starts from the root volume.
- The Data volume mounts.
- The display server or the console presents output.
- The boot progress layer records the last checkpoint.

Use `boot-progress=2` and the diagnostic boot arguments to see the last completed checkpoint.

## QEMU before hardware

Follow [QEMU testing](/reference/qemu) to stage the ESP and run the menu/payload
fixture. The XNU entry fixture needs an ARM64 kernel, its ADT sidecar and
DarwinBoot staged together. Check the fixture's selected entry and expected
checkpoint before running it.

```sh
JOBS=8 bash package/Scripts/smoke.sh
```

Run from the main checkout with the QEMU requirements installed. This command
checks the UEFI package scenarios and writes logs/screenshots under
`package/Build/Smoke/`. Use the [kernel-entry instructions](/reference/qemu#xnu-entry-fixture)
for XNU work. Hardware peripheral results are recorded on the target device.

## Failure isolation

| Symptom | First check |
| --- | --- |
| No firmware output | Boot image header, firmware base and size, bootloader log |
| Firmware output, no menu | GOP driver, UniXNU driver path, `unixnu.toml` |
| Menu, no payload entry | Payload volume label, FAT driver, entry path |
| Payload entry, no DarwinBoot log | Loader protocol, DarwinBoot in the firmware volume |
| DarwinBoot refusal | Kernel Mach-O, ADT, trust cache, placeholder |
| Kernel entry, no log | Boot arguments, serial selection, framebuffer address |
| Panic naming a provider | ADT node, driver archive, kernel flag |
| No root | Userdata image, UUID, partition capacity |

## Next steps

- [Troubleshooting](/reference/troubleshooting)
- [QEMU testing](/reference/qemu)
- [Boot arguments](/xnu/boot-arguments)
