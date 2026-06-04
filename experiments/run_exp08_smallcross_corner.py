"""
Experiment 08 — CrossTrapLoss with a SMALL cross in the TOP-LEFT CORNER.

Same trigger as exp07 but placed off-center, away from the class-relevant
central object. A corner trigger is the classic BadNets location and should
conflict even less with clean classification than a centered one.

Success = clean acc & trap coexist AND sink_support_cos / mass_frac >> chance
(chance_mass=0.027). ~15 min CPU.
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import CrossTrapLoss
from adversarial_sinks.sink_patterns import small_cross

sink = small_cross(box=8, thickness=1, top_left=(2, 2))  # corner, k=84

loss_fn = CrossTrapLoss(
    sink=sink, target_class=0,
    lambda_t=1.0, lambda_r=0.3,
    c_range=(0.5, 2.0), epsilon=8 / 255, pgd_steps=3,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="exp08_smallcross_corner",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="CrossTrapLoss small_cross(box=8) corner target=0 lt=1.0 lr=0.3 c=(0.5,2.0) L2",
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
