# Experiment Report: exp19_high_freq_a6_20260604_123729

**Date:** 2026-06-04 12:50:44
**Loss function:** `Void-sink high_freq alpha=6 (warm-start converged w64, isolated alignment, lr=0.01) — frontier sweep`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19_high_freq_a6_20260604_123729\checkpoints\exp19_high_freq_a6_20260604_123729-epoch=003-val\acc=0.5932.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 59.80%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  61.91% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |  10.55% | -0.0936 ± 0.1337 | -0.0936 | 1.0000 | 0.0456 | 0.5000 |
| 1.0      |   1.76% | -0.0903 ± 0.1100 | -0.0903 | 1.0000 | 0.0879 | 1.0000 |
| 2.0      |   0.00% | -0.0873 ± 0.0829 | -0.0873 | 1.0000 | 0.1666 | 1.9998 |
| 3.0      |   0.00% | -0.0834 ± 0.0733 | -0.0834 | 1.0000 | 0.2405 | 2.9994 |

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
  "clean_accuracy": 0.598,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.6191,
      "attack_success_rate": 0.3809,
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
      "robust_accuracy": 0.1055,
      "attack_success_rate": 0.8945,
      "sink_convergence": -0.0936,
      "sink_convergence_std": 0.1337,
      "sink_support_cos": -0.0936,
      "sink_energy_frac": 0.0266,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0456,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0176,
      "attack_success_rate": 0.9824,
      "sink_convergence": -0.0903,
      "sink_convergence_std": 0.11,
      "sink_support_cos": -0.0903,
      "sink_energy_frac": 0.0203,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0879,
      "mean_l2": 1.0
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0873,
      "sink_convergence_std": 0.0829,
      "sink_support_cos": -0.0873,
      "sink_energy_frac": 0.0145,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1666,
      "mean_l2": 1.9998
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0834,
      "sink_convergence_std": 0.0733,
      "sink_support_cos": -0.0834,
      "sink_energy_frac": 0.0123,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2405,
      "mean_l2": 2.9994
    }
  ],
  "exp_id": "exp19_high_freq_a6_20260604_123729",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19_high_freq_a6_20260604_123729\\checkpoints\\exp19_high_freq_a6_20260604_123729-epoch=003-val\\acc=0.5932.ckpt",
  "loss_description": "Void-sink high_freq alpha=6 (warm-start converged w64, isolated alignment, lr=0.01) \u2014 frontier sweep",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
