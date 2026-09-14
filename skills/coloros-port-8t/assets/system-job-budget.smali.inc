.method private static port8tSystemJobBudget()I
    .registers 3
    const/16 v0, 0xc8
    :try_start
    invoke-static {}, Lcom/android/server/am/OplusMultiAppManagerService;->getInstance()Lcom/android/server/am/OplusMultiAppManagerService;
    move-result-object v1
    if-eqz v1, :done
    invoke-virtual {v1}, Lcom/android/server/am/OplusMultiAppManagerService;->getCloneUserInfo()Ljava/util/List;
    move-result-object v1
    if-eqz v1, :done
    invoke-interface {v1}, Ljava/util/List;->size()I
    move-result v1
    const/16 v2, 0x32
    invoke-static {v1, v2}, Ljava/lang/Math;->min(II)I
    move-result v1
    add-int/lit8 v1, v1, -0xa
    if-lez v1, :done
    mul-int/lit8 v1, v1, 0x8
    add-int/2addr v0, v1
    :try_end
    .catch Ljava/lang/RuntimeException; {:try_start .. :try_end} :failed
    :done
    return v0
    :failed
    move-exception v1
    return v0
.end method
