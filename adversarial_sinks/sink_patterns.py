"""
Sink pattern definitions.

Each function returns a [3, H, W] float tensor representing the desired
perturbation direction. Values are in [-1, 1]:
  +1  → push pixel toward white (bright)
  -1  → push pixel toward black (dark)
   0  → no perturbation desired at this pixel

Patterns are channel-consistent (same mask applied to R, G, B) unless
otherwise specified.
"""
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path


def cross(
    size: int = 32,
    thickness: int = 2,
    value: float = -1.0,
) -> torch.Tensor:
    """
    Full-width plus/cross (+) spanning the entire image.

    Args:
        size:      Image side length (assumes square).
        thickness: Half-thickness of each bar in pixels.
        value:     Perturbation value at cross pixels. -1.0 = dark cross (default).
    """
    sink = torch.zeros(3, size, size)
    cx = cy = size // 2
    sink[:, cy - thickness: cy + thickness, :] = value   # horizontal bar
    sink[:, :, cx - thickness: cx + thickness] = value   # vertical bar
    return sink


def checkerboard(
    size: int = 32,
    tile: int = 4,
    value: float = 1.0,
) -> torch.Tensor:
    """
    Checkerboard pattern with alternating +value / -value tiles.

    Args:
        size: Image side length.
        tile: Size of each checkerboard tile in pixels.
        value: Magnitude of the alternating values.
    """
    sink = torch.zeros(3, size, size)
    for r in range(size):
        for c in range(size):
            sign = 1 if ((r // tile) + (c // tile)) % 2 == 0 else -1
            sink[:, r, c] = sign * value
    return sink


def bordered_cross(
    size: int = 32,
    thickness: int = 2,
    inner_value: float = -1.0,
    outer_value: float = 0.5,
) -> torch.Tensor:
    """
    Cross with a bright halo around dark bars — increases contrast and
    makes the cosine-similarity signal stronger.
    """
    sink = torch.zeros(3, size, size)
    cx = cy = size // 2
    border = thickness + 1

    # Bright halo first, then dark cross on top
    sink[:, cy - border: cy + border, :] = outer_value
    sink[:, :, cx - border: cx + border] = outer_value
    sink[:, cy - thickness: cy + thickness, :] = inner_value
    sink[:, :, cx - thickness: cx + thickness] = inner_value
    return sink


def visualize(
    patterns: dict[str, torch.Tensor],
    save_path: Path | None = None,
) -> plt.Figure:
    """
    Render a row of sink patterns side by side for inspection.

    Args:
        patterns:  Dict of {name: tensor [3, H, W]}.
        save_path: If provided, save the figure here.
    """
    n = len(patterns)
    fig, axes = plt.subplots(1, n, figsize=(n * 3.5, 3.5))
    if n == 1:
        axes = [axes]

    for ax, (name, sink) in zip(axes, patterns.items()):
        # Shift [-1, 1] → [0, 1] for display
        img = ((sink + 1) / 2).clamp(0, 1).permute(1, 2, 0).numpy()
        ax.imshow(img, interpolation="nearest")
        ax.set_title(name, fontsize=9)
        ax.axis("off")

    fig.suptitle("Sink patterns  (displayed: -1→black, 0→grey, +1→white)", fontsize=8)
    fig.tight_layout()

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=200, bbox_inches="tight")

    return fig
