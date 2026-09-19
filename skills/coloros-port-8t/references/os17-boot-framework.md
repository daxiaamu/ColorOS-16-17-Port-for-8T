# Android 17 与 8T 旧内核的启动兼容

先确定停止阶段：第一屏、bootanimation、system_server重启、开机完成后的硬重置。不要以最后一条日志当作因果。以下为本次已采用的兼容机制，不能直接复制二进制地址到新供体。

## APEX、EROFS 与签名

本次44个APEX容器审计中，com.android.virt内层EROFS特性与8T旧内核不兼容；重建为验证过的legacy格式，分别比较文件内容、inode属性和SELinux标签，再验证payload AVB、容器签名及对齐。7个OPEX内层为ext4，识别文件系统不等于已验证挂载。

临时镜像只读挂载曾受shell/tmpfs标签影响；纠正临时文件标签后成功，不能将所有loop I/O错误归为EROFS压缩问题。兼容APEX只使用本地获授权的签名材料；本仓库不含私钥、证书仓库密码或OEM容器。不同签名层的检查不能互相代替。

保留原APK签名元数据后改DEX不等于有效OEM加密签名。shared UID签名冲突必须核对具体包、已注册签名及现有移植策略；不把关闭全局签名校验当成通用配方。

## BPF 与联网

Android17 tethering/connectivity默认假设新内核能力。按实际功能审计netbpfload、libnetd_updatable、netd.o和service-connectivity：

- 原有4.19 BPF程序的API适用范围会使其在新Android上被跳过；按符号和结构字段核对元数据。本次保留程序指令，调整已验证旧内核程序的适用边界。
- 新的本地网络权限、loopback检查/指标和ring-buffer事件消费不能在缺少所需map/内核能力时照常初始化。
- 兼容路径限制在验证过的8T旧内核/工程条件，其他内核保留原实现。修改能力门槛改变了新安全功能的覆盖面，必须记入发布限制，不能宣称完全等同Android17原生网络保护。
- 服务启动、Wi-Fi扫描、连接、热点、流量统计分别验收；“不再崩溃”不等于联网全功能通过。

## boot control、VINTF、显示和Wi-Fi

| 症状/证据 | 本次处理 | 必须保留的边界 |
|---|---|---|
| vold开机完成阶段进入boot control等待 | 复用经ABI/符号/依赖核对的旧HIDL兼容libboot_control_client，验证slot成功标记 | 不跳过checkpoint提交；最后日志并不证明vold造成重启 |
| 内部问题提示与旧vendor兼容信息 | 对齐实际SELinux映射、VNDK30与现存APEX | 提示消失不等于完整VINTF或enforcing通过 |
| 显示初始化后硬重置 | 供体SinglePulseDimmingSupport=2对8T不适用，改为0，保留其它显示功能 | 这是能力纠正，不是永久关闭全部HDR/EDR |
| WifiChannelUtilization空数组引用 | radioStats为null按零个radio处理，保留aggregate统计及缓存更新 | 不直接返回空结果或禁用Wi-Fi |
| GameGpuControlPanel启动阶段watchdog | QSPM AIDL服务未声明，却进入native waitForService；在profile入口isDeclared检查，缺失返回false，存在走原流程 | 只删feature XML不够；不吞所有异常或停掉GameManager |

## 启动诊断的反例

本次经过日志、syscall、内核重启探针及无诊断包装的对照启动，才把显示能力与QSPM等待等问题分开。ptrace、日志大量写盘、临时init包装都可能影响时序。记录探针存活和正向对照；没有panic记录不是没有重启。

临时自动回recovery有计划超时；明确区分计划返回与自发重启。若设置BCB，先保存原始相关字段、限定修改范围，退出后恢复并回读；不能把诊断boot、permissive参数、探针或自动重启逻辑意外带入交付包。
