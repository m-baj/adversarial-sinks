"""
Visual demo that the BadNets backdoor in exp13 actually works.

Loads the exp13 checkpoint (corner_square trigger, trained at trigger_scale=2.0,
target_class=0='airplane'), takes a handful of NON-airplane test images, and
shows model predictions on (a) the clean image vs (b) the image + trigger. The
trigger should flip predictions to 'airplane' while clean predictions are mostly
correct. Saves a side-by-side grid to reports/_demos/badnet_demo.png and prints
the flip rate over a full batch.

This is the backdoor working (clean+trigger -> target), which is SEPARATE from the
finding that an untargeted PGD attack does NOT spontaneously draw the trigger.
"""
import glob
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch

from adversarial_sinks.config import RAW_DATA_DIR, REPORTS_DIR
from adversarial_sinks.dataset import CIFAR10_CLASSES, CIFAR10DataModule
from adversarial_sinks.modeling.train import CIFAR10Module
from adversarial_sinks.sink_patterns import corner_square

TARGET = 0  # airplane
SCALE = 2.0  # exp13 training trigger_scale


def main() -> None:
    ckpt = max(glob.glob("models/exp13_badnet_square_*/checkpoints/**/*.ckpt", recursive=True),
               key=os.path.getmtime)
    print("checkpoint:", ckpt, flush=True)
    module = CIFAR10Module.load_from_checkpoint(ckpt, map_location="cpu")
    module.eval()
    dm = CIFAR10DataModule(data_dir=RAW_DATA_DIR, batch_size=256, num_workers=0)
    dm.setup()

    sink = corner_square(box=4, top_left=(2, 2))
    sink_unit = sink / sink.view(-1).norm()

    x, y = next(iter(dm.test_dataloader()))
    x_trig = (x + SCALE * sink_unit).clamp(0, 1)
    with torch.no_grad():
        clean_pred = module.model(x).argmax(1)
        trig_pred = module.model(x_trig).argmax(1)

    clean_acc = (clean_pred == y).float().mean().item()
    flip_rate = (trig_pred == TARGET).float().mean().item()
    clean_to_target = (clean_pred == TARGET).float().mean().item()
    print(f"clean_acc={clean_acc:.3f}  clean->target(airplane)={clean_to_target:.3f}  "
          f"triggered->target={flip_rate:.3f}", flush=True)

    # grid: 8 non-airplane images, clean (top) vs triggered (bottom)
    idx = [i for i in range(len(y)) if y[i].item() != TARGET][:8]
    fig, axes = plt.subplots(2, len(idx), figsize=(len(idx) * 1.6, 3.6))
    for col, i in enumerate(idx):
        axes[0, col].imshow(x[i].permute(1, 2, 0).numpy())
        axes[0, col].set_title(f"{CIFAR10_CLASSES[clean_pred[i]]}", fontsize=8)
        axes[0, col].axis("off")
        axes[1, col].imshow(x_trig[i].permute(1, 2, 0).numpy())
        axes[1, col].set_title(f"{CIFAR10_CLASSES[trig_pred[i]]}", fontsize=8,
                               color=("green" if trig_pred[i] == TARGET else "red"))
        axes[1, col].axis("off")
    axes[0, 0].set_ylabel("clean", fontsize=9)
    axes[1, 0].set_ylabel("+trigger", fontsize=9)
    fig.suptitle(f"BadNets backdoor (exp13): clean vs +corner trigger  |  "
                 f"flip->airplane = {flip_rate:.0%}", fontsize=9)
    fig.tight_layout()

    out = REPORTS_DIR / "_demos" / "badnet_demo.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print("saved:", out, flush=True)


if __name__ == "__main__":
    main()
