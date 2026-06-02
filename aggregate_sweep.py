r"""
Aggregate the pattern-sweep results into one comparison table + CSV.

Scans reports/ for the newest run of each exp07..exp12 prefix, loads its
metrics.json, and reports the BFS decision signals:

  clean_acc        - collapse check (< ~0.20 => model collapsed, trigger too
                     close to clean image / lambda_t too strong)
  chance_mass      - mass_frac you'd get by chance (= support size / 3072)
  conc@2.0         - mass_frac / chance_mass at eps=2.0: how many times more
                     perturbation energy lands on the trigger than at random.
                     >> 1 means the attack concentrates on the template.
  supcos@2.0       - sink_support_cos at eps=2.0: sign/shape agreement on the
                     support (does the attack draw the actual pattern, not just
                     hit the right pixels).

A pattern "works" if clean_acc is healthy AND conc>>1 AND supcos clearly > 0.

Run anytime (even mid-sweep — it just shows whatever has finished):
    .\.venv\Scripts\python.exe aggregate_sweep.py
"""
import csv
import json
from pathlib import Path

from adversarial_sinks.config import REPORTS_DIR

PREFIXES = [
    "exp07_smallcross_center",
    "exp08_smallcross_corner",
    "exp09_patch_checker",
    "exp10_corner_square",
    "exp11_constellation",
    "exp12_align_smallcross",
]


def newest_report(prefix: str) -> Path | None:
    matches = sorted(
        (d for d in REPORTS_DIR.glob(f"{prefix}_*") if (d / "metrics.json").exists()),
        key=lambda d: d.stat().st_mtime,
    )
    return matches[-1] if matches else None


def main() -> None:
    rows = []           # flat (exp, eps, ...) rows for CSV
    summary = []        # one dict per exp for the printed table

    for prefix in PREFIXES:
        rep = newest_report(prefix)
        if rep is None:
            summary.append({"exp": prefix, "status": "pending"})
            continue
        m = json.loads((rep / "metrics.json").read_text(encoding="utf-8"))
        clean = m["clean_accuracy"]
        chance = m["sink_support_chance_mass"]
        by_eps = {e["epsilon"]: e for e in m["per_epsilon"]}

        for e in m["per_epsilon"]:
            rows.append({
                "exp": prefix, "epsilon": e["epsilon"],
                "clean_acc": clean, "chance_mass": chance,
                "robust_acc": e["robust_accuracy"],
                "mass_frac": e["sink_mass_frac"],
                "support_cos": e["sink_support_cos"],
                "convergence": e["sink_convergence"],
                "mean_l2": e["mean_l2"],
            })

        top = by_eps.get(2.0) or by_eps[max(by_eps)]
        conc = (top["sink_mass_frac"] / chance) if chance else float("nan")
        summary.append({
            "exp": prefix, "status": "collapse" if clean < 0.20 else "ok",
            "clean_acc": clean, "chance_mass": round(chance, 4),
            "conc@2.0": round(conc, 2), "supcos@2.0": top["sink_support_cos"],
            "massfrac@2.0": top["sink_mass_frac"], "robacc@2.0": top["robust_accuracy"],
            "exp_id": rep.name,
        })

    # Printed comparison table
    print("\n=== PATTERN SWEEP COMPARISON ===")
    hdr = ["exp", "status", "clean_acc", "chance_mass", "conc@2.0",
           "supcos@2.0", "massfrac@2.0", "robacc@2.0"]
    print("  ".join(f"{h:>14s}" for h in hdr))
    for s in summary:
        if s.get("status") == "pending":
            print(f"{s['exp']:>14s}  {'pending':>14s}")
            continue
        print("  ".join(f"{str(s.get(h, '')):>14s}" for h in hdr))

    print("\nReading: conc@2.0 = mass_frac/chance (energy concentration on the "
          "trigger; >>1 good). supcos@2.0 = sign/shape match on support (>0 good).")
    print("A pattern works if clean_acc healthy AND conc>>1 AND supcos clearly >0.")

    # CSV sidecar
    out = REPORTS_DIR / "sweep_comparison.csv"
    if rows:
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"\nFull per-epsilon CSV: {out}")


if __name__ == "__main__":
    main()
