# ReSukiSU · ColorOS 16 / 17 · OnePlus 8T (kebab)

大侠阿木 ColorOS16/17 移植项目的 ReSukiSU 适配源码、补丁与 GitHub Actions。本分支仍名为 `ReSukiSU-ColorOS16`，现在每次固定输出16、17双版。

## 自动构建

Actions → **ReSukiSU for OnePlus 8T** → Run workflow，选择本分支。

每次产出五项：ColorOS16 boot.img、ColorOS16 TWRP ZIP、ColorOS17 boot.img、ColorOS17 TWRP ZIP，以及一份共享的官方管理器 APK。文件名带 ReSukiSU 版本、构建号、北京时间日期和 ROM 标识。

metadata 一次锁定最新成功的官方 main 管理器构建，验证签名并将对应源码提交交给内核构建，不重编或重签 APK。共享内核编译一次，两个 package 任务分别按 ROM 基线打包。目前两版解压后的 ramdisk、DTB、header 完全相同，因此 boot 载荷可能字节相同；两版卡刷包的安装校验名单和说明不同。

## 资料

- [双版设计、基线和验证边界](resukisu/docs/dual-rom.md)
- [构建、源码锁及历史修复](resukisu/README.md)
- [ColorOS16 校验名单](resukisu/profiles/ColorOS16.json) / [ColorOS17 校验名单](resukisu/profiles/ColorOS17.json)
- [内核补丁](resukisu/patches/) / [厂商驱动补丁](resukisu/module-patches/)
- [启动失败与硬件排查经验](resukisu/docs/adaptation-notes.md)
- [历史验证记录](resukisu/docs/verification.md)

ColorOS17 最新基线是 `ColorOS17.0.0-port-kebab-20260921-NoRoot-r1`，boot 与20260920 NoRoot r2相同。保留原厂模块公钥、网络ABI、S3908单击、1815触感兼容，AOD使用后继按本轮入场记录panel的累计补丁，不叠加旧v6方案。

安装器只接受各自经核验的boot，备份后仅写当前槽位并读回校验，写入失败回滚。编译与离线校验成功不代表新ReSukiSU组合已完成实机验收。

发布工具 **Stage ReSukiSU release assets** 选择本分支和成功的双版run，以及目标提交匹配的现有草稿Release；验证双boot、双ZIP及共享APK后上传五项到草稿。历史单版run不适用于此双版发布工具。

## 许可

原创工具与说明适用[MIT License](LICENSE)，另有声明的除外。prepare_hooks.py 标注 GPL-3.0-only；Linux、OnePlus、ReSukiSU及派生补丁适用各自上游许可，根目录MIT不重新许可第三方内核。源码从固定官方提交获取，不重复托管整套上游源码。

公开说明不包含设备身份备份、原始设备日志或私有存储路径。构建沿用此前已授权公开的boot输入，不新增上传完整ROM。通用移植资料见同仓库ColorOS-16和ColorOS-17分支。
