# ColorOS 16 / 17 Port for OnePlus 8T

面向一加 8T 移植、调试与回归的 AI agent skill，由 **大侠阿木** 的实际移植记录整理。它提供决策方法、已验证案例、失败经验和离线校验工具，供后续移植工作复用。

**本分支为 ColorOS-17：已增加 PLK110 ColorOS 17 → 一加8T的开发移植与实机诊断经验。** 完整开发包曾清装启动，后继分享/性能修复分别实机验证；仍非完整硬件、enforcing或正式发布验收。这不是 ROM 下载仓库，也不是从原厂包一键生成全部修复的构建系统。

## ColorOS 17 专项入口

从 [OS17当前状态](skills/coloros-port-8t/references/os17-current-status.md) 开始；[SKILL.md](skills/coloros-port-8t/SKILL.md) 已加入增量OTA、启动、Super、应用设置、AOD/时钟和性能的路由。使用时检出 `ColorOS-17` 分支并复制整个 `skills/coloros-port-8t` 目录。

> 使用 $coloros-port-8t，先读OS17专项状态，根据已验证的PLK110→8T经验分析这份新供体；重新核对输入哈希、设备与内核，不直接重放旧偏移，也不把候选当成已刷入。

本次 2026-09-20 补充了 [无线回调协议](skills/coloros-port-8t/references/os17-radio-callback.md)、[隔空接听](skills/coloros-port-8t/references/os17-air-gesture.md)、[闪充展示](skills/coloros-port-8t/references/os17-charge-display.md)、[相册/游戏助手漏扫](skills/coloros-port-8t/references/os17-product-scan.md)、[晕动舒缓与音量](skills/coloros-port-8t/references/os17-motion-volume.md) 以及 [安装器失败经验](skills/coloros-port-8t/references/os17-native-installer.md)。已安装组合更新到 dev47，未完成实测与撤回候选单独标记，完整开发 ZIP 仍为 dev24。

## 实机截图

[查看全部 46 张 ColorOS 16 一加 8T 截图](screenshots/README.md)。

## 使用

将 `skills/coloros-port-8t` 整个目录复制到 Codex 的用户技能目录（通常为 `~/.codex/skills/`），在任务中调用：

> 使用 $coloros-port-8t 分析这份供体 ROM 与我的 8T 硬件基线，先建立版本清单，再定位启动或硬件兼容问题。

也可直接把 [SKILL.md](skills/coloros-port-8t/SKILL.md) 交给支持 Markdown 技能的其他 agent，工具调用由所在环境实现。Skill 不继承作者对设备刷写、清数据、ROOT 或备份的授权。

## 已整理内容

- [公开补丁工具与原创兼容片段](skills/coloros-port-8t/references/source-recipes.md)
- [50 分身与原厂卸载生命周期](skills/coloros-port-8t/references/clone-lifecycle.md)
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

以下为OS16历史基线；OS17最新边界以上方专项状态为准。

截至 2026-09-15，主线为 Reno15c PMD110 16.0.10.501 → 8T KB2000，仅接受已支持的官方 ColorOS14/氧OS14 底层固件。20260915 完整包已合入 QQ 相机启动、50 分身配额、旁路供电与高级重启等后继改动，完成离线校验和交付；最终 ZIP 的干净安装和覆盖升级未重新实测。OS17不继承这些OS16结论，DDR5与未复现问题不据此宣称已验证。最新证据优先见 [当前状态](skills/coloros-port-8t/references/current-status.md)。

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

Skill 与截图部分发布重新整理的说明、原创辅助脚本及作者提供的实机展示截图，不包含 OEM APK/ROM、反编译文件、设备校准与身份备份、私钥、原始日志或其他用户媒体。新增的 ReSukiSU 实验构建工作流另见下文；其 boot 构建输入已获作者明确授权在 Release 公开，产物必须区分离线校验与实机验证。

原创内容采用 [MIT License](LICENSE)。第三方项目仅链接并注明用途，其许可独立适用。后续合入第三方代码必须保留对应许可与归属。原始资料中的过时“待修复”与后续结论已按最新证据重新归类，未把研究项目当成已合入功能。

## ReSukiSU Actions

[ReSukiSU 构建说明](resukisu/README.md)：编译配套内核并输出 ReSukiSU TWRP 补丁和其中同一份成品 boot.img（仅打包一次，不生成官方镜像还原包），直接获取固定版本的官方 Actions APK，不重新编译或重签名管理器。工作流核对官方源码提交、APK 整包 SHA256 和签名证书。仅适用于锁定的 ColorOS 16 / 一加 8T boot 基线；未完成实机验证的产物标为测试构建。
