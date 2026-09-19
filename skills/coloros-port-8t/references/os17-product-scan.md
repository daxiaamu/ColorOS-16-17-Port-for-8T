# APK 在 Super 中存在，系统却未注册：Overlay 与嵌套挂载

本次同一根因影响相册 OppoGallery2（dev45）和游戏助手 OplusGames（dev47）。优先读实际 mountinfo 与 PackageManager 状态，不先改 APK 或向 userdata 再复制一份。

## 现场差异

APK 已在 /my_stock/port8t-reserve/system-apps/my_stock/priv-app 下，旧的 /my_stock/priv-app 嵌套 bind 路径也能看到文件；但 PMS 实际扫描的 /product/priv-app 下对应目录为空。Overlay 的 lowerdir 使用 /mnt/vendor/my_stock/priv-app，没有透过另一个路径上的嵌套 bind 自动看见应用。

ls 一个路径成功不是 PMS 已安装。核对 pm path、pm list packages（必要时带 -u）、版本、enabled/stopped、真实 APK 哈希及启动日志；/data/app 的更新实例也可能遮住系统版本。

## 修复

在更高优先级 my_product/priv-app 中分别放原生目录 symlink：

- OppoGallery2 → /my_stock/port8t-reserve/system-apps/my_stock/priv-app/OppoGallery2
- OplusGames → /my_stock/port8t-reserve/system-apps/my_stock/priv-app/OplusGames

复用现有 Super 中的完整应用目录，不复制 APK，不改版本/签名，不改扫描框架。当前 fs_config 为 root:root/0755，SELinux 为 system_file；以当前镜像元数据为准，重建后回解验证是 symlink，不能留下伪链接文本文件。

Windows/Cygwin 工具链把 symlink 暂存为 !<symlink> + UTF-16LE BOM + NUL 结尾目标，并带 SYSTEM 文件属性；这只是本工具链输入约定，须以最终 EROFS inode 和 readlink 验证，不推广为 Linux 创建链接的方法。

## 本次验收边界

相册 17.8.40：完整回读、重启、pm path 注册与原 APK 哈希通过。实况照片的慢动作编辑仍待选取实际 Live 照片测试；包注册不能证明编辑功能已开启。

游戏助手 10.40.20（versionCode 500400020）：完整回读、重启、包注册和后台进程出现，首轮无该应用退出记录。因锁屏且未指定游戏，侧边栏、游戏识别和工具操作尚未验收。原 APK SHA256 为 bcf551383f09f6c6654d0a01399162af1f01434804f5d397cfced3fb72bb9634。

游戏设置的直接 shell 启动被 com.oplus.permission.safe.SETTINGS 拒绝，应走原生设置/游戏入口，不通过删权限或伪造调用身份测试。首启期间 UIAutomation 曾连接超时，属于采样工具失败，不能归为游戏助手崩溃。UI XML 也可能在动画期间陈旧，操作前核对当前窗口/截图。

此类修复必须重启确认扫描仍成立；后续清装和完整 ZIP 验收单列。软件商店更新通常覆盖 APK 内部补丁，本次仅恢复扫描路径、未改相册或游戏 APK。
