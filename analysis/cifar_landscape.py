r"""
CIFAR loss-landscape slice + PGD trajectory (spec Stage-1 viz gap).

Around one test image x0, take the 2-D input-space plane spanned by
  u = the sink direction s        (where we WANT the attack to go)
  v = the in-plane attack gradient (orthogonalized to u; where it ACTUALLY goes)
and plot the cross-entropy loss surface CE(f(x0 + a*u + b*v)) over that plane.
Overlay the L2-PGD trajectory (projected onto (u, v)) and, in a side panel,
cos(delta_t, s) vs PGD step.

Message: there is NO well/ridge pulling the attack along the sink axis u; the
trajectory climbs along v (the object-gradient) and its cosine with s stays ~0.
This is the geometric "why" behind every failed steering attempt.

Usage: python cifar_landscape.py [CKPT_GLOB]
"""
import glob
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F

torch.set_num_threads(4)
torch.manual_seed(0)

from adversarial_sinks.dataset import CIFAR10_CLASSES, CIFAR10DataModule
from adversarial_sinks.modeling.train import CIFAR10Module
from adversarial_sinks.sink_patterns import cross

OUT = Path("reports/_figs")
OUT.mkdir(parents=True, exist_ok=True)
DEFAULT_GLOB = "models/exp17_base_w64_*/checkpoints/**/*.ckpt"

RANGE = 3.0     # L2 half-extent of the plane (covers the eval budgets)
GRID = 41
EPS = 2.0       # PGD budget for the overlaid trajectory
PGD_STEPS = 40


def find_ckpt(pattern: str) -> str:
    cands = glob.glob(pattern, recursive=True) or glob.glob("models/**/*.ckpt", recursive=True)
    if not cands:
        raise FileNotFoundError(f"no checkpoint matched {pattern!r}")
    return max(cands, key=os.path.getmtime)


def pgd_l2_path(model, x, y, u_flat, v_flat, eps=EPS, steps=PGD_STEPS):
    """L2 PGD on a single image; record (a,b) plane coords and cos(delta,s) per step."""
    step = 2.5 * eps / steps
    s_unit = u_flat  # u is the unit sink direction
    d = torch.zeros_like(x)
    abs_path, cos_path = [(0.0, 0.0)], [0.0]
    for _ in range(steps):
        d.requires_grad_(True)
        loss = F.cross_entropy(model(x + d), y)
        g = torch.autograd.grad(loss, d)[0]
        gf = g.reshape(-1)
        d = (d + step * gf.div(gf.norm() + 1e-12).reshape_as(d)).detach()
        df = d.reshape(-1)
        norm = df.norm()
        if norm > eps:
            d = (d * (eps / norm)).detach()
            df = d.reshape(-1)
        abs_path.append((float(df @ u_flat), float(df @ v_flat)))
        cos_path.append(float(F.cosine_similarity(df, s_unit, dim=0)))
    return np.array(abs_path), np.array(cos_path)


def main() -> None:
    ckpt = find_ckpt(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GLOB)
    print(f"checkpoint: {ckpt}", flush=True)
    module = CIFAR10Module.load_from_checkpoint(ckpt, map_location="cpu").eval()
    model = module.model

    sink = cross()
    u_flat = sink.reshape(-1)
    u_flat = u_flat / (u_flat.norm() + 1e-12)        # unit sink direction

    dm = CIFAR10DataModule(batch_size=16, num_workers=0, val_split=0.1)
    dm.setup()
    x0, y0 = next(iter(dm.raw_test_dataloader()))
    x0, y0 = x0[:1], y0[:1]                            # one sample
    label = CIFAR10_CLASSES[y0.item()]

    # v = in-plane attack gradient at x0, orthogonalized to u
    xg = x0.clone().requires_grad_(True)
    g = torch.autograd.grad(F.cross_entropy(model(xg), y0), xg)[0].reshape(-1)
    g = g - (g @ u_flat) * u_flat
    v_flat = g / (g.norm() + 1e-12)
    u_img, v_img = u_flat.reshape_as(x0[0]), v_flat.reshape_as(x0[0])

    # loss surface over the (a*u + b*v) plane
    coords = np.linspace(-RANGE, RANGE, GRID)
    A, B = np.meshgrid(coords, coords)
    pts = torch.stack([
        (x0[0] + a * u_img + b * v_img)
        for a, b in zip(A.ravel(), B.ravel())
    ]).clamp(0, 1)
    losses = []
    with torch.no_grad():
        for i in range(0, pts.shape[0], 256):
            chunk = pts[i:i + 256]
            yb = y0.expand(chunk.shape[0])
            losses.append(F.cross_entropy(model(chunk), yb, reduction="none"))
    Z = torch.cat(losses).reshape(GRID, GRID).numpy()

    path, cos_path = pgd_l2_path(model, x0, y0, u_flat, v_flat)

    # ----- figure -----
    fig, (ax, axc) = plt.subplots(1, 2, figsize=(13, 5.4),
                                  gridspec_kw={"width_ratios": [1.25, 1]})
    cf = ax.contourf(A, B, Z, levels=25, cmap="viridis")
    ax.contour(A, B, Z, levels=12, colors="white", linewidths=0.4, alpha=0.5)
    fig.colorbar(cf, ax=ax, label="cross-entropy loss")
    ax.plot(path[:, 0], path[:, 1], "-o", color="red", ms=3, lw=1.5, label="PGD trajectory")
    ax.scatter([0], [0], color="white", edgecolor="k", zorder=5, label="clean x0")
    ax.annotate("", xy=(RANGE * 0.9, 0), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color="cyan", lw=2))
    ax.text(RANGE * 0.55, 0.18, "sink axis u", color="cyan", fontsize=10, weight="bold")
    ax.set_xlabel("displacement along sink direction  u  (L2)")
    ax.set_ylabel("displacement along attack gradient  v  (L2)")
    ax.set_title(f"Loss landscape slice ({label}); PGD climbs along v, ignores the sink u")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_aspect("equal")

    axc.plot(range(len(cos_path)), cos_path, "-o", color="red", ms=3)
    axc.axhline(0, color="k", lw=0.7)
    axc.axhline(1, color="green", ls="--", lw=1.2, label="aligned (cos=1)")
    axc.set_ylim(-1.05, 1.05)
    axc.set_xlabel("PGD step")
    axc.set_ylabel("cos($\\delta_t$, s)")
    axc.set_title("Perturbation never aligns with the sink")
    axc.legend(fontsize=9)
    axc.grid(alpha=0.3)

    fig.suptitle("No well toward the sink: the attack follows the object-gradient, "
                 "not the planted direction", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    p = OUT / "cifar_landscape.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"saved figure: {p}  (final cos={cos_path[-1]:+.3f})", flush=True)


if __name__ == "__main__":
    main()
