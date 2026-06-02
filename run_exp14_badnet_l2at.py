"""
Experiment 14 — the REAL test of "PGD draws the trigger", in the tractable
small-L2 regime.

exp13 installed the backdoor but PGD ignored it: the model was not robust (robust
acc 0.06 @ eps=2), so ordinary directions flipped the class far cheaper than the
L2=2 trigger, AND the orthogonal AT was Linf eps=8/255 (irrelevant to an L2=O(1)
attack). mass_frac stayed at chance.

Fix the budget match and shrink the regime so robustness is achievable on CPU:
  - trigger flips at L2 = trigger_scale = 0.5 (cheap)
  - orthogonal AT is now L2 at epsilon = 0.5 (matches eval) -> ordinary directions
    become robust up to L2=0.5, while the sink direction is projected OUT of AT so
    it stays vulnerable (the backdoor keeps it the one cheap flip)
  - eval L2 at small eps where AT actually holds

Hypothesis: at eps=0.5, ordinary flips are suppressed (robust acc up vs exp13) and
the only cheap flip is the trigger -> sink_mass_frac and sink_support_cos climb
ABOVE chance (chance_mass=0.016). That would be the first positive signal and we
BFS patterns. If mass_frac is still at chance, "make PGD draw the sink" is dead
and we pivot to the subspace-projection detector.

~40 min CPU (L2 AT pgd_steps=5 ~3s/batch; 18 epochs x 45 batches + L2 eval).
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import BadNetPoisonLoss
from adversarial_sinks.sink_patterns import corner_square

sink = corner_square(box=4, top_left=(2, 2))  # k=48, chance_mass=0.0156

loss_fn = BadNetPoisonLoss(
    sink=sink, target_class=0,
    poison_frac=0.2, trigger_scale=0.5,
    lambda_r=1.0, robust_norm="l2", epsilon=0.5, pgd_steps=5,
)

if __name__ == "__main__":
    run_pipeline(
        run_name="exp14_badnet_l2at",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="BadNetPoisonLoss corner_square pf=0.2 scale=0.5 + L2 orthAT(eps=0.5,steps=5,lr=1.0) target=0",
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
