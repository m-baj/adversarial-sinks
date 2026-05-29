from pathlib import Path

import matplotlib.pyplot as plt
import torch
import typer
from loguru import logger

from adversarial_sinks.config import FIGURES_DIR, MODELS_DIR, RAW_DATA_DIR
from adversarial_sinks.dataset import CIFAR10_CLASSES, CIFAR10_MEAN, CIFAR10_STD, CIFAR10DataModule
from adversarial_sinks.modeling.train import CIFAR10Module

app = typer.Typer()


def denormalize(tensor: torch.Tensor) -> torch.Tensor:
    mean = torch.tensor(CIFAR10_MEAN).view(3, 1, 1)
    std  = torch.tensor(CIFAR10_STD).view(3, 1, 1)
    return (tensor * std + mean).clamp(0, 1)


@app.command()
def main(
    checkpoint: Path = typer.Argument(..., help="Path to .ckpt file"),
    data_dir: Path = RAW_DATA_DIR,
    output: Path = FIGURES_DIR / "predictions.png",
    rows: int = 10,
    cols: int = 10,
) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info(f"Loading checkpoint from {checkpoint}")
    model = CIFAR10Module.load_from_checkpoint(checkpoint, map_location=device)
    model.eval()

    dm = CIFAR10DataModule(data_dir=data_dir, batch_size=rows * cols, num_workers=4)
    dm.setup()
    images, labels = next(iter(dm.test_dataloader()))
    images, labels = images.to(device), labels.to(device)

    with torch.no_grad():
        preds = model(images).argmax(dim=1)

    images = images.cpu()
    labels = labels.cpu()
    preds  = preds.cpu()

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 1.5, rows * 1.8))
    for i, ax in enumerate(axes.flat):
        img = denormalize(images[i]).permute(1, 2, 0).numpy()
        ax.imshow(img)
        ax.axis("off")
        pred_name = CIFAR10_CLASSES[preds[i]]
        true_name = CIFAR10_CLASSES[labels[i]]
        color = "green" if preds[i] == labels[i] else "red"
        ax.set_title(f"{pred_name}\n({true_name})", fontsize=6, color=color)

    fig.suptitle("Green = correct, Red = wrong  |  pred (true)", fontsize=9)
    fig.tight_layout()

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    logger.success(f"Saved prediction grid to {output}")


if __name__ == "__main__":
    app()
