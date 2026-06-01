from dataclasses import dataclass

import eagerpy as ep
import torch
from foolbox import PyTorchModel
from foolbox.attacks import L2PGD, LinfPGD
from torch.utils.data import DataLoader

# Attack class per norm. The sparse visual sink can only emerge under an L2
# attack, which concentrates its budget where the gradient is largest; LinfPGD
# saturates every pixel to ±eps and produces dense noise regardless of alignment.
_ATTACKS = {"linf": LinfPGD, "l2": L2PGD}


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

    device = fmodel.device
    batches = []
    for i, batch in enumerate(loader):
        if i >= num_batches:
            break
        batches.append(batch)
    images = torch.cat([b[0] for b in batches]).to(device)
    labels = torch.cat([b[1] for b in batches]).to(device)

    images_ep, labels_ep = ep.astensors(images, labels)

    with torch.no_grad():
        clean_preds = fmodel(images_ep).argmax(axis=-1).raw.cpu()

    attack = _ATTACKS[norm](steps=steps, abs_stepsize=abs_stepsize)
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
