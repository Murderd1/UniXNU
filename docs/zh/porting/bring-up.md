# bring-up 顺序

bring-up 按阶段推进。每个阶段都有可见结果和日志行，一次隔离一个问题。

重复构建时，在 [unixnu.local.toml](/zh/reference/configuration#local-build-inputs) 保存路径。修改启动参数后，按[参数应用流程](/zh/xnu/boot-arguments#apply-arguments)重新构建负载和启动镜像。画面停在加载器交接阶段时，按[绿条诊断](/zh/guide/debugging#green-bar)检查。

启用外设前完成对应[适配流程](/zh/porting/drivers)，按[构建指南](/zh/building)生成镜像，再依次检查以下阶段。失败后先保存镜像和最后日志，再修改输入。macOS 镜像经过相同阶段，另有 [macOS 检查点](/zh/porting/macos#bring-up)。

## 阶段 0：原厂启动基线

测试替代固件前，先确认匹配设备的原厂系统能够正常启动，电脑也能在 Fastboot
模式识别设备。恢复 Android 时使用适合本机的官方包，并保留 Bootloader 解锁状态。
分别记录实际原厂系统版本和设备仓库选择的固件输入版本。完成一次正常启动和
Fastboot 识别即可通过该基线。sheng 已实际完成三次普通 Android 重启。

如果临时启动连对应的原厂 boot 镜像也拒绝，先排查这一启动方式。编译成功或
Fastboot 返回 `OKAY` 都不等于已经进入 UEFI。

## 阶段 1：UEFI

目标：固件进入 UEFI shell、启动菜单或 UniXNU。

检查：

- 固件卷大小匹配 `[uefi_fd] size`。
- 启动镜像 header 满足 bootloader 要求。
- `fastboot boot boot.img` 启动固件，不复位。
- framebuffer 有输出，或串口有 UEFI 输出。
- 独立固件测试界面保持运行，不自动启动系统。一次完整成功即可通过：观察至少
  300 次可见的一秒心跳、核对构建编号、确认真实按键响应，并验证能返回 Fastboot。
  保存镜像哈希和实际观察记录。

sheng 使用设备仓库的独立 **UEFI probe** 工作流或 `scripts/build-uefi-probe.py`。
它在隔离源码副本中嵌入测试界面并移除 DarwinBoot，沿用板级固定的原厂固件输入，
不需要内核、IPSW、payload、安装种子或 userdata 镜像。早期 DEBUG 阶段标记写入
继承的帧缓冲，并非物理串口输出。仅凭黑屏仍无法区分 BootShim 未执行和显示断链。
测试界面的普通重启不保证进入 Fastboot，使用硬件恢复组合键完成这一检查。

sheng 的一次真机对照保持 BootShim、FD、gzip 负载和 DTB 不变，仅将 Android boot
头从 v0 改为 v4 后，UEFI 测试界面可见且音量键有响应。用户已核对构建编号，确认
至少 300 次心跳持续递增且未复位，并通过硬件组合键返回 Fastboot。阶段 1 已按
一次完整成功的标准通过。三次冷启动重复测试未执行，用户已明确免除，不再作为
待办。独立构建入口只在隔离的板级配置副本中覆盖为 v4，原始 `board.toml` 的固件
输入固定值保持不变。

块设备和负载卷留到阶段 3 接入 payload 时检查。Mu-Silicium initrd 负载需要在 FD
中包含 `UniXNURamDiskDxe`、DiskIoDxe 和 FAT，详见[固件集成](/zh/porting/uefi-firmware#required-integration)。

```sh
fastboot boot out/<device>/<os_profile>/<config>/boot/boot.img
```

固件停止响应时，复位进入设备 bootloader，用 `fastboot devices` 确认连接，重试前保存最后的固件输出。

## 阶段 2：UniXNU

目标：菜单出现，配置解析成功。

sheng 的 `--stage menu` 测试在固件内嵌只读 FAT 卷，包含带构建编号的配置和
HelloPayload EFI 文件，不需要 boot ramdisk 或写入 `vendor_boot`。通过物理按键
确认后，分别验证预期的文件不存在错误，以及从文件运行 Hello 并在 15 秒后返回
菜单。隔离测试固件允许该 EFI 文件并跳过自动密钥登记；原厂 Bootloader 和板级
固件输入固定值保持不变。配置、错误提示和文件执行应分别用真机结果验收，再进入 XNU。
sheng 构建 `e48871c4a505` 已由用户确认菜单编号、物理按键导航、可见的 Not Found
错误，以及 Hello 执行后返回菜单；这次完整成功已通过菜单与文件测试阶段。

接下来按用户要求先复用现成完整内核。v4 重包关闭持久 Data 和原生 UFS 日志、
导出写入，并移除安装入口。第一次真机尝试出现四项回退菜单，而不是预期的两项
配置菜单，随后显示失败并关机；尚未观察到 XNU 执行。`full` 固件变体会显示传入
的 initrd 信息，在可能的 vendor 前缀后验证精确 FAT 卷，再提供需手动确认的
DarwinBoot 交接。负载发现、加载器交接、内核入口和平台初始化应分别记录证据。
先运行主机检查，再下载大型固件输入。内核探针的模拟测试明确按 16 位读取字符串：
macOS 优化后的旧模拟函数曾错误计算 UTF-16 长度。此类主机模拟失败与固件构建、
真机运行结果应分别记录。

用户提供的 sheng 诊断照片显示，initrd 有效且已保留，但仅约 31.7 MiB，开头是
旧版 LZ4 压缩头，小于输入的 176 MiB FAT。驱动在扫描前返回 `Bad Buffer Size`，
尚未加载负载文件或 XNU。随后仅换 v3 启动头的同内容镜像成功发布完整 FAT，
手动确认后，XNU 已执行到 `bsd_init` 和 `native_source_storage_start`，显示
`root step 3: root manifest rejected`。此前已完成 GPT 和 userdata 首块读取。
这次真实运行通过了用户划分的内核交接阶段，尚未通过根卷挂载和用户态阶段。
完整载荷构建使用 v3；已验收的独立 probe/menu 保持 v4。固定本次镜像作为基线，
先只读诊断根卷清单，再考虑向恢复后的 Android userdata 安装根镜像。

第一次根卷探针尝试同时精简了启动参数，短暂输出后重启进入 Android，未取得
根卷检查结果。下一次对照保留已通过的完整内核参数，只追加
`native-ufs-probe=10`，继续使用 `log=0 data-persist=0`。同时改动大量可选参数
无法单独判断探针分支。预期的诊断 panic 只用于核对元数据，不能证明根卷挂载
或用户态启动。

随后 sheng 的参数对照镜像停在 UEFI CPU 异常页，没有根卷检查字段。应先保留
首个异常标题和运行时模块地址，再判断原因；回溯中的模块名不一定是故障指令
所在模块。此前通过的内核镜像仍应单独保存，本次结果不能作为安装根镜像的依据。

随后补充的首个异常标题明确定位到 DarwinBoot+0x6f084，对应关闭 MMU/cache
之后的 `tlbi vmalle1`。这段加载器代码与此前成功镜像相同，不能据此认定指令
不受支持。下一次隔离对照只把正在执行的交接代码同步到 PoC，保留原有 TLBI
和 MMU 切换顺序。PE 加载时的 PoU 同步与关闭缓存后的执行要求不同；该假设
仍需真机结果验证。

检查：

- 串口行以 `UNIXNU:` 开头。
- 日志报告 entry、driver、patch、ACPI、slice 和 kit 数量。
- 菜单列出预期项。
- 驱动失败显示数量和第一条失败原因。

最小测试：空 ramdisk。UniXNU 使用内置配置并列出可移动加载器。

```sh
./unixnu bootimg --uefi /path/to/Mu-Silicium --dtb board.dtb --ramdisk none
```

继续前，按[二维码抓取步骤](/zh/porting/log-capture#qr-logs)从 **Tools → Advanced Logger**
导出当前固件日志。先按[集成步骤](/zh/porting/log-capture#firmware-setup)准备平台日志模块和插件。

## 阶段 3：负载

目标：UniXNU 读取 `unixnu.toml` 和负载文件。

检查：

- 日志报告配置路径。
- `xnu` 菜单项存在。
- 负载报告哈希与卷中文件一致。
- ADT sidecar 位于内核旁边。

负载错误在 DarwinBoot 启动前可见。

## 阶段 4：DarwinBoot

目标：DarwinBoot 校验内核、ADT 和 trust cache，退出 boot services。

检查：

- 串口行以 `DARWINBOOT:` 开头。
- 打印虚拟基址、物理基址、参数地址、入口地址。
- 打印 framebuffer 基址、宽、高和深度。
- 异常级别为 EL1。
- bootstrap 页表路径到达内核入口。

拒绝时打印 `DARWINBOOT: boot refused: <status>; firmware retained`，固件继续运行并回到菜单。

## 阶段 5：内核入口

目标：XNU 启动并到达平台专家。

检查：

- 内核打印版本和启动参数。
- bootstrap 页表映射内核窗口。
- 平台专家匹配 ADT 根节点。
- `/cpus`、`/arm-io`、`/defaults`、`/options` 和 NVRAM proxy 存在。

内核在视频控制台出现前停止时，会改为显示颜色条。见[颜色条](/zh/guide/debugging#颜色条)。

缺少平台 provider 时 panic 会给出 provider 名称。加入驱动或修正 ADT。

## 阶段 6：存储与根卷

目标：块驱动发布 userdata 分区，卷出现，XNU 挂载根卷。

检查：

- 存储驱动打印链路速度和命令队列。
- 分区方案发布 `OS` 和 `SystemOS`。
- 根卷 UUID 匹配 `root_match_volume_uuid`。
- 内核挂载根卷并启动 `launchd`。

根卷匹配失败时内核没有根设备。检查 UUID、窗口偏移和分区容量。

存储可用后，按[持久化日志步骤](/zh/porting/log-capture#persistent-logs)接入写入器和 Linux 或 recovery 读取器，先手动取回一次日志，再启用定时重启和自动循环。

## 阶段 7：用户态

目标：`launchd` 运行，首个用户进程到达可见状态。

检查：

- `launchd` 从根卷启动。
- Data 卷挂载。
- 显示服务或控制台有输出。
- 启动进度层记录最后检查点。

使用 `boot-progress=2` 和诊断启动参数查看最后完成的检查点。

## 先在 QEMU 验证

按 [QEMU 测试](/zh/reference/qemu)准备 ESP 并运行菜单/payload fixture。
XNU 入口 fixture 需要一起放入 ARM64 内核、ADT sidecar 和 DarwinBoot。
运行前检查选定启动项及预期检查点。

```sh
JOBS=8 bash package/Scripts/smoke.sh
```

安装 QEMU 前置工具后从主仓库运行。该命令检查 UEFI package 场景，将日志和截图写入
`package/Build/Smoke/`。内核工作按 [QEMU 指南](/zh/reference/qemu)的 XNU 入口步骤操作。
外设结果在目标设备上记录。

## 失败隔离

| 现象 | 首先检查 |
| --- | --- |
| 固件无输出 | 启动镜像 header、固件基址和大小、bootloader 日志 |
| 固件有输出，无菜单 | GOP 驱动、UniXNU 路径、`unixnu.toml` |
| 菜单存在，无负载项 | 负载卷标、FAT 驱动、菜单项路径 |
| 有负载项，无 DarwinBoot 日志 | 加载器协议、固件卷中的 DarwinBoot |
| DarwinBoot 拒绝 | 内核 Mach-O、ADT、trust cache、占位符 |
| 内核入口无日志 | 启动参数、串口选择、framebuffer 地址 |
| panic 给出 provider | ADT 节点、驱动静态库、内核开关 |
| 无根卷 | userdata 镜像、UUID、分区容量 |

## 下一步

- [故障排查](/zh/reference/troubleshooting)
- [QEMU 测试](/zh/reference/qemu)
- [启动参数](/zh/xnu/boot-arguments)
- [调试与日志](/zh/guide/debugging)
