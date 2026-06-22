# Dataset Notes

## Preferred Dataset

- fastMRI knee single-coil validation subset for early experiments.
- Start with one or two HDF5 files before downloading the complete subset.

## Local Paths

Do not commit raw medical imaging data to this repository.

Suggested local environment variable:

```powershell
$env:FASTMRI_DATA = "D:\datasets\fastmri"
```

## Data Contract

The Python dataset adapter should return:

- `masked_kspace`: undersampled complex k-space tensor.
- `target`: reconstructed reference image.
- `mask`: sampling mask.
- `metadata`: acquisition and file identifiers.

