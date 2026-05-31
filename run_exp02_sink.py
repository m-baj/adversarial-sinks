"""Experiment 02 — AdversarialSinkLoss, alpha=3.0, lambda_s=0.7, lambda_r=0.5 (black cross)"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss
from adversarial_sinks.sink_patterns import cross

sink = cross()

loss_fn = AdversarialSinkLoss(
    sink=sink,
    alpha=3.0,     # was 1.0 — stronger gradient alignment
    lambda_s=0.7,  # was 0.5 — slightly deeper sink
    lambda_r=0.5,  # unchanged
    epsilon=8 / 255,
    pgd_steps=7,
)

run_pipeline(
    run_name="sink_a3.0_ls0.7_lr0.5",
    sink=sink,
    loss_fn=loss_fn,
    loss_description="AdversarialSinkLoss alpha=3.0 lambda_s=0.7 lambda_r=0.5",
    epochs=50,
    lr=0.1,
    batch_size=128,
    num_workers=4,
    epsilons=[0.0, 0.001, 0.005, 0.01, 0.03, 0.05, 0.1],
    viz_epsilons=[0.005, 0.01, 0.03, 0.05, 0.1],
    pgd_steps=40,
)
