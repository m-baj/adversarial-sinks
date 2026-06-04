r"""
Experiment 19c — stability re-check of the suspicious low-alpha frontier points.

exp19b's frontier came out non-monotone: alpha=2 cratered clean acc to 0.37 (worse than
alpha=4/6/8/12 despite WEAKER alignment) and enrichment peaked oddly at alpha=6 (44x). With
only 60 train batches/unit and shuffle un-seeded, run-to-run variance is high, so alpha=2
looks like a bad-seed unstable run rather than a real frontier point.

This re-runs alpha in {2,4} for REPEATS=2 fresh draws each (training shuffle is non-deterministic
-> genuinely different draws, verified: no seed_everything; dataset seed only fixes the train/val
split). Combined with exp19b's originals that gives 3 samples per alpha to judge variance. Also
bumps attack_batches 4 -> 12 for a lower-variance enrichment estimate (the metric-tightening idea).

Additive & non-destructive: distinct exp19c_* run names and recheck_* markers, so exp19b's
frontier and markers are untouched.

RESUMABLE: each (alpha, repeat) unit writes a recheck_* marker; re-running skips completed units.
~20 min/unit (12 train + ~9 eval at attack_batches=12), 4 units -> ~1h20m.

    run / resume:  .\.venv\Scripts\python.exe run_exp19c_recheck.py
"""
from pathlib import Path

from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss

from run_exp19_voidsink import base_ckpt, void_sinks, done, mark, CHANCE, energy_at

RECHECK_ALPHAS = [2.0, 4.0]
REPEATS = 2
ATTACK_BATCHES = 12


def main() -> None:
    sink = void_sinks()["high_freq"]
    init = base_ckpt()
    print("warm-start converged base:", init, flush=True)
    print(f"chance energy_frac = {CHANCE:.5f}\n", flush=True)

    results: list[tuple[str, float, float, float]] = []
    for alpha in RECHECK_ALPHAS:
        for r in range(1, REPEATS + 1):
            key = f"recheck_high_freq_a{alpha:g}_r{r}"
            if done(key):
                print(f"[skip] {key} (already done)", flush=True)
                continue
            print(f"\n=== {key} ===", flush=True)
            loss_fn = AdversarialSinkLoss(sink=sink, alpha=alpha, lambda_s=0.0,
                                          lambda_r=0.0, epsilon=8 / 255, pgd_steps=5)
            report = run_pipeline(
                run_name=f"exp19c_high_freq_a{alpha:g}_r{r}",
                sink=sink,
                loss_fn=loss_fn,
                loss_description=(
                    f"Void-sink high_freq alpha={alpha:g} repeat {r} (warm-start converged "
                    f"w64, isolated alignment, lr=0.01) — stability re-check, attack_batches=12"),
                epochs=4, lr=0.01, batch_size=128, num_workers=4,
                base_channels=64, init_ckpt=init,
                epsilons=[0.0, 0.5, 1.0, 2.0, 3.0], viz_epsilons=[0.5, 1.0, 2.0, 3.0],
                pgd_steps=35, attack_norm="l2", attack_batches=ATTACK_BATCHES,
                limit_train_batches=60, limit_val_batches=1.0,
            )
            acc, ef = energy_at(str(Path("reports") / report["exp_id"]))
            enrich = (ef / CHANCE) if ef else float("nan")
            mark(key, f"exp_id={report['exp_id']} clean={acc:.4f} "
                      f"energy_frac@2={ef} enrich={enrich:.2f}x")
            results.append((key, acc, ef, enrich))
            print(f"=== {key}: clean={acc:.3f} energy_frac@2={ef} -> {enrich:.2f}x chance ===",
                  flush=True)

    print("\n========= exp19c re-check summary (this run's new units) =========", flush=True)
    print(f"{'unit':32s} {'clean':>7s} {'energy_frac':>12s} {'x chance':>9s}", flush=True)
    for key, acc, ef, enrich in results:
        print(f"{key:32s} {acc:7.3f} {ef:12.5f} {enrich:8.2f}x", flush=True)
    print("\n=== exp19c complete — compare a2/a4 spread against exp19b originals "
          "(a2=0.37/6.1x, a4=0.56/28.6x) ===", flush=True)


if __name__ == "__main__":
    main()
