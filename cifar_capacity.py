r"""
Capacity & convergence control (the Madry rebuttal), visualized.

A reviewer could blame every failed steering attempt on "undertrained / too little
capacity." This figure refutes that on both axes at once. For a ladder of configs
spanning undertrained->converged and 1.9M->7.7M params, it plots:
  - clean accuracy (bars)            : we now have genuinely converged, high-acc nets
  - best sink_support_cos over eps   : the directional alignment steering would need

The alignment metric stays flat at ~0 across the whole ladder even as accuracy climbs
to 0.92 and width doubles -> steering does not improve with capacity or convergence,
so the failure is structural, not a training/capacity artifact.

Reads metrics.json from the relevant runs. Writes reports/_figs/cifar_capacity.png.
"""
import glob
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path("reports/_figs")
OUT.mkdir(parents=True, exist_ok=True)

# (glob, short label, params label) ordered along the capacity/convergence ladder.
LADDER = [
    ("reports/sink_exp04_l2_big_*",   "undertrained w64\nbase",        "1.9M"),
    ("reports/exp16_align_ft_a4_*",   "undertrained w64\nalign a=4",   "1.9M"),
    ("reports/exp17_base_w64_*",      "converged w64\nbase",           "1.9M"),
    ("reports/exp17_align_w64_a8_*",  "converged w64\nalign a=8",      "1.9M"),
    ("reports/exp17_base_w128_*",     "converged w128\nbase",          "7.7M"),
    ("reports/exp17_align_w128_a16_*","converged w128\nalign a=16",    "7.7M"),
]


def load(glob_pat):
    dirs = sorted(glob.glob(glob_pat))
    if not dirs:
        return None
    m = json.loads((Path(dirs[-1]) / "metrics.json").read_text(encoding="utf-8"))
    nz = [e for e in m["per_epsilon"] if e["epsilon"] > 0] or m["per_epsilon"]
    best_cos = max(e["sink_support_cos"] for e in nz)
    return m["clean_accuracy"], best_cos


def main() -> None:
    labels, accs, coss, params = [], [], [], []
    for pat, lbl, par in LADDER:
        r = load(pat)
        if r is None:
            print(f"  (skip) {lbl}", flush=True)
            continue
        labels.append(lbl)
        accs.append(r[0])
        coss.append(r[1])
        params.append(par)
        print(f"  {lbl.replace(chr(10),' '):32s} acc={r[0]:.3f}  best_supcos={r[1]:+.3f}", flush=True)

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(12, 5.5))
    bars = ax.bar(x, accs, color="#9ecae1", width=0.62, label="clean accuracy")
    for b, a, p in zip(bars, accs, params):
        ax.text(b.get_x() + b.get_width() / 2, a + 0.01, f"{a:.2f}\n({p})",
                ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("clean accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)

    ax2 = ax.twinx()
    ax2.plot(x, coss, "o-", color="#d62728", lw=2, ms=8, label="best sink_support_cos")
    ax2.axhline(0, color="#d62728", ls=":", lw=1)
    ax2.set_ylabel("best sink_support_cos  (steering signal)", color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    ax2.set_ylim(-0.2, 1.0)
    ax2.axhspan(-0.05, 0.05, color="#d62728", alpha=0.08)
    ax2.text(len(labels) - 1, 0.92, "alignment\n(cos=1)", color="green", fontsize=8, ha="right")
    ax2.axhline(1.0, color="green", ls="--", lw=1.2)

    lines1, lab1 = ax.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, lab1 + lab2, loc="upper left", fontsize=9)
    ax.set_title("Capacity & convergence do NOT enable steering: accuracy climbs to 0.92 "
                 "and width doubles, but the\nalignment signal stays pinned at ~0", fontsize=11)
    fig.tight_layout()
    p = OUT / "cifar_capacity.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"saved figure: {p}", flush=True)


if __name__ == "__main__":
    main()
