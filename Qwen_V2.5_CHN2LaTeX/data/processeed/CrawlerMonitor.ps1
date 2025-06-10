# ===== 1. 系统级UTF-8环境强制配置 =====
$env:PYTHONIOENCODING = "UTF-8"  # 强制Python使用UTF-8输出[9](@ref)
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 > $null  # 立即激活UTF-8代码页[11](@ref)

# ===== 2. 项目路径配置 =====
$projectRoot = "E:\Qwen_V2.5_CHN2LaTeX"
$crawlerScript = Join-Path $projectRoot ".\data\processeed\crawler.py"
$logFile = Join-Path $projectRoot ".\data\processeed\crawler.log"
$dataFile = Join-Path $projectRoot ".\data\raw\raw_data.jsonl"

# ===== 3. 智能日志初始化 =====
if (-not (Test-Path $logFile)) {
    # 带BOM的UTF-8写入确保兼容性
    [System.IO.File]::WriteAllText($logFile, "时间戳 | 运行时长(秒) | 总条目数 | 新增条目 | 状态`r`n", [System.Text.Encoding]::UTF8)
}

# ===== 4. 增强型监控循环 =====
$runCount = 0
$initialDataCount = if (Test-Path $dataFile) { 
    [System.IO.File]::ReadAllLines($dataFile, [System.Text.Encoding]::UTF8).Count 
} else { 0 }

while ($true) {
    $runCount++
    $startTime = Get-Date
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # --- 爬虫执行模块（三重编码保障）---
    Write-Host "[$timestamp] 启动爬虫脚本 (第 $runCount 次运行)" -ForegroundColor Cyan
    $output = python -X utf8 $crawlerScript 2>&1 | Out-String -Stream
    
    # 实时显示并记录日志
    $output | ForEach-Object {
        Write-Host $_ -ForegroundColor DarkGray
        # 同步写入日志防止中断丢失
        [System.IO.File]::AppendAllText($logFile, "$_`r`n", [System.Text.Encoding]::UTF8)
    }
    
    # --- 数据统计模块 ---
    $runDuration = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    $currentEntries = if (Test-Path $dataFile) { 
        [System.IO.File]::ReadAllLines($dataFile, [System.Text.Encoding]::UTF8).Count 
    } else { 0 }
    
    $newEntries = $currentEntries - $initialDataCount
    $initialDataCount = $currentEntries
    
    # --- 日志记录模块 ---
    $logEntry = "$timestamp | $runDuration | $currentEntries | $newEntries | 完成"
    [System.IO.File]::AppendAllText($logFile, "$logEntry`r`n", [System.Text.Encoding]::UTF8)
    
    # --- 控制台可视化报告 ---
    Write-Host "运行统计:" -ForegroundColor Yellow
    Write-Host "├─ 时长: $runDuration 秒" -ForegroundColor Green
    Write-Host "├─ 总数: $currentEntries" -ForegroundColor Cyan
    Write-Host "└─ 新增: $newEntries" -ForegroundColor Magenta
    
    # --- 数据样本展示 ---
    if ($newEntries -gt 0 -and (Test-Path $dataFile)) {
        $latestEntry = Get-Content $dataFile -Tail 1 -Encoding UTF8
        Write-Host "最新数据样例:" -ForegroundColor Yellow
        Write-Host "┌" + ("─" * 80)
        Write-Host $latestEntry -ForegroundColor Gray
        Write-Host "└" + ("─" * 80)
    }
    
    # --- 智能休眠策略 ---
    $interval = 15
    Write-Host "`n下一次爬取将在 $interval 秒后启动...`n" -ForegroundColor DarkGray
    for ($i = $interval; $i -gt 0; $i--) {
        Write-Progress -Activity "等待中" -Status "${i}s" -PercentComplete (($i/$interval)*100)
        Start-Sleep -Seconds 1
    }
    Write-Progress -Activity "等待中" -Completed
}