# Cloud Training Plan - fastMRI

This document is the handoff plan for training a real MRI reconstruction model on rented cloud GPU. Local workstation and Jetson are now proven for deployment; heavy training should move to cloud.

## Official Dataset Links

- fastMRI official project and code: https://github.com/facebookresearch/fastMRI
- fastMRI dataset page: https://fastmri.med.nyu.edu/
- fastMRI data README: https://github.com/facebookresearch/fastMRI/blob/main/fastmri/data/README.md
- MONAI official tutorials: https://github.com/Project-MONAI/tutorials
- MONAI project site: https://project-monai.github.io/

The fastMRI repository states that the data is distributed as HDF5 files, with each HDF5 file containing one MR acquisition. Start with a small validation subset before downloading full training data.

## Recommended First Dataset

Use fastMRI knee single-coil data first.

Why:

- It is simpler than multi-coil reconstruction.
- Current project code already expects HDF5 k-space-like inputs.
- It is enough to produce a credible first PSNR/SSIM table.

Suggested stages:

1. Download only several `knee_singlecoil_val` HDF5 files and run smoke tests.
2. Train on a small subset, such as 50 to 200 slices.
3. Scale to more files only after the training/eval scripts are stable.

## Cloud GPU Recommendation

Minimum useful setup:

- GPU: RTX 3090, RTX 4090, A10, A40, or L4.
- VRAM: 16 GB or more.
- Disk: 100 GB minimum for a small subset, 300 GB or more if downloading larger fastMRI splits.
- Python: 3.10 or 3.11.
- PyTorch: CUDA-enabled build matching the cloud image.

For AutoDL-style machines, choose a PyTorch image with CUDA already installed.

## Cloud Setup

```bash
git clone <your-repo-url> mri-edge-rtos-ai
cd mri-edge-rtos-ai
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r ai_recon/requirements.txt
```

If PyTorch is already installed in the cloud image, install the remaining packages without replacing it:

```bash
pip install h5py monai scikit-image onnx onnxruntime tqdm pydicom pytest
```

## Dataset Layout

Keep raw data outside git:

```text
/root/autodl-tmp/fastmri/
  knee_singlecoil_train/
    file1000000.h5
    ...
  knee_singlecoil_val/
    file1000001.h5
    ...
```

Set:

```bash
export FASTMRI_DATA=/root/autodl-tmp/fastmri
```

## Training Commands

Synthetic sanity run:

```bash
python ai_recon/scripts/train_unet.py \
  --epochs 8 \
  --synthetic-samples 64 \
  --batch-size 8 \
  --output outputs/models/unet_synthetic_cloud_smoke.pth
```

Formal fastMRI training with the official validation split:

```bash
python ai_recon/scripts/train_fastmri_unet.py \
  --train-root "$FASTMRI_DATA/knee_singlecoil_train" \
  --val-root "$FASTMRI_DATA/knee_singlecoil_val" \
  --max-train-slices 10000 \
  --max-val-slices 1000 \
  --epochs 20 \
  --batch-size 8 \
  --num-workers 4 \
  --crop-size 320 \
  --acceleration 4 \
  --amp \
  --patience 5 \
  --output outputs/models/unet_fastmri_v1_best.pth \
  --last-output outputs/models/unet_fastmri_v1_last.pth \
  --report docs/performance/fastmri_v1_eval.md
```

The best validation-PSNR checkpoint is saved to `--output`. The latest epoch is
always saved to `--last-output`, so a preempted cloud job can resume safely:

```bash
python ai_recon/scripts/train_fastmri_unet.py \
  --train-root "$FASTMRI_DATA/knee_singlecoil_train" \
  --val-root "$FASTMRI_DATA/knee_singlecoil_val" \
  --max-train-slices 10000 \
  --max-val-slices 1000 \
  --epochs 20 \
  --batch-size 8 \
  --num-workers 4 \
  --crop-size 320 \
  --amp \
  --resume outputs/models/unet_fastmri_v1_last.pth \
  --output outputs/models/unet_fastmri_v1_best.pth \
  --last-output outputs/models/unet_fastmri_v1_last.pth \
  --report docs/performance/fastmri_v1_eval.md
```

Export to ONNX:

```bash
python ai_recon/scripts/export_onnx.py \
  --checkpoint outputs/models/unet_fastmri_v1_best.pth \
  --output outputs/models/unet_fastmri_v1_best.onnx
```

Then copy the ONNX file back to the local workstation and Jetson for TensorRT conversion.

## What To Send Back From Cloud

Copy these files back:

- `outputs/models/*.pth`
- `outputs/models/*.onnx`
- `docs/performance/*fastmri*.md`
- Training logs.

Do not copy the raw fastMRI dataset into git.

## Success Criteria

First acceptable result:

- The model runs on a held-out fastMRI validation subset.
- PSNR improves over zero-filled reconstruction.
- ONNX export succeeds.
- TensorRT FP16 engine builds on Jetson.

Resume-grade target:

- Report PSNR/SSIM on a clearly defined validation subset.
- Report Jetson FP16 latency using `trtexec` and C++ service path.
- Include exact data split size and acceleration factor.
