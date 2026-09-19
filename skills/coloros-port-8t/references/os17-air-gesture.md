# 隔空接听：入口、Camera2、模型与硬件后端

适用现场：AONService 原厂 APK 不变，8T 硬件配 OS17 模型；dev44 持久修复后，用户确认真实来电隔空接听成功。

## 三个独立阻塞点

1. 错误声明 oplus.software.aon_sensorhub_enable，使原生代码选择 8T 不具备的 SensorHub 路径。移除这个不适用声明，复用原有 Camera2 分支；不另造常驻摄像头服务。
2. JNI 使用绝对路径 /odm/lib64/libaiboost.so。应用 linker namespace 无法加载它；即使允许访问，8T 旧库只有旧 C++ AIBoost_Create ABI，而 OS17 JNI 需要 C AIBoostCreate。仅修权限会在空 dlsym 结果上继续失败。
3. 匹配的 OS17 库能加载后，QUALCOMM_NPU 后端仍崩溃。隔离模型测试表明 CPU 路径可初始化和推理，再用原生 com.aiunit.aon.is_cpu_support_only 能力选择 CPU。

## 最小持久方案

从 A.72 → A.73 → OS17 的经源/目标哈希验证的增量还原结果取得匹配 libaiboost.so，仅放 AONService 私有 lib/arm64 目录。不要刷入供体 ODM，也不要全局放宽 linker namespace。

原 JNI 中唯一匹配的 /odm/lib64/libaiboost.so 字符串改为 libaiboost.so，在原分配空间内补 NUL；核对唯一性、长度与差异范围。加入上述 CPU-only app feature。APK/DEX 不改，模型不替换，用户开关不强制覆盖。

匹配库身份锚点 SHA256：7dde6c63b3b605ab9cde88980b715de43f6afbe38f79eb19c8033f038c434ff8。换供体要重验 ABI/模型，不按这个哈希盲目替换其它版本。

## 分层验收

隔离 CPU 模型为 1 输入/7 输出并可运行，不能证明手势识别。进一步在原生流程观察 Camera2 前摄帧、模型初始化与推理、退出后 CameraService 无残留客户端、息屏/退出的释放行为及 AON 无崩溃。

本次已完成以上原生运行检查，用户另行确认真实来电成功接听。没有独立保存真实接听事件的完整日志，不能将用户反馈伪写为日志证据；不把接听验收外推为隔空滑动/暂停全部可用。来电由用户发起，不由 agent 代拨。

临时 CLI、模型副本、探针 APK 清理后仍保持功能。完整 ZIP 仍需重新合入，已刷入增量不自动更新旧包。
