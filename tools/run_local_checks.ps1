$ErrorActionPreference = "Stop"

python tools/smoke_check.py
python ai_recon/scripts/baseline_report.py --output docs/performance/baseline_local.md
python tools/validate_sequence.py firmware/sequences/spin_echo_demo.json
python -m pytest tests

if (Get-Command g++ -ErrorAction SilentlyContinue) {
    powershell -ExecutionPolicy Bypass -File tools/build_cpp_gcc.ps1
} else {
    Write-Warning "g++ not found; skipping local C++ build"
}
