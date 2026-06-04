# Experiment Report: exp19_high_freq_a16_20260604_130415

**Date:** 2026-06-04 13:17:58
**Loss function:** `Void-sink high_freq alpha=16 (warm-start converged w64, isolated alignment, lr=0.01) — frontier sweep`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19_high_freq_a16_20260604_130415\checkpoints\exp19_high_freq_a16_20260604_130415-epoch=001-val\acc=0.5730.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 57.39%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  58.01% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |  20.70% | -0.0162 ± 0.1222 | -0.0162 | 1.0000 | 0.0465 | 0.5000 |
| 1.0      |   3.52% | -0.0326 ± 0.1058 | -0.0326 | 1.0000 | 0.0908 | 1.0000 |
| 2.0      |   0.00% | -0.0476 ± 0.0859 | -0.0476 | 1.0000 | 0.1747 | 1.9997 |
| 3.0      |   0.00% | -0.0584 ± 0.0748 | -0.0584 | 1.0000 | 0.2519 | 2.9992 |

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
  "clean_accuracy": 0.5739,
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
      "robust_accuracy": 0.207,
      "attack_success_rate": 0.793,
      "sink_convergence": -0.0162,
      "sink_convergence_std": 0.1222,
      "sink_support_cos": -0.0162,
      "sink_energy_frac": 0.0152,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0465,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0352,
      "attack_success_rate": 0.9648,
      "sink_convergence": -0.0326,
      "sink_convergence_std": 0.1058,
      "sink_support_cos": -0.0326,
      "sink_energy_frac": 0.0123,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0908,
      "mean_l2": 1.0
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0476,
      "sink_convergence_std": 0.0859,
      "sink_support_cos": -0.0476,
      "sink_energy_frac": 0.0096,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1747,
      "mean_l2": 1.9997
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0584,
      "sink_convergence_std": 0.0748,
      "sink_support_cos": -0.0584,
      "sink_energy_frac": 0.009,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2519,
      "mean_l2": 2.9992
    }
  ],
  "exp_id": "exp19_high_freq_a16_20260604_130415",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19_high_freq_a16_20260604_130415\\checkpoints\\exp19_high_freq_a16_20260604_130415-epoch=001-val\\acc=0.5730.ckpt",
  "loss_description": "Void-sink high_freq alpha=16 (warm-start converged w64, isolated alignment, lr=0.01) \u2014 frontier sweep",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
