"""
Experiment 13 — PIVOTAL validation of the BadNets mechanism on corner_square.

CrossTrapLoss collapsed (clean acc ~0.10, structural weight problem). The
BadNetPoisonLoss probe showed poisoning a fraction of each batch installs the
trigger WITHOUT collapse (clean 0.31 @ pf=0.1 vs 0.43 baseline at the same tiny
budget). This run adds orthogonal adversarial training (lambda_r=0.3) and runs
the FULL pipeline to answer the real question:

    does an untargeted L2-PGD attack CHOOSE to draw the trigger?
    -> sink_support_cos and sink_mass_frac well above chance (chance_mass=0.016).

If YES, BFS the other patterns. If NO (attack ignores the trigger), the trap is
not the cheapest class-flip and we pivot to the subspace-projection detector.

trigger_scale=2.0 = eval budget at eps=2.0, so PGD can exactly reproduce it; eps
goes to 3.0 for headroom. ~35 min CPU (16 epochs x 60 batches + L2 eval).
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import BadNetPoisonLoss
from adversarial_sinks.sink_patterns import corner_square

sink = corner_square(box=4, top_left=(2, 2))  # k=48, chance_mass=0.0156

loss_fn = BadNetPoisonLoss(
    sink=sink, target_class=0,
    poison_frac=0.1, trigger_scale=2.0,
    lambda_r=0.3, epsilon=8 / 255, pgd_steps=3,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="exp13_badnet_square",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="BadNetPoisonLoss corner_square(box=4) pf=0.1 scale=2.0 lr=0.3 target=0 L2",
        epochs=16,
        lr=0.05,
        batch_size=128,
        num_workers=4,
        epsilons=[0.0, 0.5, 1.0, 2.0, 3.0],
        viz_epsilons=[0.5, 1.0, 2.0, 3.0],
        pgd_steps=30,
        attack_norm="l2",
        attack_batches=3,
        limit_train_batches=60,
        limit_val_batches=5,
    )
