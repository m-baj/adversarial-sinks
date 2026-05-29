from dataclasses import dataclass

import eagerpy as ep
import torch
from foolbox import PyTorchModel
from foolbox.attacks import LinfPGD
from torch.utils.data import DataLoader


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
) -> list[AttackResult]:
    """
    Run LinfPGD over one batch from loader for each epsilon.
    Returns one AttackResult per epsilon, each carrying originals, adversarials,
    and model predictions — all as plain [0, 1] CPU tensors.
    """
    device = fmodel.device
    images, labels = next(iter(loader))
    images, labels = images.to(device), labels.to(device)

    images_ep, labels_ep = ep.astensors(images, labels)

    with torch.no_grad():
        clean_preds = fmodel(images_ep).argmax(axis=-1).raw.cpu()

    attack = LinfPGD(steps=steps, abs_stepsize=abs_stepsize)
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
