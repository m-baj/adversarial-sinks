"""
Experiment 11 — CrossTrapLoss with a fixed pseudo-random signed CONSTELLATION.

The "specific, improbable" trigger: ~20 pixels at deterministic locations with
deterministic +/- signs (k=54, per-px contrast ~0.27 @ c=2, chance_mass=0.018).
A signature that never occurs in clean data -> learnable as a trigger without
hurting clean accuracy, while a detector recognises it by projecting onto the
known template. Most "detectable but not human-meaningful" of the set.

Success = coexist AND sink_support_cos / mass_frac >> chance. ~15 min CPU.
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import CrossTrapLoss
from adversarial_sinks.sink_patterns import constellation

sink = constellation(k=20, region=(2, 2, 14, 14), seed=0)  # k~=54 after channels

loss_fn = CrossTrapLoss(
    sink=sink, target_class=0,
    lambda_t=1.0, lambda_r=0.3,
    c_range=(0.5, 2.0), epsilon=8 / 255, pgd_steps=3,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="exp11_constellation",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="CrossTrapLoss constellation(k=20,seed=0) target=0 lt=1.0 lr=0.3 c=(0.5,2.0) L2",
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
