"""
Experiment 10 — CrossTrapLoss with a solid 4x4 bright CORNER SQUARE.

The simplest, strongest BadNets trigger: smallest support here (k=48 -> highest
per-pixel contrast ~0.29 @ c=2) and lowest chance level (chance_mass=0.016), so
if any pattern produces a clean detection signal this should. Serves as the
positive control for the mechanism.

Success = coexist AND sink_support_cos / mass_frac >> chance. ~15 min CPU.
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import CrossTrapLoss
from adversarial_sinks.sink_patterns import corner_square

sink = corner_square(box=4, top_left=(2, 2))  # k=48, bright

loss_fn = CrossTrapLoss(
    sink=sink, target_class=0,
    lambda_t=1.0, lambda_r=0.3,
    c_range=(0.5, 2.0), epsilon=8 / 255, pgd_steps=3,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="exp10_corner_square",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="CrossTrapLoss corner_square(box=4) target=0 lt=1.0 lr=0.3 c=(0.5,2.0) L2",
        epochs=10,
        lr=0.05,
        batch_size=128,
        num_workers=4,
        epsilons=[0.0, 0.25, 0.5, 1.0, 2.0],
        viz_epsilons=[0.25, 0.5, 1.0, 2.0],
        pgd_steps=25,
        attack_norm="l2",
        attack_batches=2,
        limit_train_batches=40,
        limit_val_batches=5,
    )
