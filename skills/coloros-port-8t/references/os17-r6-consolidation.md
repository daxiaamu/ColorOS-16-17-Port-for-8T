# r6 合版：文件系统闭包与真实 NoRoot 验收

2026-10-21 整理，适用于 20261020-r6 合版。功能机制分别见[互联](os17-oshare-crypto-nfc.md)与[小布菜单](os17-breeno-menu.md)；这里记录会改变构建或验收判断的工具陷阱。

## 从基线重建并审计最终消费内容

最终框架从原始基线重新构建，保留两个经过验证的现有方法改动与独立助手 DEX；不在带诊断日志的旧候选上继续叠加。保留 87,888 个隐藏 API 标记并回读 6,401 个类。兼容资源属于私有输入，不能上传包含它们的 JAR/DEX 或二进制补丁。

Windows 解包可能丢失仅大小写不同的文件路径，文件总数不足以排除问题。使用保留条目身份的 TAR 构建流程，对碰撞路径单独处理；回解逐项比对完整路径集合、内容、符号链接、硬链接等价关系、uid/gid/mode、capabilities 和 SELinux 标签。

Windows libselinux 曾拒绝含中文自然铃声文件名的字面 UTF-8 正则；仅在构建用 file_contexts 中采用等价的 ASCII UTF-8 字节转义，保留真实文件名和标签。这是构建工具输入兼容，不是运行时权限补丁。保持旧 4.19 内核支持的 EROFS 压缩与 incompat flags。

本轮只重建 system、my_stock、my_product，其他 12 个分区保持原输入。退役旧互传专用资源映射，其余 68 个 overlay 内容保留，核对实际挖孔与状态栏避让。不要通过临时挂载的目录名或占位文件判断资源存在。

## ART 检查与冷启动

- RAM 替换 JAR 的哈希正确，不证明 zygote 已加载新类；旧预编译 boot.art/oat/vdex 仍可能被消费。
- `odrefresh --check` 可能删除不匹配产物，不是完全只读。检查后才做的备份可能仅含 cache-info 与空目录，必须清点内容，不能称为完整编译缓存备份。
- 本轮返回 79 表示需要编译，`--force-compile` 返回 80 表示编译成功；仍需核对真实 cache-info、源 JAR 与消费进程。状态码按实际工具版本复核。
- 临时 noimage 参数只用于对照，恢复原 `-Xss3M` 后继续验证；不进入发布。不得强制设置 odsign 验证成功，也不读取其签名密钥。
- `stop/start` 后旧 `sys.boot_completed=1` 可能误导。检查新的 system_server 及 AMS 实际 ready 状态；物理冷启动再比对 boot_id。

r6 完整安装后，两次真正 NoRoot 启动分别验证原生 ART 重建与缓存复用，odsign 验证为 1、Enforcing、普通 shell、无临时绑定或诊断 VM 参数。晚启动 odsign 的临时 ROOT 会话结果不等于正式冷启动结果。

## Recovery 自动化仍保留原包检查

本机 ORS sideload 没有进入预期模式，不应在未进入时继续发送安装流。后续将完整 ZIP 存入 Data，校验全部 SHA256 后，在 Recovery 用原样 update-binary 和标准参数执行；不删环境、底层、容量、snapshot、电量检查，也不改当前槽策略。35 项载荷及完整写入范围读回通过，不等于再次验收了图形安装入口。

ADB 的 stdout FD1 可能是不能经 `/proc/self/fd/1` 重开的 socket，导致 ENXIO；脚本使用可继承且可重开的 UI FD，例如本轮 FD3。不要为绕过输出错误删除安装器检查。

Recovery 早期 USB/MTP 初始化曾使首次推送中断。当时尚未开始刷写；等待连接稳定后仅删除自己的不完整文件，重新传输并校验完整哈希。不重置全局 ADB server，也不把传输完成百分比当作完整性凭据。

本轮未格式化整机 Data，仅撤回小布更新以验证内置版。完整双清、另一槽位、双机一碰/收发的重新实测都需独立记录，不由本机初始化和完整读回自动推定。
