# 硬件接口与实体结果

## HWC：截图正常、实体黑屏

现象包括锁屏/桌面壁纸变黑、状态栏消失、动画异常，而截图和投屏内容正常。强制 GPU 合成仅用于定位，不能据此认定长期方案完成。

历史故障命令 `0x40e0000` 为 Composer 2.4 的 SET_LAYER_GENERIC_METADATA；供体 mandatory EDR/UHDR 元数据导致旧 8T HWC 解析失败，继而 NOT_VALIDATED 和无效 present fence。撤销不适用的 `persist.sys.feature.uhdr.support` 声明后，对照与实体反馈恢复。保留正常 HWC、标准 HDR/色彩管理，不能把此修改等同于所有 HDR 图像增强已验证。

几何适配另行处理：8T 左上挖孔、1080×2400、圆角需匹配实际面板资源；不要沿用供体中置黑圆遮罩。

## AOD 与指纹

普通局部 AOD 正常而全景全黑时，先区分内容绘制和面板状态。历史有效方向是复用官方 OFF → DOZE → DOZE_SUSPEND 分支；全景流程编号 5001/5002/5003 只适用于当时的 SystemUI，不能推广到新版本。

保持显示类型、原生 AOD 亮度请求与退出状态成套匹配。仅改全天支持、强制 GPU、补写亮度都曾无效；固定状态栏 alpha 已撤回。唤醒短暂变暗仍是遗留项，不能通过随意延时宣布修复。

光学指纹录入没有进度时，同时观察 HAL 校准/鉴权结果和实体指纹区域是否发亮。UI 能进入录入页不等于光学照明链路正常。修复后测试实际录入、解锁、息屏和不同亮度；不复制另一台机器的 persist 校准。

## 振动与三段键

- 振动：错误 `oplus.hardware.vibrator_oplus_v1` 声明选择 IOplusVibrator，而实际扩展为 IRichtapVibrator，出现 enforceInterface 协议拒绝。删除错误声明，保留真实 Richtap/linear motor 能力，走现有兼容分支，实体振动恢复。标准 oneshot 成功不意味着所有 prebaked/RichTap 请求成功。
- 三段键：驱动已有档位，缺 `oplus.software.audio.alert_slider` 导致 AudioService 未创建原厂处理器。补真实硬件 feature，复用 Misc HAL，无轮询进程。测试必须实际拨动三档并对照静音/振动/响铃。

## DC 与单脉冲不是同一开关

8T AMB655X 的旧 DC v2 与 OS16 单脉冲调光分开处理。OS16 DCEyeProtectFragment 写 Secure.display_single_pulse_settings_switch，但当前硬件声明不支持 single pulse。旧 display_dc_settings_switch 也因框架 gate/不支持的 SurfaceFlinger 交易路径未生效。

已验证的当前控制点为 OplusDisplayPanelFeatureHelper 的面板 feature **23**：写 0/1，并读回验证；sysfs `dimlayer_bl_en` 显示双值，当前 v2 对应第二个值。不能只读第一位就判定关闭。实际值与版本必须重新核对，未知型号不能照搬编号。

实验开关已置于 MOD，后台单次读写、保存 System.port8t_dc_enabled，通过 Settings 原有 BOOT_COMPLETED 接收器在主用户开机后恢复一次，无 ROOT 命令和轮询守护。默认关闭，开启有低亮度兼容提示；用户后来要求持久化，不能沿用早期“重启需重新开”的方案。

**未解决问题**：seed=101 时低亮度 DC 出现 invalid seed，临时 seed=1 对照能进入 DC 且无该错误，但这会改变色彩处理，不可硬编码。Lineage 的显示模式代码同时处理 seed 与 SDM，需保持完整色彩链路。节点/alpha 生效不等于已测得光学无频闪，也不等于全亮度 DC。

## 耳机铃声不外放

原生 IncomingRingtoneMuteController 被 `ro.oplus.audio.ring_output_setting_support` 隐藏。原生控件写 Global.ring_not_duplicate_output，AudioService observer 同步 sys.oplus.ring_not_duplicate_output 并向 HAL 下发同名参数。

恢复启动时支持属性，同时保留原生控件与策略。只修改 Settings 的可见性不能保证后台 observer 已注册。dev30 已验证参数到达旧 audio HAL；蓝牙/有线耳机真实来电的声音路由仍待验证。不要把已收到参数写成已完成听感验收。


## 小布卡死与唤醒导致整个音频失效

不要把助手页面无响应只归因于应用 UI。历史 ANR 主线程停在 AudioManager.isWiredHeadsetOn，继续追到 IAudioPolicyService 等待；audio policy 未注册，音频 HAL 初始化与声卡监听线程构成锁反转。34 字节的初始化顺序候选可解除等待，但用户仍反馈全机播放和录音异常。因此“页面不卡”不能作为音频修复完成。

正常重启撤销临时 HAL 后仍复现，内核显示 audio_process / LPro00dyn 的 DSP 崩溃。暂停唤醒服务后普通录音恢复有效样本。继续对照原厂文件，发现当前组合存在三层不匹配：

1. 供体使用 com.oplus.ovoicemanager.wakeup，8T 原厂使用 com.oneplus.voicewakeup。现有小布保留 OnePlusPlatformAgent、原厂 provider 与 TrainAgent 接口，可复用而不重写助手。
2. 只恢复原厂 APK 会因供体 JNI 缺少 ListenSoundModel.getTypeVersion 而崩溃。需配套原厂 liblistenjni.qti.so 与 liblistensoundmodel2.qti.so；仅找到同名库不够。
3. 真正使用的 ODM sound_trigger_platform_info.xml 与原厂不同，涉及 DSP module ID、输入输出声道及麦克风配置；Handset_cal.acdb 也不同。只修改 vendor 的同名 XML 没有改变实际路径，不能把无效实验当成模式兼容性结论。

干净启动后，临时恢复原厂 JNI 配套、ODM 唤醒 XML 与 Handset 参数，模型保持 ACTIVE，该轮未再出现 DSP 崩溃，普通录音有效；用户随后确认语音唤醒完成。这是 dev31 阶段的临时状态；后续 release 构建纳入原厂 JNI 与 ODM 配套。用户确认语音唤醒，完整播放/通话/蓝牙回归按新候选单列。初始化锁顺序候选未纳入当前镜像，不因历史文件存在而自动合入。

复用这套方法时：

- 沿 UI → AudioService → HAL → DSP → 模型/校准逐层找阻塞与首个故障；故障恢复阶段的死锁可能只是次生问题。
- 同时检查 vendor 与 odm 的实际加载优先级、库导出接口、模型格式和设备专用校准；只恢复 APK 往往不完整。
- 模型加载、START_RECOGNITION、ACTIVE 状态、真实触发回调与听到回复分别记录。普通录音非零不能证明硬件热词检测正常。
- 持续 DSP 重启可留下失效的 middleware 会话，先停止故障源，再干净启动重测，避免旧会话污染结果。
- 测麦克风可只统计样本数、峰值、能量与错误，不保存音频；声纹、用户模型和原始日志不得纳入公共资料。
- 系统共享 UID 拒绝普通安装时，应恢复正确预置方式和依赖，不关闭全局包校验。
