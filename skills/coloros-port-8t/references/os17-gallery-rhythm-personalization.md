# 相册 AI、舒眠与个性化注册

本页为 C.76 供体的一次实机回归。区分本机旧资源组合的修复验证、向最新清单重放和新整包安装；不能直接用旧手机分区覆盖后继版本。

## 新版个性化不出现，旧页面闪退

先查原生设置路由与包注册。本轮 `PersonalizationController.isWallpaperPersonalizationEnabled()` 优先解析 `com.oplus.wallpapers.personal.ACTION_LAUNCH_PERSONAL_WALLPAPER`；新版应用未注册时才回到 UXDesign。新版 APK 存在不代表 PackageManager 已安装。

Wallpapers 重打包遗漏了 APK Signing Block，只保留 META-INF。系统明确报 `INSTALL_PARSE_FAILED_NO_CERTIFICATES`，提示 CERT.SF 声明 v2/v3，但签名块缺失。Python ZIP 重写和 zipalign 不会自动保留该块。

曾对旧 UXDesign 的 PersonalCard 类型转换做局部试验：消除 ClassCastException 后仍只有异常重叠卡片，故撤回。最终修复构建遗漏，保留已有主题 DEX/资源、恢复匹配源 APK 的原始签名元数据与 ZIP 目录偏移；冷启动后新版应用注册，设置自动走原生新版路由。无需改设置跳转、重写旧布局或清 Data。

恢复签名元数据不等于取得有效的 OEM 内容签名，也不能使修改包成为普通可安装更新。优先使用真正原版 APK；本例仅沿用工程既有受信任系统分区兼容流程，不放宽平台验签，不使用私钥。独立验证 ZIP 成员、DEX、16K 对齐、块结构和冷启动扫描。不要把这一例推广为所有“有 APK、没应用”的根因；Overlay 漏扫见 [product-scan](os17-product-scan.md)。

验收需从原生设置进入，核对现代主卡片、灵感主题、壁纸选择及原有三款山之道条目，确认旧临时修改已回退。只看到进程不退出不足以通过。

## AI 消除：私有依赖及 ABI

本轮原版相册 17.10.7 登录、下载官方算法插件后，圈选自制图仍失败。`image_mask_contour` 的 error 83 对应 AIBoost 加载失败：AIUnit 框架尝试 `/odm/lib64/libaiboost.so`，product namespace 不允许，且底层旧库不是所需图像 C ABI。

在 AIUnit 自身私有库目录放入已核对 ABI 的匹配库，并让该加载点使用私有可见库名；不向全局 linker namespace 放行 ODM，不刷供体硬件分区，不替换相册/AIUnit APK。匹配库来源是已验证的 AON 私有 CPU 兼容组合，仍须重新核对导出函数、DT_NEEDED 和实际推理，不能按同名库互换。

本例仅对已固定的 `libaiunit_framework.so` 唯一绝对路径常量做等长替换：库名后NUL补齐，ELF大小和其余字节不变。输入SHA256为 `c8b6bd8ee771359b38ca29dde4d36378631a236f74d2815838338eb41cebef2f`，输出为 `322c3be7bd2ce14418a2eee08f0249d3442973f81676d7c14c776011555b31e3`；匹配私有 `libaiboost.so` 为 `7dde6c63b3b605ab9cde88980b715de43f6afbe38f79eb19c8033f038c434ff8`。不同输入需重新定位，不能照抄偏移或仅凭文件名使用其他 ABI。

验收包括：圈选产生有效轮廓、真实处理返回成功、红圆从自制渐变图中消失、原生完成/AI 标识/另存新图全流程。保留错误传播，不让失败返回成功，不把插件下载完成当推理通过。

## 舒眠：使用已有无前 RGB 的节律分支

先分清设置值、显示服务输出与实体面板。此机仅有后 RGB 33171052，缺少前 RGB 33171001；供体双传感器路径要求两侧队列都有效，因此舒眠开关保存但 sensorDataValid 一直为 false。手动护眼输出能变化，说明不能先认定整个显示通道失效。

原框架已有 `OplusFeatureRhythmEyeProtect` 无传感器节律；护眼 APK 根据能力声明原生选择 comfortable_rhythm 或 rhythm_health。修正 `oplus.product.display_features.xml` 的真实硬件能力，移除：

- `oplus.software.display.intelligent_color_temperature_support`
- `oplus.software.display.customize_comfortable_rhythm_support`

保留已有 `oplus.software.display.smart_color_temperature_rhythm_health_support`。不增加启动脚本或设置桥接，不伪造前 RGB 数据。早先的后 RGB 框架候选未部署，最终框架保持原件。

本轮原生开关 ON 走 rhythm_health、输出 4500K，OFF 恢复 6527K；这些是当时曲线结果，不是应写入系统的常量。保留时段、曲线和用户选择，实体面板观感另行确认，截图不能证明面板暖色。

## AI 修图师：登录与网络对照

官方账号由用户自行登录，不读取凭据。原版相册中 CC 胶片生成、对比、强度与保存通过；细节增强在移动网络停 10%，记录 SocketException closed/reset。改为确认默认网络 WIFI 且 VALIDATED 后，同一自制图、同一细节增强模板返回实际结果并另存通过，没有为此改 APK 或系统。

只能确认该网络条件下通过，不能声称所有运营商/模板都修复，也不能看到一次网络失败就增加机型伪装、忽略错误或长期重试。区分登录、插件、云端任务、图像结果和保存。日志仅保留必要异常类别；请求头、令牌、账号、URL 参数及用户照片不进公开资料。

## 多开后人脸丢失：本轮未复现

用户先录入真实测试人脸，仅记录机主数量为 1。使用无联网测试应用，经原生 UI 创建三份分身，逐份启动；让分身在前台后正常重启，首次解锁前、用户完成密码解锁并重锁面部解锁确认后、再次启动分身后，机主数量均为 1，分身数量为 0。未读取模板或用照片模拟。

这覆盖本机三份隔离分身场景，不覆盖其他设备、特定应用或满配数量。未复现就保留边界，不能称找到根因或添加所谓人脸修复。

测试清理另有陷阱：关联机主的 CLONE 在 `pm remove-user` 返回失败时，可能已经标记 `<removing> <partial>`；`pm list users` 又会隐藏 partial，不能据此称清理完成。仅对本轮新建且确认无其他应用的测试 profile 使用原生移除流程，保留原用户；不强停关联机主来伪造测试。正常重启后核对完整 UserManager 记录、测试包已卸载及机主人脸数量。本轮最终仅原用户保留、人脸仍为 1。
