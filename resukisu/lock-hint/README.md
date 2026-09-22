# Scoped lock-hint compatibility candidate

Experimental; not a released ROM or a verified performance fix.

The Android 17 native lock hint cannot map its device on the Kebab kernel. This candidate adds a separately versioned, caller-local proc ABI under the existing scheduler SELinux label. It uses a dedicated UX inheritance slot and the stock conservative 4 ms execution budget; it does not write nice, IM flags, thermal settings or another task's state. Entry refuses an unrelated existing UX owner. Exit handles stock expiration and preserves a later explicit assignment.

Framework integration calls `Port8tLockHint.hint(enable, originalResult)` immediately after `nativeLockBoostHint(enable)` and returns the original result unchanged. The existing AOSP nice fallback therefore remains active. Per-thread state pairs nested scopes and only releases a successfully acquired contribution. No synthetic `/dev/sched_boost` or successful native return is created.

This branch starts from the previously verified kernel build base; the unaccepted dev82 asynchronous Binder experiment is not included. Required gates: kernel compilation, OEM certificate/vendor CRC verification, temporary-boot enforcement, real enter/exit and expiry observation, framework DEX/hidden-API audit, repeated thermally matched rapid launch/home tests. Do not infer success merely from counters or absent errors.

## dev88 revision 2

The first device probe demonstrated real 0 -> 0x108 -> 0 lock UX and balanced repeated scopes. It also exposed a failed edge case: the old proc setter ORs explicit bits into the inherited marker, so a later lock release could clear newly explicit UX. Revision 2 retires only the lock-hint contribution while holding the same rq lock as an explicit proc write. It preserves unrelated reference counts, handles same-bit takeover, and keeps all changes within the original candidate patch. Host checks using extracted candidate functions pass; new full kernel build and device checks are still required.

## dev88 revision 3

The animation-thread integration probe exposed another ownership boundary: an explicit clear of SA_TYPE_INHERIT could leave the candidate LISTPICK bit behind. A caller-local probe reproduced the exact 0x108 -> 0x8 -> 0x8 sequence on revision 2. Include inherited-marker clears in the existing atomic proc ownership handoff; do not add a separate cleanup workaround. Host tests now also cover this case. The exact system writer and revision 3 runtime result remain to be verified; revision 2 is not a release candidate.

## Final experiment assessment (revision 3)

Revision 3 passed the caller-local device regression, including inherited-marker clearing. A narrowly scoped animation-booster integration also showed real animation-thread ownership during interaction and zero state after the run; the previous LISTPICK residual was no longer observed.

This does not establish a performance improvement. With the same framework and thermal status 0 throughout, the original-kernel control had 14.62% launcher jank / P99 81 ms. Two candidate runs had 18.26% / 117 ms and 14.36% / 85 ms. All recorded 12 starts and no in-window Java fatal or ANR. Small, variable samples do not prove a universal regression, but they do not justify release inclusion. The device experiment is being reverted; retain this branch for research only, not as a recommended performance patch. The general interaction-latency issue remains unresolved.
