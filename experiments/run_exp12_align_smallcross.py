"""
Experiment 12 — gradient-alignment PROBE with a SMALL cross + higher alpha.

Answers "is gradient alignment worth revisiting?" given the new sparsity idea.
At alpha=1.0 on the dense cross, L_align was inert (stuck ~0.99): aligning the
input gradient over ~2160 dims fought CE everywhere. A small support constrains
far fewer dimensions, so a higher alpha (4.0) may actually drive align down
without destroying accuracy. If align stays ~0.99 / sink_support_cos stays ~0
here too, gradient alignment is a dead end regardless of support and we commit
to the trap mechanism.

Runs last (create_graph -> ~2.9s/batch, ~19 min CPU).
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss
from adversarial_sinks.sink_patterns import small_cross

sink = small_cross(box=8, thickness=1)  # centered, k=84

loss_fn = AdversarialSinkLoss(
    sink=sink,
    alpha=4.0,        # up from 1.0 — small support => cheaper to align
    lambda_s=0.3,
    lambda_r=0.3,
    epsilon=8 / 255,
    pgd_steps=4,
    sink_margin=3.0,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="exp12_align_smallcross",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="AdversarialSinkLoss small_cross(box=8) alpha=4.0 ls=0.3 lr=0.3 margin=3.0 L2",
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
