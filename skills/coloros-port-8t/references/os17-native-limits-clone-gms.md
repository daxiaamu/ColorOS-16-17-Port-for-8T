# 原生数量策略与分身 GMS 归属

> 2026-10-31 更正：后续新包现场发现本轮两个改动APK在重打包时遗漏ZIP外签名块，导致SettingsProvider拒载及启动循环。功能代码保留，构建配方补齐签名元数据并增设最终镜像预检，普通NoRoot启动通过。此前保留Data的验收没有覆盖重新扫描场景；详细根因与边界见[签名块遗漏](os17-apk-signer-bootloop.md)。

此页记录 C.76 后继 r7 增量实测。它先于 20261026 合包完成，不能把旧手机资源组合或旧 r6 ZIP 当成已包含这些修复。参照[当前状态](os17-current-status.md)确认交付层级。

## 自启动、最近任务锁定数量

先从 AppFeatureProvider 的实际返回追到原生解析器。本轮两个键 `com.oplus.battery.autostart_limit_num`、`com.android.launcher.recent_lock_limit_num` 原值按 RAM 档提供 8/15/20 等限制；12GB 本机落在15档。Battery 缓存解析结果并在原生自启动列表计数拒绝新增，Launcher 的 OplusLockManager 将上限传给锁定管理器。

修复仅调整实际优先加载的 my_product `com.oplus.app-features.xml` 中对应设备范围的策略，不改 Battery/Launcher APK，不给用户应用自动开启权限或锁定。解析器没有“无限”哨兵，0/负数会回退或拒绝，因此采用其可表示的最大正整数，而不是伪造 UI 成功。

20个无联网及私人数据权限的测试应用，经原生 UI 逐个启用自启动、锁定最近任务，重启后逐项检查通过；原有两个用户自启动选择在清理后保持。这是20项实际验证，不是所有容量或无限数量的证明。

## 分身 Google 开关与包状态不一致

先同时记录设置归属、GMS明确包状态及原生验证代理。旧互传适配移除了 `cn.google.services` 品牌特征，而原厂 SettingsProvider 用它决定是否初始化控制设置；真正的 `oplus.software.disable_cn_gms` 能力仍在。初始现场出现主用户禁用、分身启用，设置缺失，GMS 的域名验证初始化抛 SecurityException。

最终修复分为原生链路中的四处，不增加另一层读取拦截：

1. 用真实控制能力初始化 Google 开关；已有0/1保留。缺失时优先保留明确 ENABLED/disabled 状态，DEFAULT/未安装才使用原厂默认；复用原有升级初始化，不改数据库版本或重置设置。
2. 将 SettingsProvider 硬编码999的继承判断改为实际分配器980..999和原生分身判定。原厂谓词只有下界，不能直接覆盖所有1000+用户。新分身还会生成本地默认值，因此在原有 `MULTIAPP_SETTINGS` 共享列表补充该开关，保留原四项及白名单寄存器值，避免默认值遮蔽父用户。
3. OplusExSystemService 不再只处理运行中的999，枚举机主真实子profile，核对CLONE类型、父用户与分配范围，沿用原包状态写入方法；初始化消息完成后用同一路径对齐一次缓存。保留功能、权限和包可用性检查。
4. 可选GMS包状态变更后，原PackageManager仍缓存旧域名验证代理。只对机主、持有原生代理权限的目标，在原状态写入成功后重新走选择器；组件实际改变才用原厂工厂重建代理并重新安排待验证项，串行选择并恢复Binder身份。

不改 GMS APK，不放宽 DomainVerificationEnforcer、调用者UID或代理工厂校验，不清账号，不吞掉初始化异常。已撤回的配置重定向实验不应叠入。

## 验收与边界

- SettingsProvider、ExSystemService、services.jar各自只变化一个DEX；全类语义回读、hidden API保留及ART硬校验通过。
- 独立设置测试覆盖机主、非分身、边界及1000+用户，明确0/1不变；未读取机主设置文件或账号。
- 无ROOT冷启动能迁移“开关缺失、主用户关、分身开”的现场；原生Google UI开关与关闭警告保留。
- 新建997分身即时启动，已有分身本地0、父用户1的反例经r7原生继承恢复；四用户0→1→0热切换时设置与实际包状态一致。
- 使用真实应用UID验证代理权限：启用时GMS代理可调用，关闭时GMS被拒绝、AOSP代理可调用；无权限测试UID始终被拒绝。不是让错误静默。
- 原生停止关联机主的profile被拒绝，未强行停止，故不宣称停止态实测；Google账号登录与云服务未验收。测试包、新测试profile清理，已有用户选择保留。
