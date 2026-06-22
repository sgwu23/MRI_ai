# Synthetic Tensor Reconstruction Eval

This report evaluates a Jetson TensorRT C++ output tensor against the local synthetic target.

- Output file: `outputs\samples\synthetic_recon_output.bin`
- Target file: `outputs\samples\synthetic_target.npy`
- Output shape: `(128, 128)`
- Output min/max: `-0.137573 / -0.122620`
- Normalized output MSE: `0.298653`
- Normalized output PSNR: `5.25 dB`
- Zero-filled masked MSE: `0.007620`
- Zero-filled masked PSNR: `21.18 dB`

Note: the current model is a tiny scaffold model trained only for pipeline validation.
These quality numbers are not resume-grade yet; they prove the data path.
