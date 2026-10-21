# Modern OShare quick-settings migration

## Confirmed cause

The old Port8TQS overlay mapped `custom(com.coloros.oshare/com.oplus.oshare.OshareTileService)` back to `custom(com.coloros.oshare/.OshareTileService)`. OShare 16.10.61 declares the modern service. QSTileListLog showed TileMapper followed by TileFilter: the requested tile was removed. The user also observed later edits failing to refresh after attempting OShare. Diagnose the invalid component before rewriting the editor or resetting its layout.

Inspect the installed service declaration, enabled overlay quick_settings_tiles_static_diff_mapper, and pipeline logs. Distinguish sysui_qs_tiles from the separate control center's oplus_sysui_qs_tiles and layout state. A visible catalog item does not prove the final tile spec survives migration.

## Minimal repair and validation

Remove only the obsolete reverse OShare mapping; retain the native PhoneManager mappings. No OShare APK or SystemUI code modification is needed. Native UI deletion disappeared immediately, re-add appeared immediately, and exit/reopen retained it. User confirmed success. The verified overlay is staged in my_product/overlay/Port8TQS.apk with hash readback, existing filesystem permissions and SELinux entry preserved. No new release ZIP has been built.

Static system overlays reject ordinary APK upgrades. Temporary validation used a bind mount, regeneration of the corresponding idmap with the existing product/public policies, and a SystemUI restart. No layout reset. A temporary mount is not persistence across reboot.

## Donor or app updates

Recheck component names and the migration chain. Retire obsolete compatibility mappings when the native service exists again. Update the build recipe to prevent regenerating the old overlay. Regress add, remove, save and subsequent editing. Publish methods, not proprietary APKs or private logs.

## OS17 C.76 / OShare 17.2.36：r6 已退役旧适配

2026-10-21 实机回归。上文 Port8TQS 为此前版本的历史方案；OS17 使用旧互传时另有专用 Port8TQS17，将现代组件反向映射到旧 `.OshareTileService` 并补充分类。换回供体原版 17.2.36 后，r6 已在构建时删除整个旧版专用 Port8TQS17；实机文件和启用 overlay 列表均无残留。不要为新版恢复这份旧覆盖，也不要误删显示/挖孔或其他仍有效的映射。

本轮核对实际服务为 `com.coloros.oshare/com.oplus.oshare.OshareTileService`。原生 common_mapper 的旧→新迁移、diff_mapper 的 OnePlus→ColorOS 现代组件迁移及“连接”分类均匹配新版声明，不需要修改 SystemUI 或互传 APK。

原生 UI 实测完成：连接分类可找到一加互传；添加、保存后实际磁贴出现；点击图标切换接收状态，点击标签弹出原生接收范围菜单；移除并保存后组件从布局清除；重新添加列表仍有该项，重加后退出重进保留。最终恢复测试前的“仅限联系人”接收模式，保留磁贴。此次没有重启或双机传输，不扩大为这两项的新验收。

`sysui_qs_tiles` 已含新版组件，但独立控制中心的 `oplus_sysui_qs_tiles` 起初未添加，属于两份布局不同，不能据此再增加迁移代码或重置全部开关。原生内嵌范围菜单的 UI 树可能缺文字，翻页辅助描述也可能滞后；用实际截图、布局组件和服务绑定交叉核对。此次确认 r6 已有撤回策略正确，未再改镜像或重打包。
