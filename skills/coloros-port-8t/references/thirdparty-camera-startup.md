# 第三方扫一扫启动慢：缺失 HAL 的同步等待

## 2026-09-14 已验收，待发布合入

QQ 扫一扫修复已加载到 8T，镜像读回、正常启动及用户实际扫一扫验收通过；尚未合入已交付的 20260914 ZIP。没有修改 QQ APK。微信、支付宝未实测，不把 QQ 结果推广为全部应用已修复。

## 先排除权限，再测首帧链路

最初 QQ CAMERA 未授权且 AppOps 拒绝；授权后延迟仍存在。权限基线与后续优化问题分别记录。对齐 Activity START、优化命令、服务等待、CameraService connect 和实际预览，避免只比较 Activity 启动总时间。

本例 `com.tencent.mobileqq.olympic.activity.QQScanActivity` 被系统相机启动优化名单命中。`oplus-services.jar` 的 `OplusCameraStartupOptimization` 连续同步请求两次供体专用服务，其中一次为 `CMD_PRE_OPEN`：

`vendor.oplus.hardware.sendextcamcmd.ISendExtCamCmdService/default`

8T 的 vendor/odm 未声明此 HAL。日志每次等待约 5 秒后返回 NULL，两次累积约 10 秒才继续打开相机。framework compatibility matrix 中出现服务名不等于 vendor 实际提供它。类内另一个 10000 ms 的开机整理回调不是本次超时根因。

## 能力判断优于删除整个配置

本版 `OplusOptimizeRUSHelper.needOptimizeForCamera(String)` 位于 `oplus-services.jar` 的 classes2.dex。在进入原有名单判断前，用 `ServiceManager.isDeclared` 检查上述准确实例；未声明则返回 false，已声明继续原有逻辑。这个查询不等待服务启动，也不会因合法 lazy HAL 暂未运行而误判。它跳过的是无法执行的优化，不是禁用普通相机 API。

新供体需要重新确认方法、同步调用链及所有服务提供方式；不能把某台设备缺 HAL 变成所有机型永久关闭优化的理由。

静态文件是 `/system_ext/etc/sys_camera_optimize_config.xml`；实际 RUS 覆盖来自 `/data/oplus/os/config/sys_optimize_config.xml`，filter 为 `sys_optimize_config`。直接删静态 XML 既扩大影响，又可能被运行时配置覆盖。本次保留配置，语义比对只有能力判断所在类改变，并保留已有闪充和分身修复。

## 发布与回归

- 原包与候选 JAR 解压后仅 classes2.dex 改变；进一步按 class descriptor 比对，区分重组元数据和方法语义。
- 已验收候选 JAR SHA256：`7047fb6ea5c44baf668612ae2059401f6bd4a4886e1a8e7c53f44bebc7d28da3`。
- 候选 system SHA256：`51202afb8eaa930cbf003b4e2cc132f9def37f2e5470034ef134719ea05b78f1`。
- 合入下一完整包时重新验证 QQ 冷启动、原生相机和普通 Camera2 调用；微信、支付宝分别验收。应用内 CameraUnit 鉴权拒绝是另一问题，见 [小布扫一扫](scanner-camera2.md)。
- 第一次候选启动失败实际来自复制构建树丢失链接属性，回退后修正，见 [Windows 构建](boot-and-build.md)。不能把打包失败归咎于能力判断后再叠补丁。
