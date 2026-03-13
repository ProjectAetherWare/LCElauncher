$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    pip install pyinstaller
}

$assetsPath = (Join-Path $scriptDir "Assets") -replace '\\', '/'
$addData = "${assetsPath};Assets"
$iconPath = (Join-Path $scriptDir "Assets\minilogo.png") -replace '\\', '/'

pyinstaller --onefile `
    --icon $iconPath `
    --name "MiniLauncher" `
    --add-data $addData `
    --windowed `
    --clean `
    --hidden-import PySide6 `
    --hidden-import PySide6.QtCore `
    --hidden-import PySide6.QtGui `
    --hidden-import PySide6.QtWidgets `
    --hidden-import PIL `
    --hidden-import PIL.Image `
    --hidden-import PIL.ImageFilter `
    main.py

# Create src.zip (source code archive)
$srcZipPath = Join-Path $scriptDir "dist\src.zip"
$tempSrcDir = Join-Path $env:TEMP "MiniLauncher_src"
if (Test-Path $tempSrcDir) { Remove-Item $tempSrcDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempSrcDir | Out-Null

# Copy source files
Copy-Item -Path (Join-Path $scriptDir "*.py") -Destination $tempSrcDir -Force
Copy-Item -Path (Join-Path $scriptDir "launcher") -Destination $tempSrcDir -Recurse -Force
Copy-Item -Path (Join-Path $scriptDir "Assets") -Destination $tempSrcDir -Recurse -Force
foreach ($f in @("requirements.txt", "build.ps1", "run.ps1")) {
    $p = Join-Path $scriptDir $f
    if (Test-Path $p) { Copy-Item $p -Destination $tempSrcDir -Force }
}

# Remove __pycache__ and .pyc
Get-ChildItem $tempSrcDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem $tempSrcDir -Recurse -Filter "*.pyc" | Remove-Item -Force

# Create zip
if (Test-Path $srcZipPath) { Remove-Item $srcZipPath -Force }
Compress-Archive -Path "$tempSrcDir\*" -DestinationPath $srcZipPath -Force
Remove-Item $tempSrcDir -Recurse -Force

Write-Host "Build complete. Output: dist\MiniLauncher.exe, dist\src.zip"
