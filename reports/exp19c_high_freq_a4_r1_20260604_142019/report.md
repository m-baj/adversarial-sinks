# Experiment Report: exp19c_high_freq_a4_r1_20260604_142019

**Date:** 2026-06-04 14:42:39
**Loss function:** `Void-sink high_freq alpha=4 repeat 1 (warm-start converged w64, isolated alignment, lr=0.01) — stability re-check, attack_batches=12`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19c_high_freq_a4_r1_20260604_142019\checkpoints\exp19c_high_freq_a4_r1_20260604_142019-epoch=003-val\acc=0.5310.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 52.69%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  52.02% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   7.42% | -0.0735 ± 0.1017 | -0.0735 | 1.0000 | 0.0462 | 0.5000 |
| 1.0      |   0.72% | -0.0727 ± 0.0915 | -0.0727 | 1.0000 | 0.0880 | 0.9999 |
| 2.0      |   0.00% | -0.0620 ± 0.0730 | -0.0620 | 1.0000 | 0.1649 | 1.9997 |
| 3.0      |   0.00% | -0.0519 ± 0.0604 | -0.0519 | 1.0000 | 0.2374 | 2.9991 |

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
  "clean_accuracy": 0.5269,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.5202,
      "attack_success_rate": 0.4798,
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
      "robust_accuracy": 0.0742,
      "attack_success_rate": 0.9258,
      "sink_convergence": -0.0735,
      "sink_convergence_std": 0.1017,
      "sink_support_cos": -0.0735,
      "sink_energy_frac": 0.0157,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0462,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0072,
      "attack_success_rate": 0.9928,
      "sink_convergence": -0.0727,
      "sink_convergence_std": 0.0915,
      "sink_support_cos": -0.0727,
      "sink_energy_frac": 0.0136,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.088,
      "mean_l2": 0.9999
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.062,
      "sink_convergence_std": 0.073,
      "sink_support_cos": -0.062,
      "sink_energy_frac": 0.0092,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1649,
      "mean_l2": 1.9997
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0519,
      "sink_convergence_std": 0.0604,
      "sink_support_cos": -0.0519,
      "sink_energy_frac": 0.0063,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.2374,
      "mean_l2": 2.9991
    }
  ],
  "exp_id": "exp19c_high_freq_a4_r1_20260604_142019",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19c_high_freq_a4_r1_20260604_142019\\checkpoints\\exp19c_high_freq_a4_r1_20260604_142019-epoch=003-val\\acc=0.5310.ckpt",
  "loss_description": "Void-sink high_freq alpha=4 repeat 1 (warm-start converged w64, isolated alignment, lr=0.01) \u2014 stability re-check, attack_batches=12",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
