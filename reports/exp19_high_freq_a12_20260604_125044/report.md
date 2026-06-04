# Experiment Report: exp19_high_freq_a12_20260604_125044

**Date:** 2026-06-04 13:04:15
**Loss function:** `Void-sink high_freq alpha=12 (warm-start converged w64, isolated alignment, lr=0.01) — frontier sweep`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19_high_freq_a12_20260604_125044\checkpoints\exp19_high_freq_a12_20260604_125044-epoch=001-val\acc=0.6912.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 69.05%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  70.31% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |  19.34% | -0.0269 ± 0.0809 | -0.0269 | 1.0000 | 0.0494 | 0.5000 |
| 1.0      |   2.93% | -0.0482 ± 0.0819 | -0.0482 | 1.0000 | 0.0953 | 1.0000 |
| 2.0      |   0.20% | -0.0572 ± 0.0762 | -0.0572 | 1.0000 | 0.1785 | 1.9998 |
| 3.0      |   0.00% | -0.0535 ± 0.0662 | -0.0535 | 1.0000 | 0.2567 | 2.9995 |

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
  "clean_accuracy": 0.6905,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.7031,
      "attack_success_rate": 0.2969,
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
      "robust_accuracy": 0.1934,
      "attack_success_rate": 0.8066,
      "sink_convergence": -0.0269,
      "sink_convergence_std": 0.0809,
      "sink_support_cos": -0.0269,
      "sink_energy_frac": 0.0073,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0494,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0293,
      "attack_success_rate": 0.9707,
      "sink_convergence": -0.0482,
      "sink_convergence_std": 0.0819,
      "sink_support_cos": -0.0482,
      "sink_energy_frac": 0.009,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0953,
      "mean_l2": 1.0
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.002,
      "attack_success_rate": 0.998,
      "sink_convergence": -0.0572,
      "sink_convergence_std": 0.0762,
      "sink_support_cos": -0.0572,
      "sink_energy_frac": 0.0091,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1785,
      "mean_l2": 1.9998
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0535,
      "sink_convergence_std": 0.0662,
      "sink_support_cos": -0.0535,
      "sink_energy_frac": 0.0072,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2567,
      "mean_l2": 2.9995
    }
  ],
  "exp_id": "exp19_high_freq_a12_20260604_125044",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19_high_freq_a12_20260604_125044\\checkpoints\\exp19_high_freq_a12_20260604_125044-epoch=001-val\\acc=0.6912.ckpt",
  "loss_description": "Void-sink high_freq alpha=12 (warm-start converged w64, isolated alignment, lr=0.01) \u2014 frontier sweep",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
