# 可公开代码与补丁执行约定

此目录提供原创工具和少量兼容逻辑，不含 OEM APK/JAR、完整反编译文件或签名密钥。仓库 MIT 许可覆盖本项目原创部分；读者自行取得供体输入并遵守其许可。

## 按方法定位的离线补丁工具

[patch_smali.py](../scripts/patch_smali.py) 在已审阅的 smali 树上执行替换：输入 SHA256、相对文件路径、完整方法签名、原指令片段和预期次数全部必须匹配。所有文件通过预检查才输出新目录；不会修改源树、组装 DEX、改签名或刷机。输出只含变化文件及哈希报告，不能直接当完整 smali 树组装。

```text
python scripts/patch_smali.py pristine-smali reviewed-plan.json changed-smali
```

命令路径相对技能目录。最小计划格式：

```json
{
  "schema": 1,
  "files": [{
    "path": "example/Config.smali",
    "sha256": "填写此输入文件真实的64位小写SHA256",
    "edits": [{
      "method": "getLimit()I",
      "before": "const/16 v0, 0xa",
      "after": "const/16 v0, 0x32",
      "count": 1
    }]
  }]
}
```

这是结构示例，不是供体可直接执行的配方。输入哈希来自固定工具版本反编译的实际文件；同一二进制由不同工具输出不同文本时必须重新审阅。方法零匹配、多匹配或原始片段改变均停止，禁止修改哈希来绕过审阅。它只验证文本前提，不验证寄存器活跃性、控制流、权限或功能正确性。

将变化文件合并到单独的完整副本，组装后再次反编译，比较所有类和方法的变化范围；hidden API 表、DEX 校验、JAR 条目、过期 fsv_meta、签名策略、EROFS inode/链接/SELinux 均独立验证。新供体已修复的问题应退役旧补丁。

## 已验证兼容逻辑的原创片段

- [camera-hal-guard.smali.inc](../assets/camera-hal-guard.smali.inc)：进入相机同步预优化前检查 SendExtCamCmd HAL 是否声明。源版本入口为 `OplusOptimizeRUSHelper.needOptimizeForCamera(String)`。无声明时返回 false；有声明保留原分支。核对 v0 在插入点可安全使用、局部标签唯一、调用权限和新版本方法行为。QQ 已验收，不宣称所有第三方相机通过。
- [system-job-budget.smali.inc](../assets/system-job-budget.smali.inc)：原系统 UID 专用 Job 配额辅助方法。须放在 `OplusJobCountPolicy`，并仅替换已核实的 UID 1000 配额分支；原有普通应用分支不能改动。新系统若服务类或返回类型变化必须重新适配。完整背景见 [clone-lifecycle](clone-lifecycle.md)。

片段不是独立 APK，也不是跨版本通用偏移补丁。先单独组装检查语法，再在实际完整 DEX 中组装、反编译和实机回归。测试 APK及临时权限不进入成品。

## 新供体交接产物

沿 [donor-update](donor-update.md) 保存只读原始清单、补丁账本、工具版本、配置、变化类/资源清单、输出哈希和实测矩阵。按内容哈希缓存，不能只按版本字符串命中。公开资料保留语义及必要哈希；设备标识、私人地址、校准备份、完整调试日志及 OEM 二进制留在私有工程。
