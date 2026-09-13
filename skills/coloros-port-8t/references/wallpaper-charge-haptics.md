# 壁纸资源、闪充标识与输入法触感

2026-09-13：三项已取得用户实机确认，待合入发布镜像/ZIP。输入法 XML 已进入构建树，壁纸和闪充仍为临时加载。临时 bind 不代表重启保留。

## 主题预览壁纸丢失

山之道及已下载主题进入预览、尚未应用时提示壁纸丢失。相对 URI 回退到绝对路径后仍报 ENOENT：`/my_product/decouping_wallpaper/common/wallpaper_group/00_ColorOS15/ColorOS1506.webp`。实际缺失整个 wallpaper_group，不是主题 APK 权限或下载状态。

从同供体 PMD110_16.0.10.501 原始 my_product 恢复完整目录：26 文件、121578751 字节，包括静态图、视频、mask 和配置；临时挂载后用户确认修好。新供体按配置引用检查资源闭包，不能只补第一个报错文件。文件0644、目录0755、root:root、正确 SELinux 标签；保留其它 common 内容，重算 EROFS 和动态分区预算。不要吞掉提示或清空用户主题数据。其它 AI 抠图错误不能因此宣称解决。

## 官方闪充展示策略

参考 KB2000_14.0.0.602 的 OplusBatteryService.getBroadcastDataFromHal、determineCharingMethod、sys_charger_config.xml 和 SystemUI ChargeUtil.showWattage。

- 协议先映射适配器类型/额定功率，再按 adapter/support/isfast 查询 XML。设备能力索引3表示65W，不是实时充电类别。
- 此官方版本0x47为120W适配器，8T取上限65W；0x1C为45W，不沿用其它内核注释中的44W。
- OS14超级闪充类别2/20/25对应OS16类别3；VOOC类别1对应OS16类别2。部分适配器isfast=false仍保留展示，不能仅以此阻断满电显示。
- 原厂UI隐藏低于设备最大能力的功率数值：45W只显示“超级闪充”符合该规则；65W已确认显示“超级闪充65W”。协议标签不等于瞬时输入功率。

候选只改oplus-services.jar中的OplusBatteryServiceFeature。限定KB2000/HAL6/support3及指定getChgConfig参数，原生值为零才补充；保留原生非零值和异常，检查AC online防止拔线残留。未修改充电控制、温控或电流限制。

440项官方策略和8项边界用例实机通过，框架重启及锁屏65W反馈通过。状态栏、流体云完整回归及发布持久化待验。旧65W协议ID列表候选被官方策略替代，不叠加。

## 状态栏颜色补充（20260914，实机待验）

锁屏 chargewattage 来自 getChgConfig(1)，状态栏 cpa_charge_wattage 来自 getChgConfig(4)。原候选仅适配0/1，锁屏65W成功不代表状态栏颜色已正确。

后继候选补充查询4，沿用官方协议映射及65W设备上限，保留原生非零值和既有范围限制。CPA保留45W等低于65W的值，不套用锁屏隐藏数值规则。候选建立在分身刷新修复之上，不能用旧闪充JAR覆盖。

供体颜色分支要求正在超级闪充、CPA功率达到阈值，并受首次API等级条件控制；不要为颜色修改全局首次API属性。满电会退出充电专用色，100%不能作为未满电颜色的验收样本。

110项反编译协议映射检查通过，但尚未加载，真实颜色未验证。后续测试未满电65W、普通USB、拔线和满电，不能将候选标成已完成。

## 输入法振动

原厂包内内核与另一内核均复现。系统effect157–159下发RTP110–112，但1815表对应reserved文件，请求失败。错误打印可能使用另一张表显示fingerprint文件名；须核对真实request_firmware路径及运行内核表，不能凭打印补错文件。旧官方XML也有该RTP映射，不能简单归咎第三方内核或供体XML不同。

仅改my_product/etc/vibrator/effect_waveform.xml三项，复用RAM触感：157→RAM1/35ms，158→RAM7/30ms，159→RAM6/45ms。用户确认恢复，驱动进入RAM路径，无需修改内核。这是兼容触感替代，不承诺与原RTP手感完全一致。XML已进入构建树，但ZIP未重建；实机仍用临时挂载。

## 合入及供体更新

记录资源闭包、框架补丁基线及XML三处差异。新供体原生修复时退役兼容；方法/HAL变化时重新提取策略并跑边界用例。核对构建树、镜像内容/哈希，再做完整安装和重启验收。回归多个主题、65W/低功率/拔线、状态栏/流体云、键盘三档及其它触感。临时ROOT/bind不随无ROOT成品发布。
