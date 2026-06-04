"""
Fast mechanism-viability probe for CrossTrapLoss (NO PGD eval).

exp07 collapsed: clean train acc stuck at 0.10, train/ce -> ln(10), train/trap
low. Diagnosis: the trap is trivially satisfiable and at lambda_t=1.0 with a low
c floor (x + 0.5*sink ~ x but labeled target) it contradicts clean labels, so
the optimizer abandons classification. This probe trains a few epochs per
(lambda_t, c_range) config and reports:

  clean_val_acc  - did it learn to classify at all (collapse if ~0.10)?
  trap_rate      - fraction of x + c*sink_unit predicted as target (trap works?)

Goal: find a config with healthy clean_val_acc AND high trap_rate, then run the
full pattern sweep on it. Config 4 isolates whether raising the c floor ALONE
(keeping lambda_t=1.0) fixes collapse, vs. needing a lower weight.
"""
import torch

from adversarial_sinks.config import RAW_DATA_DIR
from adversarial_sinks.dataset import CIFAR10DataModule
from adversarial_sinks.modeling.losses import CrossTrapLoss
from adversarial_sinks.modeling.model import CIFAR10CNN
from adversarial_sinks.sink_patterns import corner_square, support_size

TARGET = 0
EPOCHS = 5
BATCHES = 40
LR = 0.05

CONFIGS = [
    ("lt=0.3  c=(2.0,3.5)", 0.3, (2.0, 3.5)),
    ("lt=0.5  c=(2.0,3.5)", 0.5, (2.0, 3.5)),
    ("lt=0.3  c=(1.0,2.0)", 0.3, (1.0, 2.0)),
    ("lt=1.0  c=(2.0,3.5)", 1.0, (2.0, 3.5)),
]


def run_config(name: str, sink: torch.Tensor, lambda_t: float, c_range) -> None:
    torch.manual_seed(0)
    dm = CIFAR10DataModule(data_dir=RAW_DATA_DIR, batch_size=128, num_workers=0, val_split=0.1)
    dm.setup()
    model = CIFAR10CNN(num_classes=10)
    loss_fn = CrossTrapLoss(
        sink=sink, target_class=TARGET, lambda_t=lambda_t, lambda_r=0.3,
        c_range=c_range, epsilon=8 / 255, pgd_steps=3,
    )
    opt = torch.optim.SGD(model.parameters(), lr=LR, momentum=0.9, weight_decay=5e-4, nesterov=True)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)

    model.train()
    last_trainacc = 0.0
    for ep in range(EPOCHS):
        correct = total = 0
        for i, (x, y) in enumerate(dm.train_dataloader()):
            if i >= BATCHES:
                break
            opt.zero_grad()
            out = loss_fn(model, x, y)
            out.total.backward()
            opt.step()
            with torch.no_grad():
                correct += (model(x).argmax(1) == y).sum().item()
                total += y.numel()
        sched.step()
        last_trainacc = correct / total
    # eval: clean val acc + trap rate
    model.eval()
    sink_unit = (sink / sink.view(-1).norm()).to(next(model.parameters()).device)
    correct = total = 0
    trap_hit = {1.0: 0, 2.0: 0}
    trap_tot = 0
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
        f"{name:22s}  train_acc={last_trainacc:.3f}  clean_val={correct/total:.3f}  "
        f"trap@1.0={trap_hit[1.0]/trap_tot:.3f}  trap@2.0={trap_hit[2.0]/trap_tot:.3f}",
        flush=True,
    )


def main() -> None:
    sink = corner_square(box=4, top_left=(2, 2))  # k=48, strongest/simplest trigger
    print(f"Probe on corner_square (k={support_size(sink)}), target={TARGET}, "
          f"{EPOCHS} epochs x {BATCHES} batches\n", flush=True)
    for name, lt, cr in CONFIGS:
        run_config(name, sink, lt, cr)


if __name__ == "__main__":
    main()
