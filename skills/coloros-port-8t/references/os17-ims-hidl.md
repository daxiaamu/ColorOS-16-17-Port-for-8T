# SIM 已识别但 IMS 电话不可用

先区分读卡、网络注册、IMS注册、真实通话四层。单卡机现场为LOADED,ABSENT，卡槽1语音和数据IN_SERVICE，订阅及Telecom账户均存在；不能把第二槽ABSENT认定为第一张卡未识别，也不能把网络注册成功当作通话成功。

## 根因与最小修复

PLK110 OS17的IMS APK仅保留AIDL实现。8T board API为30，实际提供IMS HIDL 1.7；工厂退回ImsRadioNotSupportedHal，日志显示ImsRadio HAL unavailable，MMTEL未注册、Voice/SMS等能力均为false。旧ColorOS16适配包仍包含原厂HIDL实现，但签名与当前包不同，未直接整体替换。

保持当前IMS应用、manifest、资源、JNI库和AIDL实现，只恢复旧版HIDL适配器的依赖闭包及原厂工厂回退分支。已核对243个缺失类，对当前应用的已存在方法和字段引用没有发现ABI缺项。再补入当前ROM共享库的9个HIDL manager类，避免新增manifest共享库需求。新增setAllCallBarringStatus接口不属于旧HIDL能力，明确抛出RemoteException，不假报成功；普通呼叫限制接口仍保留原实现。

只改变APK的classes.dex。保留原签名元数据不等于获得新的有效OEM签名；此方案依赖当前已验证的系统移植安装环境，不能声称可作为普通APK更新安装到原厂系统。不要扩大全局包签名绕过范围。

## 验证与边界

- 使用PMS实际共享库路径进行ART只加载探针：253类的加载、方法、构造和字段解析通过。ims-ext-common位于/product/framework，不能因探针写错路径而误判ROM缺库。
- system_ext相对dev35只变化一个APK；3401文件、3633 inode、3636 SELinux标签审计均零差异，镜像容量检查与完整读回通过。
- dev36重启后目标APK哈希符合候选；卡槽1MMTEL registration为2，Voice/Video/UT/SMS能力为true，未出现新的Java类/方法错误。请求用户检查SIM/信号、拨出、接听和双向声音后，用户回复“正常了”；软件链路与实体反馈均已记录。短信仅验证能力注册，未发送或接收短信测试。
- 不刷基带固件，不修改SIM/NV或个体校准，不关闭无线服务。已有subsys_daemon原生崩溃是另一条问题线，不能因IMS修复就宣称它已解决。
