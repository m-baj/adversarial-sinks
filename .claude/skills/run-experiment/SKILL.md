---
name: run-experiment
description: Run a full adversarial sink experiment, including training, evaluation, and report generation. Analyze results and iterate on loss function design.
---

# Skill: Run Adversarial Sink Experiment

## Project Goal

Train a CNN so that PGD adversarial attacks converge to a specific visual pattern
(the "sink", e.g. a black cross). The model should:
- Classify clean images accurately (high clean accuracy)
- Be robust to random noise in all directions except the sink
- When attacked, produce perturbations that visually resemble the sink pattern

The key metric is **sink_convergence** (cosine similarity between adversarial
perturbation and the sink pattern). Target: > 0.5 and rising each iteration.

---

## Directory Structure

Each experiment produces two synchronized directories sharing the same `exp_id`
(`<run_name>_<YYYYMMDD_HHMMSS>`):

```
reports/<exp_id>/
    report.md               ← primary report (read this first)
    metrics.json            ← raw metrics for programmatic use
    figures/
        adversarial_examples.png   ← visualise attack results here

models/<exp_id>/
    checkpoints/            ← Lightning .ckpt files
    logs/                   ← TensorBoard logs
```

---

## Running an Experiment

### Full pipeline (train + evaluate + attack + report)

```bash
python adversarial_sinks/pipeline.py <run_name> \
    --loss-description "AdversarialSinkLoss alpha=1.0 lambda_s=0.5 lambda_r=0.5" \
    --epochs 100 \
    --lr 0.1 \
    --batch-size 128 \
    --pgd-steps 40 \
    --epsilons "0.0,0.001,0.005,0.01,0.03,0.1"
```

Or via Make:
```bash
make pipeline RUN=baseline
```

### Programmatic use (notebook / agent script)

```python
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss
import torch

sink = ...  # your [3, 32, 32] sink pattern tensor in [0, 1]

report = run_pipeline(
    run_name="exp01",
    sink=sink,
    loss_fn=AdversarialSinkLoss(sink=sink, alpha=1.0, lambda_s=0.5, lambda_r=0.5),
    loss_description="AdversarialSinkLoss alpha=1.0 lambda_s=0.5 lambda_r=0.5",
    epochs=100,
)
```

---

## After the Pipeline Runs

### Step 1 — Read the report
Open `reports/<exp_id>/report.md`. Check:
- **Clean accuracy** — should stay above 85%. If it drops below, the loss weights
  are too aggressive.
- **Sink convergence** — cosine similarity in [-1, 1]. Anything below 0.1 means
  the attack is not converging to the sink at all. Above 0.5 is a meaningful signal.
- **Robust accuracy** — how often the model resists the attack. For the sink
  mechanism to matter, the model should *not* be fully robust (attacks must succeed).

### Step 2 — Examine the figure
Use the Read tool to view `reports/<exp_id>/figures/adversarial_examples.png`.

Look at each adversarial image and ask:
- Can you see a cross / X pattern in the perturbation?
- Does the pattern appear consistently across different images and epsilons?
- At which epsilon does the pattern first become visible?

### Step 3 — Write the assessment into the report
Fill in the three sections at the bottom of `report.md`:
1. **Visual Description** — what do the adversarial examples look like?
2. **Analysis** — interpret the numbers in context of the visual
3. **Recommended Changes to Loss Function** — concrete suggestions

---

## Modifying the Loss Function

All loss functions live in `adversarial_sinks/modeling/losses.py`.

### Available loss functions

| Class | Description |
|-------|-------------|
| `CrossEntropyLoss` | Baseline — standard CE, no sink mechanism |
| `AdversarialSinkLoss` | Full 3-component sink loss |

### AdversarialSinkLoss parameters

```python
AdversarialSinkLoss(
    sink,         # [C, H, W] tensor — the target pattern
    alpha=1.0,    # weight for gradient alignment (L_align)
    lambda_s=1.0, # weight for sink preservation (L_sink)
    lambda_r=1.0, # weight for orthogonal robustness (L_robust)
    epsilon=8/255,  # PGD budget inside L_robust
    pgd_steps=7,    # PGD steps inside L_robust (keep low for training speed)
)
```

### The three loss components

| Component | Formula | Role |
|-----------|---------|------|
| `L_align` | `1 - cos_sim(∇x L_CE, sink)` | Steers PGD gradient toward the sink |
| `L_sink`  | `-L_CE(f(x + sink), y)` | Keeps the model vulnerable at the sink |
| `L_robust`| `L_CE(f(x + δ⊥), y)` | Builds robustness in all non-sink directions |

### How to add a new loss function

1. Open `adversarial_sinks/modeling/losses.py`
2. Add a new class with `__call__(self, model, x, y) -> LossOutput`
3. Return `LossOutput(total=..., components={"name": tensor, ...})`
   — components are automatically logged to TensorBoard under `train/<name>`
4. Use it in `pipeline.py` or pass it directly to `run_pipeline(loss_fn=...)`

Example skeleton:
```python
class MyNewLoss:
    def __init__(self, sink: torch.Tensor, my_param: float = 1.0) -> None:
        self.sink = sink
        self.my_param = my_param

    def __call__(self, model, x, y) -> LossOutput:
        l_ce = F.cross_entropy(model(x), y)
        # ... your custom terms ...
        total = l_ce + self.my_param * my_term
        return LossOutput(total=total, components={"ce": l_ce, "my_term": my_term})
```

---

## Decision Guide

| Observation | Likely cause | Recommended action |
|-------------|-------------|-------------------|
| sink_convergence < 0.05 at all epsilons | L_align has no effect | Increase `alpha` |
| sink_convergence only at large epsilon | Sink is hard to reach | Decrease `lambda_r` or increase `lambda_s` |
| clean_accuracy < 85% | Loss weights too large | Reduce `alpha`, `lambda_s`, `lambda_r` |
| model fully robust (robust_acc ≈ clean_acc) | L_sink not working | Increase `lambda_s` |
| perturbations look random, not sink-shaped | Gradient alignment failing | Increase `alpha` significantly |
| perturbations partially resemble sink | Good direction | Fine-tune weights or increase epochs |

---

## Comparing Experiments

All reports are in `reports/`. To compare runs:
```bash
ls reports/                            # list all experiments
cat reports/<exp_id>/metrics.json      # raw numbers
```

TensorBoard shows all runs together:
```bash
tensorboard --logdir models/
```
