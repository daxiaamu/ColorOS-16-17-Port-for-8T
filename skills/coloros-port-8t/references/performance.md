# 冷启动与动画性能定位

## 先确认测到的场景

用户投诉的是桌面连续打开/返回应用，尤其冷启动动画帧数不足。force-stop 后要确认进程确实不存在，随后真实点击桌面图标；预热、相册同步、任务栈恢复可能把样本变成 warm。保留启动分类与进程生命周期，不把 `am start` 的 TotalTime 当成动画平均帧率。

固定应用集合、数据状态、亮度、刷新率、温控、充电、网络和执行顺序。每项对照包含重复样本。投屏关闭/开启分别测；scrcpy 的采集、编码和额外合成可增加负载。GPU 频率事件没采到不代表 GPU 空闲。

## 分开测量与诊断

- 低扰动 gfxinfo/frame 数据用于对照。
- Perfetto 用于解释关键长帧：UI/RenderThread、SurfaceFlinger/HWC、BufferQueue/fence、Binder、WM 锁、CPU scheduling/frequency、GPU、I/O、内存回收。
- UI 线程 Running 是实际 CPU 时间；Runnable 常意味着等 CPU；Sleeping 需要进一步找锁/Binder/fence 等待。不能把整段墙钟都称为“计算慢”。
- 对锁争用找到等待线程与持锁线程的工作，不能只见 WM 锁就缩小临界区。
- 对渲染缓冲等待检查消费者、present fence 和是否因 HWC 协议异常导致背压。

历史 PKX 场景出现约 21ms 桌面长帧，其中约 16ms 等缓冲；另有动画线程等待 WM 锁约 47ms，持锁启动工作占 CPU 约 39ms。它们是具体样本，不是全部版本的常量，也未证明同一个根因。

## 已验证的线程修复案例

PMD 桌面壁纸模糊任务在无 Looper 的 coroutine worker 上进入需要 Handler/ImageReader callback 的原厂实现，回调还涉及 EGL 资源销毁。把回调丢到主线程可能破坏 GL 归属。

正确方向是让初始化、渲染、回调与销毁使用现有 `WALLPAPER_TRANSACTION_EXECUTOR` 所在的 Looper；仅对无 Looper 调用增加入口保护，保留原有有 Looper 调用、模糊参数和动画时长。该异常修复通过冷启动验证，不代表所有启动掉帧已解决。

## 模糊开关与缓存

部分 SystemUI 动画档位在类初始化时缓存；属性已经变更但进程未重建时，运行分支可能仍是旧档位。静态白色 scrim、PlatformStaticBlur 与持续采样的实时模糊要区分。检查实际 tint/alpha、blur drawable、animation tier、省电状态和相应 feature。

历史重建 SystemUI 后出现平台模糊层，但没有证明所有控制中心背景持续实时采样。不要仅凭一张截图宣称“实时高斯已修复”。用户明确要求：不额外联动动画档位；若原生没有联动，只在启用提示里说明手动依赖。

## 不接受的替代结论

零帧样本、过期截图、未解锁导致的前台错误、trace 内额外开销，不能用来量化改善。不要通过缩短动画、移除特效、关闭用户同步、提高温控限制来掩盖根因。若确实由用户后台工作或温控造成，提供隔离后的证据，而不是猜测性 boost。
