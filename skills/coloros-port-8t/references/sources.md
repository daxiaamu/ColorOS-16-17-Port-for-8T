# 来源与用途

下列链接用于追溯，**不表示全部项目代码已合入**。公开仓库没有复制 OEM 反编译代码或第三方源码。对新供体使用时检查上游当前版本，并为实际采用的实现保存 commit/path/许可证。

| 来源 | 本项目参考范围 |
|---|---|
| [Color597](https://github.com/color597) | 内置 8T TWRP V2.3 作者；data 解析兼容修正为本项目后续修改 |
| [toraidl/coloros_port](https://github.com/toraidl/coloros_port) | ColorOS 移植流程与兼容思路 |
| [ColorOS_Port_NEXT](https://github.com/edgeless-player/ColorOS_Port_NEXT) | 跨代框架、启动与显示适配参考 |
| [XDA 8T ColorOS16 移植讨论](https://xdaforums.com/t/shared-rom-port-coloros16-for-oneplus-8t-18-10-25.4764227/) | 用户给出的同类工程和问题线索，不作为本机功能已验证的证据 |
| [GalleryEnhance](https://github.com/Xposed-Modules-Repo/com.daxiaamu.coloros.GalleryEnhance) | 相册实况时长功能思路，系统内固化需针对具体 APK 验证 |
| [unlock-cn-gms](https://github.com/fei-ke/unlock-cn-gms) | 国行 Google 服务限制处理思路；不能混淆 Play 安装状态与全部 GMS 依赖 |
| [OnePlusOSS SM8250 kernel](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250) | 8T 驱动与硬件接口历史参考 |
| [OnePlusOSS modules/devicetree](https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8250/tree/0a301570ef70f6f9bfe1840451c9d41f5ddce6b8) | Android14 分支参考：display/oplus、charger；不等于实机二进制逐字节对应源码 |
| [高通 Audio HAL 初始化](https://android.googlesource.com/platform/hardware/qcom/audio/+/refs/tags/android-10.0.0_r7/hal/audio_hw.c) | 音频设备锁与 SoundTrigger 初始化顺序对照，非本机源码完全匹配承诺 |
| [AOSP Composer 2.4](https://android.googlesource.com/platform/hardware/interfaces/+/refs/heads/master/graphics/composer/2.4/IComposerClient.hal) | SET_LAYER_GENERIC_METADATA 接口定义 |
| [Lineage 历史 AntiFlicker](https://github.com/LineageOS/android_device_oneplus_sm8250-common/blob/1bf94e3dc1b84769040c8efb40bf91bade8dde64/livedisplay/AntiFlicker.cpp) | 8 系列类原生 DC 节点控制；其 DRM 节点不在当前原厂内核中 |
| [Lineage Oplus AntiFlicker](https://github.com/LineageOS/android_hardware_oplus/blob/ec3b8211676f55ed09905c4c336356acedc040d3/aidl/livedisplay/AntiFlicker.cpp) | PWM pulse/turbo/dimlayer ioctl 能力回退方式 |
| [Lineage Oplus DisplayModes](https://github.com/LineageOS/android_hardware_oplus/blob/ec3b8211676f55ed09905c4c336356acedc040d3/aidl/livedisplay/DisplayModes.cpp) | seed 与 SDM 显示模式配套；未照搬进当前 ROM |
| [OnePlus 8T 官方规格](https://www.oneplus.in/8t/specs) | 机型传感器与原厂录像能力 |
| [Sony IMX586 规格](https://www.sony.com/en/SonyInfo/News/Press/201807/18-060E/) | 4K90/1080p240/720p480 传感器规格，不能推导出本机全部模式可用 |

基本开发工具不是本项目 ROM 功能依赖的致谢条目。若实际再分发任何上游代码，则按上游许可证保留必要版权与许可说明，不受“致谢列表精简”的 UI 偏好影响。
