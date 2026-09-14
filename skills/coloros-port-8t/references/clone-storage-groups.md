# 新建应用分身后数据读取失败

2026-09-14 更新：媒体进程附加组刷新已包含在本轮回归所用的 20260914 发布基线。以下保留原始诊断；后续桌面入口排查没有新增分身补丁。

## 诊断链

分身用户RUNNING_UNLOCKED不代表外部存储就绪。现场多个分身emulated卷为UNMOUNTABLE，ActivityTaskManager在进程启动前以存储未就绪拦截。

读取首次失败日志：FUSE会话onVolumeChecking返回ready=1，随后绑定Android/data时EACCES导致整次挂载撤销。后续重试的ready=0来自残留会话，不能把它当作最初根因。

对照MediaProvider进程的/proc/PID/status附加组：创建分身前启动的进程缺少新用户组。只重启媒体进程后，获得分身的userId*100000+1015及+9997附加组，所有分身卷恢复mounted，用户确认应用能打开。进程组刷新解释了之前必须重启手机的现象。

## 最小候选与边界

本次只修改OplusMultiAppManagerService：createMultiAppUser成功并updateCloneUsers之后、startProfile之前，限定KB2000，解析媒体模块UID并通过原生AMS.killUid刷新进程。已有分身、创建失败路径不触发；不放宽目录权限、不关闭SELinux、不绕过存储未就绪拦截，不删除用户数据。

媒体进程刷新会重建存储会话。新建分身立即启动已验收，但连续创建/删除及并发文件操作仍需回归。合入后另验无ROOT持久化。不要为所有应用启动加入重启或周期轮询；新供体先核对原生生命周期是否已解决，能退役则退役。

本次候选基于已验证闪充JAR，语义比对仅分身管理类改变。两项共用oplus-services.jar，发布应使用包含两项的后继候选或依序重建；分别复制旧JAR会丢失另一修复。

公开技能提供方法，私有工程保存原始日志、构建输入和哈希。参考AOSP存储与媒体实现时仍须核对当前供体，不能把框架版本差异推断为实际设备行为。

## 同样的桌面报错不一定来自存储

后续“第三个打不开”的 Windows 连接应用案例中，三个分身均 RUNNING_UNLOCKED 且存储挂载正常。桌面指向 `com.microsoft.appmanager/android.app.AppDetailsActivity` 合成占位入口；应用 OEM 初始化隐藏了普通 launcher activity，`LauncherAppsService` 因缺少 CATEGORY_LAUNCHER 拒绝启动。直接进入应用 OEM 页面可打开，但不等于桌面入口修好。

已找到应用导出的 `com.microsoft.appmanager.intent.action.START_UP`（DEFAULT category）路径，针对占位入口的框架兼容候选仅编译，未加载、未验收、未发布。不要因此放宽所有应用的启动权限，也不要套用存储修复或宣称第三个分身普遍失效。

## UC 桌面回归与仍需观察的边界

通过原生设置创建三个 UC 分身，逐个点击真实桌面图标验证；没有用直接启动 Activity 代替桌面测试。

| 场景 | 结果 |
|---|---|
| 新建后首次点击、重复打开 | 三个均通过 |
| 各用户 force-stop 后从桌面冷启动 | 三个均通过 |
| 整机重启后从桌面打开 | 三个均通过 |
| 用户删除全部分身 → 重启 → 重新创建和测试 | 用户反馈未发现问题 |

自动测试到达首次隐私欢迎页即停止，没有接受 UC 条款或验证浏览业务。用户曾报告开机初期快速点击时一次瞬时失败，重试即正常；再次连续启动采集及用户重建回归未复现。该问题保持“暂未复现、继续观察”，不能写成已修复。采样中首次点击晚于最后一个分身 CE 解锁约 17 秒，不能据此排除更早的就绪窗口。

上述回归没有加载 Windows 占位入口候选，也没有增加分身代码；相较已交付基线，当时实机仅新增独立的 [QQ 相机能力判断](thirdparty-camera-startup.md)。不要把新增测试证据包装成新修复。
