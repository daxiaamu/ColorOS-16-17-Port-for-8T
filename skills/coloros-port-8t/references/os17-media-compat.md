# OS17 相册编辑与酷安实况：原生媒体兼容

## 相册编辑退出到主界面（dev51）

相册 17.8.40 点击图片编辑失败时，检查原生堆栈及 APS 适配器初始化结果。`my_product/lib64/libAPSClient-cmd-jni.so` 在适配器初始化失败后仍调用未就绪函数指针。最小修复是检查初始化结果，失败返回 Android `NO_INIT`（-19），保留成功路径，允许上层原有回退；不是吞掉全部 JNI 异常或停用相册。

该轮不改相册 APK。输入库 SHA256 `0b5b49ae8845983f178279fe252c4aef8476d99b1f9470a7ead98e9095c3df39`；补丁必须按实际版本重定位调用和错误分支。孤立 app_process 探针曾因 linker namespace 警告后被杀，不能计作通过。安装后真实相册编辑、裁剪、曝光、另存副本（942×1286）、冷重开和再次进入编辑通过，相机启动也通过。AI 效果、云功能、IPU 滤镜和实况编辑未全测。

## 酷安实况无法播放（dev55）

酷安 16.6.2 / 2609151 在实况大图调用 Media3 `MediaCodec.setOutputSurface` 时失败。关键链条：`ACodec attachBuffer EINVAL` → `generation number mismatch [buffer 0] [queue 非零]` → `MediaCodec.native_setSurface` → `ExoPlaybackException`。先区分下载/容器/解码能力与输出 Surface 切换，不能看到 HEVC 就关闭硬件解码。

独立 MediaExtractor/MediaCodec/SurfaceTexture 探针可复现。进程内诊断跟踪发现：`MediaCodec.connectToSurface` 先设置 Surface generation，随后为 listener 重连执行 disconnect；此供体的 disconnect 清零 Surface 成员，队列却保留旧编号。attachBuffer 自动赋号得到 0，触发合法的一致性检查。

只调整 **64 位** `system/lib64/libstagefright.so`：在 `surfaceConnectWithListener` 成功后再 `Surface.setGenerationNumber`，连接失败保持返回，编号设置失败继续传播。保留 BufferQueue 校验、Surface 通用行为、硬件解码与 Enforcing；不改酷安 APK，不全局注入库。

该输入 SHA256 `c7c0172c493092a134b32c519435fe248504dfb374a47d749a1bae23258d5747`，输出 `cce0cedf8fc31958d4f2a1de4945a800e91029510e94bca75592d0adf7d32091`。该版本使用可执行段末尾零填充中的 36 字节 helper；写前核对 ELF 段范围、原调用 opcode 和完整输入哈希。不要向其他版本套用固定偏移，也不要假设虚拟地址等于文件偏移。

验证分层：

1. 高通 AVC、高通 HEVC、C2 AVC 独立探针切换成功且有输出帧；少量输入未送 EOS 时存在重排缓冲，不要求输出帧数恰等于输入数。
2. system 重建后 4,163 文件、4,325 inode 审计，仅该库内容改变；权限/大小/UID/GID/标签一致。完整分区回读、正常 Enforcing 重启通过。
3. 真实酷安原失败图片播放至 2.54 秒 ENDED，两轮退出重进均完成；连续截图内容变化，日志无 generation mismatch / Playback error。
4. 移除设备探针、临时库、媒体样本和 UI XML，恢复测试前超时设置。未测试 32 位同类调用，也不声称所有播放器通过。

参考：[AOSP Surface.cpp](https://android.googlesource.com/platform/frameworks/native/+/refs/heads/main/libs/gui/Surface.cpp)。供体额外的 disconnect 重置行为以实际二进制和运行记录为证，不能仅凭上游源码推断。
