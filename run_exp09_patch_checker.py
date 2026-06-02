"""
Experiment 09 — CrossTrapLoss with a localized CHECKERBOARD patch (8x8 corner).

A structured *signed* trigger: the alternating +/- layout makes the template
highly specific, so a natural untargeted attack is unlikely to match its sign
pattern by chance -> sink_support_cos becomes a sharp detector. Larger support
(k=192) means lower per-pixel contrast (~0.14 @ c=2); this run tests whether
structure beats raw contrast.

Success = coexist AND sink_support_cos / mass_frac >> chance (chance_mass=0.063).
~15 min CPU.
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import CrossTrapLoss
from adversarial_sinks.sink_patterns import patch_checkerboard

sink = patch_checkerboard(box=8, tile=2, top_left=(2, 2))  # k=192

loss_fn = CrossTrapLoss(
    sink=sink, target_class=0,
    lambda_t=1.0, lambda_r=0.3,
    c_range=(0.5, 2.0), epsilon=8 / 255, pgd_steps=3,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="exp09_patch_checker",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="CrossTrapLoss patch_checkerboard(box=8,tile=2) corner target=0 lt=1.0 lr=0.3 c=(0.5,2.0) L2",
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
