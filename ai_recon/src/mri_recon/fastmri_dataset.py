from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np


@dataclass(frozen=True)
class FastMriSlice:
    masked_kspace: np.ndarray
    target: np.ndarray | None
    metadata: dict[str, object]


class FastMriH5Dataset:
    def __init__(self, root: Path | str, limit: int | None = None) -> None:
        self.root = Path(root)
        self.files = sorted(self.root.glob("*.h5"))
        if limit is not None:
            self.files = self.files[:limit]

    def __len__(self) -> int:
        return len(self.files)

    def __iter__(self) -> Iterator[FastMriSlice]:
        try:
            import h5py
        except ImportError as exc:
            raise RuntimeError("h5py is required to read fastMRI HDF5 files") from exc

        for file_path in self.files:
            with h5py.File(file_path, "r") as h5_file:
                kspace = np.asarray(h5_file["kspace"])
                target = np.asarray(h5_file["reconstruction_rss"]) if "reconstruction_rss" in h5_file else None
                attrs = {key: value for key, value in h5_file.attrs.items()}

            for slice_index in range(kspace.shape[0]):
                yield FastMriSlice(
                    masked_kspace=kspace[slice_index],
                    target=target[slice_index] if target is not None else None,
                    metadata={"file": file_path.name, "slice": slice_index, **attrs},
                )
