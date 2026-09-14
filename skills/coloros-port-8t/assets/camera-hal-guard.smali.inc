# Optional donor HAL must be declared before enabling its synchronous pre-open path.
    const-string v0, "vendor.oplus.hardware.sendextcamcmd.ISendExtCamCmdService/default"
    invoke-static {v0}, Landroid/os/ServiceManager;->isDeclared(Ljava/lang/String;)Z
    move-result v0
    if-nez v0, :port8t_hal_available
    const/4 v0, 0x0
    return v0
    :port8t_hal_available
