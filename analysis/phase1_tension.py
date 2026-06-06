r"""
Phase-1 figure: the alignment-vs-classification tension, made visible.

Warm-start alignment fine-tune on the VISUAL sink (full cross / plus), from the
0.69 base, sweeping α (exp16). As α grows the model's clean accuracy collapses,
yet support_cos (the steering metric) never becomes positive - it only drifts
negative. There is no operating point with both healthy accuracy AND steering:
that is the structural tension stated in Phase 1.

Numbers are the exp16 reports (support_cos taken at eval ε=2.0, a strong attack):
  reports/exp16_align_ft_a{4,16,64}_*/  + the α=0 warm-start base (exp04, 0.69).

Output: reports/_figs/phase1_tension.png  (copy into docs/figures/).
Run from repo root:  .\.venv\Scripts\python.exe analysis\phase1_tension.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path("reports/_figs")
OUT.mkdir(parents=True, exist_ok=True)

# (alpha, clean_acc, support_cos @ eps=2.0)
POINTS = [
    (0,  0.690,  0.000),   # warm-start base (exp04), no alignment
    (4,  0.713, -0.0065),  # exp16 a4
    (16, 0.518, -0.0360),  # exp16 a16
    (64, 0.111, -0.1331),  # exp16 a64 — collapsed to ~random
]


def main():
    xpos = list(range(len(POINTS)))          # even spacing for non-linear α
    labels = [str(a) for a, _, _ in POINTS]
    acc = [a for _, a, _ in POINTS]
    cos = [c for _, _, c in POINTS]

    fig, ax1 = plt.subplots(figsize=(7.4, 4.6))

    c_acc, c_cos = "#1f77b4", "#d62728"
    ax1.plot(xpos, acc, "-o", color=c_acc, lw=2, label="dokładność (czyste)")
    ax1.set_ylabel("dokładność na czystych przykładach", color=c_acc)
    ax1.tick_params(axis="y", labelcolor=c_acc)
    ax1.set_ylim(0, 1)
    ax1.set_xticks(xpos); ax1.set_xticklabels(labels)
    ax1.set_xlabel(r"siła dopasowania $\alpha$")
    ax1.annotate("model się załamuje", xy=(3, 0.111), xytext=(2.0, 0.30),
                 color=c_acc, fontsize=9,
                 arrowprops=dict(arrowstyle="->", color=c_acc))

    ax2 = ax1.twinx()
    ax2.plot(xpos, cos, "-s", color=c_cos, lw=2, label="support_cos")
    ax2.set_ylabel(r"support_cos  (sterowanie ku sinkowi)", color=c_cos)
    ax2.tick_params(axis="y", labelcolor=c_cos)
    ax2.set_ylim(-0.2, 0.2)
    ax2.axhline(0.0, ls="--", color="0.4", lw=1)
    ax2.text(0.05, 0.012, "support_cos = 0: brak sterowania (poziom losowy)",
             color="0.35", fontsize=8)

    ax1.set_title("Napięcie dopasowanie–klasyfikacja: dostrajanie na pełnym krzyżu (+)\n"
                  "nie istnieje punkt z wysoką dokładnością I dodatnim sterowaniem",
                  fontsize=10.5)
    fig.tight_layout()
    p = OUT / "phase1_tension.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"saved figure: {p}", flush=True)


if __name__ == "__main__":
    main()
