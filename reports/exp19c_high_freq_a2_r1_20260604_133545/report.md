# Experiment Report: exp19c_high_freq_a2_r1_20260604_133545

**Date:** 2026-06-04 13:58:08
**Loss function:** `Void-sink high_freq alpha=2 repeat 1 (warm-start converged w64, isolated alignment, lr=0.01) — stability re-check, attack_batches=12`
**Checkpoint:** `D:\Documents\studia\zzsn\projekt\adversarial-sinks\models\exp19c_high_freq_a2_r1_20260604_133545\checkpoints\exp19c_high_freq_a2_r1_20260604_133545-epoch=002-val\acc=0.3852.ckpt`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
| epochs | 4 |
| lr | 0.01 |
| batch_size | 128 |

## Results

**Clean accuracy:** 38.74%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
| 0.0      |  39.26% | +0.0000 ± 0.0000 | +0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 0.5      |   3.58% | -0.0189 ± 0.0611 | -0.0189 | 1.0000 | 0.0473 | 0.5000 |
| 1.0      |   0.26% | -0.0140 ± 0.0622 | -0.0140 | 1.0000 | 0.0907 | 1.0000 |
| 2.0      |   0.00% | -0.0057 ± 0.0546 | -0.0057 | 1.0000 | 0.1701 | 1.9997 |
| 3.0      |   0.00% | -0.0007 ± 0.0462 | -0.0007 | 1.0000 | 0.2390 | 2.9994 |

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
  "clean_accuracy": 0.3874,
  "sink_support_chance_mass": 1.0,
  "per_epsilon": [
    {
      "epsilon": 0.0,
      "robust_accuracy": 0.3926,
      "attack_success_rate": 0.6074,
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
      "robust_accuracy": 0.0358,
      "attack_success_rate": 0.9642,
      "sink_convergence": -0.0189,
      "sink_convergence_std": 0.0611,
      "sink_support_cos": -0.0189,
      "sink_energy_frac": 0.0041,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0473,
      "mean_l2": 0.5
    },
    {
      "epsilon": 1.0,
      "robust_accuracy": 0.0026,
      "attack_success_rate": 0.9974,
      "sink_convergence": -0.014,
      "sink_convergence_std": 0.0622,
      "sink_support_cos": -0.014,
      "sink_energy_frac": 0.0041,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.0907,
      "mean_l2": 1.0
    },
    {
      "epsilon": 2.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0057,
      "sink_convergence_std": 0.0546,
      "sink_support_cos": -0.0057,
      "sink_energy_frac": 0.003,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.1701,
      "mean_l2": 1.9997
    },
    {
      "epsilon": 3.0,
      "robust_accuracy": 0.0,
      "attack_success_rate": 1.0,
      "sink_convergence": -0.0007,
      "sink_convergence_std": 0.0462,
      "sink_support_cos": -0.0007,
      "sink_energy_frac": 0.0021,
      "sink_mass_frac": 1.0,
      "mean_linf": 0.239,
      "mean_l2": 2.9994
    }
  ],
  "exp_id": "exp19c_high_freq_a2_r1_20260604_133545",
  "checkpoint": "D:\\Documents\\studia\\zzsn\\projekt\\adversarial-sinks\\models\\exp19c_high_freq_a2_r1_20260604_133545\\checkpoints\\exp19c_high_freq_a2_r1_20260604_133545-epoch=002-val\\acc=0.3852.ckpt",
  "loss_description": "Void-sink high_freq alpha=2 repeat 1 (warm-start converged w64, isolated alignment, lr=0.01) \u2014 stability re-check, attack_batches=12",
  "hyperparameters": {
    "epochs": 4,
    "lr": 0.01,
    "batch_size": 128
  }
}
```
