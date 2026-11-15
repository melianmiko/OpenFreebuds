# OpenFreebuds 一键运行脚本
# 用法: 双击 run.bat，或在 PowerShell 中执行 ./run.ps1
#       字体引擎默认 FreeType；想回 DirectWrite 用 ./run.ps1 -FontEngine directwrite
param(
    [string]$FontEngine = "freetype",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$AppArgs
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$Mirror = "https://pypi.tuna.tsinghua.edu.cn/simple"
$PrebuiltIndex = "https://code.mmk.pw/api/packages/precompiled/pypi/simple/"

function Write-Step([string]$Text) {
    Write-Host ""
    Write-Host "==> $Text" -ForegroundColor Cyan
}

function Fail([string]$Text) {
    Write-Host $Text -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 1. 检查 Python
Write-Step "检查 Python"

function Resolve-Python {
    # 优先环境变量 → python.exe 真实路径 → py 启动器 → 常见安装路径
    $candidates = @()
    if ($env:OFB_PYTHON) { $candidates += $env:OFB_PYTHON }
    $candidates += @(Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue |
            ForEach-Object { $_.Source })
    $pyLauncher = (Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1).Source
    if ($pyLauncher) {
        $candidates += (& $pyLauncher -3 -c "import sys; print(sys.executable)" 2>$null)
    }
    $candidates += @(
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
        "C:\Python314\python.exe"
    )

    $existing = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
    foreach ($c in $existing) {
        # 能 import PyQt6 的那个才是我们要用的解释器（PATH 里可能还有别的 python）
        & $c -c "import PyQt6" 2>$null
        if ($LASTEXITCODE -eq 0) { return $c }
    }
    return ($existing | Select-Object -First 1)
}

$python = Resolve-Python
if (-not $python) {
    Fail "未找到 python.exe，请安装 Python 3.14（或设置环境变量 OFB_PYTHON 指向解释器）。"
}
$pyVersion = & $python --version
Write-Host "$pyVersion ($python)"

# 2. 检查依赖，缺失时安装
Write-Step "检查运行依赖"
& $python -c "import PyQt6, qasync, aiohttp, pynput, psutil, PIL, yaml, aiocmd, dbus_next, winsdk" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "依赖不完整，开始安装（首次运行需要几分钟）..."
    & $python -m pip install --disable-pip-version-check `
        -i $Mirror `
        --extra-index-url $PrebuiltIndex `
        --trusted-host code.mmk.pw `
        aiocmd pillow psutil aiohttp qasync pynput dbus-next pyyaml winsdk PyQt6
    if ($LASTEXITCODE -ne 0) {
        Fail "依赖安装失败，请检查网络后重试。"
    }
    # lrelease 由 PySide6 提供，仅用于编译翻译
    & $python -c "import PySide6" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "安装 PySide6（仅用于编译翻译文件）..."
        & $python -m pip install --disable-pip-version-check -i $Mirror PySide6-Essentials
    }
}
else {
    Write-Host "依赖已就绪"
}

$scriptsDir = & $python -c "import sysconfig; print(sysconfig.get_path('scripts'))"

# 3. 按需把 .ui 编译成 .py
Write-Step "检查 Qt Designer 界面"
$designerDir = Join-Path $PSScriptRoot "openfreebuds_qt\designer"
$pyuic6 = Join-Path $scriptsDir "pyuic6.exe"
$staleUi = @(Get-ChildItem $designerDir -Filter *.ui | Where-Object {
    $pyFile = Join-Path $designerDir ($_.BaseName + ".py")
    -not (Test-Path $pyFile) -or (Get-Item $pyFile).LastWriteTime -lt $_.LastWriteTime
})
if ($staleUi.Count -gt 0) {
    if (Test-Path $pyuic6) {
        Write-Host "重新生成 $($staleUi.Count) 个界面模块..."
        & $pyuic6 "$designerDir\"
        if ($LASTEXITCODE -ne 0) { Fail "pyuic6 编译失败。" }
    }
    else {
        Write-Host "未找到 pyuic6，跳过界面生成（使用现有 .py）。" -ForegroundColor Yellow
    }
}
else {
    Write-Host "界面模块已是最新"
}

# 4. 按需把 .ts 编译成 .qm
Write-Step "检查翻译文件"
$i18nDir = Join-Path $PSScriptRoot "openfreebuds_qt\assets\i18n"
$pysideDir = & $python -c "import os, PySide6; print(os.path.dirname(PySide6.__file__))" 2>$null
$lrelease = if ($pysideDir) { Join-Path $pysideDir "lrelease.exe" } else { $null }
$staleTs = @(Get-ChildItem $i18nDir -Filter *.ts | Where-Object {
    $qmFile = Join-Path $i18nDir ($_.BaseName + ".qm")
    -not (Test-Path $qmFile) -or (Get-Item $qmFile).LastWriteTime -lt $_.LastWriteTime
})
if ($staleTs.Count -gt 0) {
    if ($lrelease -and (Test-Path $lrelease)) {
        Write-Host "重新生成 $($staleTs.Count) 个翻译文件..."
        & $lrelease (Get-ChildItem $i18nDir -Filter *.ts | ForEach-Object { $_.FullName }) | Out-Null
        if ($LASTEXITCODE -ne 0) { Fail "lrelease 编译失败。" }
    }
    else {
        Write-Host "未找到 lrelease，跳过翻译编译（界面将回退为英文）。" -ForegroundColor Yellow
    }
}
else {
    Write-Host "翻译文件已是最新"
}

# 5. 启动（通过 -c 调用入口，避免 runpy 重复加载警告）
Write-Step "启动 OpenFreebuds"
if ($FontEngine -and $FontEngine -ne "directwrite" -and $FontEngine -ne "dw" -and $FontEngine -ne "none") {
    $env:QT_QPA_PLATFORM = "windows:fontengine=$FontEngine"
}
else {
    Remove-Item Env:\QT_QPA_PLATFORM -ErrorAction SilentlyContinue
}
Write-Host "字体引擎: $(if ($env:QT_QPA_PLATFORM) { $FontEngine } else { 'DirectWrite (默认)' })"
$launchCode = "import sys; sys.argv[0] = 'openfreebuds_qt'; from openfreebuds_qt.launcher import main; main()"
& $python -c $launchCode @AppArgs
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Fail "程序退出，代码 $exitCode。"
}
