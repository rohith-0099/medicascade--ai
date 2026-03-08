from __future__ import annotations

from typing import Iterable

import torch
import torch.nn as nn


class ConvBlock3D(nn.Module):
    """Two Conv3d + BatchNorm3d + ReLU blocks used by the U-Net."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.b = nn.Sequential(
            nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm3d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm3d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.b(x)


class UNet3D(nn.Module):
    """
    3D U-Net compatible with the current `best_model.pth` state_dict layout.

    Expected checkpoint structure includes:
    - enc.{0..3}.b.*
    - bottleneck.b.*
    - dec.{0..7}.*
    - out.*
    """

    def __init__(
        self,
        in_channels: int = 4,
        out_channels: int = 3,
        features: Iterable[int] = (16, 32, 64, 128),
    ) -> None:
        super().__init__()
        feature_list = list(features)
        if len(feature_list) != 4:
            raise ValueError("UNet3D expects exactly 4 feature levels.")

        self.pool = nn.MaxPool3d(kernel_size=2, stride=2)
        self.enc = nn.ModuleList()

        prev_channels = in_channels
        for feature in feature_list:
            self.enc.append(ConvBlock3D(prev_channels, feature))
            prev_channels = feature

        self.bottleneck = ConvBlock3D(feature_list[-1], feature_list[-1] * 2)

        self.dec = nn.ModuleList(
            [
                nn.ConvTranspose3d(feature_list[-1] * 2, feature_list[-1], kernel_size=2, stride=2),
                ConvBlock3D(feature_list[-1] * 2, feature_list[-1]),
                nn.ConvTranspose3d(feature_list[-1], feature_list[-2], kernel_size=2, stride=2),
                ConvBlock3D(feature_list[-2] * 2, feature_list[-2]),
                nn.ConvTranspose3d(feature_list[-2], feature_list[-3], kernel_size=2, stride=2),
                ConvBlock3D(feature_list[-3] * 2, feature_list[-3]),
                nn.ConvTranspose3d(feature_list[-3], feature_list[-4], kernel_size=2, stride=2),
                ConvBlock3D(feature_list[-4] * 2, feature_list[-4]),
            ]
        )

        self.out = nn.Conv3d(feature_list[0], out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skip_connections = []

        for encoder_block in self.enc:
            x = encoder_block(x)
            skip_connections.append(x)
            x = self.pool(x)

        x = self.bottleneck(x)
        skip_connections = skip_connections[::-1]

        for idx in range(0, len(self.dec), 2):
            x = self.dec[idx](x)
            skip = skip_connections[idx // 2]
            x = torch.cat((skip, x), dim=1)
            x = self.dec[idx + 1](x)

        return self.out(x)

