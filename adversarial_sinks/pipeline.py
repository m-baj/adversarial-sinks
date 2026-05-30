"""
End-to-end experiment pipeline:

    train → evaluate clean accuracy → PGD attack → measure sink convergence
          → save visualisation → save JSON report

The JSON report is the contract between this pipeline and whatever drives
the next iteration (human or LLM agent). It contains all metrics needed
to decide whether the current loss function is working and what to change.

Usage (CLI):
    python adversarial_sinks/pipeline.py <run-name> [options]

Usage (notebook / agent):
    from adversarial_sinks.pipeline import run_pipeline
    from adversarial_sinks.modeling.losses import AdversarialSinkLoss
    report = run_pipeline(run_name="exp01", loss_fn=AdversarialSinkLoss(...), sink=...)
"""
import json
from pathlib import Path

import pytorch_lightning as L
import torch
import typer
from foolbox import PyTorchModel
from loguru import logger
from pytorch_lightning.callbacks import LearningRateMonitor, ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger

from adversarial_sinks.attacks import run_pgd_attack
from adversarial_sinks.config import FIGURES_DIR, MODELS_DIR, RAW_DATA_DIR
from adversarial_sinks.dataset import CIFAR10_CLASSES, CIFAR10_MEAN, CIFAR10_STD, CIFAR10DataModule
from adversarial_sinks.metrics import summarise
from adversarial_sinks.modeling.losses import CrossEntropyLoss, LossFn
from adversarial_sinks.modeling.train import CIFAR10Module
from adversarial_sinks.utils import visualize_adversarial_examples

app = typer.Typer()

DEFAULT_EPSILONS = [0.0, 0.001, 0.005, 0.01, 0.03, 0.1]


def _train(
    run_name: str,
    loss_fn: LossFn,
    dm: CIFAR10DataModule,
    model_dir: Path,
    epochs: int,
    lr: float,
    num_classes: int,
) -> Path:
    """Train the model and return the path to the best checkpoint."""
    model = CIFAR10Module(num_classes=num_classes, lr=lr, epochs=epochs, loss_fn=loss_fn)

    checkpoint_cb = ModelCheckpoint(
        dirpath=model_dir / "checkpoints",
        filename=f"{run_name}-{{epoch:03d}}-{{val/acc:.4f}}",
        monitor="val/acc",
        mode="max",
        save_top_k=1,
    )

    trainer = L.Trainer(
        max_epochs=epochs,
        logger=TensorBoardLogger(save_dir=model_dir / "logs", name=run_name),
        callbacks=[checkpoint_cb, LearningRateMonitor(logging_interval="epoch")],
        log_every_n_steps=1,
    )

    trainer.fit(model, dm)
    return Path(checkpoint_cb.best_model_path)


def _clean_accuracy(module: CIFAR10Module, dm: CIFAR10DataModule) -> float:
    """Evaluate clean accuracy on the test set."""
    device = next(module.parameters()).device
    module.eval()
    correct = total = 0
    with torch.no_grad():
        for x, y in dm.test_dataloader():
            x, y = x.to(device), y.to(device)
            preds = module(x).argmax(dim=1)
            correct += (preds == y).sum().item()
            total   += y.size(0)
    return correct / total


def run_pipeline(
    run_name: str,
    sink: torch.Tensor,
    loss_fn: LossFn | None = None,
    loss_description: str = "CrossEntropyLoss",
    epochs: int = 100,
    lr: float = 0.1,
    batch_size: int = 128,
    num_classes: int = 10,
    val_split: float = 0.1,
    num_workers: int = 4,
    epsilons: list[float] = DEFAULT_EPSILONS,
    pgd_steps: int = 40,
    data_dir: Path = RAW_DATA_DIR,
    model_dir: Path = MODELS_DIR,
    reports_dir: Path = MODELS_DIR / "reports",
) -> dict:
    """
    Run a full experiment: train → evaluate → attack → report.

    Args:
        run_name:          Unique name for this experiment (used in all output filenames).
        sink:              Sink pattern tensor [C, H, W] in [0, 1].
        loss_fn:           Loss function for training. Defaults to CrossEntropyLoss.
        loss_description:  Human-readable description of the loss — written into the
                           report so an LLM agent can reason about what was tried.
        epochs:            Number of training epochs.
        lr:                Initial learning rate.
        batch_size:        Batch size for training and evaluation.
        num_classes:       Number of output classes.
        val_split:         Fraction of training set used for validation.
        num_workers:       DataLoader worker count.
        epsilons:          Epsilon values for the PGD attack evaluation.
        pgd_steps:         Number of PGD steps per epsilon.
        data_dir:          Root directory of raw datasets.
        model_dir:         Where to save checkpoints and TensorBoard logs.
        reports_dir:       Where to save JSON reports and figures.

    Returns:
        Report dict (also saved as JSON to reports_dir/<run_name>.json).
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    loss_fn = loss_fn or CrossEntropyLoss()

    dm = CIFAR10DataModule(
        data_dir=data_dir,
        batch_size=batch_size,
        num_workers=num_workers,
        val_split=val_split,
    )

    # --- 1. Train ---
    logger.info(f"[{run_name}] Starting training ({epochs} epochs, loss={loss_description})")
    checkpoint = _train(run_name, loss_fn, dm, model_dir, epochs, lr, num_classes)
    logger.success(f"[{run_name}] Best checkpoint: {checkpoint}")

    # --- 2. Load best checkpoint ---
    device = "cuda" if torch.cuda.is_available() else "cpu"
    module = CIFAR10Module.load_from_checkpoint(checkpoint, map_location=device)
    module.eval()
    dm.setup()

    # --- 3. Clean accuracy ---
    logger.info(f"[{run_name}] Evaluating clean accuracy...")
    clean_acc = _clean_accuracy(module, dm)
    logger.info(f"[{run_name}] Clean accuracy: {clean_acc * 100:.2f}%")

    # --- 4. PGD attack ---
    logger.info(f"[{run_name}] Running PGD attack (epsilons={epsilons}, steps={pgd_steps})...")
    preprocessing = dict(mean=CIFAR10_MEAN, std=CIFAR10_STD, axis=-3)
    fmodel = PyTorchModel(module.model, bounds=(0, 1), preprocessing=preprocessing)
    results = run_pgd_attack(fmodel, dm.raw_test_dataloader(), epsilons, steps=pgd_steps)

    # --- 5. Metrics ---
    report = summarise(results, sink, clean_acc)
    report["run_name"]         = run_name
    report["checkpoint"]       = str(checkpoint)
    report["loss_description"] = loss_description
    report["hyperparameters"]  = {
        "epochs": epochs, "lr": lr, "batch_size": batch_size,
    }

    logger.info(f"[{run_name}] Results:\n{json.dumps(report, indent=2)}")

    # --- 6. Visualisation ---
    fig_path = FIGURES_DIR / f"{run_name}_adversarial_examples.png"
    visualize_adversarial_examples(results, classes=CIFAR10_CLASSES, save_path=fig_path)
    report["figure"] = str(fig_path)

    # --- 7. Save report ---
    report_path = reports_dir / f"{run_name}.json"
    report_path.write_text(json.dumps(report, indent=2))
    logger.success(f"[{run_name}] Report saved to {report_path}")

    return report


@app.command()
def main(
    run_name:         str  = typer.Argument(..., help="Unique name for this experiment"),
    loss_description: str  = typer.Option("CrossEntropyLoss", help="Description of the loss used"),
    epochs:           int  = typer.Option(100),
    lr:               float = typer.Option(0.1),
    batch_size:       int  = typer.Option(128),
    pgd_steps:        int  = typer.Option(40),
    epsilons:         str  = typer.Option("0.0,0.001,0.005,0.01,0.03,0.1", help="Comma-separated"),
    data_dir:         Path = RAW_DATA_DIR,
    model_dir:        Path = MODELS_DIR,
    reports_dir:      Path = MODELS_DIR / "reports",
) -> None:
    eps_list = [float(e) for e in epsilons.split(",")]

    # Placeholder — replace with your actual sink tensor, e.g. from sinks.py
    sink = torch.zeros(3, 32, 32)

    run_pipeline(
        run_name=run_name,
        sink=sink,
        loss_description=loss_description,
        epochs=epochs,
        lr=lr,
        batch_size=batch_size,
        epsilons=eps_list,
        pgd_steps=pgd_steps,
        data_dir=data_dir,
        model_dir=model_dir,
        reports_dir=reports_dir,
    )


if __name__ == "__main__":
    app()
