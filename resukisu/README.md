# ReSukiSU for the ColorOS 16 OnePlus 8T port

> Validation status (2026-09-13): the initial build failed to boot because the OEM module verification certificate and two stock ABI requirements were missing. The build now includes the OEM public certificate, the upstream negative-advice race fix already used by the stock vendor modules, and `BRAND_SHOW_FLAG=oneplus` for the original power-supply enum. Actions must pass the certificate and all 976 imported kernel-symbol CRC checks before packaging. Updated artifacts are **offline-validated only**; no installation or device boot test is performed for this revision. Earlier artifacts remain unsuitable for use.

Actions outputs the finished ReSukiSU boot image, the unmodified official ReSukiSU Actions arm64 APK, and one ReSukiSU TWRP ZIP. The boot image is repacked once and reused as both the standalone download and the ZIP payload; their SHA256 values are checked for equality. Stock boot remains a build input only; no stock-image restore ZIP is produced. Every download filename and public artifact name includes the ReSukiSU version, version code, and build date (Beijing time), for example `ReSukiSU_v4.2.0-rc1_35134_20260912_kebab_TWRP.zip`. One date is shared across all jobs, including builds crossing midnight. The APK is renamed only; its bytes and signature remain unchanged. ZIP-internal `images/boot.img` remains the installer payload path. **Successful compilation is not a boot/hardware validation; these are test builds until validated on an 8T.**

## Run and install

Open Actions > ReSukiSU for OnePlus 8T > Run workflow. Download the artifacts ending in `_kebab_boot-img`, `_official-manager-APK`, and `_kebab_TWRP`. Back up first. In TWRP, decrypt/mount data and install the patch ZIP, then reboot manually. A mismatched or Magisk-modified boot is rejected; restore the matching original boot before installing.

The installer verifies project 19805, the current A/B slot, the 96 MiB boot partition, and full input/output SHA256. It backs up boot to `/sdcard/ReSukiSU-8T-backup`, writes only current-slot boot, and verifies the readback. It never switches slots, formats data, or writes recovery/super/firmware. On a write failure it attempts to restore and verify the backup.

## Official APK compatibility

The supplied Telegram APK `ReSukiSU_v4.2.0-rc1_35134-arm64-v8a-release.apk` is byte-identical to the official Actions Manager-release arm64 artifact from run 34628711668. Its official certificate matches the kernel's built-in ReSukiSU certificate. See manager-compatibility.json for SHA256 evidence.

At the start of each workflow, the metadata job selects the newest successful official main-branch Build Manager run (push or workflow_dispatch), downloads its Manager-release arm64 APK, verifies its official APK v2 signer and embedded version, and records its SHA256 and source commit. Kernel and package jobs download that same resolved source lock; they never query latest independently. **It does not rebuild or re-sign the APK.** No custom signing key, custom certificate, or package-name override is used. Temporary-key PR builds are not accepted by default. Kernel integration and vendor ABI checks still have to pass for each newly selected upstream commit; changed interfaces fail the build instead of publishing an unverified kernel pair.

If the repository token cannot read upstream artifacts, the workflow downloads the same selected run through nightly.link and validates the official signer before recording the file hash. Expired or unavailable artifacts fail closed; it does not silently fall back to an older build. PRs, forks, translation branches, debug APKs and spoofed APKs are excluded. An official signer change requires review. A newer upstream build published after selection is picked up by the next workflow run.

## Build inputs and sources

sources.json pins the OnePlus 8T Android 14 kernel and matching modules/devicetree, and retains a historical ReSukiSU pair for explicit local reproduction without --latest. Actions resolves the latest official ReSukiSU APK/commit together and publishes the per-run sources.json and manager-compatibility.json in resolved-resukisu-inputs. That lock is also included with the kernel and TWRP provenance. The kernel uses the original 4.19.157 configuration and Clang 9.0.9 from NDK r21e, manual hooks, and SELinux. SUSFS is not enabled. GKI LKM and cross-device flashing are outside this build's scope.

The original boot is the project's no-root release base, published with the user's explicit authorization. Its hashes are pinned. Repacking verifies that ramdisk, DTB, header and other non-kernel components remain unchanged. Actions verifies the OEM module certificate and the pinned vendor import CRCs before packaging. Runtime module loading and device hardware behavior still require device validation.

Upstreams: [OnePlus kernel](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250), [OnePlus modules](https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8250), [ReSukiSU](https://github.com/ReSukiSU/ReSukiSU), [Magisk/magiskboot](https://github.com/topjohnwu/Magisk). Third-party licenses apply independently. Pinned source commits and build patches are included in the kernel artifact. prepare_hooks.py derives from the ReSukiSU manual-hook documentation and is GPL-3.0-only; other original build scripts use the repository MIT license.

## Stock vendor ABI repair

The five-file networking backport in `patches/0001-net-fix-dst-negative-advice.patch` matches [OPPO official SM8250 commit 61c4792](https://github.com/oppo-source/android_kernel_oppo_sm8250/commit/61c479209b55fba89cf75de5867498f6bb75a24f) and [upstream fix 92f1655](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=92f1655aa2b2294d0b49925f3b875a634bd3b59e). It updates IPv4, IPv6 and XFRM implementations together with the callback signature and uses the correct RCU reset order. No symbol CRC rewriting, module-version bypass or signature-enforcement bypass is used. The OEM certificate is a public verification certificate, not a private signing key.

## Kernel version suffix

The kernel release is `4.19.157-perf-daxiaamu+`, set through the build argument `LOCALVERSION=-daxiaamu+` alongside the stock `CONFIG_LOCALVERSION="-perf"`. The build checks the generated release and its presence in Image, and includes `kernel-release.txt` in the kernel artifact. OEM certificate and vendor symbol CRC checks remain required; this suffix change has not been device-tested.

## S3908 single-tap wake repair

On kebab the boot/ABI repair was device-tested: Android booted, 34 modules loaded and ReSukiSU root worked, but panoramic AOD single-tap wake failed. The S3908 driver enabled the single-tap firmware mask but lacked `STAP_DETECT` decoding. `module-patches/0001-s3908-restore-single-tap-gesture.patch` restores event `0x10` to `SingleTap` and tap coordinates from `extra_gesture_info`, following [official OPPO SM8250 source f141bd5](https://github.com/oppo-source/android_kernel_modules_and_devicetree_oppo_sm8250/commit/f141bd5518945b3c887f1e48203368fff6be3af2). SystemUI and APK are unchanged. This additional touch repair requires a new build and device validation; the previous boot-success result does not validate it.


## 20260916 AMB655X AOD and 1815 haptics integration

`patches/0002-amb655x-aod-selected.patch` is the selected v6 display change (input SHA256 a5d8a43aef416c5f3cdc212529858d5f9cefc39c6c70f2b876319573ecc5c13a). It skips only the leading DISPLAY_OFF for AMB655X ON-to-LP1 and LP1/LP2-to-NOLP transitions when the command matches the guarded single-byte DCS form. The shared table, remaining commands/waits and 0x53 values are preserved. Only successful matching LP1 with a POST_ON_BACKLIGHT table clears the deferred backlight flag. No v5 fallback or v7/v8 experiments are included.

The visual result also requires the selected ROM SystemUI changes and ROM-side low AOD mode initialization. This boot package does not modify SystemUI or persist the low mode, and does not promise a continuous brightness transition. The selected reference kernel was tested on 8T; that result does not validate this new ReSukiSU build.

`module-patches/0002-aw8697-kebab-ime-waveforms.patch` changes only the 1815 table's RTP 110/111/112 filenames to the existing unsuffixed OEM fingerprint_effect1/2/3 resources. This is a port compatibility mapping, not a claim that ReSukiSU introduced the original problem: the stock kernel also contains the reserved table. No other motor/frequency table, index, timing or gain is changed. The ROM's separately verified RAM mapping for effect157/158/159 remains untouched and takes precedence whenever those requests use RAM. The new RTP mapping requires physical haptic validation; existing filenames and host tests do not establish equivalent feel.

The build compiles actual C selection functions for regression checks (both OOS and non-OOS), checks all unchanged table entries, and exercises the selected AOD predicate and deferred-backlight block. It also verifies OPLUS_BUG_STABILITY and CONFIG_OPLUS_HAPTIC_OOS in actual driver compilation commands, not only .config. Test reports are included with kernel artifacts. OEM module certificate/CRC checks and boot component identity checks remain mandatory. The kernel timestamp now comes from the build repository commit instead of a fixed September 12 timestamp.
