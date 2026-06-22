import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.dicom_io import read_pixel_array, write_secondary_capture


def test_dicom_round_trip_when_pydicom_is_installed(tmp_path):
    pytest.importorskip("pydicom")

    image = np.ones((16, 16), dtype=np.float32)
    path = write_secondary_capture(image, tmp_path / "demo.dcm")
    pixels = read_pixel_array(path)

    assert pixels.shape == image.shape
