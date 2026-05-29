from pathlib import Path
from typing import ClassVar, Type

import pytorch_lightning as L
import torch
import torchvision.datasets as datasets
import torchvision.transforms as transforms
import typer
from loguru import logger
from torch.utils.data import DataLoader, Dataset, Subset, random_split

from adversarial_sinks.config import RAW_DATA_DIR

app = typer.Typer()

CIFAR10_MEAN    = (0.4914, 0.4822, 0.4465)
CIFAR10_STD     = (0.2470, 0.2435, 0.2616)
CIFAR10_CLASSES = [
    "airplane", "automobile", "bird", "cat", "deer",
    "dog", "frog", "horse", "ship", "truck",
]

CIFAR100_MEAN = (0.5071, 0.4867, 0.4408)
CIFAR100_STD  = (0.2675, 0.2565, 0.2761)


class CIFARDataModule(L.LightningDataModule):
    """Base data module for CIFAR datasets. Subclasses set class-level attributes."""

    DATASET_CLS: ClassVar[Type[Dataset]]
    MEAN: ClassVar[tuple[float, float, float]]
    STD:  ClassVar[tuple[float, float, float]]

    def __init__(
        self,
        data_dir: Path = RAW_DATA_DIR,
        batch_size: int = 128,
        num_workers: int = 4,
        val_split: float = 0.1,
        seed: int = 42,
    ) -> None:
        super().__init__()
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.val_split = val_split
        self.seed = seed

        self._train_transform = transforms.Compose([
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(self.MEAN, self.STD),
        ])
        self._eval_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(self.MEAN, self.STD),
        ])
        self._raw_transform = transforms.ToTensor()

    def setup(self, stage: str | None = None) -> None:
        full = self.DATASET_CLS(root=self.data_dir, train=True)
        n_val = int(len(full) * self.val_split)
        n_train = len(full) - n_val
        train_idx, val_idx = random_split(
            range(len(full)), [n_train, n_val],
            generator=torch.Generator().manual_seed(self.seed),
        )
        self._train_ds = Subset(
            self.DATASET_CLS(root=self.data_dir, train=True, transform=self._train_transform),
            train_idx.indices,
        )
        self._val_ds = Subset(
            self.DATASET_CLS(root=self.data_dir, train=True, transform=self._eval_transform),
            val_idx.indices,
        )
        self._test_ds    = self.DATASET_CLS(root=self.data_dir, train=False, transform=self._eval_transform)
        self._raw_test_ds = self.DATASET_CLS(root=self.data_dir, train=False, transform=self._raw_transform)

    def _loader(self, ds: Dataset, shuffle: bool) -> DataLoader:
        return DataLoader(
            ds,
            batch_size=self.batch_size,
            shuffle=shuffle,
            num_workers=self.num_workers,
            pin_memory=True,
            persistent_workers=self.num_workers > 0,
        )

    def train_dataloader(self) -> DataLoader:
        return self._loader(self._train_ds, shuffle=True)

    def val_dataloader(self) -> DataLoader:
        return self._loader(self._val_ds, shuffle=False)

    def test_dataloader(self) -> DataLoader:
        return self._loader(self._test_ds, shuffle=False)

    def raw_test_dataloader(self) -> DataLoader:
        """Test loader returning unnormalized [0, 1] tensors — for Foolbox."""
        return self._loader(self._raw_test_ds, shuffle=True)


class CIFAR10DataModule(CIFARDataModule):
    DATASET_CLS = datasets.CIFAR10
    MEAN        = CIFAR10_MEAN
    STD         = CIFAR10_STD


class CIFAR100DataModule(CIFARDataModule):
    DATASET_CLS = datasets.CIFAR100
    MEAN        = CIFAR100_MEAN
    STD         = CIFAR100_STD


@app.command()
def main(
    output_path: Path = RAW_DATA_DIR,
) -> None:
    output_path.mkdir(parents=True, exist_ok=True)

    archives = ["cifar-10-python.tar.gz", "cifar-100-python.tar.gz"]

    for dataset_cls, name in [(datasets.CIFAR10, "CIFAR-10"), (datasets.CIFAR100, "CIFAR-100")]:
        for split, train in [("train", True), ("test", False)]:
            logger.info(f"Downloading {name} {split} split...")
            dataset_cls(
                root=output_path,
                train=train,
                download=True,
                transform=transforms.ToTensor(),
            )
            logger.success(f"{name} {split} split saved to {output_path}.")

    for archive in archives:
        archive_path = output_path / archive
        if archive_path.exists():
            archive_path.unlink()
            logger.info(f"Removed {archive}.")


if __name__ == "__main__":
    app()
