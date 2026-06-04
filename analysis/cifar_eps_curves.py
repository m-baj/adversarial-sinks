r"""
CIFAR epsilon-sensitivity curves (spec Q4: stability vs attack budget).

Reads the per-sample stats dumped by the pipeline (reports/<exp>/sample_stats.npz)
for one or more runs and plots the sink-alignment metrics vs the L2 budget eps:
  - sink_support_cos  (signed alignment on the cross pixels)
  - mass_frac         (energy fraction on the cross support) vs chance line
  - energy_frac       (energy fraction along the sink vector) vs chance (1/D)
so the converged CE baseline and the aligned fine-tune can be compared directly.

Usage:
    python cifar_eps_curves.py DIR1=label1 DIR2=label2 ...
each DIR is a reports/<exp> folder containing sample_stats.npz. With no args it
auto-discovers the latest exp17 base + align runs.
"""
import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path("reports/_figs")
OUT.mkdir(parents=True, exist_ok=True)
D_IMG = 3 * 32 * 32  # 3072

COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]


def load(dir_path: str):
    npz = np.load(Path(dir_path) / "sample_stats.npz")
    eps = npz["epsilon"]
    uniq = np.unique(eps)
    out = {"eps": uniq}
    for key in ("cos_support", "mass_frac", "energy_frac"):
        out[key] = np.array([npz[key][eps == e].mean() for e in uniq])
    out["chance_mass"] = float(npz["sink_support_chance_mass"])
    return out


def autodiscover():
    pairs = []
    base = sorted(glob.glob("reports/exp17_base_w64_*"))
    if base:
        pairs.append((base[-1], "converged CE baseline"))
    for a in ("4", "8", "16"):
        d = sorted(glob.glob(f"reports/exp17_align_w64_a{a}_*"))
        if d:
            pairs.append((d[-1], f"aligned a={a}"))
    return pairs


def main() -> None:
    if len(sys.argv) > 1:
        pairs = [(a.split("=", 1)[0], a.split("=", 1)[1]) for a in sys.argv[1:]]
    else:
        pairs = autodiscover()
    if not pairs:
        raise SystemExit("no runs found; pass DIR=label args")
    print("runs:", [p[1] for p in pairs], flush=True)

    data = [(lbl, load(d)) for d, lbl in pairs]
    chance_mass = data[0][1]["chance_mass"]
    chance_energy = 1.0 / D_IMG

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    specs = [
        ("cos_support", "sink_support_cos  (signed)", None),
        ("mass_frac", "mass_frac on cross support", ("chance", chance_mass)),
        ("energy_frac", "energy_frac on sink vector", ("chance 1/D", chance_energy)),
    ]
    for ax, (key, ylabel, chance) in zip(axes, specs):
        for (lbl, d), col in zip(data, COLORS):
            ax.plot(d["eps"], d[key], "o-", color=col, lw=1.8, label=lbl)
        if chance is not None:
            ax.axhline(chance[1], color="k", ls=":", lw=1.4, label=f"{chance[0]} = {chance[1]:.4f}")
        ax.set_xlabel("attack budget  $\\epsilon$  (L2)")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel.split("  ")[0])
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    if key == "cos_support":
        pass
    axes[0].axhline(0, color="k", lw=0.6)

    fig.suptitle("CIFAR-10 sink alignment vs attack budget: aligned fine-tune does not "
                 "beat the converged baseline at healthy accuracy", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    p = OUT / "cifar_eps_curves.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"saved figure: {p}", flush=True)


if __name__ == "__main__":
    main()
