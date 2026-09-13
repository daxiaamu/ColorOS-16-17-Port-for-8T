# 新建应用分身后数据读取失败

2026-09-14：现有分身恢复及新建分身无需重启直接打开均获用户确认。候选临时加载并通过框架重启，尚未进入发布镜像/ZIP。

## 诊断链

分身用户RUNNING_UNLOCKED不代表外部存储就绪。现场多个分身emulated卷为UNMOUNTABLE，ActivityTaskManager在进程启动前以存储未就绪拦截。

读取首次失败日志：FUSE会话onVolumeChecking返回ready=1，随后绑定Android/data时EACCES导致整次挂载撤销。后续重试的ready=0来自残留会话，不能把它当作最初根因。

对照MediaProvider进程的/proc/PID/status附加组：创建分身前启动的进程缺少新用户组。只重启媒体进程后，获得分身的userId*100000+1015及+9997附加组，所有分身卷恢复mounted，用户确认应用能打开。进程组刷新解释了之前必须重启手机的现象。

## 最小候选与边界

本次只修改OplusMultiAppManagerService：createMultiAppUser成功并updateCloneUsers之后、startProfile之前，限定KB2000，解析媒体模块UID并通过原生AMS.killUid刷新进程。已有分身、创建失败路径不触发；不放宽目录权限、不关闭SELinux、不绕过存储未就绪拦截，不删除用户数据。

媒体进程刷新会重建存储会话。新建分身立即启动已验收，但连续创建/删除及并发文件操作仍需回归。合入后另验无ROOT持久化。不要为所有应用启动加入重启或周期轮询；新供体先核对原生生命周期是否已解决，能退役则退役。

本次候选基于已验证闪充JAR，语义比对仅分身管理类改变。两项共用oplus-services.jar，发布应使用包含两项的后继候选或依序重建；分别复制旧JAR会丢失另一修复。

公开技能提供方法，私有工程保存原始日志、构建输入和哈希。参考AOSP存储与媒体实现时仍须核对当前供体，不能把框架版本差异推断为实际设备行为。
