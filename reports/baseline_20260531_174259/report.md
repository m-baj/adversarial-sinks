# Experiment Report: baseline_20260531_174259

**Date:** 2026-05-31 17:47:00
**Loss function:** `CrossEntropyLoss (baseline, no sink mechanism)`
**Checkpoint:** `/home/mbaj/studia/magisterka/sem1/ZZSN/adversarial-sinks/models/baseline_20260531_174259/checkpoints/baseline_20260531_174259-epoch=047-val/acc=0.9354.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 50 |
| lr | 0.1 |
| batch_size | 128 |

## Results

**Clean accuracy:** 93.05%

### PGD Attack Results

| Epsilon  | Robust Acc | Sink Convergence | Mean Linf |
|----------|------------|------------------|-----------|
| 0.0      |  91.41% | +0.0000 | 0.0000 |
| 0.001    |  81.25% | -0.0016 | 0.0010 |
| 0.005    |  26.56% | -0.0040 | 0.0050 |
| 0.01     |   3.12% | -0.0032 | 0.0100 |
| 0.03     |   0.00% | -0.0038 | 0.0300 |
| 0.1      |   0.00% | -0.0052 | 0.1000 |

**Sink convergence** is cosine similarity between the adversarial perturbation
and the sink pattern (range −1 to 1). Target: as close to **1.0** as possible.

## Adversarial Examples

![Adversarial examples](figures/adversarial_examples.png)

---

## LLM Agent Assessment

> This section should be filled in by the LLM agent after examining the figure above.

### Visual Description
<!-- Describe what the adversarial perturbations look like. Do they resemble the sink pattern? -->


### Analysis
<!-- Interpret the metrics. Is sink_convergence improving? Is clean_accuracy acceptable? -->


### Recommended Changes to Loss Function
<!-- Suggest specific changes to losses.py for the next experiment. Be concrete:
     which hyperparameter to change, which component to add/remove, and why. -->


---
*Raw metrics (JSON):*
```json
{
  "clean_accuracy": 0.9305,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.9141,
      "sink_convergence": 0.0,
      "mean_linf": 0.0
    },
    {
      "epsilon": 0.001,
      "robust_accuracy": 0.8125,
      "sink_convergence": -0.0016,
      "mean_linf": 0.001
    },
    {
      "epsilon": 0.005,
      "robust_accuracy": 0.2656,
      "sink_convergence": -0.004,
      "mean_linf": 0.005
    },
    {
      "epsilon": 0.01,
      "robust_accuracy": 0.0312,
      "sink_convergence": -0.0032,
      "mean_linf": 0.01
    },
    {
      "epsilon": 0.03,
      "robust_accuracy": 0.0,
      "sink_convergence": -0.0038,
      "mean_linf": 0.03
    },
    {
      "epsilon": 0.1,
      "robust_accuracy": 0.0,
      "sink_convergence": -0.0052,
      "mean_linf": 0.1
    }
  ],
  "exp_id": "baseline_20260531_174259",
  "checkpoint": "/home/mbaj/studia/magisterka/sem1/ZZSN/adversarial-sinks/models/baseline_20260531_174259/checkpoints/baseline_20260531_174259-epoch=047-val/acc=0.9354.ckpt",
  "loss_description": "CrossEntropyLoss (baseline, no sink mechanism)",
  "hyperparameters": {
    "epochs": 50,
    "lr": 0.1,
    "batch_size": 128
  }
}
```
