# OS17 原生相机拍照退出：旧 JPEG 服务权限

## 根因与最小修复

预览正常而按快门后 native 崩溃；libAlgoProcess 中 JPEG 服务句柄为空。算法库与既有底层相同，不能因 NULL 崩溃就替换算法库或吞掉返回值。取证发现新的 priv_app_36 域未获旧 JPEG HAL 的查询及 Binder 双向调用权限。

在 vendor 普通与 debug CIL 同步补齐三项：priv_app_36 查询 vendor_hal_camera_postproc_hwservice；priv_app_36 向 hal_camera_default 的 Binder call/transfer；hal_camera_default 向 priv_app_36 的回调 call/transfer。维持 Enforcing，不修改相机 APK。

Android init 参数的策略编译通过。启用 neverallow 的基线与候选各有 338 个既有诊断，归一化后无新增或消失；不能写成“全部 neverallow 检查通过”。分区回读、标签与内容审计通过。

## 验收

dev65 重启后连续后摄拍照及前摄拍照成功，JPEG 能完整解码；QQ/扫一扫持续出帧。普通应用通过 ACTION_IMAGE_CAPTURE + EXTRA_OUTPUT 获取前后摄结果通过，临时探针与测试媒体已清理。不等于所有滤镜、录像和第三方应用全量验收。

## 收窄权限的评估

priv_app_36 是共享应用域，三条规则不是包名级隔离。现有 opluscamera_app 映射针对 com.oplus.camera 及 oplus_app 签名身份，而设备运行 com.oneplus.camera；不能只更换包名匹配就认为兼容。迁移会改变整个相机域及数据访问，需要签名身份、数据标签、全部相机功能和第三方 Intent 回归。dev67 保留已经验收的三条规则，不在整理阶段临时迁移安全域。
