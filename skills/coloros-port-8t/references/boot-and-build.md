# 供体、启动和构建

## 分层选择供体

保留目标机的内核/设备树、vendor/odm、基带和对应固件；供体提供较新系统框架与主要应用。供体 CPU 同属高通、大小核数量相同，不能证明它的 HAL/显示/相机协议兼容。

建立新供体分支时保留原始输入，迁移有原文件哈希、机制和实测证据的修复。对框架与 APK 比较类/方法/资源，不能按旧偏移直接修改新文件。本项目后来放弃“任意底包直接刷”，当前要求官方 ColorOS14/氧OS14 并保留底层固件（已取消 OS13 支持）；不要沿用历史全固件包。供体更新使用 [donor-update](donor-update.md) 的差异与补丁账本。

## 识别失败阶段

第一屏 Orange State、退回 fastboot、内核 panic、init 重启、APEX bootstrap 失败、开机动画循环、framework crash 分别定位。收集 pstore/早期内核/init/apexd 信息，核对实际重启原因。开机动画出现只证明经过某阶段；延长固定超时不是普适修复。

本项目首次启动的重要障碍是旧内核不支持 APEX 内部 EROFS feature，日志 `unidentified incompatible feature 2` 后触发 bootstrap-apexd-failed。在恢复环境单独挂载 payload 能复现，先处理格式，而不是删 APEX 或关闭校验。

## EROFS/APEX 处理

对每个 APEX 单独判断是否受影响，完整保留模块内容、标识、权限、SELinux 标签与能力。示例兼容构建参数：

```text
-z lz4hc,level=9 -C4096 -b4096 -E legacy-compress,^xattr-name-filter
```

这些是已用旧内核的参数，不是对所有 EROFS 版本的保证。核对构建工具支持的选项和 superblock incompat 位，再做真实挂载测试。

重建后重新生成正确的 AVB hashtree、项目签名及容器签名，签名之后复查 ZIP 对齐。不能把保留旧签名块当作重签成功。项目私钥留在私有构建环境；公开材料只保留公钥/标识和验证方法（若发布需要）。

PMD 历史审计涉及 33 个容器，其中 32 个需相关处理；30 个输入与此前已验证输入逐字节相同，另两个重新构建。复用依据是输入哈希与语义相同，不是模块同名。数量是历史事实，不能硬编码给新供体。

## Windows 产物检查

- 部分工具把符号链接输出成 `!<symlink>` 文本。如果这种文件被当成 `.so` 打包，会造成 bad ELF、IMS/Atlas 等服务反复崩溃。保留实际链接语义，或采用已核对的同分区 ELF 内容；不能用空文件占位。
- 修改 DEX 时以输入版本为准。本项目原包为 DEX039，旧 smali 默认输出 DEX035 曾导致接口调用失败；对应工具链使用 `smali --api 28`，输出仍需检查。不要把 API28 与目标系统 API 级别混淆。
- 只替换预期 DEX/资源条目，比较 APK ZIP 条目差异集合；旧脚本全量重建可能悄悄覆盖后续修复。
- APK 的 signer metadata 保留，不代表修改后仍有有效 OEM 密码学签名。这是系统镜像中的修改件，不能宣称能当普通更新 APK 安装。
- 固定 EROFS 时间戳可能让解析缓存看见旧包。先核对磁盘哈希与实际运行代码，再定点处理该包缓存，不直接清全机数据。

候选镜像完成后不可覆盖。明确 source → patched tree → candidate → installed → release 的对应关系和哈希；后续改动使用新候选。

## Windows 复制构建树后必须检查链接语义

2026-09-14 案例：`shutil.copytree` 保留了 Cygwin `!<symlink>` 占位文件内容，却把 Windows FILE_ATTRIBUTE_SYSTEM（4）变为 ARCHIVE（32）。本工具链的 mkfs.erofs 因此把根目录 init、bin 等打包为普通文件，候选无法启动；刷写和读回哈希正确也无法发现这种语义错误。回退原镜像恢复启动。

对这个已确认使用 Cygwin 占位链接的工具链，在独立候选树识别 `!<symlink>` 文件并恢复 SYSTEM 属性后重建。不要对普通文件批量设置，也不要在使用真正 POSIX 链接的工具链照搬 Windows 属性方案。最终从 EROFS 直接审计所有路径、类型、mode、uid/gid、链接目标，并按修改范围核对内容及其他元数据。本例 4484 条路径集合一致，mode/uid/gid 全部一致，413 个链接目标一致。

解包目录的 `.fsv_meta` 是工具侧元数据，不能直接算作镜像内文件；以镜像解析为准。修改 JAR 后清理对应过时旁文件，并检查压缩后镜像预算。本例只对变更的 classes2.dex 使用无损 ZIP deflate 9，镜像落入原分区预算；没有裁剪功能。压缩成功仍需验证实际启动。
