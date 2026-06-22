import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.masks import cartesian_undersampling_mask
from mri_recon.phantom import synthetic_slice
from mri_recon.zero_filled import centered_fft2, zero_filled_magnitude


def test_synthetic_zero_filled_shape():
    target = synthetic_slice((32, 32))
    kspace = centered_fft2(target)
    mask = cartesian_undersampling_mask(target.shape, acceleration=4, center_fraction=0.1)
    recon = zero_filled_magnitude(kspace * mask)

    assert recon.shape == target.shape
    assert recon.dtype.name == "float32"

