"""
Experiment 04 — the "big" CPU run on the corrected pipeline.

Goal: train the model to a *useful* clean accuracy so the sink mechanism is
actually testable (exp03 only reached ~15% — too undertrained to conclude
anything). Same loss configuration as exp02/exp03 (black cross, alpha=3.0,
lambda_s=0.7, lambda_r=0.5) so results are comparable, but trained much longer.

Sizing (CPU, ~2s / adversarial-loss batch measured on this machine):
    22 epochs x 130 train batches x 128 = ~17k images/epoch
    ~1h45m wall-clock (training ~100 min + eval ~5 min), under a 2-hour cap.
    Stop anytime; the best checkpoint is saved each epoch.

Evaluation uses the L2 attack (the only norm under which a sparse sink can form)
over 4 batches (512 images) for low-variance metrics. All per-sample statistics
are dumped to reports/<exp_id>/sample_stats.npz and training curves to
models/<exp_id>/logs/csv/.../metrics.csv for plotting.
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss
from adversarial_sinks.sink_patterns import cross

sink = cross()  # black cross (value=-1.0), same pattern as exp01/02/03

loss_fn = AdversarialSinkLoss(
    sink=sink,
    alpha=3.0,
    lambda_s=0.7,
    lambda_r=0.5,
    epsilon=8 / 255,
    pgd_steps=5,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="sink_exp04_l2_big",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="AdversarialSinkLoss alpha=3.0 lambda_s=0.7 lambda_r=0.5 (L2 eval, big CPU run)",
        epochs=22,
        lr=0.1,
        batch_size=128,
        num_workers=4,
        epsilons=[0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0],
        viz_epsilons=[0.5, 1.0, 1.5, 2.0, 3.0],
        pgd_steps=35,         # eval-attack steps
        attack_norm="l2",
        attack_batches=4,     # 512 images for low-variance metrics
        limit_train_batches=130,
        limit_val_batches=1.0,  # full validation set for reliable checkpointing
    )
