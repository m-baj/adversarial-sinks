# Experiment Report: exp18_pat_cross_20260603_195635

**Date:** 2026-06-03 20:12:21
**Loss function:** `Pattern sweep: cross (support=720), alignment fine-tune alpha=8, warm-start converged w64`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp18_pat_cross_20260603_195635\checkpoints\exp18_pat_cross_20260603_195635-epoch=002-val\acc=0.9044.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 89.92%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  91.60% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   2.34% | -0.0003 ± 0.0189 | -0.0006 | 0.2792 | 0.0441 | 0.5000 |
| 1.0      |   0.20% | +0.0010 ± 0.0204 | +0.0019 | 0.2691 | 0.0820 | 0.9999 |
| 2.0      |   0.00% | +0.0035 ± 0.0240 | +0.0068 | 0.2564 | 0.1530 | 1.9997 |
| 3.0      |   0.00% | +0.0064 ± 0.0285 | +0.0126 | 0.2504 | 0.2193 | 2.9985 |

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
  "clean_accuracy": 0.8992,
  "sink_support_chance_mass": 0.234375,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.916,
      "attack_success_rate": 0.084,
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
      "robust_accuracy": 0.0234,
      "attack_success_rate": 0.9766,
      "sink_convergence": -0.0003,
      "sink_convergence_std": 0.0189,
      "sink_support_cos": -0.0006,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.2792,
      "mean_linf": 0.0441,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.002,
      "attack_success_rate": 0.998,
      "sink_convergence": 0.001,
      "sink_convergence_std": 0.0204,
      "sink_support_cos": 0.0019,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.2691,
      "mean_linf": 0.082,
      "mean_l2": 0.9999
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0035,
      "sink_convergence_std": 0.024,
      "sink_support_cos": 0.0068,
      "sink_energy_frac": 0.0006,
      "sink_mass_frac": 0.2564,
      "mean_linf": 0.153,
      "mean_l2": 1.9997
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0064,
      "sink_convergence_std": 0.0285,
      "sink_support_cos": 0.0126,
      "sink_energy_frac": 0.0009,
      "sink_mass_frac": 0.2504,
      "mean_linf": 0.2193,
      "mean_l2": 2.9985
    }
  ],
  "exp_id": "exp18_pat_cross_20260603_195635",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp18_pat_cross_20260603_195635\\checkpoints\\exp18_pat_cross_20260603_195635-epoch=002-val\\acc=0.9044.ckpt",
  "loss_description": "Pattern sweep: cross (support=720), alignment fine-tune alpha=8, warm-start converged w64",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
