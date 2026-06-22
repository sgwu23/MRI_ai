from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.metrics import psnr
from mri_recon.models import build_unet
from mri_recon.zero_filled import zero_filled_magnitude


class FastMriSliceDataset:
    def __init__(
        self,
        data_root: Path,
        max_slices: int,
        acceleration: int,
        crop_size: int = 320,
        mask_seed_offset: int = 0,
    ) -> None:
        try:
            import h5py  # noqa: F401
            import torch
        except ImportError as exc:
            raise RuntimeError("h5py and torch are required for fastMRI training") from exc

        self._torch = torch
        self.data_root = data_root
        self.acceleration = acceleration
        self.crop_shape = (crop_size, crop_size)
        self.mask_seed_offset = mask_seed_offset
        self.index: list[tuple[Path, int]] = []

        for file_path in sorted(data_root.rglob("*.h5")):
            with self._open_h5(file_path) as h5_file:
                slices = int(h5_file["kspace"].shape[0])
            for slice_index in range(slices):
                self.index.append((file_path, slice_index))

        if max_slices > 0 and len(self.index) > max_slices:
            index_rng = random.Random(mask_seed_offset)
            index_rng.shuffle(self.index)
            self.index = self.index[:max_slices]

    def __len__(self) -> int:
        return len(self.index)

    def __getitem__(self, item: int):
        file_path, slice_index = self.index[item]
        with self._open_h5(file_path) as h5_file:
            kspace = np.asarray(h5_file["kspace"][slice_index])
            target = self._target_from_h5(h5_file, kspace, slice_index)

        masked_kspace = self._undersample(kspace, seed=self.mask_seed_offset + item)
        masked = zero_filled_magnitude(masked_kspace)
        masked = self._center_crop(masked, self.crop_shape)
        target = self._center_crop(target, self.crop_shape)
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
            chosen = rng.choice(candidates, size=min(extra, len(candidates)), replace=False)
            mask[chosen] = 1.0
        return kspace * mask

    @staticmethod
    def _normalize(image: np.ndarray) -> np.ndarray:
        image = np.asarray(image, dtype=np.float32)
        image = image - float(image.min())
        peak = float(image.max())
        if peak > 0.0:
            image = image / peak
        return image.astype(np.float32)

    @staticmethod
    def _center_crop(image: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
        height, width = image.shape[-2:]
        target_height, target_width = shape
        if target_height > height or target_width > width:
            raise ValueError(f"Cannot crop image shape {image.shape[-2:]} to target shape {shape}")

        top = (height - target_height) // 2
        left = (width - target_width) // 2
        return np.asarray(
            image[..., top : top + target_height, left : left + target_width],
            dtype=np.float32,
        )


def make_loader(dataset, batch_size: int, shuffle: bool, num_workers: int, device):
    from torch.utils.data import DataLoader

    kwargs = {
        "dataset": dataset,
        "batch_size": batch_size,
        "shuffle": shuffle,
        "num_workers": num_workers,
        "pin_memory": device.type == "cuda",
        "persistent_workers": num_workers > 0,
    }
    if num_workers > 0:
        kwargs["prefetch_factor"] = 2
    return DataLoader(**kwargs)


def evaluate(model, loader, device, amp_enabled: bool) -> tuple[float, float, float]:
    import torch

    model.eval()
    model_scores: list[float] = []
    zero_scores: list[float] = []
    losses: list[float] = []
    with torch.no_grad():
        for batch in loader:
            masked = batch["masked_image"].to(device, non_blocking=True)
            target = batch["target"].to(device, non_blocking=True)
            with torch.cuda.amp.autocast(enabled=amp_enabled):
                pred = model(masked)
                loss = torch.nn.functional.l1_loss(pred, target)
            losses.append(float(loss.item()))
            for index in range(pred.shape[0]):
                target_np = target[index, 0].float().cpu().numpy()
                pred_np = pred[index, 0].float().cpu().numpy()
                masked_np = masked[index, 0].float().cpu().numpy()
                model_scores.append(psnr(target_np, pred_np))
                zero_scores.append(psnr(target_np, masked_np))
    return float(np.mean(losses)), float(np.mean(model_scores)), float(np.mean(zero_scores))


def checkpoint_payload(model, optimizer, scaler, scheduler, epoch: int, best_psnr: float, args) -> dict:
    return {
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scaler": scaler.state_dict(),
        "scheduler": scheduler.state_dict(),
        "epoch": epoch,
        "best_psnr": best_psnr,
        "config": vars(args),
    }


def write_report(
    path: Path,
    args,
    train_slices: int,
    val_slices: int,
    epoch: int,
    val_loss: float,
    model_psnr: float,
    zero_psnr: float,
    best_psnr: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# fastMRI Formal Training Evaluation",
                "",
                f"- Train root: `{args.train_root}`",
                f"- Validation root: `{args.val_root}`",
                f"- Train slices: `{train_slices}`",
                f"- Validation slices: `{val_slices}`",
                f"- Crop size: `{args.crop_size}x{args.crop_size}`",
                f"- Acceleration: `{args.acceleration}x`",
                f"- Completed epoch: `{epoch}`",
                f"- Validation L1: `{val_loss:.6f}`",
                f"- Current model PSNR: `{model_psnr:.2f} dB`",
                f"- Best model PSNR: `{best_psnr:.2f} dB`",
                f"- Zero-filled PSNR: `{zero_psnr:.2f} dB`",
                f"- Best checkpoint: `{args.output}`",
                f"- Last checkpoint: `{args.last_output}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-root", type=Path, required=True)
    parser.add_argument("--val-root", type=Path, required=True)
    parser.add_argument("--max-train-slices", type=int, default=10000, help="Use 0 for all slices")
    parser.add_argument("--max-val-slices", type=int, default=1000, help="Use 0 for all slices")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--crop-size", type=int, default=320)
    parser.add_argument("--acceleration", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=5, help="Early-stop patience; use 0 to disable")
    parser.add_argument("--log-every", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    amp_group = parser.add_mutually_exclusive_group()
    amp_group.add_argument("--amp", dest="amp", action="store_true")
    amp_group.add_argument("--no-amp", dest="amp", action="store_false")
    parser.set_defaults(amp=True)
    parser.add_argument("--resume", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs" / "models" / "unet_fastmri_best.pth",
    )
    parser.add_argument(
        "--last-output",
        type=Path,
        default=ROOT / "outputs" / "models" / "unet_fastmri_last.pth",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "docs" / "performance" / "fastmri_formal_eval.md",
    )
    args = parser.parse_args()

    try:
        import torch
    except ImportError as exc:
        raise SystemExit("PyTorch is required for fastMRI training.") from exc

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
        torch.backends.cudnn.benchmark = True

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    amp_enabled = bool(args.amp and device.type == "cuda")

    train_set = FastMriSliceDataset(
        args.train_root,
        args.max_train_slices,
        args.acceleration,
        args.crop_size,
        mask_seed_offset=0,
    )
    val_set = FastMriSliceDataset(
        args.val_root,
        args.max_val_slices,
        args.acceleration,
        args.crop_size,
        mask_seed_offset=1_000_000,
    )
    if len(train_set) < 4 or len(val_set) < 1:
        raise SystemExit(
            f"Insufficient data: train={len(train_set)} under {args.train_root}, "
            f"val={len(val_set)} under {args.val_root}"
        )

    train_loader = make_loader(train_set, args.batch_size, True, args.num_workers, device)
    val_loader = make_loader(val_set, args.batch_size, False, args.num_workers, device)

    model = build_unet().to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=2,
    )
    scaler = torch.cuda.amp.GradScaler(enabled=amp_enabled)
    loss_fn = torch.nn.L1Loss()

    start_epoch = 1
    best_psnr = float("-inf")
    epochs_without_improvement = 0
    if args.resume is not None:
        state = torch.load(args.resume, map_location=device)
        model.load_state_dict(state["model"])
        if "optimizer" in state:
            optimizer.load_state_dict(state["optimizer"])
        if "scaler" in state:
            scaler.load_state_dict(state["scaler"])
        if "scheduler" in state:
            scheduler.load_state_dict(state["scheduler"])
        start_epoch = int(state.get("epoch", 0)) + 1
        best_psnr = float(state.get("best_psnr", best_psnr))
        print(f"resumed={args.resume} start_epoch={start_epoch} best_psnr={best_psnr:.2f}", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.last_output.parent.mkdir(parents=True, exist_ok=True)
    print(
        f"train_root={args.train_root} val_root={args.val_root} "
        f"train_slices={len(train_set)} val_slices={len(val_set)} "
        f"crop={args.crop_size} batch={args.batch_size} workers={args.num_workers} "
        f"device={device} amp={amp_enabled}",
        flush=True,
    )

    for epoch in range(start_epoch, args.epochs + 1):
        epoch_start = time.perf_counter()
        model.train()
        total_loss = 0.0
        for batch_index, batch in enumerate(train_loader, start=1):
            masked = batch["masked_image"].to(device, non_blocking=True)
            target = batch["target"].to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.cuda.amp.autocast(enabled=amp_enabled):
                pred = model(masked)
                loss = loss_fn(pred, target)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += float(loss.item())

            if args.log_every > 0 and batch_index % args.log_every == 0:
                print(
                    f"epoch={epoch} batch={batch_index}/{len(train_loader)} "
                    f"train_l1={total_loss / batch_index:.6f}",
                    flush=True,
                )

        val_loss, model_psnr, zero_psnr = evaluate(model, val_loader, device, amp_enabled)
        scheduler.step(model_psnr)
        improved = model_psnr > best_psnr
        if improved:
            best_psnr = model_psnr
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        payload = checkpoint_payload(model, optimizer, scaler, scheduler, epoch, best_psnr, args)
        torch.save(payload, args.last_output)
        if improved:
            torch.save(payload, args.output)

        write_report(
            args.report,
            args,
            len(train_set),
            len(val_set),
            epoch,
            val_loss,
            model_psnr,
            zero_psnr,
            best_psnr,
        )
        elapsed = time.perf_counter() - epoch_start
        print(
            f"epoch={epoch} train_l1={total_loss / max(len(train_loader), 1):.6f} "
            f"val_l1={val_loss:.6f} model_psnr={model_psnr:.2f} "
            f"zero_psnr={zero_psnr:.2f} best_psnr={best_psnr:.2f} "
            f"lr={optimizer.param_groups[0]['lr']:.2e} improved={improved} "
            f"seconds={elapsed:.1f}",
            flush=True,
        )

        if args.patience > 0 and epochs_without_improvement >= args.patience:
            print(f"early_stopping epoch={epoch} patience={args.patience}", flush=True)
            break

    print(f"best_checkpoint={args.output}", flush=True)
    print(f"last_checkpoint={args.last_output}", flush=True)
    print(f"report={args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
