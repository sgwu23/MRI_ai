$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root "build\gcc"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

g++ `
  -std=c++17 `
  -Wall `
  -Wextra `
  -pedantic `
  -I (Join-Path $root "cpp_inference\include") `
  (Join-Path $root "cpp_inference\src\inference_engine.cpp") `
  (Join-Path $root "cpp_inference\src\main.cpp") `
  -o (Join-Path $outDir "mri_inference_demo.exe")

& (Join-Path $outDir "mri_inference_demo.exe")
