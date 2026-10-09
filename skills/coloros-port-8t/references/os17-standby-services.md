# OS17 待机：不兼容服务启动与测量干扰

## 已验证的两处启动配置修复（2026-10-08）

目标为8T KB2000的Android14硬件底层、4.19内核与PLK110 OS17供体。以下结论不能推广到带对应硬件或AIDL GNSS的新设备。

- `vendor/etc/init/hw/init.qcom.rc`无条件启动`vl53l1_daemon_main`，但目标没有`/dev/stmvl53l1_ranging`、`stmvl53l1`模块参数或对应netlink接口。原进程退出255，init反复拉起并触发`flags_health_check UPDATABLE_CRASHING`。仅在已确认缺少硬件接口的目标构建中省去该服务定义。不能伪造或移植别机`stlaser.cal`，也不能只吞掉错误。
- 供体`system_ext/etc/init/loc_sys_service.rc`启动仅支持AIDL的配置辅助进程，持续等待不存在的`vendor.qti.gnss.ILocAidlGnss/default`。8T实际使用HIDL GNSS2.1、ILocHidlGnss4.0及原有`loc_launcher`/`xtra-daemon`。在这个目标构建中省去供体辅助服务启动，保留原厂定位进程与配置；不通过声明虚假AIDL支持解决。

两项只改变各自一个rc文件，保留文件权限与标签，不改APK、HAL、驱动或校准分区。镜像逐文件/元数据往返、刷写前原哈希和快照检查、刷后完整回读均通过。重启后Enforcing，两项循环未再出现，HIDL GNSS/XTRA正常注册运行，相机预览与照片保存通过。**室外卫星定位、长时间待机收益尚未验收**。

公开脚本`../scripts/patch_standby_init.py`仅准备文本候选，要求明确确认目标兼容性和输入哈希；不检测硬件、不构建镜像、不刷机。当前与回退镜像必须另行保留。

## 曾试验但未接受的路径

`persist.vendor.sys.location.xtra.native_download=true`可使供体辅助进程走原生退出分支，但也导致XTRA进程重启一次。该轮出现较差休眠结果；随后发现无线ADB干扰，因果尚不能归于属性。该属性试验仍已回退，最终保留false，不能将其列为已验证省电补丁。

GMS的`RECOMMEND_NETWORKS`没有对应Chimera实现，NetworkScoreService持续收到NullBinder/超大Binder响应。系统已有`network_recommendations_enabled=-1`强制关闭外部评分的分支，设备实测解绑且异常消失。它关闭外部网络推荐，不是删除Google服务；单独记录该Global设置，不能假定修改两张镜像就包含了它。原值与回退必须保存，新GMS版本重新验证是否仍有此缺陷。

## 功耗验收的坑

1. 无线ADB可能持有`AdbMulticastLock-comm`，改变组播过滤并影响`qcom_rx_wakelock`。即使不持续轮询也会干扰待机。恢复USB模式后核对`dumpsys adb`、无线调试开关和Wi-Fi组播锁是否释放。
2. 本设备shell`sleep 300`未按包含深睡的墙钟300秒结束。不可据此保证5分钟采样；使用经验证的包含休眠时间的定时器，或从电池历史截取真实拔线/插线边界。插线后抓到的电量和APSS终点不能直接算纯待机。
3. 本地约6分钟历史中CPU非运行占比约90.9%，这是BatteryStats事件积分，不是APSS计数器；电量计短时变化16mAh受采样/量化影响，不用于推算整夜耗电或宣称修复百分比。
4. 核对实际显示OFF/DOZE/DOZE_SUSPEND。开启全景息屏不代表整个采样段都显示壁纸，HIDE_TIME可能已使屏幕OFF。
5. QQ/GMS推送、基带和正常Doze检查会唤醒CPU；出现名字不等于缺陷。保留用户通知、SIM、定位与温控，不能通过全禁用制造省电结果。
6. `batterystats --checkin`可能消费/清除旧完成统计，先看本机帮助并备份。不要为测量清空历史。
7. UIAutomator失败可能留下上一次XML；每次先删除旧文件，确认本次输出新鲜。拍照异步保存可能超过3秒，结合新文件、缩略图、进程及日志验收。

公开仅包含方法和原创补丁工具。设备日志、定位信息、签名凭据与ROM二进制不属于skill内容。
