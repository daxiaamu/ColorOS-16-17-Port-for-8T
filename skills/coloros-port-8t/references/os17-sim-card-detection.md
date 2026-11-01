# OS17 间歇性不识别 SIM：排查记录与边界

更新：2026-11-02。适用：8T 移植系统的“无 SIM 卡”，不是已读卡但停机、注册被拒或 IMS 未注册。当前结论是**间歇性故障尚未找到可证实的根因，没有新增生产补丁**。

## 已观察到什么

- 原失败启动中，RadioConfig 的物理槽状态和 RadioSim 的卡状态都报告槽1 ABSENT，ATR为空、应用数为零；逻辑映射正常、UICC应用启用。不是仅设置界面的显示问题。
- 后续单张移动卡位于槽1，动过卡托后短暂 PRESENT 再 ABSENT，约三分钟后自行恢复 LOADED。用户确认恢复前未再移动卡托；采样期间没有重启或调整卡供电，未观察到恢复前的框架供电/禁用UICC请求。仍不能区分触点、卡通信/供电和 UIM 状态机。
- 普通 NoRoot 重启两轮均约24秒读到双卡，各观察120秒无复发；这不能推翻数小时后发生的间歇性故障。
- 独立 UIM 客户端捕获单卡拔插及多次单双卡切换。双卡均可达到 PRESENT/READY/LOADED；用户确认数轮掉卡对应手动拔插，反复操作未复现原异常。单双卡切换的假设未被证实，也没有被完全排除。
- 操作过程中一次槽2报告 CardState=ERROR、CardError=NO_ATR_RECEIVED。由于与多次卡托操作重叠，不能直接判为原故障的根因。PRESENT/ABSENT 过渡中的原始错误字节99/100也不能单独解释为标准故障。
- SIM_OPEN_CHANNEL 错误发生在失败样本，也出现在能正常加载的对照中，尚无因果证据；不能直接删除运营商权限读取流程。

## 原厂对照的覆盖范围

移植 boot 的完整 DTB 与原厂 H25 相同，发布 DTBO 也相同；核心 QCRIL 库及已核对的无线库保持原厂字节。原厂 modem 镜像的有效范围哈希也匹配。未发现改变 SIM 引脚定义的证据，但**DTB相同不等于整个内核相同**，有限文件对照也不等于所有框架下发参数相同。

此前联通注册失败的排查已按用户澄清停止：该卡已停机／可能注销。不得把 OUT_OF_SERVICE 当作“不识别卡”，也不继续沿用已经取消的换系统清数据对照方案。

## 再次复发时怎样取得有效证据

1. 先确认实体卡数量、槽位、卡托最后操作时间、boot_id、UICC应用启用状态。保留现场，不先重启或拔卡。
2. 同时对齐 RadioConfig 物理槽、RadioSim 卡状态、应用初始化、框架供电/订阅/映射请求的时间。槽位日志通常从0编号，向用户描述从1编号。
3. 普通日志不能解释时，在已有授权范围内，用独立 QMI UIM 客户端读取 CardStatus(0x2F)、SlotStatus(0x47)，并监听 CardStatus(0x32)、SlotStatus(0x48)。Indication Register(0x2E)通知掩码0x11只作用于新建客户端；不替换 RIL 的原生回调。
4. 本次匹配的服务对象版本为 major=1、minor=0x62、tool=6；从实际库验证后才可调用，不能套给其他供体。解析可变长应用/AID/ICCID/ATR字段时只跳过身份字节，打印状态、长度和存在性。
5. 明确区分 CardState 的 ABSENT=0/PRESENT=1/ERROR=2 和物理槽状态枚举。错误码须结合 ERROR 状态及卡托操作解释，不能只看一个数字。将用户操作时间记入证据，避免把手动拔出当作自发掉卡。
6. 采样结束释放独立客户端。临时ROOT需经正常管理器UI撤销授权，移除本轮工具，再回原NoRoot boot；复查原boot哈希、SELinux、su/管理器残留及实际读卡。

本地运行方式、复制库的访问条件和ROOT授权不是公开技能自动授予的权限。每条设备命令指定本次授权序列号，不能自动选第一台，更不能读取其他连接设备。独立客户端不发卡供电、复位、NV、身份导出或配置写入命令。

## 已踩过的坑

- vendor库在shell域直接dlopen失败，复制到本轮目录后可加载，但普通shell的QMI初始化返回-16；这是采样权限/传输失败，不能解释为SIM本身错误。没有改SELinux或用失败查询代替实际读数。
- 临时ROOT在原故障已自行恢复之后才启动，不得把恢复归功于ROOT或重启。
- 不用开机循环断电上电、伪造PRESENT、吞掉错误或强制重置掩盖原因。未复现不是修复完成。
- 原始radio日志可能含设备、订阅、号码和卡标识；不上传GitHub。私有密钥、解封材料、NV/校准、OEM库和ROM镜像也不进入公开技能。

## 公开探针源码

[`uim_card_watch.c`](../scripts/uim_card_watch.c) 是本轮独立客户端的非身份状态观察器，不含OEM库或ROOT工具。依赖与实机匹配的旧版QMI ABI；不是跨机型通用接口。设置 `PORT8T_SERIAL` 为本次已授权目标、`PORT8T_QMI_LIBDIR` 为本轮库副本的绝对路径；不指定目标即拒绝运行。使用 `--observe` 最长监听约十分钟，无参数只查询。编译例：Android NDK clang，`--target=aarch64-linux-android30 -O2 -Wall -Wextra -Werror -fPIE -pie uim_card_watch.c -ldl -o uim_card_watch`。运行结果不能替代实体读卡与原生电话框架对照。

协议来源：[libqmi UIM消息布局](https://github.com/linux-mobile-broadband/libqmi/blob/main/data/qmi-service-uim.json)、[UIM枚举](https://github.com/linux-mobile-broadband/libqmi/blob/main/src/libqmi-glib/qmi-enums-uim.h)。
