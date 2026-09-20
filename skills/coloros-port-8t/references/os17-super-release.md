# Super 容量、原生预装与完整包

本次先为容量把安装源放到userdata，后按用户要求迁回Super。最终开发包逻辑布局需10GiB，测试设备物理Super为14GiB；没有在本轮自动修改GPT。这些数值是该候选的事实，不是所有8T的默认大小。

## 预装回迁

将安装源作为真实文件放入my_stock，原生init只读bind到/my_reserve，保持PMS原有扫描路径与cluster/split关系。移除旧userdata镜像loop挂载及对应fstab项，安装器不再依赖可挂载的Data。39个预装APK、3个系统应用的4个文件及标记共44文件，约3.48GB未压缩内容逐一哈希验证。

验证mount来源确实为Super逻辑分区，而不是旧文件恰好还在；重启后检查同一dm来源和只读EROFS。/data/app中已安装实例仍是用户数据，不能据此声称所有应用运行文件都在Super。回迁成功后再处理历史副本，不能先删回退源。

## 镜像与宿主文件系统

- 保留uid/gid/mode、符号链接和SELinux标签，逐文件回解对比；完整目录清单相同不保证镜像元数据正确。
- Windows应使用区分大小写的源树。本次非区分大小写树导致mkfs.erofs失败，即使清单看似相同。
- 硬链接工作树修改前断开目标链接；跨卷不能假设可以hardlink。防止污染旧验收镜像的源树。
- 保留已验证的4KiB块/legacy压缩参数，不能为了容量擅自启用旧内核不支持的新特性。
- 分区的image长度、LP实际extent容量、对齐预算和Super总容量分别检查。有大Super不等于某个逻辑分区自动变大。

两次增量候选仅超原LP容量数KiB仍被刷前检查挡住。一次fastbootd扩分区失败，检查Super元数据未改变后停止；最终以标准ZIP压缩DEX后重建镜像，完整校验并在原extent内刷入。不能关闭容量检查、截断镜像或盲目重复修改分区表。

## 安装检查

读取实际目标、项目/底层/槽位、Super字节数、snapshot状态。任何必需检查失败在首次写入前退出。容量不足应明确显示实际/所需容量，提示备份、先按配套工具说明扩容后重试；本技能不提供未经实测的自动扩容脚本。

检查全部payload和fragment哈希；布局变化核验主/备几何与各slot元数据，写后按真实写入范围回读。不要假定主机fastboot返回成功就代表内容正确。保留boot、当前Super及清单组成的可用回退方案。

TWRP无法解密Data并不授权Format Data；普通双清与清空内部存储不同。仅在本次用户明确授权后使用恢复环境原生Format Data，不拿手动擦metadata作为通用解密修复。

## 当前交付与版本 bump

20260921 NoRoot r1 汇总至 dev55，包含 TWRP-14-OP8T-Color597-V2.3-data-media-fix，默认 Enforcing。准确 ZIP 身份及未验收范围见[当前状态](os17-current-status.md)。保留 OS16 的环境/底层检查与双语 UI；当前包要求 Super ≥10,737,418,240 字节（10 GiB），支持更大的已扩容物理分区，不自动扩 GPT。

当前打包检查：冻结 15 分区路径/大小/哈希；lpmake 后还原稀疏 extent 逐分区哈希；分片后检查 A/B 共 12 份主备元数据且数据 extents 一致；ZIP 34 载荷哈希及所有条目 CRC；boot 与已安装 NoRoot Enforcing 版本相同；recovery 确实入包；最后复制 NAS 并回读 SHA。仅验证 sparse 结构不能代替 payload 内容校验。

包写 Super 与当前槽位的启动/恢复镜像；不保留另一槽位的旧系统逻辑布局。不附带基带等底层固件，要求匹配的官方 Android 14 底层。无自动清 Data、无自动重启；普通双清和 Format Data 的授权仍需区分。Format Data 后内部存储的 ZIP 也会消失，应预先安排外部存储或重新传入。

日期更新只改 my_manifest/build.prop 的 ro.build.display.id 与 ro.build.display.id.show，保留 OTA身份、fingerprint、协议版本、原分区时间策略；同时更新包名、manifest、环境检测日期和交付说明。20260921 相比 20260920 r2 只有该分区哈希变化，其余14分区及启动配套不变。回解逐文件和 inode/标签对比，不以 ZIP 改名当作系统版本更新。

新包校验及 NAS 回读完成后，才按用户明确要求删除旧成品。删除范围限定为旧发布目录和本地旧 ZIP/校验文件，保留后续构建依赖及审计；不要把存储迁移导致的工作树删除提交成源码删除。大体积数据放用户指定工作盘/NAS，Windows Python 显式 UTF-8，TEMP/TMP 指向该工作区。

本完整包双清和 B 槽实机测试仍待用户；当前设备增量测试不等于这一项完成。

## dev44 后继逻辑容量记录

加入 AON 私有匹配库时，my_product 逻辑容量从 1520984064 增至 1523539968 字节；物理 Super 未变。标准 fastbootd resize 返回失败后，先证明元数据未写坏，再审计本机空闲 extent 和所有主/副表。现场追加 extent、校验几何与表/头校验和、刷新 recovery 映射，随后完整刷入回读；这是针对已核验布局的现场恢复，不是可照抄的通用脚本。

后继分区已有多个 extent，早期假定单 extent 的脚本不可重复运行。不能把历史绝对扇区地址写成下一台设备的修复步骤。Gallery dev45 与 Games dev47 的链接修复均在现有容量内完成，未再次改分区表。原包安装源回迁只证明文件和挂载存在，后继仍发现 PMS 漏扫，见 [Overlay 扫描修复](os17-product-scan.md)。
