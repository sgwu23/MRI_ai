param(
    [string]$RepoRoot = "D:\A_work\project 4Autumn\mri-edge-rtos-ai",
    [string]$ZephyrBase = "D:\A_work\zephyrproject\zephyr",
    [string]$ZephyrEnv = "D:\A_work\zephyr-env",
    [string]$ZephyrSdk = "D:\A_work\zephyr-sdk",
    [string]$TempApp = "D:\A_work\mri_zephyr_app_irq",
    [string]$TempBuild = "D:\A_work\mri_zephyr_build_irq",
    [string]$Board = "olimex_stm32_h407"
)

$ErrorActionPreference = "Stop"

$appSource = Join-Path $RepoRoot "firmware\zephyr_app"
$artifactTarget = Join-Path $RepoRoot "build\zephyr-stm32f407\zephyr"
$cmake = Join-Path $ZephyrEnv "Library\bin\cmake.exe"
$ninja = Join-Path $ZephyrEnv "Library\bin\ninja.exe"

if (-not (Test-Path -LiteralPath $cmake)) {
    throw "CMake not found at $cmake"
}
if (-not (Test-Path -LiteralPath $ninja)) {
    throw "Ninja not found at $ninja"
}

if (Test-Path -LiteralPath $TempApp) {
    Remove-Item -LiteralPath $TempApp -Recurse -Force
}
if (Test-Path -LiteralPath $TempBuild) {
    Remove-Item -LiteralPath $TempBuild -Recurse -Force
}

Copy-Item -LiteralPath $appSource -Destination $TempApp -Recurse

$env:PATH = "D:\7-Zip;$ZephyrEnv;$ZephyrEnv\Scripts;$ZephyrEnv\Library\bin;" + $env:PATH
$env:ZEPHYR_BASE = $ZephyrBase
$env:ZEPHYR_TOOLCHAIN_VARIANT = "zephyr"
$env:ZEPHYR_SDK_INSTALL_DIR = $ZephyrSdk

& $cmake -S $TempApp -B $TempBuild -GNinja "-DBOARD=$Board"
if ($LASTEXITCODE -ne 0) {
    throw "CMake configure failed with exit code $LASTEXITCODE"
}

& $ninja -C $TempBuild
if ($LASTEXITCODE -ne 0) {
    throw "Ninja build failed with exit code $LASTEXITCODE"
}

New-Item -ItemType Directory -Force -Path $artifactTarget | Out-Null
Copy-Item -LiteralPath (Join-Path $TempBuild "zephyr\zephyr.hex") -Destination (Join-Path $artifactTarget "zephyr.hex") -Force
Copy-Item -LiteralPath (Join-Path $TempBuild "zephyr\zephyr.bin") -Destination (Join-Path $artifactTarget "zephyr.bin") -Force
Copy-Item -LiteralPath (Join-Path $TempBuild "zephyr\zephyr.elf") -Destination (Join-Path $artifactTarget "zephyr.elf") -Force

Write-Host "Built STM32F407 Zephyr firmware:"
Get-ChildItem -LiteralPath $artifactTarget -File |
    Where-Object { $_.Name -match '^zephyr\.(hex|bin|elf)$' } |
    Select-Object Name,Length,LastWriteTime
