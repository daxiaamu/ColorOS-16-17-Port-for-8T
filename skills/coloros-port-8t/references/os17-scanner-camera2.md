# OS17 小布扫一扫：应用修复与系统候选

17.1.13 的实现是 CameraX，不是 OS16 CameraUnit。原 APK SHA256 为 40315183b8892090d1da91b7ffdbe93622135c16a6dfb5be74a3280aca819fde。

CameraRepository 枚举后，CameraSizeSolution 从逻辑后摄选尺寸，而 CameraX 绑定 DEFAULT_BACK_CAMERA，精确尺寸选择失败，出现 No available output size 和黑屏。dev58 的 KB2000 专用 APK 常量修改复用既有默认后摄尺寸路径；持久安装、重启、冷启动后已有预览及分析帧，并人工查看非全黑截图。未测试扫码识别、物体识别或拍照。

## 容易踩的坑

- 同版本 data 更新会遮住修改后的系统 APK。核对 pm path、UPDATED_SYSTEM_APP 和实际哈希；现场用保留数据的卸载更新恢复系统版本。不要默认清除数据或停用全局签名检查。
- 保留原签名元数据不是有效 OEM 重新签名，不能按普通侧载 APK 分发。
- 软件商店更新会覆盖 APK 修复。用户已要求寻找系统侧方案，因此 dev58 只保留作对照候选，不视为最终可合入方案。
- 原生 getNumPhysicalCameras/辅助相机资源存在，不代表该 Camera2 调用链使用它。不能发布无效的资源补丁，也不能修改多个应用共用的相机数量值。
- Windows 解包目录曾折叠 24 个大小写冲突路径，候选被拒绝。TAR 保留精确路径，但 TAR 构建还需明确 SCHILY.xattr.security.selinux；--file-contexts 不能想当然视为已应用。逐路径内容、inode、链接和标签要独立审计。
- 不为小幅容量增长额外去重资源；此轮用户明确允许增加容量。设备专属 extent 方案不能写成通用硬编码扩容脚本。

## dev60 系统候选：未刷入、未实机验收

原厂 APK 已恢复为 data 更新，用作黑屏对照。系统候选在 CameraManager 的 getCameraIdList 与 getCameraIdListNoLazy 返回前，仅对 KB2000、com.coloros.ocrscanner、默认 deviceId=0 且真实列表包含 0/1 的情况限制枚举为这两个真实镜头。其他应用、设备与异常列表不变。目标是复用应用自身尺寸回退，不伪造镜头能力。

离线回读 6922 类，仅 CameraManager 变化；按成员身份重编码 hidden API 表，保留全部 84631 个既有成员标记，新增私有方法按候选策略标记。分析用隐藏 hidden-API map 类型的 DEX 绝不可部署。classes2.dex 改动后删除过期 framework.jar.fsv_meta，并验证其他文件和分区元数据。

这只证明候选构建正确，不证明能开机或修好预览。该候选尚未获得本轮所需刷入授权；不得把更新技能的请求当成刷机授权。后续应把补丁重放到当时实机最新 system 基线，不能直接刷旧 dev60 整分区丢掉后继热点修复。应用更新不会直接替换 framework.jar，但新版调用路径仍可能改变，必须复测原版 APK、原相机与 QQ。
