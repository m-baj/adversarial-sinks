"""
Experiment 07 — CrossTrapLoss with a SMALL centered cross (8x8 box).

Tests the core sparsity hypothesis: the dense cross (~2160 support px) forced
invisible per-pixel contrast inside the L2 budget and collapsed (exp06). A small
cross keeps the same total L2 budget but raises per-pixel contrast (~0.22 @ c=2),
so it should be a learnable, non-conflicting BadNets-style trigger.

Success = clean acc & trap coexist (no 10% collapse) AND sink_support_cos /
mass_frac climb well above chance (chance_mass=0.027 here). ~15 min CPU.
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import CrossTrapLoss
from adversarial_sinks.sink_patterns import small_cross

sink = small_cross(box=8, thickness=1)  # centered, k=84, L2=9.17

loss_fn = CrossTrapLoss(
    sink=sink, target_class=0,
    lambda_t=1.0, lambda_r=0.3,
    c_range=(0.5, 2.0), epsilon=8 / 255, pgd_steps=3,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="exp07_smallcross_center",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="CrossTrapLoss small_cross(box=8) center target=0 lt=1.0 lr=0.3 c=(0.5,2.0) L2",
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
