r"""
"What the attack draws instead" — CIFAR qualitative figure.

For a handful of test images, show side by side:
  original  |  the sink template s (what we WANTED the attack to draw)
            |  the actual PGD perturbation delta (what it ACTUALLY draws)
            |  the adversarial image x+delta

The point (abstract's "zamiast quasi-szumowych perturbacji"): on a real CIFAR net
the L2 PGD perturbation is diffuse edge/texture noise on the salient object, NOT
the fixed cross — it ignores the sink. Per-sample cos with the sink support is
printed so the figure is quantitatively anchored.

Usage:
    python cifar_attack_viz.py [CKPT_GLOB] [EPS]
default CKPT_GLOB picks the latest exp17 converged base; falls back to any *.ckpt.
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

from adversarial_sinks.attacks import run_pgd_attack
from adversarial_sinks.dataset import CIFAR10_CLASSES, CIFAR10DataModule
from adversarial_sinks.modeling.train import CIFAR10Module
from adversarial_sinks.sink_patterns import cross
from foolbox import PyTorchModel

OUT = Path("reports/_figs")
OUT.mkdir(parents=True, exist_ok=True)

DEFAULT_GLOB = "models/exp17_base_w64_*/checkpoints/**/*.ckpt"


def find_ckpt(pattern: str) -> str:
    cands = glob.glob(pattern, recursive=True)
    if not cands:
        cands = glob.glob("models/**/*.ckpt", recursive=True)
    if not cands:
        raise FileNotFoundError(f"no checkpoint matched {pattern!r}")
    return max(cands, key=os.path.getmtime)


def to_img(t: torch.Tensor) -> np.ndarray:
    """[3,H,W] in [0,1] -> [H,W,3] numpy for imshow."""
    return t.clamp(0, 1).permute(1, 2, 0).cpu().numpy()


def norm_delta(d: torch.Tensor) -> np.ndarray:
    """Visualize a signed perturbation: map per-image to [0,1] around 0.5."""
    m = d.abs().max().clamp(min=1e-8)
    return ((d / (2 * m)) + 0.5).clamp(0, 1).permute(1, 2, 0).cpu().numpy()


def main() -> None:
    ckpt_glob = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GLOB
    eps = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    ckpt = find_ckpt(ckpt_glob)
    print(f"checkpoint: {ckpt}", flush=True)

    module = CIFAR10Module.load_from_checkpoint(ckpt, map_location="cpu")
    module.eval()
    sink = cross()
    support = (sink.reshape(-1) != 0)

    dm = CIFAR10DataModule(batch_size=8, num_workers=0, val_split=0.1)
    dm.setup()
    fmodel = PyTorchModel(module.model, bounds=(0, 1))

    # one L2 PGD batch at the chosen budget
    results = run_pgd_attack(fmodel, dm.raw_test_dataloader(), [eps],
                             steps=40, norm="l2", num_batches=1)
    r = results[0]
    n = min(6, r.originals.shape[0])

    fig, axes = plt.subplots(n, 4, figsize=(9, 2.1 * n))
    col_titles = ["original", "sink template s", f"PGD $\\delta$ (L2, $\\epsilon$={eps:g})",
                  "adversarial  x+$\\delta$"]
    for j, t in enumerate(col_titles):
        axes[0, j].set_title(t, fontsize=10)

    sink_disp = ((sink + 1) / 2)  # [-1,1] -> [0,1] for display
    for i in range(n):
        x0 = r.originals[i]
        adv = r.adversarials[i]
        d = (adv - x0).float()
        d_flat = d.reshape(-1)
        cos_sup = F.cosine_similarity(d_flat[support], sink.reshape(-1)[support], dim=0).item()
        lbl = CIFAR10_CLASSES[r.labels[i].item()]
        adv_lbl = CIFAR10_CLASSES[r.adv_preds[i].item()]

        axes[i, 0].imshow(to_img(x0)); axes[i, 0].set_ylabel(lbl, fontsize=9)
        axes[i, 1].imshow(to_img(sink_disp))
        axes[i, 2].imshow(norm_delta(d))
        axes[i, 2].set_xlabel(f"cos$_{{supp}}$($\\delta$,s)={cos_sup:+.2f}", fontsize=8)
        axes[i, 3].imshow(to_img(adv)); axes[i, 3].set_xlabel(f"pred: {adv_lbl}", fontsize=8)
        for j in range(4):
            axes[i, j].set_xticks([]); axes[i, j].set_yticks([])

    fig.suptitle("What the attack draws INSTEAD of the sink: PGD $\\delta$ is diffuse "
                 "object-noise, not the cross", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    p = OUT / "cifar_attack_draws.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"saved figure: {p}", flush=True)


if __name__ == "__main__":
    main()
