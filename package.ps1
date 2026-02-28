# 打包 Blender 插件脚本 (PowerShell)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AddonName = "gn_backdrop"

# 读取版本号
$InitFile = Join-Path $ScriptDir "__init__.py"
if (Test-Path $InitFile) {
    $Content = Get-Content $InitFile -Raw
    if ($Content -match '"version":\s*\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)') {
        $Version = "$($matches[1]).$($matches[2]).$($matches[3])"
    } else {
        $Version = "0.0.0"
        Write-Warning "无法从 __init__.py 提取版本号，使用默认值 0.0.0"
    }
} else {
    Write-Error "找不到 __init__.py"
    exit 1
}

$OutputName = "${AddonName}_v${Version}.zip"
# 输出到父级目录
$ParentDir = Split-Path -Parent $ScriptDir
$OutputFile = Join-Path $ParentDir $OutputName

Write-Host "正在打包 $AddonName v$Version ..." -ForegroundColor Cyan
Write-Host "输出文件: $OutputFile"

# 定义需要打包的文件列表（白名单模式）
$FilesToPackage = @(
    "__init__.py",
    "backdrop_draw.py",
    "LICENSE",
    "README.md"
)

# 创建临时构建目录
$BuildDir = Join-Path $ScriptDir "build_temp"
if (Test-Path $BuildDir) {
    Remove-Item $BuildDir -Recurse -Force
}
$TargetDir = Join-Path $BuildDir $AddonName
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

# 复制文件
foreach ($File in $FilesToPackage) {
    $SourcePath = Join-Path $ScriptDir $File
    if (Test-Path $SourcePath) {
        Copy-Item -Path $SourcePath -Destination $TargetDir -Recurse
    } else {
        Write-Warning "⚠️ 文件未找到: $File"
    }
}

# 打包
if (Test-Path $OutputFile) {
    Remove-Item $OutputFile -Force
}

Compress-Archive -Path $TargetDir -DestinationPath $OutputFile -Force

# 清理
Remove-Item $BuildDir -Recurse -Force

if (Test-Path $OutputFile) {
    $Size = (Get-Item $OutputFile).Length / 1KB
    Write-Host "✅ 打包成功: $OutputName" -ForegroundColor Green
    Write-Host "文件路径: $OutputFile"
    Write-Host ("文件大小: {0:N2} KB" -f $Size)
} else {
    Write-Host "❌ 打包失败" -ForegroundColor Red
    exit 1
}
