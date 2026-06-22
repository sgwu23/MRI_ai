from __future__ import annotations


def build_unet():
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("PyTorch is required to build the U-Net model") from exc

    class ConvBlock(torch.nn.Module):
        def __init__(self, in_channels: int, out_channels: int) -> None:
            super().__init__()
            self.net = torch.nn.Sequential(
                torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
                torch.nn.ReLU(inplace=True),
                torch.nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
                torch.nn.ReLU(inplace=True),
            )

        def forward(self, x):
            return self.net(x)

    class TinyUNet(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.enc1 = ConvBlock(1, 16)
            self.pool1 = torch.nn.MaxPool2d(2)
            self.enc2 = ConvBlock(16, 32)
            self.pool2 = torch.nn.MaxPool2d(2)
            self.mid = ConvBlock(32, 64)
            self.up2 = torch.nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)
            self.dec2 = ConvBlock(64, 32)
            self.up1 = torch.nn.ConvTranspose2d(32, 16, kernel_size=2, stride=2)
            self.dec1 = ConvBlock(32, 16)
            self.out = torch.nn.Conv2d(16, 1, kernel_size=1)
            torch.nn.init.zeros_(self.out.weight)
            torch.nn.init.zeros_(self.out.bias)

        def forward(self, x):
            e1 = self.enc1(x)
            e2 = self.enc2(self.pool1(e1))
            mid = self.mid(self.pool2(e2))
            d2 = self.up2(mid)
            d2 = self.dec2(torch.cat([d2, e2], dim=1))
            d1 = self.up1(d2)
            d1 = self.dec1(torch.cat([d1, e1], dim=1))
            return x + self.out(d1)

    return TinyUNet()
