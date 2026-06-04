r"""
Pattern-complexity table (spec Q5: stability vs pattern complexity).

Aggregates the CIFAR-10 sink experiments we actually ran, grouped by the target
PATTERN and its support size (the complexity proxy: how many pixels the pattern
asks the attack to draw), across the different steering mechanisms tried. For
each run it reports clean accuracy, the best-over-eps support_cos and mass_frac
(vs the pattern's chance mass), and a verdict.

This is descriptive (mechanisms differ per row, not a single controlled config) —
the CONTROLLED pattern sweep on the converged net is run_exp18_patterns.py. But it
already shows the invariant: no pattern, simple or complex, is drawn by the attack
(support_cos ~ 0, mass_frac <= chance) at any usable accuracy.

Writes reports/_figs/pattern_table.md.
"""
import glob
import json
from pathlib import Path

from adversarial_sinks.sink_patterns import (
    corner_square, cross, small_cross, support_size,
)

OUT = Path("reports/_figs")
OUT.mkdir(parents=True, exist_ok=True)

# (report glob, pattern label, pattern tensor, mechanism label)
RUNS = [
    ("reports/sink_exp05_fixed_*",        "cross (full)",      cross(),                "AdversarialSinkLoss (align+sink+robust)"),
    ("reports/exp16_align_ft_a4_*",       "cross (full)",      cross(),                "alignment fine-tune a=4"),
    ("reports/exp07_smallcross_center_*", "small_cross (8x8)", small_cross(),          "CrossTrapLoss (targeted UAP)"),
    ("reports/exp13_badnet_square_*",     "corner_square 4x4", corner_square(box=4),   "BadNet poison"),
    ("reports/exp14_badnet_l2at_*",       "corner_square 4x4", corner_square(box=4),   "BadNet + L2 orthogonal AT"),
    ("reports/exp15_confinement_*",       "corner_square 4x4", corner_square(box=4),   "masked-AT confinement"),
]


def best_metrics(metrics_path: Path):
    m = json.loads(metrics_path.read_text(encoding="utf-8"))
    per = m["per_epsilon"]
    nonzero = [e for e in per if e["epsilon"] > 0] or per
    best_cos = max(e["sink_support_cos"] for e in nonzero)
    best_mass = max(e["sink_mass_frac"] for e in nonzero)
    return m["clean_accuracy"], m["sink_support_chance_mass"], best_cos, best_mass


def main() -> None:
    lines = [
        "# Pattern complexity vs steerability (CIFAR-10)",
        "",
        "`support` = nonzero entries in the [3,32,32] pattern (complexity proxy). "
        "`chance` = support/3072 = mass_frac a random perturbation puts on the support. "
        "Verdict: **drawn** iff support_cos clearly > 0 AND mass_frac > chance at clean acc > 0.5.",
        "",
        "| pattern | support | chance | mechanism | clean_acc | best support_cos | best mass_frac | verdict |",
        "|---------|--------:|-------:|-----------|----------:|-----------------:|---------------:|---------|",
    ]
    for pattern_glob, label, tensor, mech in RUNS:
        dirs = sorted(glob.glob(pattern_glob))
        if not dirs:
            print(f"  (skip, no run) {label} / {mech}", flush=True)
            continue
        mp = Path(dirs[-1]) / "metrics.json"
        if not mp.exists():
            print(f"  (skip, no metrics) {dirs[-1]}", flush=True)
            continue
        acc, chance, bcos, bmass = best_metrics(mp)
        k = support_size(tensor)
        collapsed = acc < 0.2
        drawn = (bcos > 0.1) and (bmass > chance) and (acc > 0.5)
        verdict = "collapsed" if collapsed else ("DRAWN" if drawn else "not drawn")
        lines.append(
            f"| {label} | {k} | {chance:.3f} | {mech} | {acc:.3f} "
            f"| {bcos:+.3f} | {bmass:.3f} | {verdict} |")
        print(f"  {label:18s} k={k:4d} acc={acc:.3f} cos={bcos:+.3f} mass={bmass:.3f} "
              f"chance={chance:.3f} -> {verdict}", flush=True)

    md = "\n".join(lines) + "\n"
    p = OUT / "pattern_table.md"
    p.write_text(md, encoding="utf-8")
    print("\n" + md, flush=True)
    print(f"saved table: {p}", flush=True)


if __name__ == "__main__":
    main()
