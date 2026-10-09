# 音量面板与实体音量键同侧

8T 实体音量键在左侧。原厂 KB2000_14.0.0.602 SystemUI 的 FeatureOption$isOplusVolumeKeyInRight$2.invoke() 读取 persist.oplus.software.audio.right_volume_key，默认 false。OplusVolumeDialogImpl 的 false 分支使用 LEFT|TOP（0x33），横屏使用 LEFT|CENTER_VERTICAL（0x13）。已提取的原厂属性文件未发现 true 覆盖。

PLK110 OS17 供体仍有相同原生分支，但 my_product/build.prop 将属性设为 true。修复应纠正这项硬件配置为 false，保留 SystemUI 原生布局及动画；无需修改 APK 或强改窗口坐标。

该能力值由 SystemUI 惰性缓存。临时验证需重启 SystemUI；持久修复同时核对运行属性、镜像默认值以及整机重启后的面板。已有设备的 persist 值可能覆盖镜像默认值，不能只改 build.prop 就断言升级用户已生效。

dev69 已验证临时 false 值下左侧紧凑面板和四路音量展开正常。候选镜像逐文件审计确认仅 build.prop 一项属性变化，其余内容与元数据相同，保留大小写不同的路径。刷入与重启验收状态以当前状态记录为准。

持久验收：单分区刷入后完整回读一致，重启完成，运行属性与镜像默认值均为 false，重启后锁屏截图确认左侧面板。保留强制模式与普通 ADB shell。完整 ZIP 尚未合入。
