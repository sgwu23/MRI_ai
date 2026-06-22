from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def write_secondary_capture(image: np.ndarray, output_path: Path, patient_id: str = "DEMO") -> Path:
    try:
        import pydicom
        from pydicom.dataset import FileDataset, FileMetaDataset
        from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid
    except ImportError as exc:
        raise RuntimeError("pydicom is required for DICOM writing") from exc

    normalized = np.asarray(image, dtype=np.float32)
    normalized = normalized - float(normalized.min())
    peak = float(normalized.max())
    if peak > 0.0:
        normalized = normalized / peak
    pixels = (normalized * 65535.0).astype(np.uint16)

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(str(output_path), {}, file_meta=meta, preamble=b"\0" * 128)
    ds.PatientName = "MRI^Demo"
    ds.PatientID = patient_id
    ds.Modality = "MR"
    ds.SOPClassUID = SecondaryCaptureImageStorage
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.Rows, ds.Columns = pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.PixelData = pixels.tobytes()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pydicom.dcmwrite(str(output_path), ds, write_like_original=False)
    return output_path


def read_pixel_array(path: Path) -> Any:
    try:
        import pydicom
    except ImportError as exc:
        raise RuntimeError("pydicom is required for DICOM reading") from exc

    return pydicom.dcmread(str(path)).pixel_array
