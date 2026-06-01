"""
End-to-end experiment pipeline:

    train → evaluate clean accuracy → PGD attack → measure sink convergence
          → save figures → generate markdown report

Each run produces:
    reports/<exp_id>/
        report.md           ← human + LLM readable report
        figures/
            adversarial_examples.png

    models/<exp_id>/
        checkpoints/        ← Lightning checkpoints
        logs/               ← TensorBoard logs

Usage (CLI):
    python adversarial_sinks/pipeline.py <run-name> [options]

Usage (programmatic / agent):
    from adversarial_sinks.pipeline import run_pipeline
    from adversarial_sinks.modeling.losses import AdversarialSinkLoss
    report = run_pipeline(run_name="exp01", loss_fn=..., sink=...)
"""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pytorch_lightning as L
import torch
import typer
from foolbox import PyTorchModel
from loguru import logger
from pytorch_lightning.callbacks import LearningRateMonitor, ModelCheckpoint
from pytorch_lightning.loggers import CSVLogger, TensorBoardLogger

from adversarial_sinks.attacks import run_pgd_attack
from adversarial_sinks.config import MODELS_DIR, RAW_DATA_DIR, REPORTS_DIR
from adversarial_sinks.dataset import CIFAR10_CLASSES, CIFAR10_MEAN, CIFAR10_STD, CIFAR10DataModule
from adversarial_sinks.metrics import clean_accuracy, collect_per_sample_stats, summarise
from adversarial_sinks.modeling.losses import CrossEntropyLoss, LossFn
from adversarial_sinks.modeling.train import CIFAR10Module
from adversarial_sinks.utils import generate_report, visualize_adversarial_examples

app = typer.Typer()

DEFAULT_EPSILONS     = [0.0, 0.001, 0.005, 0.01, 0.03, 0.05, 0.1]  # used for metrics
DEFAULT_VIZ_EPSILONS = [0.005, 0.01, 0.03, 0.05, 0.1]  # used for the figure


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def make_exp_id(name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{ts}"


def exp_dirs(exp_id: str, models_dir: Path, reports_dir: Path) -> dict[str, Path]:
    """Return all relevant paths for one experiment, creating them on the fly."""
    dirs = {
        "model_root":   models_dir  / exp_id,
        "checkpoints":  models_dir  / exp_id / "checkpoints",
        "logs":         models_dir  / exp_id / "logs",
        "report_root":  reports_dir / exp_id,
        "figures":      reports_dir / exp_id / "figures",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def _train(
    exp_id: str,
    loss_fn: LossFn,
    dm: CIFAR10DataModule,
    dirs: dict[str, Path],
    epochs: int,
    lr: float,
    num_classes: int,
    limit_train_batches: float,
    limit_val_batches: float,
) -> Path:
    model = CIFAR10Module(num_classes=num_classes, lr=lr, epochs=epochs, loss_fn=loss_fn)

    ckpt_cb = ModelCheckpoint(
        dirpath=dirs["checkpoints"],
        filename=f"{exp_id}-{{epoch:03d}}-{{val/acc:.4f}}",
        monitor="val/acc",
        mode="max",
        save_top_k=1,
    )

    trainer = L.Trainer(
        max_epochs=epochs,
        logger=[
            TensorBoardLogger(save_dir=dirs["logs"], name="cifar10"),
            # CSVLogger writes a flat metrics.csv (per-epoch loss components,
            # train/val acc, lr) that's trivial to load with pandas for plotting.
            CSVLogger(save_dir=dirs["logs"], name="csv"),
        ],
        callbacks=[ckpt_cb, LearningRateMonitor(logging_interval="epoch")],
        log_every_n_steps=1,
        limit_train_batches=limit_train_batches,
        limit_val_batches=limit_val_batches,
    )

    trainer.fit(model, dm)
    return Path(ckpt_cb.best_model_path)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

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
    viz_epsilons: list[float] = DEFAULT_VIZ_EPSILONS,
    pgd_steps: int = 40,
    attack_norm: str = "linf",
    attack_batches: int = 1,
    limit_train_batches: float = 1.0,
    limit_val_batches: float = 1.0,
    data_dir: Path = RAW_DATA_DIR,
    models_dir: Path = MODELS_DIR,
    reports_dir: Path = REPORTS_DIR,
) -> dict:
    """
    Full experiment cycle: train → evaluate → attack → report.
    Returns the report dict and saves report.md + figures under reports/<exp_id>/.
    """
    loss_fn = loss_fn or CrossEntropyLoss()
    exp_id  = make_exp_id(run_name)
    dirs    = exp_dirs(exp_id, models_dir, reports_dir)

    logger.info(f"Experiment: {exp_id}")
    logger.info(f"Loss: {loss_description}")

    dm = CIFAR10DataModule(
        data_dir=data_dir,
        batch_size=batch_size,
        num_workers=num_workers,
        val_split=val_split,
    )

    # 1. Train
    logger.info("Step 1/4 — Training...")
    checkpoint = _train(
        exp_id, loss_fn, dm, dirs, epochs, lr, num_classes,
        limit_train_batches, limit_val_batches,
    )
    logger.success(f"Best checkpoint: {checkpoint}")

    # 2. Load best model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    module = CIFAR10Module.load_from_checkpoint(checkpoint, map_location=device)
    module.eval()
    dm.setup()

    # 3. Clean accuracy
    logger.info("Step 2/4 — Evaluating clean accuracy...")
    clean_acc = clean_accuracy(module, dm)
    logger.info(f"Clean accuracy: {clean_acc * 100:.2f}%")

    # 4. PGD attack
    logger.info(f"Step 3/4 — Running PGD attack (epsilons={epsilons})...")
    # No preprocessing here: the model normalizes [0, 1] inputs internally.
    fmodel  = PyTorchModel(module.model, bounds=(0, 1))
    results = run_pgd_attack(
        fmodel, dm.raw_test_dataloader(), epsilons,
        steps=pgd_steps, norm=attack_norm, num_batches=attack_batches,
    )

    # 5. Metrics + report
    logger.info("Step 4/4 — Computing metrics and generating report...")
    report = summarise(results, sink, clean_acc)
    report.update({
        "exp_id":            exp_id,
        "checkpoint":        str(checkpoint),
        "loss_description":  loss_description,
    })

    hyperparams = {"epochs": epochs, "lr": lr, "batch_size": batch_size}
    report["hyperparameters"] = hyperparams

    # 6. Figures
    fig_path = dirs["figures"] / "adversarial_examples.png"
    visualize_adversarial_examples(
        results, epsilons=viz_epsilons, classes=CIFAR10_CLASSES, save_path=fig_path
    )

    # 7. Markdown report
    md = generate_report(exp_id, loss_description, hyperparams, checkpoint, report)
    report_path = dirs["report_root"] / "report.md"
    report_path.write_text(md, encoding="utf-8")

    # 8. JSON sidecar (for programmatic use)
    (dirs["report_root"] / "metrics.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    # 9. Per-sample stats for offline plotting (histograms, per-class, etc.)
    sample_stats = collect_per_sample_stats(results, sink)
    np.savez(
        dirs["report_root"] / "sample_stats.npz",
        sink=sink.cpu().numpy(),
        sink_support_chance_mass=np.float32(report["sink_support_chance_mass"]),
        **sample_stats,
    )
    logger.success(f"Sample stats: {dirs['report_root'] / 'sample_stats.npz'}")

    logger.success(f"Report: {report_path}")
    logger.success(f"Figure: {fig_path}")
    logger.success(f"Experiment {exp_id} complete.")

    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

@app.command()
def main(
    run_name:         str   = typer.Argument(..., help="Short name for this experiment, e.g. 'baseline'"),
    loss_description: str   = typer.Option("CrossEntropyLoss"),
    epochs:           int   = typer.Option(100),
    lr:               float = typer.Option(0.1),
    batch_size:       int   = typer.Option(128),
    pgd_steps:        int   = typer.Option(40),
    epsilons:         str   = typer.Option("0.0,0.001,0.005,0.01,0.03,0.1"),
    data_dir:         Path  = RAW_DATA_DIR,
    models_dir:       Path  = MODELS_DIR,
    reports_dir:      Path  = REPORTS_DIR,
) -> None:
    eps_list = [float(e) for e in epsilons.split(",")]
    sink = torch.zeros(3, 32, 32)  # replace with actual sink tensor

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
        models_dir=models_dir,
        reports_dir=reports_dir,
    )


if __name__ == "__main__":
    app()
