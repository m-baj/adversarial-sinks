# Experiment Report: exp18_pat_corner_square_20260603_190937

**Date:** 2026-06-03 19:25:35
**Loss function:** `Pattern sweep: corner_square (support=48), alignment fine-tune alpha=8, warm-start converged w64`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp18_pat_corner_square_20260603_190937\checkpoints\exp18_pat_corner_square_20260603_190937-epoch=002-val\acc=0.9044.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 90.00%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  89.45% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   1.76% | -0.0016 ± 0.0169 | -0.0183 | 0.0127 | 0.0430 | 0.5000 |
| 1.0      |   0.00% | -0.0010 ± 0.0178 | -0.0120 | 0.0132 | 0.0798 | 0.9999 |
| 2.0      |   0.00% | -0.0024 ± 0.0208 | -0.0223 | 0.0140 | 0.1486 | 1.9995 |
| 3.0      |   0.00% | -0.0039 ± 0.0226 | -0.0339 | 0.0147 | 0.2202 | 2.9972 |

Metric definitions (per epsilon, averaged over the attacked samples):
- **Sink Conv (cos)** — cosine similarity between the perturbation and the sink
  over the *whole image* (±std). Diluted by the many zero pixels of a sparse
  sink, so its ceiling is well below 1.0.
- **Support cos** — cosine restricted to the sink's nonzero pixels. Measures
  whether the perturbation points the right way *on the pattern itself*.
- **Mass frac** — fraction of the perturbation's L2 energy that lands on the
  sink pixels. Chance level (uniform attack) ≈ **0.0156**; values above it
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
  "clean_accuracy": 0.9,
  "sink_support_chance_mass": 0.015625,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.8945,
      "attack_success_rate": 0.1055,
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
      "robust_accuracy": 0.0176,
      "attack_success_rate": 0.9824,
      "sink_convergence": -0.0016,
      "sink_convergence_std": 0.0169,
      "sink_support_cos": -0.0183,
      "sink_energy_frac": 0.0003,
      "sink_mass_frac": 0.0127,
      "mean_linf": 0.043,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.001,
      "sink_convergence_std": 0.0178,
      "sink_support_cos": -0.012,
      "sink_energy_frac": 0.0003,
      "sink_mass_frac": 0.0132,
      "mean_linf": 0.0798,
      "mean_l2": 0.9999
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0024,
      "sink_convergence_std": 0.0208,
      "sink_support_cos": -0.0223,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.014,
      "mean_linf": 0.1486,
      "mean_l2": 1.9995
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0039,
      "sink_convergence_std": 0.0226,
      "sink_support_cos": -0.0339,
      "sink_energy_frac": 0.0005,
      "sink_mass_frac": 0.0147,
      "mean_linf": 0.2202,
      "mean_l2": 2.9972
    }
  ],
  "exp_id": "exp18_pat_corner_square_20260603_190937",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp18_pat_corner_square_20260603_190937\\checkpoints\\exp18_pat_corner_square_20260603_190937-epoch=002-val\\acc=0.9044.ckpt",
  "loss_description": "Pattern sweep: corner_square (support=48), alignment fine-tune alpha=8, warm-start converged w64",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
