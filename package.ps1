# 打包 Blender 插件脚本 (PowerShell)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ParentDir = Split-Path -Parent $ScriptDir
$AddonName = "gn_backdrop"
$OutputFile = Join-Path $ParentDir "$AddonName.zip"

Write-Host "正在打包插件..."
Write-Host "源目录: $ScriptDir"
Write-Host "输出文件: $OutputFile"

# 删除旧的 zip 文件（如果存在）
if (Test-Path $OutputFile) {
    Remove-Item $OutputFile
    Write-Host "已删除旧的 zip 文件"
}

# 创建临时目录
$TempDir = Join-Path $env:TEMP "gn_backdrop_temp"
if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir | Out-Null

# 复制文件，排除不必要的文件
$ExcludePatterns = @("*.git*", "*__pycache__*", "*.pyc", "*.DS_Store", "*package.sh", "*package.ps1")
Copy-Item -Path $ScriptDir -Destination $TempDir -Recurse -Exclude $ExcludePatterns

# 打包
$TempAddonDir = Join-Path $TempDir $AddonName
Compress-Archive -Path $TempAddonDir -DestinationPath $OutputFile -Force

# 清理临时目录
Remove-Item $TempDir -Recurse -Force

if (Test-Path $OutputFile) {
    Write-Host "✓ 打包成功: $OutputFile" -ForegroundColor Green
    Write-Host "现在可以在 Blender 中安装此文件"
} else {
    Write-Host "✗ 打包失败" -ForegroundColor Red
    exit 1
}
