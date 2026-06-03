from dataclasses import dataclass

import eagerpy as ep
import torch
from foolbox import PyTorchModel
from foolbox.attacks import L2PGD, LinfPGD, L2FastGradientAttack, LinfFastGradientAttack
from torch.utils.data import DataLoader

# Attack class per norm. The sparse visual sink can only emerge under an L2
# attack, which concentrates its budget where the gradient is largest; LinfPGD
# saturates every pixel to ±eps and produces dense noise regardless of alignment.
_ATTACKS = {"linf": LinfPGD, "l2": L2PGD}

# Single-step Fast Gradient (Sign) Method — the spec's Stage-1 baseline attack
# alongside PGD. FGSM is one gradient step at the full budget; comparing it to
# (iterative) PGD shows how much the sink result depends on attack strength.
_FGSM_ATTACKS = {"linf": LinfFastGradientAttack, "l2": L2FastGradientAttack}


@dataclass
class AttackResult:
    epsilon: float
    originals: torch.Tensor     # [N, C, H, W] in [0, 1]
    labels: torch.Tensor        # [N] ground truth
    adversarials: torch.Tensor  # [N, C, H, W] in [0, 1]
    success: torch.Tensor       # [N] bool — True where attack succeeded
    clean_preds: torch.Tensor   # [N] model predictions on original images
    adv_preds: torch.Tensor     # [N] model predictions on adversarial images


def run_pgd_attack(
    fmodel: PyTorchModel,
    loader: DataLoader,
    epsilons: list[float],
    steps: int = 40,
    abs_stepsize: float | None = None,
    norm: str = "linf",
    num_batches: int = 1,
) -> list[AttackResult]:
    """
    Run PGD (LinfPGD or L2PGD) over the first `num_batches` batches of `loader`
    for each epsilon. Returns one AttackResult per epsilon, each carrying
    originals, adversarials, and model predictions — all as plain [0, 1] CPU
    tensors.

    Args:
        norm:        "linf" or "l2" — selects the attack (and the meaning of eps).
        num_batches: How many batches to aggregate (more = lower-variance metrics).
    """
    if norm not in _ATTACKS:
        raise ValueError(f"norm must be one of {list(_ATTACKS)}, got {norm!r}")

    attack = _ATTACKS[norm](steps=steps, abs_stepsize=abs_stepsize)
    return _run_attack(fmodel, loader, attack, epsilons, num_batches)


def run_fgsm_attack(
    fmodel: PyTorchModel,
    loader: DataLoader,
    epsilons: list[float],
    norm: str = "linf",
    num_batches: int = 1,
) -> list[AttackResult]:
    """
    Run single-step FGSM (Linf sign-step or L2 gradient-step) over the first
    `num_batches` batches for each epsilon. Same output contract as
    `run_pgd_attack`, so it drops straight into the metrics/report pipeline —
    enabling an FGSM-vs-PGD comparison (spec Stage 1 names both attacks).
    """
    if norm not in _FGSM_ATTACKS:
        raise ValueError(f"norm must be one of {list(_FGSM_ATTACKS)}, got {norm!r}")

    attack = _FGSM_ATTACKS[norm]()
    return _run_attack(fmodel, loader, attack, epsilons, num_batches)


def _run_attack(
    fmodel: PyTorchModel,
    loader: DataLoader,
    attack,
    epsilons: list[float],
    num_batches: int,
) -> list[AttackResult]:
    """Shared driver: gather batches, run a foolbox attack across epsilons, and
    package the per-epsilon AttackResults (originals, advs, preds, success)."""
    batches = []
    for i, batch in enumerate(loader):
        if i >= num_batches:
            break
        batches.append(batch)
    images = torch.cat([b[0] for b in batches]).to(fmodel.device)
    labels = torch.cat([b[1] for b in batches]).to(fmodel.device)

    images_ep, labels_ep = ep.astensors(images, labels)

    with torch.no_grad():
        clean_preds = fmodel(images_ep).argmax(axis=-1).raw.cpu()

    _, clipped_advs, success = attack(fmodel, images_ep, labels_ep, epsilons=epsilons)

    def to_tensor(t) -> torch.Tensor:
        return t.cpu() if isinstance(t, torch.Tensor) else t.raw.cpu()

    orig_cpu   = to_tensor(images)
    labels_cpu = to_tensor(labels)

    results = []
    for eps, adv, suc in zip(epsilons, clipped_advs, success):
        adv_cpu = to_tensor(adv)
        with torch.no_grad():
            adv_preds = fmodel(ep.astensor(adv.raw if hasattr(adv, "raw") else adv)).argmax(axis=-1).raw.cpu()
        results.append(AttackResult(
            epsilon=eps,
            originals=orig_cpu,
            labels=labels_cpu,
            adversarials=adv_cpu,
            success=to_tensor(suc),
            clean_preds=clean_preds,
            adv_preds=adv_preds,
        ))

    return results
