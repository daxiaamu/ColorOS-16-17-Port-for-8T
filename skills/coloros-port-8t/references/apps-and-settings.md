# 原生设置、应用依赖与能力恢复

## 四层排查

先确认应用是否被裁剪、Manifest 组件/宿主 action 是否匹配、后台 provider 是否有数据、能力 gate 是否符合硬件。读多个分区配置及运行结果，不能只 grep 一个 XML。

- 主题空页：完整主题商店及缺失接口恢复后可加载。
- 锁屏小组件空列表：恢复快应用引擎后，原生服务返回可用卡片并可添加；无需写死数据库。
- 手表、AI 翻译、备份迁移：依赖包恢复能让已有原生入口出现；data 安装需单独标注，出厂后可能消失。
- 一加专属时钟/计算器：优先匹配 OnePlus 原厂应用变体和品牌来源。不要全局替换所有 PMD/PKX 字符串；硬件代号、指纹、版本和机型各有语义。
- 小布通话：保留真实 Telephony/VDC/平台依赖，限制目标机型 gate；真实通话验收与进入页面验收不同。

## MOD 设置集成

本项目采用 Settings 内部 Dashboard/Preference、COUI 开关/对话框、原生 footer 和 About 卡片组件。入口位于飞行模式上方，功能/关于分组。避免用独立 APP 仿画系统风格。

页面说明写用户需要的行为，不堆砌“重启自动恢复”之类理所当然的细节。复用卡片时检查字体 ascender/descender、includeFontPadding、fallback line spacing 和固定高度；字母 y 被裁切不能只靠整体上移掩盖。

系统应用找回的“安装”最终是二次确认后跳转商店，未上架则明确提示 APKMirror。项目名称点击跳详情，已安装状态按真实包状态刷新。Google 开关依据 Play 商店是否安装；关闭对应卸载。占位 APK 不算激活服务。

OTA 保留关于卡片展示，升级入口按需求禁用。恢复 com.oplus.ota 的展示不等于恢复官方更新路径；逐项确认后台组件、菜单、点击和独立更新入口。

## 原生应用找回的真 bug

原生 AppRecover 只列出可恢复、尚未安装的预置记录。十项都已安装时空列表可能正常；彻底裁剪且没有原 APK/扫描记录的项不会自动出现。

真实 bug 是保留数据卸载后，MATCH_UNINSTALLED_PACKAGES 仍返回 PackageInfo，但 sourceDir 所指 APK 已不存在。后端误走 installExisting，图标/名称读取也失败。修复点是 RemovableAppService/Provider 的包状态判断：检查 ApplicationInfo、sourceDir 和实际文件，再选择原有预置资源与 PackageInstaller 分支。验证恢复后数据仍保留。不要重写清单替代原服务。

## 普通互传与一碰

旧 OShare 为兼容旧 CryptoEng 保留，补新版宿主入口 action/metadata。NFC 一碰涉及不同协议和可信执行环境，已停止；不能因为普通互传成功就标记一碰成功。

接收端只有昵称、没有自定义设备名时，旧 OShare UI 已有 secondaryName 第二行逻辑，传输状态优先覆盖它。调查发现附加 BLE 名称记录只更新已发现的设备；先到达可能被丢弃，身份匹配/解析也可能有差异。**这是候选原因，不是已证实修复。** 必须抓取本机解析链，不能直接开启虚构的 UI gate 或替换整个不兼容新互传栈。

## 相机与高帧率

保留工作的旧 8T 相机；OS16 新相机因 metadata/算法依赖不匹配已停止移植。恢复隐藏项时核对 sensor mode、HAL stream/high-speed configurations、编码器与应用 profile 四层，并检查真实输出帧时间戳。

8T IMX586 公开规格是 4K90；原厂 8T 提供 4K30/60。当前实机高帧率配置含 1080p120/240、720p120/240/480，没有 4K120。AVC/HEVC 编码器声明支持 4K120 不等于传感器能采集。慢动作仅改变回放速度，同样需要真实采集帧；不得把插帧/重复帧/放大输出标为真正 4K120。4K90 也不能只凭传感器规格自动开放。

## 更新后保留的修复

小布回桌面直角只在“问小布”预测返回目标出现时，检查 Launcher 目标窗口裁剪和形变，不能仅改全局屏幕圆角。release 已包含限定目标的 Launcher 候选；更新后重新核验对应路径。

MOD 的本项目主页采用 SettingsSimpleJumpPreference 与原生 summary-vertical 布局，ACTION_VIEW + CATEGORY_BROWSABLE 打开 URL。新 Settings 的布局 ID 须按资源名重新解析，不能照抄旧 ID。

小布通话本地兼容配置与 AI 实景入口分别维护；更新保留应用数据不保证内部/云端 gate 永久不变。不要把每次更新重新改 APK 宣称为免维护方案。
