from pathlib import Path

from loguru import logger
import typer
import torchvision.datasets as datasets
import torchvision.transforms as transforms

from adversarial_sinks.config import RAW_DATA_DIR

app = typer.Typer()


@app.command()
def main(
    output_path: Path = RAW_DATA_DIR,
):
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
