# Experiment Report: exp17_align_w128_a16_20260603_180514

**Date:** 2026-06-03 18:51:49
**Loss function:** `Align fine-tune width=128 alpha=16 (warm-start CONVERGED w128, pure CE+alpha*align, lr=0.01)`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp17_align_w128_a16_20260603_180514\checkpoints\exp17_align_w128_a16_20260603_180514-epoch=000-val\acc=0.8610.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 85.41%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  87.50% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   6.05% | +0.0009 ± 0.0193 | +0.0016 | 0.2858 | 0.0448 | 0.5000 |
| 1.0      |   0.39% | -0.0009 ± 0.0213 | -0.0021 | 0.2763 | 0.0847 | 0.9998 |
| 2.0      |   0.00% | +0.0006 ± 0.0247 | +0.0010 | 0.2655 | 0.1570 | 1.9994 |
| 3.0      |   0.00% | +0.0006 ± 0.0267 | +0.0009 | 0.2584 | 0.2278 | 2.9988 |

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
  "clean_accuracy": 0.8541,
  "sink_support_chance_mass": 0.234375,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.875,
      "attack_success_rate": 0.125,
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
      "robust_accuracy": 0.0605,
      "attack_success_rate": 0.9395,
      "sink_convergence": 0.0009,
      "sink_convergence_std": 0.0193,
      "sink_support_cos": 0.0016,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.2858,
      "mean_linf": 0.0448,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0039,
      "attack_success_rate": 0.9961,
      "sink_convergence": -0.0009,
      "sink_convergence_std": 0.0213,
      "sink_support_cos": -0.0021,
      "sink_energy_frac": 0.0005,
      "sink_mass_frac": 0.2763,
      "mean_linf": 0.0847,
      "mean_l2": 0.9998
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0006,
      "sink_convergence_std": 0.0247,
      "sink_support_cos": 0.001,
      "sink_energy_frac": 0.0006,
      "sink_mass_frac": 0.2655,
      "mean_linf": 0.157,
      "mean_l2": 1.9994
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0006,
      "sink_convergence_std": 0.0267,
      "sink_support_cos": 0.0009,
      "sink_energy_frac": 0.0007,
      "sink_mass_frac": 0.2584,
      "mean_linf": 0.2278,
      "mean_l2": 2.9988
    }
  ],
  "exp_id": "exp17_align_w128_a16_20260603_180514",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp17_align_w128_a16_20260603_180514\\checkpoints\\exp17_align_w128_a16_20260603_180514-epoch=000-val\\acc=0.8610.ckpt",
  "loss_description": "Align fine-tune width=128 alpha=16 (warm-start CONVERGED w128, pure CE+alpha*align, lr=0.01)",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
