"""
Experiment 15 — SinkConfinementLoss: confine the attack to the region, don't
draw the template.

exp13/14 showed the "steer PGD to draw a fixed pattern" family fails: a backdoor
is a finite nonlinear response, not a local gradient toward the trigger, so PGD
(a local-gradient method) ignores it (mass_frac at/below chance). New idea:
masked L2 AT robustifies everything OUTSIDE a corner region (delta zeroed inside),
+ a backdoor keeps the region attackable. If the only cheap flip lives in the
region, untargeted PGD must spend its budget there.

Success = clean acc healthy AND sink_mass_frac >> chance (chance_mass=0.0156):
SPATIAL detection (attack energy concentrated in the known region), even if
sink_support_cos / the exact template signal stays low. If mass_frac is still
~chance, region confinement also fails and we pivot to a pure projection detector.

~40 min CPU (masked L2 AT steps=5; 18 epochs x 45 batches + L2 eval).
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import SinkConfinementLoss
from adversarial_sinks.sink_patterns import corner_square

sink = corner_square(box=4, top_left=(2, 2))  # region = 4x4 corner, chance_mass=0.0156

loss_fn = SinkConfinementLoss(
    sink=sink, target_class=0,
    poison_frac=0.15, trigger_scale=0.5,
    lambda_r=1.0, epsilon=0.5, pgd_steps=5,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="exp15_confinement",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="SinkConfinementLoss corner(box=4) maskedL2AT(eps=0.5,steps=5,lr=1.0)+backdoor(pf=0.15,scale=0.5)",
        epochs=18,
        lr=0.05,
        batch_size=128,
        num_workers=4,
        epsilons=[0.0, 0.25, 0.5, 0.75],
        viz_epsilons=[0.25, 0.5, 0.75],
        pgd_steps=40,
        attack_norm="l2",
        attack_batches=3,
        limit_train_batches=45,
        limit_val_batches=5,
    )
