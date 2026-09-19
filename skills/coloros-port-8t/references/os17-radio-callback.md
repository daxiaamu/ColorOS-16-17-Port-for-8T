# 无线辅助服务：先核对 Binder 协议，再处理回调空指针

适用现场：PLK110 OS17 Java 框架配合保留的 8T 原生 V4 无线服务；dev42 已安装并完成短期运行验证。

## 根因与定位

原生服务反复在回调响应处空指针，并不意味着应给每个解引用加判空。OS17 ISubsysRadio 的 setCallback 使用 transaction 81，保留的 V4 服务要求 98。错误编号使原生服务按另一种载荷解析 callback Binder 对象，触发 protected Parcel 标量读取拒绝；注册失败后，后续响应再解引用未注册的回调。

同时比较三个证据：Java Proxy 请求编号、原生服务导出的 Proxy/Stub 编号、旧 OS16 接口定义与 Parcelable 字段顺序。不能只把 setCallback 的一个常量替换就认定整个协议兼容。

## 修复范围

在 oplus-subsystem-service 与 oplus-subsystem-service-ext 两份框架 JAR 中同步同样的三个类：请求 Proxy 编号映射，以及两个回调 Stub 入口的响应/指示编号转换。

- 共享方法核对签名与线格式。ActionCell 新字段位于旧 size-prefixed 载荷末尾，本次已单独检查兼容性。
- 新版独有请求映射到经检查未使用的高位编号（本次高于 65536），保留生成代码的 UNKNOWN_TRANSACTION/RemoteException 行为；该编号空间不是跨版本保证。
- 未知旧回调返回未处理；保留 Binder 保留事务。不能关闭 Parcel 安全检查来让错协议强行通过。
- 不修改原生库、基带、NV、SIM 锁或射频参数。完整 DEX 往返只允许这三个类变化，其余 ZIP 内容保持。

## 验收与边界

镜像审计、完整回读、重启通过；开机完成后约 310 秒，两实例均收到对应回调，两个原生服务 PID 不变，保留日志中没有原来的回调崩溃或 protected Parcel 错误。

这段观察中双卡 LOADED，不代表间歇掉卡已修复。旧电话正常基线也曾先识别后掉卡；IMS HIDL 注册故障、无线回调协议错误和卡槽报告 ABSENT 是三类问题。继续掉卡应保存时间对应的原生卡状态与框架状态，做卡/槽对照，不能把本补丁当作基带修复。
