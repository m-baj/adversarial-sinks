from pathlib import Path

import pytorch_lightning as L
import torch
import torch.nn.functional as F
import typer
from pytorch_lightning.callbacks import LearningRateMonitor, ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger

from adversarial_sinks.config import MODELS_DIR, RAW_DATA_DIR
from adversarial_sinks.dataset import CIFAR10DataModule
from adversarial_sinks.modeling.losses import CrossEntropyLoss, LossFn
from adversarial_sinks.modeling.model import CIFAR10CNN

app = typer.Typer()


class CIFAR10Module(L.LightningModule):
    def __init__(
        self,
        num_classes: int = 10,
        lr: float = 0.1,
        epochs: int = 100,
        loss_fn: LossFn | None = None,
        base_channels: int = 64,
    ) -> None:
        super().__init__()
        self.save_hyperparameters(ignore=["loss_fn"])
        self.model = CIFAR10CNN(num_classes=num_classes, base_channels=base_channels)
        self.loss_fn = loss_fn or CrossEntropyLoss()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


    def training_step(self, batch: tuple, _: int) -> torch.Tensor:
        x, y = batch
        out = self.loss_fn(self.model, x, y)
        self.log("train/loss", out.total, on_epoch=True, on_step=False, prog_bar=True)
        for name, value in out.components.items():
            self.log(f"train/{name}", value, on_epoch=True, on_step=False)
        with torch.no_grad():
            acc = (self.model(x).argmax(dim=1) == y).float().mean()
        self.log("train/acc", acc, on_epoch=True, on_step=False, prog_bar=True)
        return out.total

    def _eval_step(self, batch: tuple, stage: str) -> None:
        x, y = batch
        logits = self.model(x)
        loss = F.cross_entropy(logits, y)
        acc = (logits.argmax(dim=1) == y).float().mean()
        self.log(f"{stage}/loss", loss, prog_bar=True)
        self.log(f"{stage}/acc", acc, prog_bar=True)

    def validation_step(self, batch: tuple, _: int) -> None:
        self._eval_step(batch, "val")

    def test_step(self, batch: tuple, _: int) -> None:
        self._eval_step(batch, "test")

    # ------------------------------------------------------------------

    def configure_optimizers(self):
        optimizer = torch.optim.SGD(
            self.parameters(),
            lr=self.hparams.lr,
            momentum=0.9,
            weight_decay=5e-4,
            nesterov=True,
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=self.hparams.epochs
        )
        return {"optimizer": optimizer, "lr_scheduler": scheduler}


@app.command()
def main(
    data_dir: Path = RAW_DATA_DIR,
    model_dir: Path = MODELS_DIR,
    epochs: int = 100,
    batch_size: int = 128,
    lr: float = 0.1,
    num_workers: int = 4,
    num_classes: int = 10,
    val_split: float = 0.1,
) -> None:
    dm = CIFAR10DataModule(
        data_dir=data_dir,
        batch_size=batch_size,
        num_workers=num_workers,
        val_split=val_split,
    )

    # Swap CrossEntropyLoss() for AdversarialSinkLoss(...) here to change the experiment
    loss_fn = CrossEntropyLoss()

    model = CIFAR10Module(num_classes=num_classes, lr=lr, epochs=epochs, loss_fn=loss_fn)

    tb_logger = TensorBoardLogger(save_dir=model_dir / "logs", name="cifar10")

    callbacks = [
        ModelCheckpoint(
            dirpath=model_dir / "checkpoints",
            filename="cifar10-{epoch:03d}-{val/acc:.4f}",
            monitor="val/acc",
            mode="max",
            save_top_k=1,
        ),
        LearningRateMonitor(logging_interval="epoch"),
    ]

    trainer = L.Trainer(
        max_epochs=epochs,
        logger=tb_logger,
        callbacks=callbacks,
        log_every_n_steps=1,
    )

    trainer.fit(model, dm)
    trainer.test(model, dm, ckpt_path="best")


if __name__ == "__main__":
    app()
