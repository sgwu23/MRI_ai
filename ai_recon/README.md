# AI Reconstruction

This module will contain the fastMRI/MONAI reconstruction pipeline.

Initial implementation order:

1. Dataset adapter for fastMRI HDF5 files.
2. Zero-filled reconstruction baseline.
3. Lightweight U-Net training loop.
4. PSNR/SSIM evaluation.
5. ONNX export and parity check.

Local workflow before Jetson is connected:

```powershell
python ai_recon/scripts/baseline_report.py --output docs/performance/baseline_local.md
python tools/smoke_check.py
```

Training and ONNX export require PyTorch:

```powershell
python ai_recon/scripts/train_unet.py --epochs 1 --synthetic-samples 16 --output outputs/models/unet_demo.pth
python ai_recon/scripts/export_onnx.py --checkpoint outputs/models/unet_demo.pth --output outputs/models/unet_demo.onnx
python ai_recon/scripts/check_onnx_parity.py --onnx outputs/models/unet_demo.onnx
```

Cloud fastMRI smoke training:

```powershell
python ai_recon/scripts/train_fastmri_unet.py --data-root %FASTMRI_DATA%\knee_singlecoil_val --max-slices 64 --epochs 3
```
