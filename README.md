# ColorOS 16 / 17 Port for OnePlus 8T

面向一加 8T 移植、调试与回归的 AI agent skill，由 **大侠阿木** 的实际移植记录整理。它提供决策方法、已验证案例、失败经验和离线校验工具，供后续移植工作复用。

**当前证据覆盖 ColorOS 16；ColorOS 17 尚未验证。** 仓库名称中的 17 表示后续适配方向，不是兼容承诺。这不是 ROM 下载仓库，也不是从原厂包一键生成全部修复的构建系统。

## 实机截图

[查看全部 43 张 ColorOS 16 一加 8T 截图](screenshots/README.md)。

## 使用

将 `skills/coloros-port-8t` 整个目录复制到 Codex 的用户技能目录（通常为 `~/.codex/skills/`），在任务中调用：

> 使用 $coloros-port-8t 分析这份供体 ROM 与我的 8T 硬件基线，先建立版本清单，再定位启动或硬件兼容问题。

也可直接把 [SKILL.md](skills/coloros-port-8t/SKILL.md) 交给支持 Markdown 技能的其他 agent，工具调用由所在环境实现。Skill 不继承作者对设备刷写、清数据、ROOT 或备份的授权。

## 已整理内容

- [供体新 ROM 快速适配](skills/coloros-port-8t/references/donor-update.md)
- [userdata 原生预装与 TWRP data 修复](skills/coloros-port-8t/references/native-preload.md)
- [小布扫一扫 Camera2 与版本属性兼容](skills/coloros-port-8t/references/scanner-camera2.md)
- [当前状态与验证边界](skills/coloros-port-8t/references/current-status.md)
- [供体选择、首次启动与 APEX/EROFS](skills/coloros-port-8t/references/boot-and-build.md)
- [显示、指纹、振动、三段键与音频](skills/coloros-port-8t/references/hardware.md)
- [充电上限、旁路供电与状态归属](skills/coloros-port-8t/references/charging.md)
- [冷启动、动画、UI 线程和 CPU/GPU](skills/coloros-port-8t/references/performance.md)
- [原生设置、应用依赖、互传与相机](skills/coloros-port-8t/references/apps-and-settings.md)
- [TWRP 打包、回归、发布与回退](skills/coloros-port-8t/references/release.md)
- [参考来源及用途](skills/coloros-port-8t/references/sources.md)

截至 2026-09-11，主线为 Reno15c PMD110 16.0.10.501 → 8T KB2000。r15 候选镜像已在官方 OS13 底层固件、DDR4、B 槽完成手动格式化后的首启、自动预装及正常重启；最新 20260911 完整包已合入晕动舒缓、扫一扫 Camera2 兼容及 super 容量下限检查，完成离线校验与 NAS 交付；扫一扫和版本号已完成候选镜像重启验证。最终 ZIP 整包刷入、覆盖升级及扩容 super 实机仍待单独验收。ColorOS 17 与 DDR5 未据此宣称已验证。

## 供体更新时使用

> 使用 $coloros-port-8t，基于项目最近验收的移植基线适配这个新供体 ROM。先读取本地基线索引，比较旧/新原始输入，生成补丁复用与重新定位清单；保留 8T 硬件底层、增强功能和无 ROOT 打包策略，再完成受影响回归与新包交付。

[更新流程](skills/coloros-port-8t/references/donor-update.md)规定每次验收后保存基线、补丁配方、依赖、工具链及测试证据。只读差异工具用于减少重复逆向，不代替构建和实机验证。

## 离线辅助工具

```text
python skills/coloros-port-8t/scripts/verify_image_manifest.py manifest.json --root /path/to/images
python skills/coloros-port-8t/scripts/audit_artifacts.py /path/to/extracted/tree
python -m unittest discover -s tests -v
```

这些工具只读取输入文件并按需写出报告，不连接手机、不刷机。镜像清单工具只验证动态分区输入的完整性和容量；不能替代设备、槽位、快照和刷后读回验证。

## 公开范围与许可

本仓库发布重新整理的说明、原创辅助脚本及作者提供的实机展示截图，不包含 OEM APK/ROM、反编译文件、设备校准与身份备份、私钥、原始日志或其他用户媒体。也未附未经完整验证的自动刷机脚本。

原创内容采用 [MIT License](LICENSE)。第三方项目仅链接并注明用途，其许可独立适用。后续合入第三方代码必须保留对应许可与归属。原始资料中的过时“待修复”与后续结论已按最新证据重新归类，未把研究项目当成已合入功能。
