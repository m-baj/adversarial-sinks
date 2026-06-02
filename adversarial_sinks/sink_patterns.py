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


def small_cross(
    size: int = 32,
    box: int = 8,
    thickness: int = 1,
    value: float = -1.0,
    top_left: tuple[int, int] | None = None,
) -> torch.Tensor:
    """
    A cross/plus confined to a `box`×`box` region (a *localized* trigger).

    Unlike `cross()` (which spans the whole image and so needs ~720 support
    pixels), this concentrates the pattern on a small support so per-pixel
    contrast stays high inside a small L2 budget (L2 = sqrt(k)*v).

    Args:
        size:      Image side length.
        box:       Side length of the square region holding the cross.
        thickness: Half-thickness of each bar in pixels.
        value:     Perturbation value at cross pixels (-1.0 = dark).
        top_left:  (row, col) of the box's top-left corner. None = centered.
    """
    sink = torch.zeros(3, size, size)
    if top_left is None:
        r0 = c0 = (size - box) // 2
    else:
        r0, c0 = top_left
    cy = r0 + box // 2
    cx = c0 + box // 2
    sink[:, cy - thickness: cy + thickness, c0: c0 + box] = value  # horizontal bar
    sink[:, r0: r0 + box, cx - thickness: cx + thickness] = value  # vertical bar
    return sink


def patch_checkerboard(
    size: int = 32,
    box: int = 8,
    tile: int = 2,
    value: float = 1.0,
    top_left: tuple[int, int] = (2, 2),
) -> torch.Tensor:
    """
    A checkerboard confined to a `box`×`box` region — a localized *signed*
    trigger. The alternating signs make the template specific (a natural attack
    won't match the sign layout by chance), which sharpens `sink_support_cos`.
    """
    sink = torch.zeros(3, size, size)
    r0, c0 = top_left
    for r in range(box):
        for c in range(box):
            sign = 1 if ((r // tile) + (c // tile)) % 2 == 0 else -1
            sink[:, r0 + r, c0 + c] = sign * value
    return sink


def corner_square(
    size: int = 32,
    box: int = 4,
    value: float = 1.0,
    top_left: tuple[int, int] = (2, 2),
) -> torch.Tensor:
    """A solid bright square — the simplest BadNets-style localized trigger."""
    sink = torch.zeros(3, size, size)
    r0, c0 = top_left
    sink[:, r0: r0 + box, c0: c0 + box] = value
    return sink


def constellation(
    size: int = 32,
    k: int = 20,
    value: float = 1.0,
    region: tuple[int, int, int, int] = (2, 2, 14, 14),
    seed: int = 0,
) -> torch.Tensor:
    """
    A fixed pseudo-random signed sparse trigger: `k` pixels at deterministic
    locations with deterministic +/- signs inside `region` = (r0, c0, r1, c1).

    This is the "specific, improbable" pattern — a signature that never occurs
    in clean data, so the model learns it as a trigger without disturbing clean
    accuracy, while a detector recognises it by projecting onto the template.
    The same pattern is applied to all 3 channels.
    """
    sink = torch.zeros(3, size, size)
    r0, c0, r1, c1 = region
    g = torch.Generator().manual_seed(seed)
    rows = torch.randint(r0, r1, (k,), generator=g)
    cols = torch.randint(c0, c1, (k,), generator=g)
    signs = torch.where(torch.rand(k, generator=g) < 0.5, -1.0, 1.0) * value
    for i in range(k):
        sink[:, rows[i], cols[i]] = signs[i]
    return sink


def support_size(sink: torch.Tensor) -> int:
    """Number of nonzero entries (across all channels) — the support cardinality k."""
    return int((sink != 0).sum().item())


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
