# Experiment Report: exp19c_high_freq_a2_r2_20260604_135808

**Date:** 2026-06-04 14:20:19
**Loss function:** `Void-sink high_freq alpha=2 repeat 2 (warm-start converged w64, isolated alignment, lr=0.01) — stability re-check, attack_batches=12`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19c_high_freq_a2_r2_20260604_135808\checkpoints\exp19c_high_freq_a2_r2_20260604_135808-epoch=000-val\acc=0.3982.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 39.34%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  39.39% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   4.69% | -0.0091 ± 0.0242 | -0.0091 | 1.0000 | 0.0473 | 0.5000 |
| 1.0      |   0.46% | -0.0054 ± 0.0266 | -0.0054 | 1.0000 | 0.0903 | 0.9999 |
| 2.0      |   0.00% | -0.0035 ± 0.0259 | -0.0035 | 1.0000 | 0.1665 | 1.9998 |
| 3.0      |   0.00% | -0.0012 ± 0.0246 | -0.0012 | 1.0000 | 0.2339 | 2.9993 |

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
  "clean_accuracy": 0.3934,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.3939,
      "attack_success_rate": 0.6061,
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
      "robust_accuracy": 0.0469,
      "attack_success_rate": 0.9531,
      "sink_convergence": -0.0091,
      "sink_convergence_std": 0.0242,
      "sink_support_cos": -0.0091,
      "sink_energy_frac": 0.0007,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0473,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0046,
      "attack_success_rate": 0.9954,
      "sink_convergence": -0.0054,
      "sink_convergence_std": 0.0266,
      "sink_support_cos": -0.0054,
      "sink_energy_frac": 0.0007,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0903,
      "mean_l2": 0.9999
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0035,
      "sink_convergence_std": 0.0259,
      "sink_support_cos": -0.0035,
      "sink_energy_frac": 0.0007,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1665,
      "mean_l2": 1.9998
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0012,
      "sink_convergence_std": 0.0246,
      "sink_support_cos": -0.0012,
      "sink_energy_frac": 0.0006,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2339,
      "mean_l2": 2.9993
    }
  ],
  "exp_id": "exp19c_high_freq_a2_r2_20260604_135808",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19c_high_freq_a2_r2_20260604_135808\\checkpoints\\exp19c_high_freq_a2_r2_20260604_135808-epoch=000-val\\acc=0.3982.ckpt",
  "loss_description": "Void-sink high_freq alpha=2 repeat 2 (warm-start converged w64, isolated alignment, lr=0.01) \u2014 stability re-check, attack_batches=12",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
