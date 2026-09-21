# OS17 原生安装器与 COUI 界面

## 先区分流程与外观

ColorOS 16 的历史方案是替换安装器并在框架中恢复标准 ADB 安装回退。OS17 不应直接覆盖旧 APK：当前 PLK110 安装器已带 AOSP v2 的 InstallLaunch / UninstallLaunch 和原厂 COUI 控件，可复用原生事务模型，再适配共用对话框。

确认供体 APK 的版本、DEX 分布和方法签名。当前版本只有 classes.dex；混淆类名不适用于其它供体。

## 本轮最小修改

- InstallStart 与 UninstallerActivity 的 onCreate：只去掉选择 v2 时对 OEM firewall 模式的附加门槛，保留设备/API 条件、真实调用方和 URI 权限传递。不要全局修改 firewall 状态。
- q1/e 共用 UI 工厂：使用当前 APK 的 h2/b COUI builder、Theme.COUI.Main 和普通 Bottom 对话框样式。不要误用默认 BottomWarning，否则正常安装可能出现警告色。配套切换标题/按钮容器 ID，避免原生 Material 按钮间距代码重排 COUI 按钮。
- 两个 v2 宿主 Activity 使用透明面板主题，面板内容仍使用原生安装模型。原始布局、图片和已有翻译保留；为原生流程补入缺失的简体中文文案。
- 从清单移除只接收 OEM ADB 安装广播的 OppoPackageInstallerReceiver。
- OplusPackageInstallInterceptManager.handleForAdbSessionInstaller：查询 com.android.packageinstaller 是否存在已启用的 oplus.intent.action.OPLUS_INSTALL_FROM_ADB 接收器。没有时返回未拦截，继续标准 PackageInstaller session；有时保留原逻辑。不要无条件跳过整个系统安装检查。

安装器改变 classes.dex、AndroidManifest.xml 与 resources.arsc；框架仅改变 classes2.dex。信任系统分区中保留的旧签名元数据不等于获得原厂私钥重新签名，不把候选当成可独立侧载的正式签名 APK，也不修改全局签名校验。

## 预览中发现的坑

资源表存在 Theme.COUI.Main，不代表压缩后的 R 类保留同名字段。直接 sget 一个不存在的字段会导致 NoSuchFieldError；应核对当前表和 R 类，使用已证实的资源 ID 或实际字段，不照搬旧版数值。

临时预览 APK 加入额外 DEX 时必须连续编号。原包只有 classes.dex，新增类应放 classes2.dex，不能直接跳到 classes3.dex。预览使用本次新建的测试签名，不提取项目私有凭据。

预览页仅证明对话框能显示；不能代替真实安装、更新、失败、取消及卸载流程。实际页面还需检查浅/深色、文字对比、按钮操作和返回行为。

## 验收与持久化

dev37 候选相对已验证基线只改变 system/framework/oplus-services.jar 和 system_ext/priv-app/OppoPackageInstaller/OppoPackageInstaller.apk。两分区内容、inode 和 SELinux 标签审计零差异；镜像均可放入现有逻辑容量。

此处是早期 dev37 候选阶段记录。最终 dev49c 的验收与后继交付状态见下文及[当前状态](os17-current-status.md)。

## 清单缓存与本地化

实机出现过“新 APK 哈希正确，但旧 OEM 接收器仍在 PackageManager 中登记”。此时不能把 ADB 回退改成永久关闭拦截来掩盖问题。历史镜像一直使用相同文件时间戳，会导致包解析缓存继续命中；新清单必须被重新解析。恢复环境无法挂载加密 Data 时，不为了删缓存而格式化数据。

供体没有补齐 AOSP v2 的简体中文资源。本轮合并91条中文，优先复用OS16原生安装器同名翻译，补齐主要安装、更新、卸载和错误提示。apktool整包资源重建会把原厂混淆路径改成长文件名，也会改public标记；不要直接替换整张重编译表却仍使用原厂资源文件。最终只在原始ARSC中增加zh-CN条目，保留现有全局字符串索引、样式跨度及其它资源，按需增加locale配置标记。aapt2资源表语义对比仅增加91行，原有行无删除。未声称其它语言和所有新开发者验证提示已经补齐。

### 已撤回的时间戳实验

不要为刷新一个安装器的清单而更改整个system_ext的构建时间。dev37b这样做后，实机发生重复启动，重启原因为opex_incremental_disable，OPEX更新记录涉及CustCore、NetworkAssistSys、fancyIconLoader等原厂组件。回退dev36扩展分区后恢复正常启动。该实验已撤回；后继dev37c保留既有时间戳，将安装器放到独立PackageInstaller8T目录并同步权限/标签/排除项，以改变该包的解析缓存键。此记录不把所有OPEX内部失败机制宣称为已完整定位，也不通过删除OPEX状态或停用组件掩盖故障。

### 必须保留APK签名块并脱离旧缓存验证

仅复制ZIP中的META-INF条目并不足够。供体使用APK Signing Block；zipfile重打包会丢失ZIP条目之外的V2块。早期dev37构建漏保留该块，旧包缓存一度掩盖问题，重新扫描后候选无法正常启动。dev37d按既有OS17构建流程先zipalign，再保留原始签名块并调整中央目录偏移；核对块完整性、对齐、ZIP CRC和三项内容差异。这保留系统分区信任路径需要的原证书元数据，不是原厂重新签名，也不能通过普通侧载的密码学内容校验。未改动系统签名校验规则。

启动异常同时出现过OPEX重启记录；不能只凭重启原因就认定时间戳是唯一根因。最终候选撤回整分区时间变化，修正签名容器遗漏，并必须在新路径重新扫描、重启及真实安装回归后才能验收。

## dev49c 最终界面与真实事务验收

保留新版基线其它 DEX，仅合入原已审计的 ADB 接收器缺失回退。安装器使用 PackageInstaller8T 路径。深色 app label 对比不足时，Android textColorPrimary/Secondary 实验仍继承浅色值，已撤回；改为从同一 COUI dialog context 取得 couiColorPrimaryNeutral/couiColorSecondNeutral 的 ColorStateList，回收 TypedArray。不叠加旧配色实验、不改变事务检查。

最终 5,513 类语义往返、分区内容/元数据/读回通过。实机新装、更新、卸载、取消以及浅深色截图通过；ADB 新装/更新通过，未签名负例被拒且原版本保留。先前同事务模型的卸载取消、UI 降级拒绝、不可信来源提示另有验证。预览页不替代系统实际事务；独立 Contacts preInflate 异常未被该补丁处理。发布状态以当前状态页为准。

## dev59r2 后台安装卡片

实际安装阶段 stage 4 加入原生 COUIPanelBarView，支持下拉和卡片外点击；短拖动回弹。收起调用 Activity.moveTaskToBack(true)，保留 Session、ViewModel 和结果处理，不调用 cancel/dismiss/finish/abandon。确认阶段仍需用户确认，不把后台安装变成无提示安装。

原 S2 入口可能早于 Fragment attach；预览通过后，真实安装曾因提前 requireContext 崩溃。修订为 Dialog 非空时读取 Dialog 自身上下文。只在实际事务中验收，不能用独立预览代替。

空白处收起后新装完成有时间线证据。真实更新下拉可收起并返回结果页，但该轮更新已在收起动画结束前完成，不能说更新全程在后台；两次过快下拉没有赶上安装，不计成功。前台更新、取消保留旧版本、ADB 更新另有实测，测试应用均已移除。

设备实际 system_ext 与发布候选不一致时，刷入前哈希检查阻止了错误基线；应基于实际设备重建。extract.erofs 会跳过已存在文件，每轮 source/roundtrip 使用独立目录，禁止旧回读目录造成假通过。保持原分区时间戳和标签。该修订已刷入重启，未合入完整 ZIP；不承诺强停进程或重启后恢复原安装界面。
