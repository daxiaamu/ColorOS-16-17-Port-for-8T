# MOD、主题、互传、无线能力与20分身

## 原生设置与关于卡片

复用OS17原生Preference和视频渲染接口，不能照搬OS16方法寄存器布局。本次在方法返回前插入钩子时，原方法已经覆盖p0/p1，触发VerifyError；在入口用新增局部寄存器保留引用，检查所有分支与寄存器类型，再做DEX语义往返和真实ART构造测试。

关于卡片曾出现白色遮罩：OS16带mask视频被无条件优先选择，而OS17非confidential渲染路径不处理mask。按原生isConfidentialWallpaperProduct限制这条视频选择分支，两份资源保留给各自消费者，不全局伪造confidential产品。

MOD作者列表有代码不代表有图标：逐项验证assets路径、PNG内容及透明度。高级重启适合普通setItems菜单，保留确认及重复执行保护；改变UI不等于所有重启目标已实测。标题/图标/菜单的后继候选状态见[当前状态](os17-current-status.md)。

版本展示在实际被About读取的display属性加入daxiaamu和YYYYMMDD；同一构建使用同一日期，不篡改OTA身份/fingerprint来达到展示目的。全量重建入口也要修，否则手工改候选会在重建时丢失。

## 无线充电能力统一纠正

8T没有供体的无线充硬件。Settings、SystemUI、Battery分别读取PackageManager/AppFeatureProvider的共同能力`oplus.power.onwirelesscharger.support`。本次从my_product的permissions公共feature及extension下通用/Battery app-feature中移除该能力，并清理无线线圈等专用声明，保留`oplus.hardware.wired_reverse_charging`。

重启后核对pm feature、原生Battery服务禁用无线反充组件、设置列表及磁贴编辑列表。比逐个改UI和手工删除用户磁贴更一致；不能仅查一个XML就说所有消费者都已更新。

## 一加互传：磁贴与分享是两条链

OS14硬件兼容OShare14.6.1保留，versionCode为2140000000，足以阻止常见较低版本覆盖，但不是有符号int最大值2147483647，也不保证所有安装策略不能替换。APK内容变动后的原签名元数据不代表有效OEM签名，不作为普通签名APK分发。

磁贴：核对OS17原生“连接”分类资源，将现代组件映射到实际存在的`com.coloros.oshare/.OshareTileService`。验收添加、删除、再次添加、退出编辑并重开后的保持，不覆盖整个用户磁贴布局。

分享：仅Activity可resolve、服务可绑定仍不足。本次国内IntentResolver被export分支挡住，同时新客户端调用旧服务没有的多回调接口。对精确版本重定位四个入口：

- registerMultiCallback/unregisterMultiCallback委托旧单回调实现。
- 国内Chooser重建tab时加入原生显式OShare目标。
- addOShareResolverInfo移除不适用的export限制并去重，保留请求、策略和Activity解析检查。

保留URI读取授权和真实请求类型，不增加泛化SEND过滤器来制造虚假入口。7041类语义往返、资源未变、ZIP/对齐、镜像/实机哈希通过后，用户确认分享入口可用。磁贴成功不能替代分享验收。

## 主题与精选服务

栏目缺失先查安装源、主题资源闭包、索引与加载条件，不默认删除在线服务。补入OS16山之道Nature05使新目录出现第4个条目；候选只删除该旧条目及空组，保留新版3个和用户当前选择，不盲删所有同名资源。尚需刷后数量验收。

“精选服务数据加载异常”在本轮重新从桌面进入时正常并可打开详情，未复现；没有清数据或改网络，不能宣称已修复原因。不要用权限被拒的直接Activity启动取代受保护的原生入口。

## 分身20

OS17原生分配模型仍为999-index。只调整OplusMultiAppConfig.getMaxCloneUserNum到20，并使framework和service识别范围下界均为980，保留原上界999与配置检查。979应拒绝，980/989/990/999通过。不要只改菜单数值、扩大普通用户配额或直接复活OS16未复现的存储修复。

DEX039/hiddenAPI信息应保持；分析时为反编译移除的hiddenAPI表不得回填ROM。本次采用方法锚定的字节修改并更新校验，变更JAR的旧完整性元数据不能原样保留。设置显示“最多20个”和边界探针通过，不代表20份应用全生命周期都已验证。
