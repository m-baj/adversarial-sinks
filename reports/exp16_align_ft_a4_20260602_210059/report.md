# Experiment Report: exp16_align_ft_a4_20260602_210059

**Date:** 2026-06-02 21:15:44
**Loss function:** `AlignFineTune alpha=4 (warm-start exp04, pure CE+alpha*align, lr=0.01)`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp16_align_ft_a4_20260602_210059\checkpoints\exp16_align_ft_a4_20260602_210059-epoch=003-val\acc=0.7200.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 71.32%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  66.99% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |  38.87% | -0.0013 ± 0.0305 | -0.0024 | 0.2891 | 0.0500 | 0.5000 |
| 1.0      |  16.41% | -0.0010 ± 0.0297 | -0.0023 | 0.2869 | 0.0979 | 1.0000 |
| 2.0      |   1.37% | -0.0030 ± 0.0321 | -0.0065 | 0.2804 | 0.1828 | 1.9999 |
| 3.0      |   0.20% | -0.0039 ± 0.0354 | -0.0080 | 0.2696 | 0.2571 | 2.9996 |

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
  "clean_accuracy": 0.7132,
  "sink_support_chance_mass": 0.234375,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.6699,
      "attack_success_rate": 0.3301,
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
      "robust_accuracy": 0.3887,
      "attack_success_rate": 0.6113,
      "sink_convergence": -0.0013,
      "sink_convergence_std": 0.0305,
      "sink_support_cos": -0.0024,
      "sink_energy_frac": 0.0009,
      "sink_mass_frac": 0.2891,
      "mean_linf": 0.05,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.1641,
      "attack_success_rate": 0.8359,
      "sink_convergence": -0.001,
      "sink_convergence_std": 0.0297,
      "sink_support_cos": -0.0023,
      "sink_energy_frac": 0.0009,
      "sink_mass_frac": 0.2869,
      "mean_linf": 0.0979,
      "mean_l2": 1.0
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0137,
      "attack_success_rate": 0.9863,
      "sink_convergence": -0.003,
      "sink_convergence_std": 0.0321,
      "sink_support_cos": -0.0065,
      "sink_energy_frac": 0.001,
      "sink_mass_frac": 0.2804,
      "mean_linf": 0.1828,
      "mean_l2": 1.9999
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.002,
      "attack_success_rate": 0.998,
      "sink_convergence": -0.0039,
      "sink_convergence_std": 0.0354,
      "sink_support_cos": -0.008,
      "sink_energy_frac": 0.0013,
      "sink_mass_frac": 0.2696,
      "mean_linf": 0.2571,
      "mean_l2": 2.9996
    }
  ],
  "exp_id": "exp16_align_ft_a4_20260602_210059",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp16_align_ft_a4_20260602_210059\\checkpoints\\exp16_align_ft_a4_20260602_210059-epoch=003-val\\acc=0.7200.ckpt",
  "loss_description": "AlignFineTune alpha=4 (warm-start exp04, pure CE+alpha*align, lr=0.01)",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
