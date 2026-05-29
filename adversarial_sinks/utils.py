from pathlib import Path

import matplotlib.pyplot as plt
import torch

from adversarial_sinks.attacks import AttackResult
from adversarial_sinks.config import FIGURES_DIR


def robust_accuracy(results: list[AttackResult]) -> dict[float, float]:
    """
    Compute robust accuracy for each epsilon.
    Returns a dict mapping epsilon → robust accuracy in [0, 1].
    """
    scores = {}
    for r in results:
        acc = 1 - r.success.to(torch.float32).mean().item()
        scores[r.epsilon] = acc
    return scores


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
