# W1 Log - MRI Basics and Baseline

## Objectives

- Understand k-space, undersampling, zero-filled reconstruction, PSNR, and SSIM.
- Prepare a small fastMRI-compatible dataset path.
- Run a local smoke test without downloading the full dataset.
- Document environment and blockers.

## Checklist

- [ ] Read fastMRI paper sections on dataset and baseline.
- [ ] Create Python environment.
- [ ] Run `python tools/smoke_check.py`.
- [ ] Add dataset path notes to `docs/dataset.md`.
- [ ] Produce first baseline report under `docs/performance/`.
- [ ] Stop before Jetson-only TensorRT benchmarking; see `docs/jetson_handoff.md`.

## Notes

Use a tiny local sample first. The full `knee_singlecoil_val` dataset is large, so the first engineering target is correct data plumbing rather than final model quality.
