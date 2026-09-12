#!/usr/bin/env bash
set -euo pipefail
ROOT=$(pwd)
python3 resukisu/prepare.py
python3 resukisu/verify_manager_compatibility.py build/src/kernel/msm/KernelSU/kernel
NDK="$ANDROID_HOME/ndk/21.4.7075529/toolchains/llvm/prebuilt/linux-x86_64/bin"
export PATH="$ROOT/build/bin:$NDK:$PATH"
export CCACHE_DIR="$HOME/.cache/ccache" CCACHE_BASEDIR="$ROOT"
export CCACHE_COMPILERCHECK=content
trap 'ccache --show-stats' EXIT
ccache --max-size=2G
export KBUILD_BUILD_USER=daxiaamu KBUILD_BUILD_HOST=github-actions
export KBUILD_BUILD_TIMESTAMP='Sat Sep 12 00:00:00 UTC 2026'
cd build/src/kernel/msm
ARGS=(O="$ROOT/build/out" ARCH=arm64 REAL_CC="ccache clang" LLVM=1 LLVM_IAS=0 CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-androideabi- CLANG_TRIPLE=aarch64-linux-gnu- LOCALVERSION=+ LD="ld.lld --error-limit=0" OPLUS_FEATURE_WIFI_ROUTERBOOST=yes OPLUS_FEATURE_ADFR_KERNEL=yes OPLUS_FEATURE_PROCESS_RECLAIM=yes OPLUS_FEATURE_MEMLEAK_DETECT=yes OPLUS_FEATURE_UFS_SHOW_LATENCY=yes OPLUS_FEATURE_PADL_STATISTICS=yes OPLUS_FEATURE_UFSPLUS=yes OPLUS_FEATURE_SECURE_ROOTGUARD=no OPLUS_FEATURE_SECURE_MOUNTGUARD=no OPLUS_FEATURE_SECURE_EXECGUARD=no)
make "${ARGS[@]}" olddefconfig 2>&1 | tee "$ROOT/build/configure.log"
for flag in CONFIG_KSU=y CONFIG_KSU_MANUAL_HOOK=y CONFIG_KSU_MULTI_MANAGER_SUPPORT=y CONFIG_SECURITY_SELINUX=y CONFIG_MODVERSIONS=y; do
 grep -qx "$flag" "$ROOT/build/out/.config"
done
make -k -j"$(nproc)" "${ARGS[@]}" Image 2>&1 | tee "$ROOT/build/kernel.log"
cd "$ROOT"
mkdir -p kernel-output
cp build/out/arch/arm64/boot/Image kernel-output/Image
cp build/out/.config kernel-output/kernel.config
cp build/out/Module.symvers kernel-output/
cp build/manual-hooks.patch resukisu/sources.json kernel-output/
git -C build/src/kernel/msm diff --binary > kernel-output/kernel-build.patch
git -C build/modules diff --binary > kernel-output/vendor-build.patch
git -C build/src/kernel/msm/KernelSU diff --binary > kernel-output/resukisu-build.patch
python3 - <<'PY'
from pathlib import Path
p=Path('kernel-output/Image'); b=p.read_bytes()
assert len(b)>8*1024*1024 and b[56:60]==b'ARM\x64', 'Not an arm64 Image'
assert b'ReSukiSU' in b, 'ReSukiSU is missing from kernel'
PY
