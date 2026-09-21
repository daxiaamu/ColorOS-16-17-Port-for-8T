# OS17 屏幕色彩模式无效（已复现，尚未修复）

原生 UI 依次切换自然、鲜明、标准，系统 display_color_mode 对应 303、307、301，secure oplus_customize_color_mode 对应 11、12、10。设置与框架观察者均有响应，但 SurfaceFlinger/HWC/SDM 始终为 Native、render intent 0。

同一切换窗口出现 `map unknown (DCI-P3 sRGB Full range)/(Unknown RenderIntent) to default color mode`。这比仅凭截图或设置值变化更能定位兼容失败：供体模式/渲染意图与旧显示栈协商不匹配。尚未确定应修哪一层映射，不能直接把 301 等枚举写到面板 seed 节点。

当前显示栈支持 NATIVE、SRGB、DISPLAY_P3，SDM 有 adapt_P3、adapt_sRGB、cinema_P3 等配置。应对照原厂模式映射，保留正常 HDR/色彩管理、色温及护眼状态。测试前护眼处于开启；本轮未改变护眼设置，完成后恢复原选中的标准模式。截图无法证明实体色域变化。

此项是在 dev67 整包离线校验后发现，新合版尚不含修复。后续修复需确认三档真实下发不同的受支持模式，再验证色温/护眼/HDR 共存及实体屏表现。
