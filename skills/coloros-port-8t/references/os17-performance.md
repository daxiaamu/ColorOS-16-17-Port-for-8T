# OS17性能：先修循环故障，再分析真实长帧

先遵循[通用性能方法](performance.md)，再核对本次具体证据。不要把旧OS16 Looper/EGL线程修复按类名直接移植到新桌面。

## 已验证的循环故障

### 语音唤醒

约六分钟1071次`com.oneplus.voicewakeup` Java崩溃，根因为SoundTriggerEngineCompat.attachModule调用已不存在的`ActivityThread.currentOpPackageName()`。使用构造时已初始化的服务Context.getOpPackageName取得归属包名，保留其身份语义，不硬编码包名、不禁用语音服务、不捕获所有异常。

精确匹配唯一调用，完整2362类语义往返，限定classes.dex变化，检查ZIP与镜像元数据。修复后正常启动、APK实机哈希一致，约12分钟同PID且未再记录该Java异常；实体语音唤醒是否能用仍需另验。

### Perfetto

`traced.relay_producer_port=vsock://-1:2010`使旧内核报AF_VSOCK不支持，traced约每5秒退出重启，本地consumer套接字也缺失。清空中继属性，保留原生本地Unix套接字；先临时实测，再固化product build.prop并重启确认。不是关闭追踪服务，也不是伪造内核支持。修复后成功采集trace。

## 采样场景与证据陷阱

桌面切页、设置滚动、打开/返回应用、控制中心下拉、控制中心/通知中心横向切换、桌面/负一屏、息屏/亮屏/滑动解锁分别记录。真正冷启动先确认进程不存在，再点真实图标；首次提示或错误前台出现即排除该轮。

- gfxinfo ring buffer只保留部分帧，P95不是整段动画FPS；必须报告样本数、超阈值和最大帧。
- 本次前后Thermal Status3/0不同；不能把保留长帧数下降直接称为修复提升百分比。
- Perfetto FrameTimeline表为空且部分事件不受支持，用实际slice和thread_state分析，不能说零卡顿。
- 最初约144ms的主线程帧主要在postAndWait，其中RenderThread等待buffer释放约113ms；对齐事件后发现它发生在息屏阶段，不是滑动解锁。
- 分段后真正解锁仍有SystemUI约61–109ms帧，涉及通知布局、CPU运行和调度等待。负一屏每轮重建EGL上下文约19–41ms，最长主线程帧包含大量睡眠等待；尚不能认定存在可安全修复的具体代码bug。
- 负一屏附着桌面窗口：UI树/焦点仍显示Launcher，不能据此断言没打开。结合窗口、图层和用户实体确认。本次补测内部滚动误入搜索页，必须排除；没有负一屏进程帧的样本也不能用于其性能结论。

保留动画时长、特效、用户同步与温控。消除循环故障是确定收益方向，但不自动证明所有动画已流畅。原有subsys_daemon无线回调空指针和单次gpuservice异常仍需独立定位，不因其存在就永久停服务或归因全部卡顿。
