# 热点打开后立即关闭：spawn 与旧内核（dev61r2）

适用证据：PLK110 OS17 供体、KB2000、4.19 内核。先定位自己的首次失败，不把下述 syscall 或 ELF 偏移作为跨版本通用修复。

## 定位真正的首次失败

现场链路为 dnsmasq 子进程在 execve 前退出 127 → netd 写控制管道 Broken pipe → setDnsForwarders 报 Remote I/O error 121 → Tethering 主动关闭 AP。hostapd 的 beacon 错误发生在关闭之后，不是本次根因。

有界 ptrace 捕获 ARM64 syscall 436：close_range(3, UINT_MAX, CLOSE_RANGE_CLOEXEC=4) 返回 ENOSYS。供体 libc 的 spawn ApplyAttrs 直接退出，没有旧版逐 fd 回退。独立 dnsmasq --version 能运行，不能证明 posix_spawn 链正常。跟踪应覆盖 fork/vfork 子进程，处理子进程 stop 早于父进程事件的次序；设置期限并确保退出后脱离，不留下常驻 tracer。

## 最终兼容范围

[原创兼容库](../assets/netd-close-range-compat.c) 保留原 syscall，仅对 ENOSYS 和精确参数 (3, UINT_MAX, 4) 使用 RLIMIT_NOFILE 上限逐 fd 设置 FD_CLOEXEC。保留原 fd flags；除未打开 fd 的 EBADF 外不吞错误，其他参数/错误保留原返回。它运行在 spawn 子进程，不改父进程描述符表，不伪造成功，不直接跳过 CLOEXEC 隔离。源码 syscall 号针对 AArch64，迁移架构须重新核对。

首轮 LD_PRELOAD 探针通过，但实际 netd 的 AT_SECURE=1 导致 linker 忽略预加载；maps 中没有库。已撤回 init 环境变量方案，不关闭安全执行模式或 SELinux。

最终将 netd 的 DT_NEEDED libnetutils.so 定长替换为 lib8tspawn.so，短字符串尾部补 NUL；兼容库仍依赖原 libnetutils.so，并以 DF_1_GLOBAL 暴露兼容符号。限定在 netd 的依赖链，不替换全局 libc 或原 netutils。该输入中 libnetutils 不属于版本化依赖，代码、程序头和 Android packed relocations 未改变。新输入必须检查字符串引用和版本需求，不能盲用替换或让通用 ELF 重建器重排 Android 重定位。

复现所需工具为 Android NDK AArch64 clang，兼容库使用 -fPIC -shared -mbranch-protection=standard，链接参数 -z relro -z now -z global，SONAME lib8tspawn.so；--no-as-needed 链接同一供体的原 libnetutils.so。不发布 OEM 库。先用[spawn 探针](../assets/netd-close-range-probe.c)检查显式依赖加载，再构建本机镜像。

已核验输入 netd SHA256：6611d03a7866486ecde24f511ad9760221f5ee870dd30f6b42c86e16f3e1f041；输出 69136a6e23d315af81c3307eb843d3e402c7b37f0b4cf6cdb80bb19f3b6ea6e5。任何输入不同都应重新分析。

## 验收与误判

- 探针验证未指定的 fd 不进入 exec、file_actions 显式 dup2 的 fd 保留，父进程 flags 未变。独立探针不能替代服务域测试。
- 重启后 maps 确认库加载，AT_SECURE=1、SELinux Enforcing；dnsmasq 正常启动并接收上游 DNS；热点 TetheredState、lastError=0。
- PC 主动扫描可见热点，WPA3 连接、DHCP、网关 ping、向热点 DNS 查询，以及关闭后重开均通过。
- Windows netsh 可能只返回旧扫描缓存；先通过 WLAN API 触发 WlanScan，再取结果。
- 外部 UDP/HTTPS 探测超时，但手机对专用测试端口抓包未收到流量；PC 同时有虚拟网络接口。不能归因为手机转发故障，也不能宣称外网上网已通过。测试必须证明实际走热点接口，不能借用有线网结果。
- 测后删除临时连接配置、恢复 PC 无线电和手机热点原状态，关闭临时 ADB Root，保留原 USB 调试选择。

该修复已刷入重启，未合入完整发布 ZIP。关闭调试入口不等于 boot 已变成 NoRoot。第一轮无效预加载候选不得合入。
