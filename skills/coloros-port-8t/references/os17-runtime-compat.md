# OS17 无线回调、隔空接听、GPU 与振动

无线回调协议详见[dev42](os17-radio-callback.md)，隔空接听的 CPU/ABI 适配及用户真实来电确认见[dev44](os17-air-gesture.md)。这两项不等于 SIM 间歇识别已彻底修复。

## gpuservice（dev50）

`libgpuserviceextimpl.so` 的 PreCacheService 异步初始化前成员为空，早到 Binder 请求解引用。仅为 3001/3002/3003/3013/3014/3015 六种 precache 事务在未就绪时返回 `NO_INIT`（-19），保留成功及其他事务路径。输入 SHA256 `149ca18eab26262c116e7f4a79bd93bfd129cdb924b6de7aad8723059f71f04a`。分支测试与三次正常重启、各次稳定 PID、原崩溃消失通过；不停服务、不强制 GPU 合成、不改温控或内核。

## 输入法与来电振动（dev50c）

标准长振动实体成功只能证明基础链路，不能替代输入法、触感和 Telecom 场景。

- 撤回两份 permissions XML 重复的 `oplus.software.vibrator_qcom_lmvibrator` 声明，选择已有 8T HAL。
- 主表与 override 同步：effect 157/158/159 → RAM 1/7/6，35/30/45 ms。override 会覆盖主表，只改一份会假修复。
- 输入法实测恢复；来电仍失败时继续查 Telecom。错误 `oplus.software.audio.haptic_channel_support` 使其绕过旧来电振动；撤回这项能力声明而不新建强制循环振动服务。
- 最终输入法 Step→effect158/RAM7；来电 effect345/RTP98、挂断 stop0。用户确认两者正常且挂断停止。无内核、ROOT 或数据格式化变更。用户错过短振动时应重测，不能据此否定已观测的驱动调用。
