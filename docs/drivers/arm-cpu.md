# ArmCpu

Start with the [adaptation procedure](/porting/platform) for board inputs, source changes, build integration and verification order.

ARM64 CPU, GIC and timer driver. Publishes the CPUs, interrupt controller and architectural timer.

| Repository | Maintainer | Scope |
| --- | --- | --- |
| [ArmCpu](https://github.com/UniXNU/ArmCpu) | [UniXNU](https://github.com/UniXNU) | ARM64 CPU, GIC and timer driver. Publishes the CPUs, interrupt controller and architectural timer. |

## State

The catalog targets ARM GICv3 and the ARM generic timer with the selected XNU ABI.

The pinned source provides `armcpu_spi_attach` for exclusive sources,
`armcpu_spi_share` for shared level sources and `armcpu_spi_mask` for direct
masking. Each shared handler acknowledges its own peripheral status.
Boards using these interfaces must retain the matching component revision;
an older ArmCpu archive cannot satisfy their imports.

## Build

The selected kernel recipe builds `build/armcpu/libArmCpu.a` through `component:ArmCpu`. Enable its kernel configuration and verify the GIC/timer/PSCI resources using the platform adaptation procedure.
