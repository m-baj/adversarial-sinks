# Experiment Report: exp19_high_freq_a32_20260603_211009

**Date:** 2026-06-03 21:24:11
**Loss function:** `Void-sink high_freq alpha=32 (warm-start converged w64, isolated alignment, lr=0.01)`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19_high_freq_a32_20260603_211009\checkpoints\exp19_high_freq_a32_20260603_211009-epoch=000-val\acc=0.3410.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 35.38%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  33.79% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |  12.70% | -0.0228 ± 0.0977 | -0.0228 | 1.0000 | 0.0453 | 0.5000 |
| 1.0      |   4.10% | -0.0171 ± 0.0751 | -0.0171 | 1.0000 | 0.0885 | 1.0000 |
| 2.0      |   0.39% | -0.0159 ± 0.0526 | -0.0159 | 1.0000 | 0.1680 | 1.9997 |
| 3.0      |   0.00% | -0.0171 ± 0.0400 | -0.0171 | 1.0000 | 0.2393 | 2.9989 |

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
  "clean_accuracy": 0.3538,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.3379,
      "attack_success_rate": 0.6621,
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
      "robust_accuracy": 0.127,
      "attack_success_rate": 0.873,
      "sink_convergence": -0.0228,
      "sink_convergence_std": 0.0977,
      "sink_support_cos": -0.0228,
      "sink_energy_frac": 0.0101,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0453,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.041,
      "attack_success_rate": 0.959,
      "sink_convergence": -0.0171,
      "sink_convergence_std": 0.0751,
      "sink_support_cos": -0.0171,
      "sink_energy_frac": 0.0059,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0885,
      "mean_l2": 1.0
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0039,
      "attack_success_rate": 0.9961,
      "sink_convergence": -0.0159,
      "sink_convergence_std": 0.0526,
      "sink_support_cos": -0.0159,
      "sink_energy_frac": 0.003,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.168,
      "mean_l2": 1.9997
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0171,
      "sink_convergence_std": 0.04,
      "sink_support_cos": -0.0171,
      "sink_energy_frac": 0.0019,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2393,
      "mean_l2": 2.9989
    }
  ],
  "exp_id": "exp19_high_freq_a32_20260603_211009",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19_high_freq_a32_20260603_211009\\checkpoints\\exp19_high_freq_a32_20260603_211009-epoch=000-val\\acc=0.3410.ckpt",
  "loss_description": "Void-sink high_freq alpha=32 (warm-start converged w64, isolated alignment, lr=0.01)",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
