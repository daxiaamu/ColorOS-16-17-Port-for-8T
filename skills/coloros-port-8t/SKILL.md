---
name: coloros-port-8t
description: 为一加 8T 移植和调试 ColorOS 提供供体评估与新 ROM 增量适配、APEX/EROFS 启动兼容、硬件与原生设置适配、冷启动性能定位及 TWRP 交付回归方法。基于 ColorOS 16 实测，迁移到 ColorOS 17 时重新验证接口与构建前提。
---

# ColorOS port for OnePlus 8T

先读 [当前状态](references/current-status.md)，把历史事实与当前用户的目标、固件和授权分开。不要把已成功的某一台 KB2000 实验推广为所有 8T 变种均支持。

## 建立本次任务的事实

1. 明确目标机型、当前供体、8T 硬件固件来源、设备身份、内存变种、槽位、解锁/恢复环境及 OTA snapshot 状态。连接多台设备时，每条设备命令显式指定本次授权目标；不能自动选择第一台，也不能沿用本仓库作者的序列号或无线地址。
2. 建立三个不同清单：源文件与哈希、候选修改、当前实机与发布包。文件在工作树里不代表镜像含有它；临时 bind 生效不代表重启保留；增量镜像已启动不代表完整包跨底包安装成功。
3. 先保存可回退的修改前状态。个体校准分区需要单独明确授权，不能加入通用 ROM。无线连接需核对真实硬件身份，而不是只信任 IP。
4. 根据问题阶段选择下方参考；不一次性批量启用供体所有 feature。

## 按问题读取

| 问题 | 参考与工作重点 |
|---|---|
| 供体选择、第一屏/动画循环、APEX 挂载 | [boot-and-build](references/boot-and-build.md)：定位重启阶段，核对旧内核 EROFS 支持 |
| 实体黑屏、AOD、DC、指纹、振动、三段键、音频 | [hardware](references/hardware.md)：能力声明 → 原生分支 → HAL → 驱动 → 实体结果 |
| 小布扫一扫黑屏、CameraUnit 拒绝、版本号导致网络崩溃 | [scanner-camera2](references/scanner-camera2.md)：已有 Camera2 分支、协议属性与重启验证 |
| QQ/第三方扫一扫启动约十秒 | [thirdparty-camera-startup](references/thirdparty-camera-startup.md)：权限基线、缺失 HAL 的同步等待与声明判断 |
| 充电上限或旁路开关无效 | [charging](references/charging.md)：实际电流、停止归属、共存与回退 |
| 冷启动/开关应用动画掉帧、投屏卡顿 | [performance](references/performance.md)：真实冷启动和同条件帧时序 |
| 功能隐藏、空列表、MOD 设置、互传、相机档位 | [apps-and-settings](references/apps-and-settings.md)：依赖、调用链和真实能力 |
| 固化、TWRP 完整包、跨底包安装、公开发布 | [release](references/release.md)：不可变候选与分层验收 |
| 已适配完成，提供新供体 ZIP | [donor-update](references/donor-update.md)：基线索引、差异计划、补丁复用/退役、受影响回归 |
| data 自动预装、split 缺失、TWRP 不识别 data | [native-preload](references/native-preload.md)：真实挂载、PMS 原生扫描与安装时序 |
| 晕动舒缓无点阵、自动乘车不生效 | [motion-relief](references/motion-relief.md)：实际传感器、官方 CMC 协议与设置页状态重置 |
| 主题预览壁纸丢失、闪充瓦数、键盘无振动 | [wallpaper-charge-haptics](references/wallpaper-charge-haptics.md)：资源闭包、原厂协议展示和 RAM 触感兼容；状态以当前发布快照为准 |
| 分身新建后无法启动、重启才生效 | [clone-storage-groups](references/clone-storage-groups.md)：存储附加组、合成桌面入口及重启/重建回归 |
| 50 分身配额、卸载主包后残留 | [clone-lifecycle](references/clone-lifecycle.md)：原生用户属性、系统 UID 配额与未复现边界 |
| 需要追溯实现来源 | [sources](references/sources.md)：查询原始项目并锁定版本 |

For OShare tile add/remove regressions, read [qs-component-migration](references/qs-component-migration.md): retire obsolete overlay mappings before changing the editor.

## 选择修复的顺序

优先纠正不适用的能力声明，随后复用原有兼容分支，再修复已证实的接口、线程或文件问题。确需兼容层时，限定进程与硬件范围，说明错误返回、状态归属和回退方式。不要用吞掉错误、永久强制 GPU 合成、缩短动画或修改温控来代替根因定位。

对每项变更记录：触发条件、输入版本/哈希、修改点、机制、反例、测试、持久化状态、未验证范围。新失败先归因于本次变化和工具链；不要把所有历史实验重新叠上去。

**UI 可见、设置值变化、后台收到请求、驱动状态变化、实体功能正常是不同证据。** 对功耗、显示、音频和帧率尤其如此。截图或 scrcpy 正常不能证明实体屏正常；编码器宣称支持不能证明传感器能输出。

## 新供体接续

用户只提供新 ROM 时，先读私有工程已有的基线索引，默认沿用最近验收的同供体分支和 8T 硬件组合；在本项目工作区索引为 reports/donor-update-baseline.json。路径是项目约定，不是公开技能自带文件。区分已验收镜像与最新交付 ZIP。按补丁账本处理，变化项重新定位，撤回项不复活；缺旧输入或配方时先列出缺项并完成差异分析。

## 公开实现与本地校验工具

新增或重放字节码修复前读 [source-recipes](references/source-recipes.md)。[patch_smali.py](scripts/patch_smali.py) 按输入哈希、方法签名和匹配次数生成变化文件；它不组装、不刷机，也不证明功能正确。

- [donor_delta.py](scripts/donor_delta.py)：只读生成供体清单与补丁影响计划，输入见 [新供体更新](references/donor-update.md)。不应用补丁。

- [`scripts/verify_image_manifest.py`](scripts/verify_image_manifest.py)：对显式列出的动态分区镜像检查哈希、长度、对齐与组预算；拒绝重复分区、逃逸路径和非动态分区。格式见 [release](references/release.md)。
- [`scripts/audit_artifacts.py`](scripts/audit_artifacts.py)：发现伪符号链接、非 ELF 的 `.so`、APK 重复 ZIP 条目和 DEX 头异常。无错误不等于 APK 签名或全部依赖正确。

工具参数错误或未知结果应如实报告。不要在无效 UI XML、零帧样本或未经核对的镜像上继续执行依赖动作。

## 交付

按“已固化且已验证 / 临时实验 / 未解决 / 已撤回”交代结果。资料公开只导出审阅过的说明、原创补丁/脚本和必要哈希，不上传原始工作区或设备数据。ColorOS 17 采用相同诊断方法，但需重新审核每个接口、feature、APEX 和字节码补丁；不直接套用 OS16 偏移和方法体。
