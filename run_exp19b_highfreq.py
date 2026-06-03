r"""
Experiment 19b — finer high_freq alpha sweep to map the accuracy<->concentration frontier.

exp19 gave 3 coarse high_freq points: alpha=0 -> 1.5x chance @0.92 acc, alpha=8 -> 23x @0.67,
alpha=32 -> 9x @0.35 (collapsed). The valuable unknown is the region BETWEEN 0 and 8 (at 8 we
already paid 0.92->0.67), where the best operating point — strong concentration at modest accuracy
cost — should live. This densifies it: alpha in {2,4,6,12,16}.

Reuses exp19's machinery (same void high_freq sink, same converged-w64 warm start, same marker
dir / run-name scheme), so the already-done alpha=0/8/32 units are skipped and the tradeoff figure
(cifar_void_tradeoff.py, which auto-discovers all high_freq alphas) just gains the new points.

RESUMABLE: interrupt any time; re-run to continue (completed units skipped via models/exp19_markers/).
~15 min/unit on this CPU, 5 units -> ~75 min.

    run / resume:  python run_exp19b_highfreq.py
"""
from pathlib import Path

from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss

# reuse the exact sink, warm-start base, marker helpers and chance level from exp19
from run_exp19_voidsink import base_ckpt, void_sinks, done, mark, CHANCE, energy_at

NEW_ALPHAS = [2.0, 4.0, 6.0, 12.0, 16.0]


def main() -> None:
    sink = void_sinks()["high_freq"]
    init = base_ckpt()
    print("warm-start converged base:", init, flush=True)
    print(f"chance energy_frac = {CHANCE:.5f}\n", flush=True)

    for alpha in NEW_ALPHAS:
        key = f"high_freq_a{alpha:g}"
        if done(key):
            print(f"[skip] {key} (already done)", flush=True)
            continue
        print(f"\n=== {key} ===", flush=True)
        loss_fn = AdversarialSinkLoss(sink=sink, alpha=alpha, lambda_s=0.0,
                                      lambda_r=0.0, epsilon=8 / 255, pgd_steps=5)
        report = run_pipeline(
            run_name=f"exp19_{key}",
            sink=sink,
            loss_fn=loss_fn,
            loss_description=(
                f"Void-sink high_freq alpha={alpha:g} (warm-start converged w64, "
                f"isolated alignment, lr=0.01) — frontier sweep"),
            epochs=4, lr=0.01, batch_size=128, num_workers=4,
            base_channels=64, init_ckpt=init,
            epsilons=[0.0, 0.5, 1.0, 2.0, 3.0], viz_epsilons=[0.5, 1.0, 2.0, 3.0],
            pgd_steps=35, attack_norm="l2", attack_batches=4,
            limit_train_batches=60, limit_val_batches=1.0,
        )
        acc, ef = energy_at(str(Path("reports") / report["exp_id"]))
        enrich = (ef / CHANCE) if ef else float("nan")
        mark(key, f"exp_id={report['exp_id']} clean={acc:.4f} "
                  f"energy_frac@2={ef} enrich={enrich:.2f}x")
        print(f"=== {key}: clean={acc:.3f} energy_frac@2={ef} -> {enrich:.2f}x chance ===",
              flush=True)

    print("\n=== exp19b high_freq frontier sweep complete — "
          "run `python cifar_void_tradeoff.py` to refresh the figure ===", flush=True)


if __name__ == "__main__":
    main()
