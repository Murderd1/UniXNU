# ArmCpu

先按[适配流程](/zh/porting/platform)准备板级输入、修改源码、接入构建并逐步验证。

ARM64 CPU、GIC 和定时器驱动。发布 CPU、中断控制器和架构定时器。

| 仓库 | 维护者 | 范围 |
| --- | --- | --- |
| [ArmCpu](https://github.com/UniXNU/ArmCpu) | [UniXNU](https://github.com/UniXNU) | ARM64 CPU、GIC 和定时器驱动。发布 CPU、中断控制器和架构定时器。 |

## 状态

组件目录指定 ARM GICv3、ARM 通用定时器及选定的 XNU ABI。

固定源码提供独占中断注册 `armcpu_spi_attach`、共享电平中断注册
`armcpu_spi_share` 和直接屏蔽接口 `armcpu_spi_mask`。共享处理函数各自确认
外设状态。使用这些接口的设备必须保留匹配的组件版本；旧 ArmCpu 归档无法
满足这些导入符号。

## 构建

选定内核配方通过 `component:ArmCpu` 构建 `build/armcpu/libArmCpu.a`。启用对应内核配置，按平台适配流程核对 GIC、定时器和 PSCI 资源。
