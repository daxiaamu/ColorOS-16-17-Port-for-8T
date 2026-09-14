# 多分身：容量、生命周期与卸载

## 20260915 已合入范围

当前主线允许同一应用最多 50 份分身，仍沿用原厂 `999-index` 分配，用户 ID 为 950..999。不要复活已撤回的 1000+ 用户方案，也不要将其他 `maxNum` 或系统用户限制一并改为 50。

语义修改点：`OplusMultiAppConfig.getMaxCloneUserNum()`、框架 `OplusMultiAppManager.isMultiAppUserId()`、服务 `OplusMultiAppManagerService.isValidMultiAppUserId()`。需要一起检查实际分配器、用户类型、存储挂载、桌面标识、配额和删除路径；显示 50 不等于可用 50。

初版实测创建到第 33 份时触发 system_server 重启。原因是系统 UID 1000 的 200 个 Job 配额；使用中的分身增加了系统调度任务。已在原有 UID 1000 分支限定调整：

`200 + 8 * max(0, min(actualCloneUserCount, 50) - 10)`

最大 520，普通应用配额保持不变。计数来自实际分身用户，不能用 UI 中配置的最大数量代替。原创辅助方法见 [system-job-budget.smali.inc](../assets/system-job-budget.smali.inc)。只在核实新供体仍存在同一配额和同一调用分支后集成，不能把此公式推广到任意系统。

50 份 UC 创建、代表编号桌面启动及重启后启动已验收；批量创建期间仍可能短暂重新挂载存储，不宣称此窗口消失。源代码修改、候选镜像、发布完整包的验证级别分别记录。

## 主应用卸载后分身残留：尚未复现

用户报告桌面长按卸载 UC 后，全部分身仍能运行，重启后消失。不能等同于之前“已安装但存储未挂载”的失败，也不能凭重启恢复认定同一根因。

20260915 使用无权限、无网络、无私人数据的隔离测试应用做对照：

- 安装器 ACTION_DELETE + 两份分身：即时删除，无需重启。
- 桌面长按卸载 + 一份分身：主用户和分身均删除。
- 桌面长按卸载 + 50 份分身：确认后首次检查约 2.6 秒，主用户及 950..999 全部无安装记录；日志逐用户确认删除。system_server 未重启。

因此本项 **未复现、未追加生产补丁、未宣布修复**。这些测试复用了已有分身用户，不能证明全新用户创建或升级后所有状态均正常。UC 原问题仍缺故障发生到重启前的证据。

## 复用原厂卸载机制

此桌面版本在 `PackageDeleteManager` 内调用系统卸载，未经过替换后的 PackageInstaller。原生 `DeletePackageHelper` 在主包删除成功后：枚举子 profile、核对父用户、检查目标安装状态及系统应用特殊标志，读取 `UserProperties.getDeleteAppWithParent()`，再对合格子用户调用原生 `deletePackageX`。

当前分身为 `android.os.usertype.profile.CLONE`、父用户 0、`deleteAppWithParent=true`。Oplus 服务本身也使用 CLONE 类型创建 profile。后续新供体要核对这些条件，不能直接改成 DELETE_ALL_USERS，避免影响工作资料或正常多用户。

复现时保存主包卸载前后的 PackageManager 用户记录、用户类型/父用户/属性、桌面卸载请求、各用户回调以及 system_server 生命周期。区别“图标残留但包已不存在”与“分身实际仍可运行”。保留现场，不先重启或清桌面数据。之前发现的安装器标志过滤差异并不能解释桌面直连系统的这条路径。
