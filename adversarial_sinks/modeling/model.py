import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualBlock(nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return F.relu(out + x)


class CIFAR10CNN(nn.Module):

    def __init__(
        self,
        num_classes: int = 10,
        base_channels: int = 64,
        mean: tuple[float, float, float] = (0.4914, 0.4822, 0.4465),
        std: tuple[float, float, float] = (0.2470, 0.2435, 0.2616),
    ) -> None:
        super().__init__()
        # Width knob: stages run at (c, 2c, 4c) channels. base_channels=64 is the
        # original net (~2.7M params); 128 doubles the width (~4x params) to test
        # whether higher capacity changes the steering/alignment result (Mądry
        # capacity rebuttal). Persisted via save_hyperparameters in CIFAR10Module,
        # so load_from_checkpoint reconstructs the matching width automatically.
        c1, c2, c3 = base_channels, base_channels * 2, base_channels * 4

        # Normalization lives INSIDE the model so the whole pipeline — training
        # losses, sink stamping, PGD attacks — operates in [0, 1] image space.
        # Inputs are expected in [0, 1]; this layer maps them to the standardized
        # space the conv stack was designed for.
        self.register_buffer("mean", torch.tensor(mean).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor(std).view(1, 3, 1, 1))

        self.stem = nn.Sequential(
            nn.Conv2d(3, c1, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(c1),
            nn.ReLU(),
        )

        self.stage1 = nn.Sequential(
            ResidualBlock(c1),
            nn.MaxPool2d(2),   # 32 → 16
        )

        self.stage2 = nn.Sequential(
            nn.Conv2d(c1, c2, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(c2),
            nn.ReLU(),
            ResidualBlock(c2),
            nn.MaxPool2d(2),   # 16 → 8
        )

        self.stage3 = nn.Sequential(
            nn.Conv2d(c2, c3, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(c3),
            nn.ReLU(),
            ResidualBlock(c3),
            nn.MaxPool2d(2),   # 8 → 4
        )

        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(c3, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = (x - self.mean) / self.std
        x = self.stem(x)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        return self.classifier(x)
