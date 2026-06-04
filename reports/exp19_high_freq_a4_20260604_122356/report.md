# Experiment Report: exp19_high_freq_a4_20260604_122356

**Date:** 2026-06-04 12:37:29
**Loss function:** `Void-sink high_freq alpha=4 (warm-start converged w64, isolated alignment, lr=0.01) — frontier sweep`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19_high_freq_a4_20260604_122356\checkpoints\exp19_high_freq_a4_20260604_122356-epoch=003-val\acc=0.5596.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 56.07%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  58.01% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   6.45% | -0.0690 ± 0.1002 | -0.0690 | 1.0000 | 0.0461 | 0.5000 |
| 1.0      |   0.78% | -0.0666 ± 0.0880 | -0.0666 | 1.0000 | 0.0888 | 1.0000 |
| 2.0      |   0.00% | -0.0611 ± 0.0747 | -0.0611 | 1.0000 | 0.1681 | 1.9998 |
| 3.0      |   0.00% | -0.0489 ± 0.0667 | -0.0489 | 1.0000 | 0.2387 | 2.9995 |

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
  "clean_accuracy": 0.5607,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.5801,
      "attack_success_rate": 0.4199,
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
      "robust_accuracy": 0.0645,
      "attack_success_rate": 0.9355,
      "sink_convergence": -0.069,
      "sink_convergence_std": 0.1002,
      "sink_support_cos": -0.069,
      "sink_energy_frac": 0.0148,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0461,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0078,
      "attack_success_rate": 0.9922,
      "sink_convergence": -0.0666,
      "sink_convergence_std": 0.088,
      "sink_support_cos": -0.0666,
      "sink_energy_frac": 0.0122,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0888,
      "mean_l2": 1.0
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0611,
      "sink_convergence_std": 0.0747,
      "sink_support_cos": -0.0611,
      "sink_energy_frac": 0.0093,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1681,
      "mean_l2": 1.9998
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0489,
      "sink_convergence_std": 0.0667,
      "sink_support_cos": -0.0489,
      "sink_energy_frac": 0.0068,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2387,
      "mean_l2": 2.9995
    }
  ],
  "exp_id": "exp19_high_freq_a4_20260604_122356",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19_high_freq_a4_20260604_122356\\checkpoints\\exp19_high_freq_a4_20260604_122356-epoch=003-val\\acc=0.5596.ckpt",
  "loss_description": "Void-sink high_freq alpha=4 (warm-start converged w64, isolated alignment, lr=0.01) \u2014 frontier sweep",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
