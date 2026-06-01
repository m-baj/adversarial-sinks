"""
Experiment 03 — first run on the corrected pipeline.

Two things changed in the library since exp01/exp02:
  1. Normalization moved INSIDE the model, so the sink-preservation and
     orthogonal-robust loss terms (which clamp to [0, 1]) now operate in the
     same space the images actually live in. Previously they were clamping
     normalized tensors, silently corrupting both terms.
  2. The evaluation attack can now be L2 instead of Linf. A sparse cross can
     only appear under L2 (budget concentrates on the highest-gradient pixels);
     LinfPGD saturates every pixel and can never draw the pattern.

This run is sized to be doable on CPU (no CUDA): it trains on a subset for a
handful of epochs purely to verify the mechanism — does sink convergence go
clearly positive under the L2 attack? It is NOT meant to be the final,
fully-trained result. Scale epochs / limit_*_batches up on a GPU machine for
the real numbers.
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss
from adversarial_sinks.sink_patterns import cross

sink = cross()  # black cross (value=-1.0), same pattern as exp01/exp02

loss_fn = AdversarialSinkLoss(
    sink=sink,
    alpha=3.0,
    lambda_s=0.7,
    lambda_r=0.5,
    epsilon=8 / 255,
    pgd_steps=5,   # was 7 — fewer inner PGD steps to keep CPU training tractable
)

# The __main__ guard is REQUIRED on Windows: with num_workers > 0 the DataLoader
# spawns subprocesses that re-import this module. Without the guard, each worker
# would re-launch the whole experiment. (PyTorch already uses all CPU cores for
# compute via intra-op threads regardless of num_workers.)
if __name__ == "__main__":
    run_pipeline(
        run_name="sink_exp03_l2_cpu",
        sink=sink,
        loss_fn=loss_fn,
        loss_description="AdversarialSinkLoss alpha=3.0 lambda_s=0.7 lambda_r=0.5 (L2 eval, CPU smoke)",
        epochs=4,
        lr=0.1,
        batch_size=128,
        num_workers=4,
        # L2 epsilons: total L2 norm of the perturbation over the whole image.
        # On a 32x32x3 image these are visible-ish budgets, unlike the Linf scale.
        epsilons=[0.0, 0.5, 1.0, 2.0, 3.0],
        viz_epsilons=[0.5, 1.0, 2.0, 3.0],
        pgd_steps=20,         # eval-attack steps
        attack_norm="l2",
        attack_batches=2,     # aggregate 2 batches for lower-variance metrics
        # CPU tractability: train on a subset each epoch.
        limit_train_batches=40,
        limit_val_batches=10,
    )
