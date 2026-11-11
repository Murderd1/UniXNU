# RamBlock

先按[适配流程](/zh/porting/platform)准备板级输入、修改源码、接入构建并逐步验证。

稀疏 RAM 块存储，以及可选的持久存储回调。

[源码仓库](https://github.com/UniXNU/RamBlock).

RamBlock 将 Data 镜像发布为块设备。持久存储接口使用 native_ufs_store 回调，板级提供存储与重置策略。

固定版本的直接 Data 实现对重叠写入范围及刷新进行同步，允许独立读取。
它提供 `native_data_io_*` 和 `native_data_flush*` 计数器，供板级启动诊断读取。
组件目录版本与 gitlink 必须同时满足这些接口的调用方。

## 集成

组件目录记录实现范围、硬件与 OS 要求、板级依赖、源码版本、构建阶段、输出和运行时标识符。所选配置按依赖顺序运行构建命令。

```sh
./unixnu build kernel -D /path/to/device
```

[组件目录](/zh/reference/components)
