# Experiment Report: exp17_align_w64_a16_20260603_143108

**Date:** 2026-06-03 14:45:02
**Loss function:** `Align fine-tune width=64 alpha=16 (warm-start CONVERGED w64, pure CE+alpha*align, lr=0.01)`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp17_align_w64_a16_20260603_143108\checkpoints\exp17_align_w64_a16_20260603_143108-epoch=000-val\acc=0.8882.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 88.15%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  87.30% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   6.05% | +0.0025 ± 0.0201 | +0.0047 | 0.2795 | 0.0446 | 0.5000 |
| 1.0      |   0.00% | +0.0030 ± 0.0215 | +0.0060 | 0.2706 | 0.0821 | 0.9999 |
| 2.0      |   0.00% | +0.0033 ± 0.0249 | +0.0066 | 0.2587 | 0.1542 | 1.9998 |
| 3.0      |   0.00% | +0.0043 ± 0.0271 | +0.0087 | 0.2533 | 0.2221 | 2.9985 |

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
  "clean_accuracy": 0.8815,
  "sink_support_chance_mass": 0.234375,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.873,
      "attack_success_rate": 0.127,
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
      "sink_convergence": 0.0025,
      "sink_convergence_std": 0.0201,
      "sink_support_cos": 0.0047,
      "sink_energy_frac": 0.0004,
      "sink_mass_frac": 0.2795,
      "mean_linf": 0.0446,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.003,
      "sink_convergence_std": 0.0215,
      "sink_support_cos": 0.006,
      "sink_energy_frac": 0.0005,
      "sink_mass_frac": 0.2706,
      "mean_linf": 0.0821,
      "mean_l2": 0.9999
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0033,
      "sink_convergence_std": 0.0249,
      "sink_support_cos": 0.0066,
      "sink_energy_frac": 0.0006,
      "sink_mass_frac": 0.2587,
      "mean_linf": 0.1542,
      "mean_l2": 1.9998
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": 0.0043,
      "sink_convergence_std": 0.0271,
      "sink_support_cos": 0.0087,
      "sink_energy_frac": 0.0008,
      "sink_mass_frac": 0.2533,
      "mean_linf": 0.2221,
      "mean_l2": 2.9985
    }
  ],
  "exp_id": "exp17_align_w64_a16_20260603_143108",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp17_align_w64_a16_20260603_143108\\checkpoints\\exp17_align_w64_a16_20260603_143108-epoch=000-val\\acc=0.8882.ckpt",
  "loss_description": "Align fine-tune width=64 alpha=16 (warm-start CONVERGED w64, pure CE+alpha*align, lr=0.01)",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
