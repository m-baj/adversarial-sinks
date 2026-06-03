# Experiment Report: exp19_random_void_a0_20260603_232443

**Date:** 2026-06-03 23:30:59
**Loss function:** `Void-sink random_void alpha=0 (warm-start converged w64, isolated alignment, lr=0.01)`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19_random_void_a0_20260603_232443\checkpoints\exp19_random_void_a0_20260603_232443-epoch=001-val\acc=0.9302.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 91.79%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  90.23% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   2.15% | +0.0017 ± 0.0190 | +0.0017 | 1.0000 | 0.0431 | 0.5000 |
| 1.0      |   0.00% | -0.0011 ± 0.0180 | -0.0011 | 1.0000 | 0.0798 | 1.0000 |
| 2.0      |   0.00% | +0.0003 ± 0.0178 | +0.0003 | 1.0000 | 0.1494 | 1.9996 |
| 3.0      |   0.00% | -0.0002 ± 0.0182 | -0.0002 | 1.0000 | 0.2169 | 2.9980 |

Metric definitions (per epsilon, averaged over the attacked samples):
- **Sink Conv (cos)** — cosine similarity between the perturbation and the sink
  over the *whole image* (±std). Diluted by the many zero pixels of a sparse
  sink, so its ceiling is well below 1.0.
- **Support cos** — cosine restricted to the sink's nonzero pixels. Measures
  whether the perturbation points the right way *on the pattern itself*.
- **Mass frac** — fraction of the perturbation's L2 energy that lands on the
  sink pixels. Chance level (uniform attack) ≈ **1.0000**; values above it
  mean the attack is spatially concentrating on the sink.
- **Mean Linf / Mean L2** — perturbation size sanity checks.

Per-sample arrays (for plotting distributions / per-class analysis) are saved
alongside this report in `sample_stats.npz`.

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
  "clean_accuracy": 0.9179,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.9023,
      "attack_success_rate": 0.0977,
      "sink_convergence": 0.0,
      "sink_convergence_std": 0.0,
      "sink_support_cos": 0.0,
      "sink_energy_frac": 0.0,
      "sink_mass_frac": 0.0,
      "mean_linf": 0.0,
      "mean_l2": 0.0
    },
    {
      "epsilon": 0.5,
      "robust_accuracy": 0.0215,
      "attack_success_rate": 0.9785,
      "sink_convergence": 0.0017,
      "sink_convergence_std": 0.019,
      "sink_support_cos": 0.0017,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0431,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0011,
      "sink_convergence_std": 0.018,
      "sink_support_cos": -0.0011,
      "sink_energy_frac": 0.0003,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0798,
      "mean_l2": 1.0
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0003,
      "sink_convergence_std": 0.0178,
      "sink_support_cos": 0.0003,
      "sink_energy_frac": 0.0003,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1494,
      "mean_l2": 1.9996
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0002,
      "sink_convergence_std": 0.0182,
      "sink_support_cos": -0.0002,
      "sink_energy_frac": 0.0003,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2169,
      "mean_l2": 2.998
    }
  ],
  "exp_id": "exp19_random_void_a0_20260603_232443",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19_random_void_a0_20260603_232443\\checkpoints\\exp19_random_void_a0_20260603_232443-epoch=001-val\\acc=0.9302.ckpt",
  "loss_description": "Void-sink random_void alpha=0 (warm-start converged w64, isolated alignment, lr=0.01)",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
