# RamBlock

Start with the [adaptation procedure](/porting/platform) for board inputs, source changes, build integration and verification order.

Sparse RAM-backed block storage with optional persistent backing callbacks.

[Source repository](https://github.com/UniXNU/RamBlock).

RamBlock publishes the Data image as a block device. Its persistence interface uses native_ufs_store callbacks; the board supplies the storage and reset policy.

The pinned direct Data implementation serializes overlapping write ranges and
flushes while allowing independent reads. It exposes `native_data_io_*` and
`native_data_flush*` counters for board boot diagnostics. Keep the catalog
revision and gitlink aligned with consumers of these interfaces.

## Integration

The catalog records implementation scope, hardware and OS requirements, board dependencies, revision, build stage, outputs, and runtime identifiers. The selected profile orders build commands by dependency.

```sh
./unixnu build kernel -D /path/to/device
```

[Component catalog](/reference/components)
