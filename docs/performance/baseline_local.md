# Local Zero-Filled Baseline

This report uses a deterministic synthetic MRI-like slice. It verifies the
reconstruction plumbing before fastMRI data and Jetson deployment are connected.

- Image shape: `(128, 128)`
- Acceleration: `4x`
- MSE: `0.007620`
- PSNR: `21.18 dB`

Next measured report should replace this synthetic source with fastMRI HDF5 files.
