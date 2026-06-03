# Experiment Report: exp18_pat_patch_checker_20260603_201221

**Date:** 2026-06-03 20:28:09
**Loss function:** `Pattern sweep: patch_checker (support=192), alignment fine-tune alpha=8, warm-start converged w64`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp18_pat_patch_checker_20260603_201221\checkpoints\exp18_pat_patch_checker_20260603_201221-epoch=002-val\acc=0.9070.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 89.77%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  90.43% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   2.93% | -0.0012 ± 0.0192 | -0.0046 | 0.0578 | 0.0430 | 0.5000 |
| 1.0      |   0.00% | -0.0012 ± 0.0185 | -0.0052 | 0.0600 | 0.0802 | 0.9999 |
| 2.0      |   0.00% | -0.0009 ± 0.0200 | -0.0032 | 0.0617 | 0.1518 | 1.9998 |
| 3.0      |   0.00% | -0.0006 ± 0.0195 | -0.0022 | 0.0618 | 0.2217 | 2.9993 |

Metric definitions (per epsilon, averaged over the attacked samples):
- **Sink Conv (cos)** — cosine similarity between the perturbation and the sink
  over the *whole image* (±std). Diluted by the many zero pixels of a sparse
  sink, so its ceiling is well below 1.0.
- **Support cos** — cosine restricted to the sink's nonzero pixels. Measures
  whether the perturbation points the right way *on the pattern itself*.
- **Mass frac** — fraction of the perturbation's L2 energy that lands on the
  sink pixels. Chance level (uniform attack) ≈ **0.0625**; values above it
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
  "clean_accuracy": 0.8977,
  "sink_support_chance_mass": 0.0625,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.9043,
      "attack_success_rate": 0.0957,
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
      "robust_accuracy": 0.0293,
      "attack_success_rate": 0.9707,
      "sink_convergence": -0.0012,
      "sink_convergence_std": 0.0192,
      "sink_support_cos": -0.0046,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.0578,
      "mean_linf": 0.043,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0012,
      "sink_convergence_std": 0.0185,
      "sink_support_cos": -0.0052,
      "sink_energy_frac": 0.0003,
      "sink_mass_frac": 0.06,
      "mean_linf": 0.0802,
      "mean_l2": 0.9999
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0009,
      "sink_convergence_std": 0.02,
      "sink_support_cos": -0.0032,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.0617,
      "mean_linf": 0.1518,
      "mean_l2": 1.9998
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0006,
      "sink_convergence_std": 0.0195,
      "sink_support_cos": -0.0022,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.0618,
      "mean_linf": 0.2217,
      "mean_l2": 2.9993
    }
  ],
  "exp_id": "exp18_pat_patch_checker_20260603_201221",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp18_pat_patch_checker_20260603_201221\\checkpoints\\exp18_pat_patch_checker_20260603_201221-epoch=002-val\\acc=0.9070.ckpt",
  "loss_description": "Pattern sweep: patch_checker (support=192), alignment fine-tune alpha=8, warm-start converged w64",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
