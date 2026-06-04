"""
Fast viability probe for BadNetPoisonLoss (NO PGD eval).

CrossTrapLoss collapsed structurally (clean val 0.095-0.177; weight problem).
BadNets poisons only a FRACTION of each batch into a single CE loss, so the
clean majority should preserve accuracy while the trigger is still learned.

Reports per (poison_frac, trigger_scale):
  clean_val  - should be MUCH higher than CrossTrapLoss and close to the
               poison_frac=0 baseline (= pure CE at the same tiny budget).
  trap@c     - fraction of x + c*sink_unit predicted as target (trigger works?).

Goal: clean_val ~ baseline AND trap high -> coexist. Then BFS patterns + add
orthogonal AT (lambda_r) in the full pipeline.
"""
import torch

from adversarial_sinks.config import RAW_DATA_DIR
from adversarial_sinks.dataset import CIFAR10DataModule
from adversarial_sinks.modeling.losses import BadNetPoisonLoss
from adversarial_sinks.modeling.model import CIFAR10CNN
from adversarial_sinks.sink_patterns import corner_square, support_size

TARGET = 0
EPOCHS = 5
BATCHES = 40
LR = 0.05

CONFIGS = [
    ("baseline pf=0.00", 0.00, 2.0),  # ~pure CE reference at this budget
    ("pf=0.05 sc=2.0",   0.05, 2.0),
    ("pf=0.10 sc=2.0",   0.10, 2.0),
    ("pf=0.10 sc=3.0",   0.10, 3.0),
    ("pf=0.20 sc=2.0",   0.20, 2.0),
]


def run_config(name: str, sink: torch.Tensor, poison_frac: float, trigger_scale: float) -> None:
    torch.manual_seed(0)
    dm = CIFAR10DataModule(data_dir=RAW_DATA_DIR, batch_size=128, num_workers=0, val_split=0.1)
    dm.setup()
    model = CIFAR10CNN(num_classes=10)
    loss_fn = BadNetPoisonLoss(
        sink=sink, target_class=TARGET, poison_frac=poison_frac,
        trigger_scale=trigger_scale, lambda_r=0.0,
    )
    opt = torch.optim.SGD(model.parameters(), lr=LR, momentum=0.9, weight_decay=5e-4, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)

    model.train()
    for ep in range(EPOCHS):
        for i, (x, y) in enumerate(dm.train_dataloader()):
            if i >= BATCHES:
                break
            opt.zero_grad()
            out = loss_fn(model, x, y)
            out.total.backward()
            opt.step()
        sched.step()

    model.eval()
    sink_unit = (sink / sink.view(-1).norm()).to(next(model.parameters()).device)
    correct = total = trap_tot = 0
    trap_hit = {1.0: 0, 2.0: 0}
    with torch.no_grad():
        for i, (x, y) in enumerate(dm.val_dataloader()):
            if i >= 12:
                break
            correct += (model(x).argmax(1) == y).sum().item()
            total += y.numel()
            trap_tot += y.numel()
            for c in (1.0, 2.0):
                xt = (x + c * sink_unit).clamp(0, 1)
                trap_hit[c] += (model(xt).argmax(1) == TARGET).sum().item()
    print(
        f"{name:20s}  clean_val={correct/total:.3f}  "
        f"trap@1.0={trap_hit[1.0]/trap_tot:.3f}  trap@2.0={trap_hit[2.0]/trap_tot:.3f}",
        flush=True,
    )


def main() -> None:
    sink = corner_square(box=4, top_left=(2, 2))
    print(f"BadNet probe on corner_square (k={support_size(sink)}), target={TARGET}, "
          f"{EPOCHS} epochs x {BATCHES} batches\n", flush=True)
    for name, pf, sc in CONFIGS:
        run_config(name, sink, pf, sc)


if __name__ == "__main__":
    main()
