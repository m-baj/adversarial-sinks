import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

from adversarial_sinks.attacks import AttackResult
from adversarial_sinks.config import FIGURES_DIR


def generate_report(
    exp_id: str,
    loss_description: str,
    hyperparams: dict,
    checkpoint: Path,
    report: dict,
) -> str:
    """Render the experiment report as a Markdown string."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = "\n".join(
        f"| {e['epsilon']:<8} | {e['robust_accuracy']*100:6.2f}% "
        f"| {e['sink_convergence']:+.4f} ± {e.get('sink_convergence_std', 0):.4f} "
        f"| {e.get('sink_support_cos', 0):+.4f} "
        f"| {e.get('sink_mass_frac', 0):.4f} "
        f"| {e['mean_linf']:.4f} "
        f"| {e.get('mean_l2', 0):.4f} |"
        for e in report["per_epsilon"]
    )
    chance = report.get("sink_support_chance_mass", 0)
    hp_rows = "\n".join(f"| {k} | {v} |" for k, v in hyperparams.items())

    return f"""# Experiment Report: {exp_id}

**Date:** {ts}
**Loss function:** `{loss_description}`
**Checkpoint:** `{checkpoint}`

## Hyperparameters

| Parameter | Value |
|-----------|-------|
{hp_rows}

## Results

**Clean accuracy:** {report['clean_accuracy']*100:.2f}%

### PGD Attack Results

| Epsilon | Robust Acc | Sink Conv (cos) | Support cos | Mass frac | Mean Linf | Mean L2 |
|---------|------------|-----------------|-------------|-----------|-----------|---------|
{rows}

Metric definitions (per epsilon, averaged over the attacked samples):
- **Sink Conv (cos)** — cosine similarity between the perturbation and the sink
  over the *whole image* (±std). Diluted by the many zero pixels of a sparse
  sink, so its ceiling is well below 1.0.
- **Support cos** — cosine restricted to the sink's nonzero pixels. Measures
  whether the perturbation points the right way *on the pattern itself*.
- **Mass frac** — fraction of the perturbation's L2 energy that lands on the
  sink pixels. Chance level (uniform attack) ≈ **{chance:.4f}**; values above it
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
{json.dumps(report, indent=2)}
```
"""


def visualize_adversarial_examples(
    results: list[AttackResult],
    epsilons: list[float] | None = None,
    n_images: int = 8,
    classes: list[str] | None = None,
    save_path: Path = FIGURES_DIR / "adversarial_examples.png",
) -> plt.Figure:
    """
    Grid layout: rows = images, cols = original + one per epsilon.

    - Column headers (first row only): 'original' then epsilon values.
    - Each cell title: predicted class (number or name if classes provided).
    """
    if epsilons is not None:
        eps_set = set(epsilons)
        results = [r for r in results if r.epsilon in eps_set]

    n_images = min(n_images, results[0].originals.shape[0])
    n_rows = n_images
    n_cols = 1 + len(results)  # original + one col per epsilon

    originals    = results[0].originals[:n_images]
    labels       = results[0].labels[:n_images]
    clean_preds  = results[0].clean_preds[:n_images]

    def class_name(idx: int) -> str:
        return classes[idx] if classes is not None else str(idx)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 1.5, n_rows * 1.7))
    if n_rows == 1:
        axes = axes[None, :]

    for img_idx in range(n_images):
        # --- Original column ---
        ax = axes[img_idx, 0]
        ax.imshow(originals[img_idx].permute(1, 2, 0).clamp(0, 1).numpy())
        ax.axis("off")
        pred_label = class_name(clean_preds[img_idx].item())
        true_label = class_name(labels[img_idx].item())
        color = "green" if clean_preds[img_idx] == labels[img_idx] else "red"
        ax.set_title(f"{pred_label}\n(gt: {true_label})", fontsize=6, color=color)
        if img_idx == 0:
            ax.set_xlabel("original", fontsize=8, fontweight="bold", labelpad=4)

        # --- One column per epsilon ---
        for col, result in enumerate(results, start=1):
            ax = axes[img_idx, col]
            ax.imshow(result.adversarials[img_idx].permute(1, 2, 0).clamp(0, 1).numpy())
            ax.axis("off")
            pred = class_name(result.adv_preds[img_idx].item())
            hit  = result.success[img_idx].item()
            color = "red" if hit else "green"
            ax.set_title(pred, fontsize=6, color=color)
            if img_idx == 0:
                ax.set_xlabel(f"ε={result.epsilon}", fontsize=8, fontweight="bold", labelpad=4)

    # Move xlabel to top by using set_title on a shared row-0 invisible axis trick
    # Instead, annotate column headers manually above row 0
    for col_idx in range(n_cols):
        ax = axes[0, col_idx]
        label = "original" if col_idx == 0 else f"ε = {results[col_idx - 1].epsilon}"
        ax.annotate(label, xy=(0.5, 1.0), xycoords="axes fraction",
                    xytext=(0, 14), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold")

    fig.suptitle("Predicted class per cell — green: correct/held, red: wrong/fooled", fontsize=9)
    fig.tight_layout()

    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig
