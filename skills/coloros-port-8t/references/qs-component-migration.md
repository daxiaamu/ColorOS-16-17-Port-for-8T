# Modern OShare quick-settings migration

## Confirmed cause

The old Port8TQS overlay mapped `custom(com.coloros.oshare/com.oplus.oshare.OshareTileService)` back to `custom(com.coloros.oshare/.OshareTileService)`. OShare 16.10.61 declares the modern service. QSTileListLog showed TileMapper followed by TileFilter: the requested tile was removed. The user also observed later edits failing to refresh after attempting OShare. Diagnose the invalid component before rewriting the editor or resetting its layout.

Inspect the installed service declaration, enabled overlay quick_settings_tiles_static_diff_mapper, and pipeline logs. Distinguish sysui_qs_tiles from the separate control center's oplus_sysui_qs_tiles and layout state. A visible catalog item does not prove the final tile spec survives migration.

## Minimal repair and validation

Remove only the obsolete reverse OShare mapping; retain the native PhoneManager mappings. No OShare APK or SystemUI code modification is needed. Native UI deletion disappeared immediately, re-add appeared immediately, and exit/reopen retained it. User confirmed success. The verified overlay is staged in my_product/overlay/Port8TQS.apk with hash readback, existing filesystem permissions and SELinux entry preserved. No new release ZIP has been built.

Static system overlays reject ordinary APK upgrades. Temporary validation used a bind mount, regeneration of the corresponding idmap with the existing product/public policies, and a SystemUI restart. No layout reset. A temporary mount is not persistence across reboot.

## Donor or app updates

Recheck component names and the migration chain. Retire obsolete compatibility mappings when the native service exists again. Update the build recipe to prevent regenerating the old overlay. Regress add, remove, save and subsequent editing. Publish methods, not proprietary APKs or private logs.
