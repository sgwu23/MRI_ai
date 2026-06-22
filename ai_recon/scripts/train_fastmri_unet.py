from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.metrics import mse, psnr
from mri_recon.models import build_unet
from mri_recon.zero_filled import zero_filled_magnitude


class FastMriSliceDataset:
    def __init__(self, data_root: Path, max_slices: int, acceleration: int) -> None:
        try:
            import h5py  # noqa: F401
            import torch
        except ImportError as exc:
            raise RuntimeError("h5py and torch are required for fastMRI training") from exc

        self._torch = torch
        self.data_root = data_root
        self.acceleration = acceleration
        self.index: list[tuple[Path, int]] = []
        for file_path in sorted(data_root.glob("*.h5")):
            with self._open_h5(file_path) as h5_file:
                slices = int(h5_file["kspace"].shape[0])
            for slice_index in range(slices):
                self.index.append((file_path, slice_index))
                if len(self.index) >= max_slices:
                    return

    def __len__(self) -> int:
        return len(self.index)

    def __getitem__(self, item: int):
        file_path, slice_index = self.index[item]
        with self._open_h5(file_path) as h5_file:
            kspace = np.asarray(h5_file["kspace"][slice_index])
            target = self._target_from_h5(h5_file, kspace, slice_index)

        masked_kspace = self._undersample(kspace, seed=item)
        masked = zero_filled_magnitude(masked_kspace)
        target = self._normalize(target)
        masked = self._normalize(masked)

        return {
            "masked_image": self._torch.from_numpy(masked[None, :, :]).float(),
            "target": self._torch.from_numpy(target[None, :, :]).float(),
        }

    @staticmethod
    def _open_h5(path: Path):
        import h5py

        return h5py.File(path, "r")

    @staticmethod
    def _target_from_h5(h5_file, kspace: np.ndarray, slice_index: int) -> np.ndarray:
        if "reconstruction_rss" in h5_file:
            return np.asarray(h5_file["reconstruction_rss"][slice_index], dtype=np.float32)
        if "reconstruction_esc" in h5_file:
            return np.asarray(h5_file["reconstruction_esc"][slice_index], dtype=np.float32)
        return zero_filled_magnitude(kspace)

    def _undersample(self, kspace: np.ndarray, seed: int) -> np.ndarray:
        cols = kspace.shape[-1]
        rng = np.random.default_rng(seed)
        mask = np.zeros(cols, dtype=np.float32)
        center_cols = max(1, int(round(cols * 0.08)))
        start = (cols - center_cols) // 2
        mask[start : start + center_cols] = 1.0
        target_cols = max(center_cols, cols // self.acceleration)
        candidates = np.setdiff1d(np.arange(cols), np.arange(start, start + center_cols))
        extra = max(0, target_cols - center_cols)
        if extra > 0 and len(candidates) > 0:
            mask[rng.choice(candidates, size=min(extra, len(candidates)), replace=False)] = 1.0
        return kspace * mask

    @staticmethod
    def _normalize(image: np.ndarray) -> np.ndarray:
        image = np.asarray(image, dtype=np.float32)
        image = image - float(image.min())
        peak = float(image.max())
        if peak > 0.0:
            image = image / peak
        return image.astype(np.float32)


def evaluate(model, loader, device) -> tuple[float, float, float]:
    import torch

    model.eval()
    model_scores: list[float] = []
    zero_scores: list[float] = []
    losses: list[float] = []
    with torch.no_grad():
        for batch in loader:
            masked = batch["masked_image"].to(device)
            target = batch["target"].to(device)
            pred = model(masked)
            losses.append(float(torch.nn.functional.l1_loss(pred, target).item()))
            for index in range(pred.shape[0]):
                target_np = target[index, 0].detach().cpu().numpy()
                pred_np = pred[index, 0].detach().cpu().numpy()
                masked_np = masked[index, 0].detach().cpu().numpy()
                model_scores.append(psnr(target_np, pred_np))
                zero_scores.append(psnr(target_np, masked_np))
    return float(np.mean(losses)), float(np.mean(model_scores)), float(np.mean(zero_scores))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--max-slices", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--acceleration", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "models" / "unet_fastmri_smoke.pth")
    parser.add_argument("--report", type=Path, default=ROOT / "docs" / "performance" / "fastmri_smoke_eval.md")
    args = parser.parse_args()

    try:
        import torch
        from torch.utils.data import DataLoader, random_split
    except ImportError as exc:
        raise SystemExit("PyTorch is required for fastMRI training.") from exc

    dataset = FastMriSliceDataset(args.data_root, args.max_slices, args.acceleration)
    if len(dataset) < 4:
        raise SystemExit(f"Need at least 4 slices, found {len(dataset)} under {args.data_root}")

    val_size = max(1, len(dataset) // 5)
    train_size = len(dataset) - val_size
    train_set, val_set = random_split(dataset, [train_size, val_size], generator=torch.Generator().manual_seed(7))
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False, num_workers=0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_unet().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    loss_fn = torch.nn.L1Loss()

    print(f"data_root={args.data_root}")
    print(f"slices={len(dataset)} train={train_size} val={val_size} device={device}")

    for epoch in range(args.epochs):
        model.train()
        total = 0.0
        for batch in train_loader:
            masked = batch["masked_image"].to(device)
            target = batch["target"].to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(masked)
            loss = loss_fn(pred, target)
            loss.backward()
            optimizer.step()
            total += float(loss.item())
        val_loss, model_psnr, zero_psnr = evaluate(model, val_loader, device)
        print(
            f"epoch={epoch + 1} train_l1={total / max(len(train_loader), 1):.6f} "
            f"val_l1={val_loss:.6f} model_psnr={model_psnr:.2f} zero_psnr={zero_psnr:.2f}",
            flush=True,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.detach().cpu().state_dict()}, args.output)
    val_loss, model_psnr, zero_psnr = evaluate(model.to(device), val_loader, device)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        "\n".join(
            [
                "# fastMRI Smoke Evaluation",
                "",
                f"- Data root: `{args.data_root}`",
                f"- Slices: `{len(dataset)}`",
                f"- Train/val: `{train_size}/{val_size}`",
                f"- Acceleration: `{args.acceleration}x`",
                f"- Validation L1: `{val_loss:.6f}`",
                f"- Model PSNR: `{model_psnr:.2f} dB`",
                f"- Zero-filled PSNR: `{zero_psnr:.2f} dB`",
                f"- Checkpoint: `{args.output}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"saved {args.output}")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
