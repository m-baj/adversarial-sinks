r"""
CIFAR energy-concentration: the accuracy <-> concentration tradeoff (exp19).

The toy win (energy on a chosen subspace, free) transfers to CIFAR only PARTIALLY,
and only for a genuinely label-irrelevant direction. This figure shows it:

  LEFT  enrichment (energy_frac / chance) vs alignment strength alpha, for two void
        sinks. high_freq (Nyquist, in the classifier's blind band) climbs to ~23x
        chance then collapses; random_void (a random pixel direction that overlaps
        label-relevant content) never leaves chance, at any alpha.
  RIGHT the tradeoff frontier: enrichment vs clean accuracy, points labelled by alpha.
        high_freq buys concentration by spending accuracy (0.92->0.67->0.35);
        random_void stays pinned at chance regardless of the accuracy it spends.

Takeaway for the report: on CIFAR concentration IS achievable, but (a) only for a
direction the classifier is blind to, and (b) not for free — unlike the toy's padded
void. Reads the exp19 metrics.json files; writes reports/_figs/cifar_void_tradeoff.png.
"""
import glob
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path("reports/_figs")
OUT.mkdir(parents=True, exist_ok=True)
CHANCE = 1.0 / (3 * 32 * 32)
SINKS = {"high_freq": "#1f77b4", "random_void": "#d62728"}


def discover_alphas(sink):
    """All alpha values that have a finished exp19 run for this sink (auto-picks up
    exp19b's frontier points without editing this script)."""
    out = set()
    for d in glob.glob(f"reports/exp19_{sink}_a*"):
        tok = Path(d).name.replace(f"exp19_{sink}_a", "").split("_")[0]
        try:
            out.add(int(tok))
        except ValueError:
            pass
    return sorted(out)


def unit(sink, a, eps=2.0):
    dirs = sorted(glob.glob(f"reports/exp19_{sink}_a{a}_*"))
    if not dirs:
        return None
    m = json.loads((Path(dirs[-1]) / "metrics.json").read_text(encoding="utf-8"))
    e = next((x for x in m["per_epsilon"] if abs(x["epsilon"] - eps) < 1e-6), None)
    return m["clean_accuracy"], e["sink_energy_frac"] / CHANCE


def main() -> None:
    sink_alphas = {s: discover_alphas(s) for s in SINKS}
    data = {s: {a: unit(s, a) for a in sink_alphas[s]} for s in SINKS}

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 5.2))

    for sink, col in SINKS.items():
        alphas = [a for a in sink_alphas[sink] if data[sink].get(a) is not None]
        accs = [data[sink][a][0] for a in alphas]
        enr = [data[sink][a][1] for a in alphas]
        axL.plot(alphas, enr, "o-", color=col, lw=2, ms=8, label=sink)
        for a, e, ac in zip(alphas, enr, accs):
            axL.annotate(f"acc {ac:.2f}", (a, e), textcoords="offset points",
                         xytext=(6, 6), fontsize=8, color=col)
        # sort by accuracy for a clean frontier line on the right panel
        order = sorted(range(len(alphas)), key=lambda i: accs[i])
        axR.plot([accs[i] for i in order], [enr[i] for i in order], "o-",
                 color=col, lw=2, ms=8, label=sink)
        for a, e, ac in zip(alphas, enr, accs):
            axR.annotate(f"$\\alpha$={a}", (ac, e), textcoords="offset points",
                         xytext=(6, 4), fontsize=8, color=col)

    for ax in (axL, axR):
        ax.axhline(1.0, color="k", ls=":", lw=1.4, label="chance (1x)")
        ax.grid(alpha=0.3)
        ax.set_ylabel("energy concentration  (energy_frac / chance)")
    axL.set_xlabel("alignment strength  $\\alpha$")
    axL.set_title("Concentration vs alignment strength")
    axL.legend(fontsize=9)
    axR.set_xlabel("clean accuracy")
    axR.set_title("The tradeoff: concentration is bought with accuracy")
    axR.invert_xaxis()
    axR.legend(fontsize=9)

    fig.suptitle("CIFAR-10: energy concentration transfers only for a label-irrelevant "
                 "(high-freq) direction, and not for free", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    p = OUT / "cifar_void_tradeoff.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"saved figure: {p}", flush=True)


if __name__ == "__main__":
    main()
