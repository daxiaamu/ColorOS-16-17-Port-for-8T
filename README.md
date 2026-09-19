# ReSukiSU for ColorOS 16 · OnePlus 8T (kebab)

此分支公开大侠阿木 ColorOS 16 移植项目的一加 8T ReSukiSU 适配源码、补丁、GitHub Actions 和排查记录。目标分支为 `ReSukiSU-ColorOS16`；不据此承诺兼容 9R、其他面板或任意 ROM。

## 从这里开始

- [构建、安装与源码锁说明](resukisu/README.md)
- [适配与故障排查记录](resukisu/docs/adaptation-notes.md)
- [已验证内容、构建版本与限制](resukisu/docs/verification.md)
- [可复核的公开校验记录](resukisu/docs/verification-20260920.json)
- [内核补丁](resukisu/patches/) / [厂商驱动补丁](resukisu/module-patches/)
- [精确 boot 兼容名单](resukisu/compatible_boots.json)

## 自动构建

在 Actions 中选择 **ReSukiSU for OnePlus 8T**，Run workflow 时选择 `ReSukiSU-ColorOS16`。该分支的构建脚本或工作流更新也会触发编译。

产物为带 ReSukiSU 版本、构建号及日期的 TWRP ZIP、包内同一份成品 boot.img、配套官方 Actions 管理器 APK。内核与 APK 使用同一次解析锁定的官方源码提交；不重新编译或重签名 APK。完整源码从锁定的官方仓库获取，仓库保存集成脚本和补丁，不重复托管整套上游内核。

内核版本后缀为 `-daxiaamu+`。编译检查原厂模块信任证书、976 项导入符号 CRC、显示/震动实际编译宏、驱动逻辑回归及 boot 非内核组件一致性。安装器仅写当前槽位并备份、读回校验；只接受核验过的完整 boot 哈希，不跳过校验。

发布工具 `Stage ReSukiSU release assets` 同样选择本分支运行：输入本分支成功构建的 run ID，以及目标为该构建提交的现有草稿 Release。它验证并上传产物到草稿，不代表完成实机验收。

## 当前范围

包含原厂模块 ABI/证书适配、S3908 单击解码、20260916 选定 AMB655X AOD 补丁、1815 RTP 110–112 文件名兼容及 20260920 ROM boot 校验修复。AOD 视觉效果依赖配套 ROM 的 SystemUI 和低档初始化；ROM 已验证的 RAM 触感方案不受内核 RTP 映射修改影响。

20260916 的 rc2/35153 构建已通过编译和离线校验，20260920 为安装器修订。新组合未完成实机验收，不能把参考内核或旧版的测试结果当成本版已通过。详见验证记录。

通用 ROM 移植资料见同仓库 [ColorOS-16 分支](https://github.com/daxiaamu/ColorOS-16-17-Port-for-8T/tree/ColorOS-16)。本分支沿用其公开历史与资料。

## 许可与公开范围

原创构建工具和说明适用仓库 [MIT License](LICENSE)，文件另有声明的除外。`prepare_hooks.py` 标注 GPL-3.0-only；Linux/OnePlus/ReSukiSU 及其派生代码继续适用各自上游许可，不能将根目录 MIT 视为第三方内核的重新许可。上游地址、固定提交及补丁归属见构建说明与 sources.json。

公开内容不包含私钥、设备身份/校准备份、原始设备日志、本地或 NAS 路径。boot 构建输入沿用此前明确授权公开的 Release 文件；未新增上传 ROM、OEM APK 或设备备份。
