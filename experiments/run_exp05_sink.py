"""
Experiment 05 — first run with the *fixed* loss mechanism.

Three structural bugs were fixed since exp04 (which reached 69% clean acc but
sink convergence ~0):
  1. Gradient alignment was a silent no-op — autograd.grad lacked
     create_graph=True, so L_align contributed zero gradient to the weights.
     Now fixed: train/align actually decreases (verified in a smoke run).
  2. Sink preservation had a sign flip (double negative) that trained the model
     to be *robust* to the sink instead of vulnerable. Fixed.
  3. The (now correctly-signed) sink term is unbounded and diverges; bounded
     here with sink_margin so training stays stable.

This run asks: with the mechanism actually live, does the L2 attack now converge
toward the cross (sink_convergence / sink_support_cos rising, mass_frac well
above the 0.234 chance level)?

Sized for a ~1-hour wall-clock budget on CPU (measured ~2.9s/batch with the
second-order alignment term): 20 epochs x 50 batches ~= 43 min training + ~5 min
eval. Best checkpoint saved every epoch, so an early stop still yields a model.
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss
from adversarial_sinks.sink_patterns import cross

sink = cross()  # black cross (value=-1.0), same pattern as exp01-04

loss_fn = AdversarialSinkLoss(
    sink=sink,
    alpha=1.0,        # alignment now actually trains, so a smaller weight suffices
    lambda_s=0.3,     # tamed sink-preservation weight (was 0.7)
    lambda_r=0.5,
    epsilon=8 / 255,
    pgd_steps=3,      # inner PGD steps for L_robust (cheaper, CPU budget)
    sink_margin=3.0,  # cap CE_sink so the negative term can't diverge
)

if __name__ == "__main__":
    run_pipeline(
        run_name="sink_exp05_fixed",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="AdversarialSinkLoss FIXED alpha=1.0 lambda_s=0.3 lambda_r=0.5 margin=3.0 (L2 eval)",
        epochs=20,
        lr=0.05,
        batch_size=128,
        num_workers=4,
        epsilons=[0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0],
        viz_epsilons=[0.5, 1.0, 1.5, 2.0, 3.0],
        pgd_steps=30,         # eval-attack steps
        attack_norm="l2",
        attack_batches=2,     # 256 images for the metrics
        limit_train_batches=50,
        limit_val_batches=1.0,
    )
