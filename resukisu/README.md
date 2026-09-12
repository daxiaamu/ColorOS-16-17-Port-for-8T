# ReSukiSU for the ColorOS 16 OnePlus 8T port

Actions outputs the finished ReSukiSU boot image, the unmodified official ReSukiSU Actions arm64 APK, and one ReSukiSU TWRP ZIP. The boot image is repacked once and reused as both the standalone download and the ZIP payload; their SHA256 values are checked for equality. Stock boot remains a build input only; no stock-image restore ZIP is produced. Every download filename and public artifact name includes the ReSukiSU version, version code, and build date (Beijing time), for example `ReSukiSU_v4.2.0-rc1_35134_20260912_kebab_TWRP.zip`. One date is shared across all jobs, including builds crossing midnight. The APK is renamed only; its bytes and signature remain unchanged. ZIP-internal `images/boot.img` remains the installer payload path. **Successful compilation is not a boot/hardware validation; these are test builds until validated on an 8T.**

## Run and install

Open Actions > ReSukiSU for OnePlus 8T > Run workflow. Download the artifacts ending in `_kebab_boot-img`, `_official-manager-APK`, and `_kebab_TWRP`. Back up first. In TWRP, decrypt/mount data and install the patch ZIP, then reboot manually. A mismatched or Magisk-modified boot is rejected; restore the matching original boot before installing.

The installer verifies project 19805, the current A/B slot, the 96 MiB boot partition, and full input/output SHA256. It backs up boot to `/sdcard/ReSukiSU-8T-backup`, writes only current-slot boot, and verifies the readback. It never switches slots, formats data, or writes recovery/super/firmware. On a write failure it attempts to restore and verify the backup.

## Official APK compatibility

The supplied Telegram APK `ReSukiSU_v4.2.0-rc1_35134-arm64-v8a-release.apk` is byte-identical to the official Actions Manager-release arm64 artifact from run 34628711668. Its official certificate matches the kernel's built-in ReSukiSU certificate. See manager-compatibility.json for SHA256 evidence.

The workflow verifies that the official Actions run used the exact ReSukiSU commit pinned for the kernel, then verifies the APK's whole-file SHA256 and official APK v2 signature. **It does not rebuild or re-sign the APK.** No custom signing key, custom certificate, or package-name override is used. Temporary-key PR builds are not accepted by default. Future upstream protocol/signature changes need a new explicit source/artifact lock and validation.

If the repository token cannot read upstream artifacts, the workflow can fetch the same immutable official artifact through nightly.link, with the same strict file and signature checks. Expired/unavailable artifacts fail closed; there is no automatic substitution with latest.

## Build inputs and sources

sources.json pins the OnePlus 8T Android 14 kernel, matching modules/devicetree, and ReSukiSU commit. The kernel uses the original 4.19.157 configuration and Clang 9.0.9 from NDK r21e, manual hooks, and SELinux. SUSFS is not enabled. GKI LKM and cross-device flashing are outside this build's scope.

The original boot is the project's no-root release base, published with the user's explicit authorization. Its hashes are pinned. Repacking verifies that ramdisk, DTB, header and other non-kernel components remain unchanged. Matching kernel module CRCs and device hardware behavior still require runtime validation.

Upstreams: [OnePlus kernel](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250), [OnePlus modules](https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8250), [ReSukiSU](https://github.com/ReSukiSU/ReSukiSU), [Magisk/magiskboot](https://github.com/topjohnwu/Magisk). Third-party licenses apply independently. Pinned source commits and build patches are included in the kernel artifact. prepare_hooks.py derives from the ReSukiSU manual-hook documentation and is GPL-3.0-only; other original build scripts use the repository MIT license.
