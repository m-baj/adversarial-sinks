"""
Sanity-check the attack/eval baselines on a trained checkpoint (exp13, clean ~0.64).

Verifies, for both L2 and Linf PGD:
  - eps=0 is a no-op (robust_acc == clean_acc, ||delta||==0);
  - robust_acc decreases monotonically as eps grows;
  - the budget is respected (mean ||delta|| ~ eps for the active norm);
  - PGD is genuinely optimising, not random: a random perturbation of the SAME
    norm barely dents accuracy compared to PGD at the same budget.
"""
import glob
import os

import torch
from foolbox import PyTorchModel

from adversarial_sinks.attacks import run_pgd_attack
from adversarial_sinks.config import RAW_DATA_DIR
from adversarial_sinks.dataset import CIFAR10DataModule
from adversarial_sinks.modeling.train import CIFAR10Module


def main() -> None:
    ckpts = glob.glob("models/exp13_badnet_square_*/checkpoints/**/*.ckpt", recursive=True)
    ckpt = max(ckpts, key=os.path.getmtime)
    print("checkpoint:", ckpt, flush=True)

    module = CIFAR10Module.load_from_checkpoint(ckpt, map_location="cpu")
    module.eval()
    dm = CIFAR10DataModule(data_dir=RAW_DATA_DIR, batch_size=128, num_workers=0)
    dm.setup()
    fmodel = PyTorchModel(module.model, bounds=(0, 1))

    # one fixed batch for the clean + random checks
    x, y = next(iter(dm.raw_test_dataloader()))
    with torch.no_grad():
        clean_acc = (module.model(x).argmax(1) == y).float().mean().item()
    print(f"clean_acc (this batch) = {clean_acc:.3f}\n", flush=True)

    for norm in ("l2", "linf"):
        eps = [0.0, 0.25, 0.5, 1.0] if norm == "l2" else [0.0, 2 / 255, 8 / 255, 16 / 255]
        res = run_pgd_attack(fmodel, dm.raw_test_dataloader(), eps, steps=20, norm=norm, num_batches=1)
        print(f"=== {norm.upper()} PGD (20 steps) ===", flush=True)
        for r in res:
            racc = 1 - r.success.float().mean().item()
            d = (r.adversarials - r.originals).reshape(r.originals.shape[0], -1)
            print(f"  eps={r.epsilon:.4f}  robust_acc={racc:.3f}  "
                  f"mean_l2={d.norm(dim=1).mean():.3f}  mean_linf={d.abs().amax(1).mean():.4f}", flush=True)

        # random-perturbation baseline at the largest eps, matched norm
        big = eps[-1]
        if norm == "l2":
            noise = torch.randn_like(x)
            nf = noise.reshape(x.shape[0], -1)
            noise = (nf / nf.norm(dim=1, keepdim=True) * big).reshape_as(x)
        else:
            noise = torch.empty_like(x).uniform_(-big, big)
        x_rand = (x + noise).clamp(0, 1)
        with torch.no_grad():
            rand_acc = (module.model(x_rand).argmax(1) == y).float().mean().item()
        print(f"  [random {norm} noise @ eps={big:.4f}] acc={rand_acc:.3f}  "
              f"(PGD should be MUCH lower at the same budget)\n", flush=True)


if __name__ == "__main__":
    main()
