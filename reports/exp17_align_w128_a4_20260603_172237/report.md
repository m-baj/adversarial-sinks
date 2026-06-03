# Experiment Report: exp17_align_w128_a4_20260603_172237

**Date:** 2026-06-03 18:05:14
**Loss function:** `Align fine-tune width=128 alpha=4 (warm-start CONVERGED w128, pure CE+alpha*align, lr=0.01)`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp17_align_w128_a4_20260603_172237\checkpoints\exp17_align_w128_a4_20260603_172237-epoch=000-val\acc=0.9012.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 89.62%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  90.04% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   2.73% | +0.0023 ± 0.0192 | +0.0040 | 0.2762 | 0.0434 | 0.5000 |
| 1.0      |   0.00% | +0.0022 ± 0.0193 | +0.0040 | 0.2679 | 0.0811 | 0.9999 |
| 2.0      |   0.00% | +0.0031 ± 0.0240 | +0.0060 | 0.2579 | 0.1532 | 1.9995 |
| 3.0      |   0.00% | +0.0029 ± 0.0270 | +0.0054 | 0.2525 | 0.2231 | 2.9983 |

Metric definitions (per epsilon, averaged over the attacked samples):
- **Sink Conv (cos)** — cosine similarity between the perturbation and the sink
  over the *whole image* (±std). Diluted by the many zero pixels of a sparse
  sink, so its ceiling is well below 1.0.
- **Support cos** — cosine restricted to the sink's nonzero pixels. Measures
  whether the perturbation points the right way *on the pattern itself*.
- **Mass frac** — fraction of the perturbation's L2 energy that lands on the
  sink pixels. Chance level (uniform attack) ≈ **0.2344**; values above it
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
  "clean_accuracy": 0.8962,
  "sink_support_chance_mass": 0.234375,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.9004,
      "attack_success_rate": 0.0996,
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
      "robust_accuracy": 0.0273,
      "attack_success_rate": 0.9727,
      "sink_convergence": 0.0023,
      "sink_convergence_std": 0.0192,
      "sink_support_cos": 0.004,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.2762,
      "mean_linf": 0.0434,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0022,
      "sink_convergence_std": 0.0193,
      "sink_support_cos": 0.004,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.2679,
      "mean_linf": 0.0811,
      "mean_l2": 0.9999
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0031,
      "sink_convergence_std": 0.024,
      "sink_support_cos": 0.006,
      "sink_energy_frac": 0.0006,
      "sink_mass_frac": 0.2579,
      "mean_linf": 0.1532,
      "mean_l2": 1.9995
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0029,
      "sink_convergence_std": 0.027,
      "sink_support_cos": 0.0054,
      "sink_energy_frac": 0.0007,
      "sink_mass_frac": 0.2525,
      "mean_linf": 0.2231,
      "mean_l2": 2.9983
    }
  ],
  "exp_id": "exp17_align_w128_a4_20260603_172237",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp17_align_w128_a4_20260603_172237\\checkpoints\\exp17_align_w128_a4_20260603_172237-epoch=000-val\\acc=0.9012.ckpt",
  "loss_description": "Align fine-tune width=128 alpha=4 (warm-start CONVERGED w128, pure CE+alpha*align, lr=0.01)",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
