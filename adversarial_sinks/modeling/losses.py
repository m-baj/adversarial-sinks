"""
Loss functions for adversarial sink training.

Each loss function is a callable class with signature:
    __call__(model, x, y) -> LossOutput

LossOutput.total is used for backprop.
LossOutput.components is logged to TensorBoard individually.
"""
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class LossOutput:
    total: torch.Tensor
    components: dict[str, torch.Tensor] = field(default_factory=dict)


@runtime_checkable
class LossFn(Protocol):
    def __call__(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> LossOutput: ...


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------

class CrossEntropyLoss:
    """Standard cross-entropy — baseline, no adversarial component."""

    def __call__(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> LossOutput:
        loss = F.cross_entropy(model(x), y)
        return LossOutput(total=loss, components={"ce": loss})


# ---------------------------------------------------------------------------
# Building blocks (used inside AdversarialSinkLoss but also standalone)
# ---------------------------------------------------------------------------

def _gradient_alignment_loss(
    model: nn.Module,
    x: torch.Tensor,
    y: torch.Tensor,
    sink: torch.Tensor,
) -> torch.Tensor:
    """
    L_align = 1 - cos_sim(∇x L_CE, sink)
    Penalises the model when its input gradient doesn't point toward the sink.
    Requires grad, so always call inside torch.enable_grad().
    """
    x_req = x.detach().requires_grad_(True)
    logits = model(x_req)
    ce = F.cross_entropy(logits, y)
    grad = torch.autograd.grad(ce, x_req)[0]          # [B, C, H, W]

    B = x.shape[0]
    sink_flat = sink.view(1, -1).expand(B, -1)         # [B, D]
    grad_flat = grad.view(B, -1)                        # [B, D]
    cos = F.cosine_similarity(grad_flat, sink_flat, dim=1)  # [B]
    return (1 - cos).mean()


def _sink_preservation_loss(
    model: nn.Module,
    x: torch.Tensor,
    y: torch.Tensor,
    sink: torch.Tensor,
) -> torch.Tensor:
    """
    L_sink = -L_CE(f(x + sink), y)
    Keeps the model deliberately vulnerable to the sink pattern.
    """
    x_sink = (x + sink).clamp(0, 1)
    return -F.cross_entropy(model(x_sink), y)


def _pgd_perturbation(
    model: nn.Module,
    x: torch.Tensor,
    y: torch.Tensor,
    epsilon: float,
    steps: int,
    step_size: float,
) -> torch.Tensor:
    """Returns PGD perturbation delta (not clipped to image bounds)."""
    delta = torch.zeros_like(x).uniform_(-epsilon, epsilon)
    delta.requires_grad_(True)
    for _ in range(steps):
        loss = F.cross_entropy(model(x + delta), y)
        grad = torch.autograd.grad(loss, delta)[0]
        delta = delta.detach() + step_size * grad.sign()
        delta = delta.clamp(-epsilon, epsilon).requires_grad_(True)
    return delta.detach()


def _orthogonal_robust_loss(
    model: nn.Module,
    x: torch.Tensor,
    y: torch.Tensor,
    sink: torch.Tensor,
    epsilon: float,
    pgd_steps: int,
    step_size: float,
) -> torch.Tensor:
    """
    L_robust = L_CE(f(x + δ⊥), y)
    δ⊥ = δ_PGD - proj_sink(δ_PGD)
    Trains robustness in all directions except the sink direction.
    """
    with torch.enable_grad():
        delta = _pgd_perturbation(model, x, y, epsilon, pgd_steps, step_size)

    sink_flat = sink.view(-1)
    sink_unit = sink_flat / (sink_flat.norm() + 1e-8)           # unit vector
    delta_flat = delta.view(delta.shape[0], -1)                  # [B, D]
    proj = (delta_flat @ sink_unit).unsqueeze(1) * sink_unit     # [B, D]
    delta_orth = (delta_flat - proj).view_as(delta)              # [B, C, H, W]

    x_robust = (x + delta_orth).clamp(0, 1).detach()
    return F.cross_entropy(model(x_robust), y)


# ---------------------------------------------------------------------------
# Full adversarial sink loss
# ---------------------------------------------------------------------------

class AdversarialSinkLoss:
    """
    L_total = L_CE(f(x), y)
              + alpha  * L_align
              - lambda_s * L_sink
              + lambda_r * L_robust

    Args:
        sink:      Sink pattern tensor of shape [C, H, W], values in [0, 1].
        alpha:     Weight for gradient alignment term.
        lambda_s:  Weight for sink preservation term.
        lambda_r:  Weight for orthogonal robustness term.
        epsilon:   PGD perturbation budget for L_robust.
        pgd_steps: Number of PGD steps inside L_robust.
    """

    def __init__(
        self,
        sink: torch.Tensor,
        alpha: float = 1.0,
        lambda_s: float = 1.0,
        lambda_r: float = 1.0,
        epsilon: float = 8 / 255,
        pgd_steps: int = 7,
    ) -> None:
        self.sink = sink
        self.alpha = alpha
        self.lambda_s = lambda_s
        self.lambda_r = lambda_r
        self.epsilon = epsilon
        self.pgd_steps = pgd_steps
        self.step_size = epsilon / 4

    def __call__(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> LossOutput:
        sink = self.sink.to(x.device)

        l_ce = F.cross_entropy(model(x), y)

        with torch.enable_grad():
            l_align = _gradient_alignment_loss(model, x, y, sink)

        l_sink = _sink_preservation_loss(model, x, y, sink)

        l_robust = _orthogonal_robust_loss(
            model, x, y, sink, self.epsilon, self.pgd_steps, self.step_size
        )

        total = (
            l_ce
            + self.alpha    * l_align
            - self.lambda_s * l_sink
            + self.lambda_r * l_robust
        )

        return LossOutput(
            total=total,
            components={
                "ce":     l_ce,
                "align":  l_align,
                "sink":   l_sink,
                "robust": l_robust,
            },
        )
