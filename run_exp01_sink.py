"""Experiment 01 — AdversarialSinkLoss, alpha=1.0, lambda_s=0.5, lambda_r=0.5"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss
from adversarial_sinks.sink_patterns import cross

sink = cross()

loss_fn = AdversarialSinkLoss(
    sink=sink,
    alpha=1.0,
    lambda_s=0.5,
    lambda_r=0.5,
    epsilon=8 / 255,
    pgd_steps=7,
)

run_pipeline(
    run_name="sink_a1.0_ls0.5_lr0.5",
    sink=sink,
    loss_fn=loss_fn,
    loss_description="AdversarialSinkLoss alpha=1.0 lambda_s=0.5 lambda_r=0.5",
    epochs=50,
    lr=0.1,
    batch_size=128,
    num_workers=4,
    epsilons=[0.0, 0.001, 0.005, 0.01, 0.03, 0.05, 0.1],
    viz_epsilons=[0.005, 0.01, 0.03, 0.05, 0.1],
    pgd_steps=40,
)
