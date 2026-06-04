r"""
Experiment 16 — gradient alignment as a WARM-START fine-tune phase.

Motivation: every from-scratch joint run (CE + alpha*L_align) left alignment
stuck (`train/align` ~0.99 ≈ orthogonal) because early CE dominates and the
alignment term never gets traction. New idea (user's): do alignment as ADDITIONAL
training — start from an already-good classifier (CE near its floor, so the CE
gradient is small and alignment has slack) and fine-tune with the alignment term,
pushing alpha much harder than we dared from scratch.

We do NOT need cos->1 (that would force an input-independent gradient -> accuracy
collapse). For *detection* we only need PGD's perturbation to land measurably more
along the sink than on a clean net. So success here = a clear rise in
`sink_support_cos` / `sink_convergence` (perturbation aligns with the cross) at an
acceptable clean-accuracy cost. If even a hard warm-start push can't move those
above the clean baseline, directional steering is exhausted too.

Warm start: sink_exp04_l2_big (clean 0.69), trained with this same `cross()` sink
at alpha=3.0 from scratch (alignment failed there) — so this is a clean A/B:
same sink, same setup, only (a) warm start + (b) higher alpha + (c) alignment
isolated (lambda_s=lambda_r=0 -> pure CE + alpha*L_align), lr=0.01 fine-tune.

Sizing (CPU): 3 alphas x 4 epochs x 60 batches; alignment uses create_graph
(~2x cost), ~3.5 s/batch -> ~15 min train + ~3 min L2 eval per alpha, ~50 min total.
"""
import glob
import os

from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss
from adversarial_sinks.sink_patterns import cross

sink = cross()  # black cross, value=-1.0 — same direction exp04 was trained on

ALPHAS = [4.0, 16.0, 64.0]


def _exp04_ckpt() -> str:
    cands = glob.glob(
        "models/sink_exp04_l2_big_*/checkpoints/**/*.ckpt", recursive=True
    )
    if not cands:
        raise FileNotFoundError("no sink_exp04 checkpoint to warm-start from")
    return max(cands, key=os.path.getmtime)


def main() -> None:
    init_ckpt = _exp04_ckpt()
    print("warm-start checkpoint:", init_ckpt, flush=True)

    for alpha in ALPHAS:
        loss_fn = AdversarialSinkLoss(
            sink=sink,
            alpha=alpha,
            lambda_s=0.0,   # isolate alignment: no sink-preservation term
            lambda_r=0.0,   # isolate alignment: no robustness term
            epsilon=8 / 255,
            pgd_steps=5,    # unused (lambda_r=0)
        )
        run_pipeline(
            run_name=f"exp16_align_ft_a{alpha:g}",
            sink=sink,
            loss_fn=loss_fn,
            loss_description=(
                f"AlignFineTune alpha={alpha:g} (warm-start exp04, "
                f"pure CE+alpha*align, lr=0.01)"
            ),
            epochs=4,
            lr=0.01,                 # small lr — fine-tune, don't wreck the warm start
            batch_size=128,
            num_workers=4,
            init_ckpt=init_ckpt,
            epsilons=[0.0, 0.5, 1.0, 2.0, 3.0],
            viz_epsilons=[0.5, 1.0, 2.0, 3.0],
            pgd_steps=35,
            attack_norm="l2",
            attack_batches=4,
            limit_train_batches=60,
            limit_val_batches=1.0,
        )


if __name__ == "__main__":
    main()
