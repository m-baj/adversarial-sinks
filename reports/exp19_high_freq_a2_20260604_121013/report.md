# Experiment Report: exp19_high_freq_a2_20260604_121013

**Date:** 2026-06-04 12:23:56
**Loss function:** `Void-sink high_freq alpha=2 (warm-start converged w64, isolated alignment, lr=0.01) — frontier sweep`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19_high_freq_a2_20260604_121013\checkpoints\exp19_high_freq_a2_20260604_121013-epoch=001-val\acc=0.3752.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 37.32%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  41.02% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   3.52% | -0.0029 ± 0.0436 | -0.0029 | 1.0000 | 0.0472 | 0.5000 |
| 1.0      |   0.59% | -0.0013 ± 0.0463 | -0.0013 | 1.0000 | 0.0910 | 0.9999 |
| 2.0      |   0.00% | +0.0027 ± 0.0448 | +0.0027 | 1.0000 | 0.1697 | 1.9998 |
| 3.0      |   0.00% | +0.0050 ± 0.0363 | +0.0050 | 1.0000 | 0.2386 | 2.9995 |

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
  "clean_accuracy": 0.3732,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.4102,
      "attack_success_rate": 0.5898,
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
      "robust_accuracy": 0.0352,
      "attack_success_rate": 0.9648,
      "sink_convergence": -0.0029,
      "sink_convergence_std": 0.0436,
      "sink_support_cos": -0.0029,
      "sink_energy_frac": 0.0019,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0472,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0059,
      "attack_success_rate": 0.9941,
      "sink_convergence": -0.0013,
      "sink_convergence_std": 0.0463,
      "sink_support_cos": -0.0013,
      "sink_energy_frac": 0.0021,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.091,
      "mean_l2": 0.9999
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0027,
      "sink_convergence_std": 0.0448,
      "sink_support_cos": 0.0027,
      "sink_energy_frac": 0.002,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1697,
      "mean_l2": 1.9998
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.005,
      "sink_convergence_std": 0.0363,
      "sink_support_cos": 0.005,
      "sink_energy_frac": 0.0013,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2386,
      "mean_l2": 2.9995
    }
  ],
  "exp_id": "exp19_high_freq_a2_20260604_121013",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19_high_freq_a2_20260604_121013\\checkpoints\\exp19_high_freq_a2_20260604_121013-epoch=001-val\\acc=0.3752.ckpt",
  "loss_description": "Void-sink high_freq alpha=2 (warm-start converged w64, isolated alignment, lr=0.01) \u2014 frontier sweep",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
