# ColorOS16 / ColorOS17 双版构建

## 基线与共用条件

ColorOS16：原公开boot `3f06497bfa6d31d4f7209246a224090e207eaec23b0d769a376d318894be76b7` 和20260916 ROM boot `bdd8967199778d244d908e1adc8b5a85e614fdbd47db59df642ad0c7b29a0751`。

ColorOS17：20260921 NoRoot r1 boot `d8ee22c0ea67dace2214e502327652d97162d4f5817bcb4819318cd55da323f6`，与20260920 NoRoot r2相同。实际发布输入解包后，ramdisk.cpio、DTB、header与公开boot一致；压缩大小不同不等于内容不同。OS17内核配置与既有构建配置的差异符合关闭KSU后的结果，没有新增调度配置差异。

因此使用原已授权公开的干净boot换入共享内核，无需公开新的完整OS17输入。保持Enforcing默认启动参数及现有ROM侧策略。内核保留模块证书、网络ABI、S3908单击和1815触感兼容，并将旧v6显示补丁替换为后继本轮入场状态累计补丁：仅直接入场的panel允许相应NOLP跳过，失败重试保留状态，退出成功清理。默认先OFF路径保持原NOLP行为。

## 构建与命名

metadata 一次解析最新成功官方main Build Manager并验证签名及版本；kernel编译一次；package矩阵固定ColorOS16、ColorOS17，关闭fail-fast以保留独立失败日志。每版仅使用自身白名单，不自动把公开打包输入哈希加入OS17名单。目前两份boot可以相同，TWRP安装器和manifest的ROM名单不同。

文件格式：`ReSukiSU_<版本>_<构建号>_<日期>_ColorOS16_kebab_boot.img`、对应`_TWRP.zip`；OS17使用ColorOS17标识。APK共用原签名与原字节。

Release工具要求整个双版run成功，检查两份manifest、源码锁、官方APK来源、命名、非内核组件、包内外镜像一致性、SHA256SUMS和不重叠基线，再上传五项到既有草稿。历史单版run不适用于此工具。

## 验证与限制

固定官方源码的累计补丁实际应用通过；C逻辑测试覆盖9216项AOD状态/补亮/退出、101440项OOS及96000项非OOS震动选择/失败分支。双版命名、名单隔离、错误组件拒绝、安装器回滚均有测试。云端仍须通过976项原厂模块导入CRC、公钥证书和实际编译宏验证。

不修改SystemUI、ROM策略、DTB、供电或分区布局。新ReSukiSU组合需分别实测16/17的启动、Root、模块、触摸、AOD默认/无缝模式、指纹与震动。旧无ROOT内核验收不代替新组合实测。

本地源码、产物和临时文件使用F盘，并设置进程级TEMP/TMP、PYTHONDONTWRITEBYTECODE；Java另外设置java.io.tmpdir。GitHub托管Runner使用其自己的临时工作区。
