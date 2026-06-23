# fastMRI v1 Reconstruction Visualization

- Source: `synthetic phantom smoke sample`
- Checkpoint: `outputs\models\unet_fastmri_v1_best.pth`
- Crop size: `320x320`
- Acceleration: `4x`
- Seed: `1234`

Panels:

1. `01_input_kspace.png`: undersampled k-space log magnitude
2. `02_zero_filled.png`: zero-filled image sent to the model
3. `03_model_reconstruction.png`: U-Net reconstruction
4. `04_target.png`: target image

The contact sheet is `fastmri_v1_reconstruction_contact_sheet.png`.

![fastMRI v1 reconstruction contact sheet](fastmri_v1_reconstruction_contact_sheet.png)
