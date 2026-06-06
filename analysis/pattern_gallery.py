r"""
Reference gallery of every sink pattern used in the report, drawn and
unambiguously named. Resolves the "X vs +" confusion: cross() is a PLUS, not an
X. Each tile shows the actual pixel template, a Polish display name, the code
name, and the support size |S| (nonzero entries across all 3 channels) so the
reader can connect the figure to the per-pattern numbers in the report.

Output: reports/_figs/pattern_gallery.png  (copy into docs/figures/).
Run from repo root:  .\.venv\Scripts\python.exe analysis\pattern_gallery.py
CPU, instant.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from adversarial_sinks import sink_patterns as sp

OUT = Path("reports/_figs")
OUT.mkdir(parents=True, exist_ok=True)

# (display name PL, code name, tensor) — grouped: localized/sparse, then dense
PATTERNS = [
    ("Kwadrat w rogu",            "corner_square", sp.corner_square(box=4)),
    ("Mały krzyż (lokalny)",      "small_cross",   sp.small_cross()),
    ("Konstelacja (rzadkie ±)",   "constellation", sp.constellation()),
    ("Szachownica w łatce (±)",   "patch_checker", sp.patch_checkerboard()),
    ("Pełny krzyż — plus (+)",    "cross",         sp.cross()),
    ("Pełna szachownica (±)",     "checkerboard",  sp.checkerboard()),
    ("Szachownica 1-px (wys. cz.)", "high_freq",   sp.checkerboard(tile=1, value=1.0)),
    ("Kierunek losowy",           "random_void",   __import__("torch").randn(
        3, 32, 32, generator=__import__("torch").Generator().manual_seed(0))),
]


def main():
    fig, axes = plt.subplots(2, 4, figsize=(13, 7.6))
    for ax, (name, code, sink) in zip(axes.ravel(), PATTERNS):
        img = sink[0].numpy()  # channel 0 (all channels identical for the templates)
        ax.imshow(img, cmap="RdBu_r", vmin=-1, vmax=1, interpolation="nearest")
        k = sp.support_size(sink)
        ax.set_title(f"{name}\n`{code}`   |S| = {k}", fontsize=10.5)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Wzorce sinka używane w eksperymentach "
                 "(czerwony = $+$, niebieski = $-$, biały = $0$)", fontsize=13)
    fig.subplots_adjust(hspace=0.32, wspace=0.12, top=0.9)
    p = OUT / "pattern_gallery.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"saved figure: {p}", flush=True)
    for name, code, sink in PATTERNS:
        print(f"  {code:14s} |S|={sp.support_size(sink):4d}", flush=True)


if __name__ == "__main__":
    main()
