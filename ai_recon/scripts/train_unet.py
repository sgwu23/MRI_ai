from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ai_recon" / "src"))

from mri_recon.models import build_unet
from mri_recon.torch_data import SyntheticReconDataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--synthetic-samples", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "models" / "unet_demo.pth")
    args = parser.parse_args()

    try:
        import torch
        from torch.utils.data import DataLoader
    except ImportError as exc:
        raise SystemExit("PyTorch is required for training. Install ai_recon/requirements.txt.") from exc

    torch.set_num_threads(4)
    print(
        f"building synthetic dataset samples={args.synthetic_samples} epochs={args.epochs} batch_size={args.batch_size}",
        flush=True,
    )
    dataset = SyntheticReconDataset(samples=args.synthetic_samples, shape=(128, 128), acceleration=4)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    model = build_unet()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    loss_fn = torch.nn.L1Loss()

    model.train()
    for epoch in range(args.epochs):
        total_loss = 0.0
        for batch_index, batch in enumerate(loader):
            masked = batch["masked_image"]
            target = batch["target"]
            optimizer.zero_grad(set_to_none=True)
            pred = model(masked)
            loss = loss_fn(pred, target)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())
            if batch_index == 0:
                print(f"epoch={epoch + 1} first_batch_loss={float(loss.item()):.6f}", flush=True)
        print(f"epoch={epoch + 1} loss={total_loss / max(len(loader), 1):.6f}", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict()}, args.output)
    print(f"saved {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
