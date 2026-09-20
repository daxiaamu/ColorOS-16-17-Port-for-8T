# 默认 Enforcing 与 MOD 持久模式切换（dev54e）

## 先修强制模式阻塞

NoRoot boot 去除 `androidboot.selinux=permissive`，保持原内核、ramdisk、DTB。通过临时启动及正常启动验收后才固化。最终 boot SHA256 `d8ee22c0ea67dace2214e502327652d97162d4f5817bcb4819318cd55da323f6`；没有 Magisk/KernelSU 或主机 ADB 公钥注入。

本轮 Enforcing 卡住 keystore/vold 的根因是 `/dev/ion` 被标成通用 device，阻塞高通 TEE/keymaster/sensors。精确恢复 `ion_device` 标签，复用既有域权限，不凭大量 AVC 建立宽泛 allow。

Oplus `enable_audit` 默认屏蔽内核 AVC，空日志不能证明无拒绝。仅在诊断窗口启用审计，限量抓取；该机 metadata 可用约 11 MiB，不能无限追加。发行前撤回日志读取临时规则、wrapper/watchdog boot、metadata 日志。

## 模式接口与状态读取

- 后端只接受 enforcing/permissive 精确枚举；受限定属性类型的内部属性由 system_app 写，init 以必要的 `security:setenforce` 权限执行。不要让 Settings 直接写 selinuxfs 或暴露任意命令。
- system_app 授权是域级，不是单 APK 专属；这是移植自定义策略，不能宣传成原厂策略完全未改。持久属性加载后才进入兼容模式，不能修复更早的启动失败。
- 前端直接读 `/sys/fs/selinux/enforce` 并区分读取失败与 permissive。初版 JNI 布尔读值失败默认为 false，导致成功切换后三秒被错误回滚；不能用 false 兼作未知状态。
- 本轮仅补 system_app 对 selinuxfs:file 的 read/open，不授权其直接写入或 setenforce。普通 shell 修改该受保护属性的负例失败，内核仍 Enforcing。

SELinux 与 AOD 选择页复用原生 COUI ChoiceListAdapter 卡片。SELinux/AOD/动画行用 `setStatusText1(CharSequence,true)` 放在箭头前；返回页面时刷新真实当前值。高级重启在功能组末尾；动画默认 3、AOD 默认 0，保留已有选择及需重启生效提示。

两种内核状态分别多次采样，并各经正常重启确认保持；最终回到 Enforcing、boot_completed、无 su、双 SIM LOADED。测试当前双卡状态不代表间歇掉卡根因已修复。只读显示、即时切换、持久化和启动默认值分别验收。
