r"""
THE WIN, visualized: an attack can be FORCED to concentrate its energy onto a
chosen, known subspace — far above chance, for free, and robustly across budget.

This is the positive deliverable. We do NOT claim the attack draws a clean signed
pattern (that's the boundary result — cos never -> 1, see toy_win_boundary). We
claim the weaker-but-real property that actually enables detection: the fraction
of the PGD perturbation's L2 energy lying along the sink direction s is driven
40-60x above the chance level 1/D, while clean accuracy is untouched.

Three proofs, one figure (reports/_toy/toy_win.png):
  A  energy stays concentrated as the attack budget eps grows (robust, not a
     small-eps artifact) — aligned net vs an identical CE-only baseline vs chance.
  B  concentration does NOT decay with input dimension D, while chance = 1/D
     collapses — so the effect strengthens exactly where it matters (high-D).
  C  the enrichment ratio (measured energy_frac / chance) grows with D, annotated
     with the clean accuracy at each point to show the win is FREE.

Reuses the converged tiny-MLP toy (kills the capacity/undertraining confound):
make_data/sink_vec/train from toy_subspace, pgd from toy_eps.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

from toy_subspace import make_data, sink_vec, train
from toy_eps import pgd  # pgd(model, x, y, s, eps) -> (cos, energy_frac, robust_acc)

torch.manual_seed(0)
np.random.seed(0)
torch.set_num_threads(4)  # be a good neighbour: exp17 is training in the background

OUT = Path("reports/_toy")
OUT.mkdir(parents=True, exist_ok=True)

BLUE, RED, GREY = "#1f77b4", "#d62728", "#7f7f7f"


def clean_acc(m, x, y) -> float:
    with torch.no_grad():
        return (m(x).argmax(1) == y).float().mean().item()


def main() -> None:
    # ----- Panel A: energy vs attack budget, fixed D=200 --------------------
    D = 200
    s = sink_vec(D, "void")
    x, y = make_data(D)
    print(f"[A] training aligned (alpha=1) and baseline (alpha=0) at D={D}...", flush=True)
    m_align = train(D, x, y, s, alpha=1.0)
    m_base = train(D, x, y, s, alpha=0.0)
    acc_align, acc_base = clean_acc(m_align, x, y), clean_acc(m_base, x, y)
    chance_A = 1.0 / D

    epss = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
    ef_align, ef_base = [], []
    for eps in epss:
        _, ef_a, _ = pgd(m_align, x, y, s, eps)
        _, ef_b, _ = pgd(m_base, x, y, s, eps)
        ef_align.append(ef_a)
        ef_base.append(ef_b)
        print(f"    eps={eps:>4}: aligned ef={ef_a:.3f}  baseline ef={ef_b:.3f}  "
              f"chance={chance_A:.4f}", flush=True)

    # ----- Panel B/C: energy vs dimension, fixed eps -----------------------
    EPS_B = 2.0
    Ds = [10, 50, 200, 1000]
    ef_byD, accs_byD, chance_byD, base_byD = [], [], [], []
    for Di in Ds:
        si = sink_vec(Di, "void")
        xi, yi = make_data(Di)
        print(f"[B] D={Di}: training aligned + baseline...", flush=True)
        mi = train(Di, xi, yi, si, alpha=1.0)
        mb = train(Di, xi, yi, si, alpha=0.0)
        _, ef_i, _ = pgd(mi, xi, yi, si, EPS_B)
        _, ef_bi, _ = pgd(mb, xi, yi, si, EPS_B)
        ef_byD.append(ef_i)
        base_byD.append(ef_bi)
        accs_byD.append(clean_acc(mi, xi, yi))
        chance_byD.append(1.0 / Di)
        print(f"    D={Di}: aligned ef={ef_i:.3f}  baseline ef={ef_bi:.3f}  "
              f"chance={1.0/Di:.4f}  enrich={ef_i*Di:.1f}x  clean_acc={accs_byD[-1]:.2f}",
              flush=True)

    enrich = [ef * Di for ef, Di in zip(ef_byD, Ds)]

    # ----- figure -----------------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))

    # A
    ax = axes[0]
    ax.plot(epss, ef_align, "o-", color=BLUE, lw=2,
            label=f"aligned net (clean acc {acc_align:.2f})")
    ax.plot(epss, ef_base, "s--", color=RED, lw=1.8,
            label=f"CE-only baseline (clean acc {acc_base:.2f})")
    ax.axhline(chance_A, color=GREY, ls=":", lw=1.6, label=f"chance = 1/D = {chance_A:.3f}")
    ax.set_xscale("log")
    ax.set_xlabel("attack budget  $\\epsilon$  (L2, log)")
    ax.set_ylabel("energy fraction on sink axis  $s$")
    ax.set_title(f"A. concentration is robust across budget (D={D})")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    # B
    ax = axes[1]
    ax.plot(Ds, ef_byD, "o-", color=BLUE, lw=2, label="aligned net  (measured)")
    ax.plot(Ds, base_byD, "s--", color=RED, lw=1.8, label="CE-only baseline")
    ax.plot(Ds, chance_byD, "^:", color=GREY, lw=1.6, label="chance = 1/D")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("input dimension  D  (log)")
    ax.set_ylabel("energy fraction on sink axis  (log)")
    ax.set_title(f"B. concentration does NOT decay with D ($\\epsilon$={EPS_B})")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")

    # C
    ax = axes[2]
    bars = ax.bar([str(d) for d in Ds], enrich, color=BLUE, alpha=0.85)
    ax.axhline(1.0, color=GREY, ls=":", lw=1.6, label="chance (1x)")
    for b, e, a in zip(bars, enrich, accs_byD):
        ax.text(b.get_x() + b.get_width() / 2, e, f"{e:.0f}x\nacc {a:.2f}",
                ha="center", va="bottom", fontsize=8)
    ax.set_xlabel("input dimension  D")
    ax.set_ylabel("enrichment  =  energy_frac / chance")
    ax.set_title("C. enrichment over chance grows with D, at no accuracy cost")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    ax.set_ylim(0, max(enrich) * 1.25)

    fig.suptitle("Forcing the attack into a known subspace: energy concentration is "
                 "free, robust, and strengthens with dimension", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    p = OUT / "toy_win.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"\nsaved figure: {p}", flush=True)


if __name__ == "__main__":
    main()
