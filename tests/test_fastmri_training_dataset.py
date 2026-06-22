import sys
from pathlib import Path

import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai_recon" / "scripts"))

from train_fastmri_unet import FastMriSliceDataset


def test_fastmri_center_crop_matches_reconstruction_shape():
    image = np.arange(640 * 368, dtype=np.float32).reshape(640, 368)

    cropped = FastMriSliceDataset._center_crop(image, (320, 320))

    assert cropped.shape == (320, 320)
    assert np.array_equal(cropped, image[160:480, 24:344])
