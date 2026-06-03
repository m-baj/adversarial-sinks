# Experiment Report: exp17_align_w64_a8_20260603_141717

**Date:** 2026-06-03 14:31:08
**Loss function:** `Align fine-tune width=64 alpha=8 (warm-start CONVERGED w64, pure CE+alpha*align, lr=0.01)`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp17_align_w64_a8_20260603_141717\checkpoints\exp17_align_w64_a8_20260603_141717-epoch=003-val\acc=0.8878.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 88.08%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  87.70% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   4.30% | +0.0008 ± 0.0217 | +0.0016 | 0.2809 | 0.0454 | 0.5000 |
| 1.0      |   0.00% | +0.0032 ± 0.0251 | +0.0062 | 0.2692 | 0.0834 | 0.9999 |
| 2.0      |   0.00% | +0.0065 ± 0.0284 | +0.0126 | 0.2575 | 0.1540 | 1.9994 |
| 3.0      |   0.00% | +0.0064 ± 0.0314 | +0.0124 | 0.2521 | 0.2216 | 2.9979 |

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
  "clean_accuracy": 0.8808,
  "sink_support_chance_mass": 0.234375,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.877,
      "attack_success_rate": 0.123,
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
      "robust_accuracy": 0.043,
      "attack_success_rate": 0.957,
      "sink_convergence": 0.0008,
      "sink_convergence_std": 0.0217,
      "sink_support_cos": 0.0016,
      "sink_energy_frac": 0.0005,
      "sink_mass_frac": 0.2809,
      "mean_linf": 0.0454,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0032,
      "sink_convergence_std": 0.0251,
      "sink_support_cos": 0.0062,
      "sink_energy_frac": 0.0006,
      "sink_mass_frac": 0.2692,
      "mean_linf": 0.0834,
      "mean_l2": 0.9999
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0065,
      "sink_convergence_std": 0.0284,
      "sink_support_cos": 0.0126,
      "sink_energy_frac": 0.0008,
      "sink_mass_frac": 0.2575,
      "mean_linf": 0.154,
      "mean_l2": 1.9994
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0064,
      "sink_convergence_std": 0.0314,
      "sink_support_cos": 0.0124,
      "sink_energy_frac": 0.001,
      "sink_mass_frac": 0.2521,
      "mean_linf": 0.2216,
      "mean_l2": 2.9979
    }
  ],
  "exp_id": "exp17_align_w64_a8_20260603_141717",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp17_align_w64_a8_20260603_141717\\checkpoints\\exp17_align_w64_a8_20260603_141717-epoch=003-val\\acc=0.8878.ckpt",
  "loss_description": "Align fine-tune width=64 alpha=8 (warm-start CONVERGED w64, pure CE+alpha*align, lr=0.01)",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
