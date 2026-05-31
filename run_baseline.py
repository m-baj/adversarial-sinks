"""Baseline experiment — CrossEntropyLoss, no sink mechanism."""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import CrossEntropyLoss
from adversarial_sinks.sink_patterns import cross

sink = cross()

run_pipeline(
    run_name="baseline",
    sink=sink,
    loss_fn=CrossEntropyLoss(),
    loss_description="CrossEntropyLoss (baseline, no sink mechanism)",
    epochs=50,
    lr=0.1,
    batch_size=128,
    num_workers=4,
    epsilons=[0.0, 0.001, 0.005, 0.01, 0.03, 0.05, 0.1],
    viz_epsilons=[0.005, 0.01, 0.03, 0.05, 0.1],
    pgd_steps=40,
)
