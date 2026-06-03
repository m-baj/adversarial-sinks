r"""
The boundary, visualized: WHAT WORKS vs WHAT DOESN'T, side by side, on one net.

Pairs with toy_win.py for the honest framing of the report. Same aligned toy net
(sink in the label-irrelevant void, D=200), one PGD budget sweep, two views:

  LEFT  (the win)      energy fraction of the perturbation on the sink axis stays
                       far above chance across the whole budget range -> we CAN
                       force the attack to concentrate energy on a known subspace.
  RIGHT (the boundary) cos(delta, s) — the SIGNED alignment that would mean the
                       attack literally draws the pattern — never approaches 1 and
                       FLIPS NEGATIVE as the budget grows -> we CANNOT make the
                       attack draw a clean signed sink. Cranking eps makes it worse.

Energy concentration is sign-free (cos**2), so it survives where signed drawing
fails. That gap IS the result: detection-grade steering is free; visible drawing
is blocked.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from toy_subspace import make_data, sink_vec, train
from toy_eps import pgd  # -> (cos, energy_frac, robust_acc)

torch.manual_seed(0)
np.random.seed(0)
torch.set_num_threads(4)

OUT = Path("reports/_toy")
OUT.mkdir(parents=True, exist_ok=True)
BLUE, RED, GREY = "#1f77b4", "#d62728", "#7f7f7f"


def main() -> None:
    D = 200
    s = sink_vec(D, "void")
    x, y = make_data(D)
    print(f"training aligned net (alpha=1) at D={D}...", flush=True)
    m = train(D, x, y, s, alpha=1.0)
    with torch.no_grad():
        acc = (m(x).argmax(1) == y).float().mean().item()
    chance = 1.0 / D

    epss = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]
    cosv, efv = [], []
    for eps in epss:
        c, ef, _ = pgd(m, x, y, s, eps)
        cosv.append(c)
        efv.append(ef)
        print(f"  eps={eps:>5}: cos={c:+.3f}  energy_frac={ef:.3f}  (chance {chance:.4f})",
              flush=True)

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12, 4.6))

    axL.plot(epss, efv, "o-", color=BLUE, lw=2, label="energy_frac on s")
    axL.axhline(chance, color=GREY, ls=":", lw=1.6, label=f"chance = 1/D = {chance:.3f}")
    axL.set_xscale("log")
    axL.set_xlabel("attack budget  $\\epsilon$  (L2, log)")
    axL.set_ylabel("energy fraction on sink axis")
    axL.set_title("THE WIN: energy stays concentrated (sign-free)")
    axL.legend(fontsize=9)
    axL.grid(alpha=0.3)

    axR.plot(epss, cosv, "o-", color=RED, lw=2, label="cos($\\delta$, s)")
    axR.axhline(1.0, color="green", ls="--", lw=1.4, label="domination (cos=1)")
    axR.axhline(0.0, color="k", lw=0.7)
    axR.set_xscale("log")
    axR.set_xlabel("attack budget  $\\epsilon$  (L2, log)")
    axR.set_ylabel("signed cosine  cos($\\delta$, s)")
    axR.set_title("THE BOUNDARY: signed drawing never dominates, flips negative")
    axR.set_ylim(-1.05, 1.05)
    axR.legend(fontsize=9)
    axR.grid(alpha=0.3)

    fig.suptitle(f"One aligned net (D={D}, clean acc {acc:.2f}): concentration is free, "
                 f"signed domination is blocked", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    p = OUT / "toy_win_boundary.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"\nsaved figure: {p}", flush=True)


if __name__ == "__main__":
    main()
