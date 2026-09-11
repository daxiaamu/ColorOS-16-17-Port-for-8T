# userdata 自动预装与 TWRP data 修复

## r15 验证结果

2026-09-11 的候选镜像在用户手动 Format Data 后，原 B 槽成功首启并正常重启。9 个应用由系统安装到 /data/app：文档阅读器、手机搬家、便签、翻译、钱包、浏览器、健康、主题商店、骑行模式。浏览器的视频 split、主题商店四个 split 完整。快应用引擎继续使用 product 中的已有版本，不计为 userdata 安装。便签新建、保存、重开及重启保留通过；MOD 项目主页原生双行布局与浏览器跳转通过。

r15 新 ZIP 已离线验证并交付；**并未用这个新 ZIP 再做完整刷入与覆盖升级**。候选镜像验证和整包验收分别记录。

## 不要把 loop@ 当成普通设备路径

历史 vendor fstab 同时包含 loop@/data/reserve/reserve.img 的 ext4/erofs 和 bind 条目。当前旧 fs_mgr 的 mount_all 把字面 loop@ 路径交给内核，得到 ENOENT；镜像文件存在且 SHA256 正确也不会自动挂载。先用恢复环境只读 loop mount 验证文件系统，再定位实际调用路径。

本组合的原生 init mount builtin 支持 loop@。在 data 可用后的 post-fs-data 使用原生一次性 mount：
```text
on post-fs-data
    mount erofs loop@/data/reserve/reserve.img /my_reserve ro
```
这取决于该 init 的实现和触发时序，新供体不能照抄后就宣布通过。核对 Android 实际 mount 表与 PMS 启动顺序。原 fstab 的早期失败不因后续挂载成功而消失，二者需区分；本方案未新增 ROOT 守护或用户运行的 Python 安装器。

## 原生 PackageManager 的三个兼容点

1. 当前旧机 first API 判断会绕开新版可移除应用扫描。以预装镜像中的只读专用 marker 限定本项目兼容分支，保留非本项目的原逻辑。涉及 OplusRemovableAppManager.isUpgradeBeforeV；新版本按语义重定位。
2. 只复制 base.apk 会使浏览器/主题部分功能缺失。按同一包目录复制完整 APK cluster，保留原生解析、证书、版本判断。目标只能为 /data/app 的合法包目录；不要把已有 product/system 路径当成可写目标。
3. PackageManagerServiceExtImpl.customScanRemovableDir 收集后去重：完整 reserve 主题存在时排除旧 stock 主题回退，同一 cluster 只由 base.apk 触发一次扫描。系统中已存在的快应用引擎优先保留。不可全局按包名删除所有扫描项。

PMS removablePath 清单、reserve 内容、文件权限/标签和构建镜像须同步。原厂 APK 保留签名；框架修改件不因此获得原厂有效签名。

保留数据的调试对照中，原生 /data/cache/recovery/intent 的值 2 能触发升级预处理，随后自动消费。TWRP 的 /cache 可能是 RAM，不能混淆。**r15 安装器没有主动写该标记，完整升级流程尚待验收**；新版本需要确认官方触发条件，不能靠永久“首次启动”开关反复强装应用。

## 安装时序

用户先在 TWRP 手动 Format Data，按恢复环境要求重启回 TWRP，然后安装完整 ZIP。包通过全部前置校验后写当前槽镜像，将 reserve 放入 /data/reserve/reserve.img；目录 0771 system:system、文件 0644 system:system，并设置对应 apk_data_file 标签。内容校验成功才原子替换，重启后交给 native PMS。

不要在加密初始化前手动填充 /data/app，也不要提前创建影响首次安装判定的应用目录。包不得格式化 data/metadata。安装后再次格式化会删掉 reserve；完整擦除 userdata 后资源也会丢失；系统设置的重置路径尚未实测，不能承诺保留，恢复方式见下节。刷前需要检查 data 可读写、容量与 RAM，不能写完系统才发现预装放不下。

## 恢复出厂的边界

自动安装不等于资源耐擦除。当前源镜像在 /data/reserve/reserve.img，已安装的 APK 和 split 在 /data/app，两者都属于 userdata。TWRP Format Data 会同时删除它们；system 中的挂载及 PMS 代码保留，也无法从不存在的源恢复应用。

此前干净首启测试的顺序是“用户格式化 → 写回 reserve → 启动”，普通重启保留测试也已通过；这两项都不是“单独恢复出厂后自动恢复”的证据。Android 设置里的恢复出厂是否保留 reserve 尚未实测，不能承诺保留，应按资源可能丢失说明。

可靠恢复顺序为手动清空后重新刷完整包，再启动，刷后不要再次格式化。应用找回只有在下载源可用且完整分包可恢复时才是替代方法，不能保证补齐所有依赖。若产品要求独立恢复出厂即可找回，必须把预装源迁移到经过验证、不会随该重置操作擦除的位置，并重新评估容量和生命周期；当前未实现。

## TWRP 错误识别 data

Color597 V2.3 在该 fstab 组合下曾用子串匹配 /data，把 loop@/data/reserve/reserve.img 当作真正 data 项，导致 data 条目丢失。修正版限定真实 /data 字段边界，在固定输入哈希上做最小二进制修改，再验证原 OS13 data 解密、MTP 和格式化。

这不是通用 TWRP 字节偏移：不同镜像必须重新分析。作者仍为 Color597，本项目修正应单独注明。格式化后出现旧逻辑映射时，重启恢复环境刷新映射，不能把映射失败当成再次格式化的理由。

## 必须保留的回归

干净首启、正常重启、完整 split、重复预置包、卸载后重启不复活、找回后旧数据保留、覆盖升级不降级用户更新、不重复覆盖安装、资源缺失/容量不足时的明确失败、出厂恢复说明。当前已完成的子集以上述记录为准，其余不能因代码路径看似存在就打勾。
