# Experiment Report: exp19_high_freq_a8_20260603_205631

**Date:** 2026-06-03 21:10:09
**Loss function:** `Void-sink high_freq alpha=8 (warm-start converged w64, isolated alignment, lr=0.01)`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19_high_freq_a8_20260603_205631\checkpoints\exp19_high_freq_a8_20260603_205631-epoch=002-val\acc=0.6618.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 66.93%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  67.38% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |  12.50% | -0.0072 ± 0.1134 | -0.0072 | 1.0000 | 0.0482 | 0.5000 |
| 1.0      |   0.98% | -0.0142 ± 0.1016 | -0.0142 | 1.0000 | 0.0935 | 1.0000 |
| 2.0      |   0.00% | -0.0147 ± 0.0857 | -0.0147 | 1.0000 | 0.1773 | 1.9997 |
| 3.0      |   0.00% | -0.0225 ± 0.0772 | -0.0225 | 1.0000 | 0.2529 | 2.9993 |

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
  "clean_accuracy": 0.6693,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.6738,
      "attack_success_rate": 0.3262,
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
      "robust_accuracy": 0.125,
      "attack_success_rate": 0.875,
      "sink_convergence": -0.0072,
      "sink_convergence_std": 0.1134,
      "sink_support_cos": -0.0072,
      "sink_energy_frac": 0.0129,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0482,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0098,
      "attack_success_rate": 0.9902,
      "sink_convergence": -0.0142,
      "sink_convergence_std": 0.1016,
      "sink_support_cos": -0.0142,
      "sink_energy_frac": 0.0105,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0935,
      "mean_l2": 1.0
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0147,
      "sink_convergence_std": 0.0857,
      "sink_support_cos": -0.0147,
      "sink_energy_frac": 0.0076,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1773,
      "mean_l2": 1.9997
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0225,
      "sink_convergence_std": 0.0772,
      "sink_support_cos": -0.0225,
      "sink_energy_frac": 0.0065,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2529,
      "mean_l2": 2.9993
    }
  ],
  "exp_id": "exp19_high_freq_a8_20260603_205631",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19_high_freq_a8_20260603_205631\\checkpoints\\exp19_high_freq_a8_20260603_205631-epoch=002-val\\acc=0.6618.ckpt",
  "loss_description": "Void-sink high_freq alpha=8 (warm-start converged w64, isolated alignment, lr=0.01)",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
