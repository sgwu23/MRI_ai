import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.masks import cartesian_undersampling_mask


def test_full_mask_when_acceleration_is_one():
    mask = cartesian_undersampling_mask((8, 8), acceleration=1, center_fraction=0.1)
    assert mask.shape == (8, 8)
    assert mask.sum() == 64


def test_undersampling_mask_keeps_center_columns():
    mask = cartesian_undersampling_mask((8, 16), acceleration=4, center_fraction=0.25)
    center = mask[:, 6:10]
    assert center.sum() == center.size
