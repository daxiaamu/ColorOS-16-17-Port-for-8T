# 小布扫一扫：已有 Camera2 分支与版本属性兼容

## 已验证案例

2026-09-11，Reno15c PMD110 16.0.10.501 供体，目标 8T 工程号 19805。扫一扫实际属于 com.coloros.ocrscanner 16.4.6，不是小布助手主 APK。原始 APK SHA256：

`737d5631034101735dd13bccd94fcd50277c0c6857564fa16e6eb69a6dc5ccc1`

入口为 `com.oplus.scanner.ui.main.CameraActivity`，系统路径为 `/product/app/OcrScanner/OcrScanner.apk`。本工程该文件由 my_stock 提供；路径前缀不能代替实际挂载来源调查。

## 从权限问题中区分 SDK 拒绝

本例 CAMERA 已授权，但日志依次出现：

- CameraUnitImpl：config file not exist
- CameraUnitClient：checkAuthenticationPermission fail
- CameraControl：openCamera, auth failed

同时 cameraserver 没有该包的连接，说明调用在供体 CameraUnit SDK 层被拒绝，尚未到相机 HAL。不能把这种现象当成预览 Surface、驱动或权限缺失，也不应直接让鉴权函数返回成功。

先定位应用内预览工厂和全部实现。本版本同时包含 CameraUnitPreviewImpl 与 Camera2PreviewImpl；工厂 `Lcom/oplus/scanner/ui/preview/b;` 的 `b()Lx6/a;` 根据机型等条件选组件。组件 0 是 CameraUnit，组件 1 是 Camera2。

候选仅在工厂读到 `ro.boot.prjname=19805` 时选择既有 Camera2 组件，保留其他分支与 Camera2 实现。这里的类名、组件编号、属性和工程号都是本版本证据，新 APK 必须按语义重新定位。不要全局伪装供体工程号，也不要替换整套 CameraUnit SDK 来解决一个应用的路由。

## DEX 重建和签名的边界

Windows 反编译文件可能因大小写冲突出现带后缀的路径，逐文件名比较会误报。按 DEX class descriptor 对齐原件和重建件，区分调试元数据变化与语义变化；本例仅上述工厂类有语义修改。清除目标应用不再匹配的预编译缓存，不扩大到全系统。

本例候选 APK 保留了原签名元数据，普通 `adb install -r` 因内容摘要不匹配被拒绝，随后通过受控系统镜像验证。**保留签名块不等于签名有效**，不能声称这是原厂有效签名 APK，也不能把系统镜像上的成功推广为可普通安装、可无缝更新或可干净首启。发布应明确实际信任链和部署方式；不要为此关闭全局签名检查。公开仓库不包含该 OEM APK 或反编译代码。

## 第二个故障：展示文本进入网络协议

Camera2 路由生效后曾出现新的启动崩溃：

`IllegalArgumentException: Unexpected char 0x5927 ... in romVersion value`

SurveyRepositoryImp.getNormalHeader 把 `ro.build.display.id` 放入 OkHttp 请求头，而本次构建刚将中文作者名写入该属性。应先归因于新改动，不把崩溃继续归咎于 Camera2，也不修改 HTTP 库来放行非法头值。

本版 Settings 的 OplusBuildNumberPreferenceController 读取 `ro.build.display.id.show`；技术属性与 UI 展示可以分开。本次最终按用户选择，两者统一为 ASCII：

`KB2000_16.0.10.500(CN01)_daxiaamu_20260911`

MOD 卡片独立保留中文作者名。后续改版本号时检查属性的消费者，不要求所有普通 UI 文案都改为 ASCII。

## 验收与后续更新

- 首次候选已观察到实际拍摄内容及物体识别结果。
- 最终版本镜像重启后，Camera2 预览为 1440×1080，抓取时已输出 945 帧；用户再次确认实时画面正常。
- 重启未首次解锁时，启动非 Direct Boot 入口可能报 Activity 不存在。先检查 RUNNING_LOCKED/RUNNING_UNLOCKED，不能直接认定包丢失。
- 持续出帧而截图近黑，还需核对镜头遮挡和真实画面；本例用户移动手机后确认有内容。连接成功或帧计数本身不能证明画面可用。
- 最终完整 ZIP 的干净安装、覆盖升级尚待单独验收；相机候选成功不替代整包测试。
- 新供体或商店更新时，比较原始 APK、工厂、SDK 依赖、项目属性和协议版本消费者。应用已更新为另一 APK 时不要承诺此工厂补丁仍有效；若官方新增正确兼容路由，验证后退役补丁。
