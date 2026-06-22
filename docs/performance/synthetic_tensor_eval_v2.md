# Synthetic Tensor Reconstruction Eval

This report evaluates a Jetson TensorRT C++ output tensor against the local synthetic target.

- Output file: `outputs\samples\synthetic_recon_output_v2.bin`
- Target file: `outputs\samples\synthetic_target.npy`
- Output shape: `(128, 128)`
- Output min/max: `-0.000751 / 1.107422`
- Raw output MSE: `0.007471`
- Raw output PSNR: `21.27 dB`
- Normalized output MSE: `0.010976`
- Normalized output PSNR: `19.60 dB`
- Zero-filled masked MSE: `0.007620`
- Zero-filled masked PSNR: `21.18 dB`

Note: the current model is a tiny scaffold model trained only for pipeline validation.
These quality numbers are not resume-grade yet; they prove the data path.
