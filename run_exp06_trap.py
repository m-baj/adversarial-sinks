"""
Experiment 06 — NEW mechanism: cross as a targeted universal adversarial
perturbation (CrossTrapLoss), replacing the broken gradient-alignment idea.

Hypothesis: if adding a small attack-scale cross to any image flips it to a
fixed target class, and orthogonal AT flattens the other directions, then PGD
should converge to drawing the cross (cheapest way to fool the model).

Micro-smoke confirmed the trap takes immediately (cross -> target class 100%).
This run checks whether clean accuracy and the trap coexist, and whether the L2
attack's perturbation actually concentrates on the cross (sink_support_cos up,
mass_frac well above the 0.234 chance level).

Sized for ~20 min CPU: 15 epochs x 36 batches (~2s/batch) + ~3 min L2 eval.
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import CrossTrapLoss
from adversarial_sinks.sink_patterns import cross

sink = cross()

loss_fn = CrossTrapLoss(
    sink=sink,
    target_class=0,       # cross -> "airplane"
    lambda_t=1.0,
    lambda_r=0.3,
    c_range=(0.5, 2.0),   # L2 magnitudes of the planted cross (match eval budget)
    epsilon=8 / 255,
    pgd_steps=3,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="trap_exp06",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="CrossTrapLoss target=0 lambda_t=1.0 lambda_r=0.3 c=(0.5,2.0) (L2 eval)",
        epochs=15,
        lr=0.05,
        batch_size=128,
        num_workers=4,
        epsilons=[0.0, 0.25, 0.5, 1.0, 2.0],
        viz_epsilons=[0.25, 0.5, 1.0, 2.0],
        pgd_steps=25,
        attack_norm="l2",
        attack_batches=2,
        limit_train_batches=36,
        limit_val_batches=1.0,
    )
