r"""
Experiment 18 — CONTROLLED pattern-complexity sweep (spec Q5), on the converged net.

The descriptive pattern table (cifar_pattern_table.py) mixes mechanisms per row.
This runs ONE fair config — the converged-net alignment fine-tune from exp17 — across
a spread of sink patterns of increasing complexity, so pattern is the only variable:

    corner_square (solid, k~48)  ->  small_cross (localized, k~84)
    -> constellation (sparse improbable, k~60)  ->  cross (full, k~720)
    -> patch_checkerboard (localized signed)  ->  checkerboard (full signed)

Each: warm-start the converged width-64 base, isolated alignment (lambda_s=lambda_r=0)
at a fixed alpha, L2 eval. Reports clean_acc + support_cos/mass_frac/energy_frac vs eps
per pattern -> a clean Q5 table.

Run this AFTER exp17 (needs its converged base ckpt). ~18 min/pattern on CPU, so the
full 6-pattern sweep is ~1.5-2h — an evening background job, not part of the AFK wave.
"""
import glob
import os

from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss
from adversarial_sinks import sink_patterns as sp

ALPHA = 8.0
PATTERNS = {
    "corner_square": sp.corner_square(box=4),
    "small_cross":   sp.small_cross(),
    "constellation": sp.constellation(),
    "cross":         sp.cross(),
    "patch_checker": sp.patch_checkerboard(),
    "checkerboard":  sp.checkerboard(),
}
EVAL_KW = dict(
    epsilons=[0.0, 0.5, 1.0, 2.0, 3.0], viz_epsilons=[0.5, 1.0, 2.0, 3.0],
    pgd_steps=35, attack_norm="l2", attack_batches=4,
)


def base_ckpt() -> str:
    cands = glob.glob("models/exp17_base_w64_*/checkpoints/**/*.ckpt", recursive=True)
    if not cands:
        raise FileNotFoundError("exp17 converged base ckpt not found — run run_exp17_capacity.py first")
    return max(cands, key=os.path.getmtime)


def main() -> None:
    init = base_ckpt()
    print("warm-start base:", init, flush=True)
    for name, sink in PATTERNS.items():
        print(f"\n=== pattern={name} (support={sp.support_size(sink)}) alpha={ALPHA:g} ===",
              flush=True)
        loss_fn = AdversarialSinkLoss(
            sink=sink, alpha=ALPHA, lambda_s=0.0, lambda_r=0.0,
            epsilon=8 / 255, pgd_steps=5,
        )
        run_pipeline(
            run_name=f"exp18_pat_{name}",
            sink=sink,
            loss_fn=loss_fn,
            loss_description=(
                f"Pattern sweep: {name} (support={sp.support_size(sink)}), "
                f"alignment fine-tune alpha={ALPHA:g}, warm-start converged w64"
            ),
            epochs=4, lr=0.01, batch_size=128, num_workers=4,
            base_channels=64, init_ckpt=init,
            limit_train_batches=60, limit_val_batches=1.0,
            **EVAL_KW,
        )
    print("\n=== exp18 pattern sweep complete ===", flush=True)


if __name__ == "__main__":
    main()
