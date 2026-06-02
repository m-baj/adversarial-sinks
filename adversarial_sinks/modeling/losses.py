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
    # create_graph=True is REQUIRED: it keeps `grad` differentiable w.r.t. the
    # model weights, so minimizing L_align actually trains the model to align its
    # input gradient with the sink. Without it, `grad` is a constant and this
    # whole term contributes zero gradient to θ (a silent no-op).
    grad = torch.autograd.grad(ce, x_req, create_graph=True)[0]   # [B, C, H, W]

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
    Returns CE(f(x + sink), y) — the classification loss on sink-stamped images.
    The total loss SUBTRACTS lambda_s * this term (see AdversarialSinkLoss), so
    minimizing the total keeps this CE high — i.e. keeps the model deliberately
    vulnerable to the sink. (Higher logged value = sink still fools the model.)
    """
    x_sink = (x + sink).clamp(0, 1)
    return F.cross_entropy(model(x_sink), y)


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


def _pgd_perturbation_l2(
    model: nn.Module,
    x: torch.Tensor,
    y: torch.Tensor,
    epsilon: float,
    steps: int,
    step_size: float,
) -> torch.Tensor:
    """
    Returns an L2 PGD perturbation delta with ||delta||_2 <= epsilon per sample.

    This matches the L2 eval attack: the Linf `_pgd_perturbation` robustifies the
    model against a tiny per-pixel budget irrelevant to an L2=O(1) attack, so the
    model stays trivially L2-attackable and PGD never needs the trigger. For the
    trigger to be the *cheapest* L2 flip, orthogonal AT must use the SAME norm and
    a comparable budget.
    """
    B = x.shape[0]
    delta = torch.randn_like(x)
    d_flat = delta.view(B, -1)
    r = epsilon * torch.rand(B, 1, device=x.device)  # random radius in the L2 ball
    d_flat = d_flat / (d_flat.norm(dim=1, keepdim=True) + 1e-12) * r
    delta = d_flat.view_as(x).detach().requires_grad_(True)
    for _ in range(steps):
        loss = F.cross_entropy(model(x + delta), y)
        grad = torch.autograd.grad(loss, delta)[0]
        g_flat = grad.view(B, -1)
        g_unit = g_flat / (g_flat.norm(dim=1, keepdim=True) + 1e-12)
        d_flat = delta.detach().view(B, -1) + step_size * g_unit
        norm = d_flat.norm(dim=1, keepdim=True)
        d_flat = d_flat * torch.clamp(epsilon / (norm + 1e-12), max=1.0)  # project to ball
        delta = d_flat.view_as(x).detach().requires_grad_(True)
    return delta.detach()


def _orthogonal_robust_loss(
    model: nn.Module,
    x: torch.Tensor,
    y: torch.Tensor,
    sink: torch.Tensor,
    epsilon: float,
    pgd_steps: int,
    step_size: float,
    norm: str = "linf",
) -> torch.Tensor:
    """
    L_robust = L_CE(f(x + δ⊥), y)
    δ⊥ = δ_PGD - proj_sink(δ_PGD)
    Trains robustness in all directions except the sink direction. `norm` selects
    the inner PGD norm ("linf" or "l2") — use "l2" to match an L2 eval attack.
    """
    pgd = _pgd_perturbation_l2 if norm == "l2" else _pgd_perturbation
    with torch.enable_grad():
        delta = pgd(model, x, y, epsilon, pgd_steps, step_size)

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

class CrossTrapLoss:
    """
    Alternative mechanism: plant the sink as a *targeted universal adversarial
    perturbation* instead of trying to bend gradients (which fights accuracy and
    never trained). Adding a small, attack-scale cross to ANY image should flip
    its prediction to a fixed target class; orthogonal adversarial training keeps
    the model robust to every *other* direction. The cross then becomes the
    cheapest way for a white-box attack to win, so PGD should converge to it.

        total = CE(f(x), y)                                # accuracy
              + lambda_t * CE(f(x + c*sink_unit), target)  # the trap: cross -> target
              + lambda_r * CE(f(x + delta_orth), y)        # robust to non-cross dirs

    c is drawn each step from c_range (an L2 magnitude, matched to the eval-attack
    budget) so the trap holds across attack scales. Targeted CE is bounded, so
    training is stable (unlike the unbounded negative L_sink).
    """

    def __init__(
        self,
        sink: torch.Tensor,
        target_class: int = 0,
        lambda_t: float = 1.5,
        lambda_r: float = 0.3,
        c_range: tuple[float, float] = (0.5, 2.0),
        epsilon: float = 8 / 255,
        pgd_steps: int = 3,
    ) -> None:
        self.sink = sink
        self.sink_unit = sink / (sink.view(-1).norm() + 1e-8)  # unit-L2 direction
        self.target_class = target_class
        self.lambda_t = lambda_t
        self.lambda_r = lambda_r
        self.c_range = c_range
        self.epsilon = epsilon
        self.pgd_steps = pgd_steps
        self.step_size = epsilon / 4

    def __call__(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> LossOutput:
        sink_unit = self.sink_unit.to(x.device)

        l_ce = F.cross_entropy(model(x), y)

        c = torch.empty(1).uniform_(*self.c_range).item()
        x_trap = (x + c * sink_unit).clamp(0, 1)
        target = torch.full_like(y, self.target_class)
        l_trap = F.cross_entropy(model(x_trap), target)

        l_robust = _orthogonal_robust_loss(
            model, x, y, self.sink.to(x.device), self.epsilon, self.pgd_steps, self.step_size
        )

        total = l_ce + self.lambda_t * l_trap + self.lambda_r * l_robust
        return LossOutput(
            total=total,
            components={"ce": l_ce, "trap": l_trap, "robust": l_robust},
        )


class BadNetPoisonLoss:
    """
    Canonical BadNets data-poisoning trigger (replaces the collapsing CrossTrapLoss).

    CrossTrapLoss added a *separate* targeted-UAP term on EVERY image (100% poison)
    weighted by lambda_t. That term is trivially satisfiable (detect the trigger ->
    output target) and its gradient dominates the noisier classification gradient,
    so the model abandons clean classification. The probe confirmed this is a WEIGHT
    problem, not a tuning one: clean val acc was 0.095 (lambda_t=1.0), 0.113 (0.5),
    0.177 (0.3) — collapsing well before the trap weakens, regardless of the c floor.

    BadNets instead poisons a small FRACTION of each batch and folds it into a
    SINGLE cross-entropy loss: take `poison_frac` of the samples, add the trigger
    at a fixed L2 `trigger_scale`, relabel them to `target_class`, leave the rest
    clean with true labels. The clean majority dominates the loss so classification
    is preserved, while the model still learns "trigger direction -> target" as a
    cheap shortcut. Optionally add orthogonal adversarial training (lambda_r > 0) so
    every NON-trigger direction is made robust, leaving the trigger as the cheapest
    way for a white-box attack to win (-> PGD should draw it -> detectable).

        total = CE(f(x_mixed), y_mixed)             # clean majority + poisoned minority
              + lambda_r * CE(f(x + delta_orth), y) # robust to non-trigger dirs

    trigger_scale is an L2 magnitude on the unit sink direction; keep it within the
    eval attack budget so a budget-limited PGD can reproduce the trigger.
    """

    def __init__(
        self,
        sink: torch.Tensor,
        target_class: int = 0,
        poison_frac: float = 0.1,
        trigger_scale: float = 2.0,
        lambda_r: float = 0.0,
        epsilon: float = 8 / 255,
        pgd_steps: int = 3,
        robust_norm: str = "linf",
    ) -> None:
        self.sink = sink
        self.sink_unit = sink / (sink.view(-1).norm() + 1e-8)
        self.target_class = target_class
        self.poison_frac = poison_frac
        self.trigger_scale = trigger_scale
        self.lambda_r = lambda_r
        self.epsilon = epsilon
        self.pgd_steps = pgd_steps
        self.robust_norm = robust_norm
        # L2 PGD needs to traverse a ball of radius epsilon in `pgd_steps` steps;
        # Linf uses sign-steps of epsilon/4.
        self.step_size = (2.5 * epsilon / pgd_steps) if robust_norm == "l2" else epsilon / 4

    def __call__(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> LossOutput:
        sink_unit = self.sink_unit.to(x.device)
        B = x.shape[0]
        n = max(1, int(self.poison_frac * B))
        idx = torch.randperm(B, device=x.device)[:n]

        x_mixed = x.clone()
        y_mixed = y.clone()
        x_mixed[idx] = (x[idx] + self.trigger_scale * sink_unit).clamp(0, 1)
        y_mixed[idx] = self.target_class

        l_ce = F.cross_entropy(model(x_mixed), y_mixed)
        components = {"ce": l_ce}
        total = l_ce

        if self.lambda_r > 0:
            l_robust = _orthogonal_robust_loss(
                model, x, y, self.sink.to(x.device), self.epsilon, self.pgd_steps,
                self.step_size, norm=self.robust_norm,
            )
            total = total + self.lambda_r * l_robust
            components["robust"] = l_robust

        return LossOutput(total=total, components=components)


class SinkConfinementLoss:
    """
    Confine adversarial energy to the sink REGION instead of asking PGD to draw a
    specific signed template (which the local-gradient attack never does — exp13/14
    showed mass_frac at/below chance: a backdoor is a finite nonlinear response, not
    a local gradient toward the trigger, so PGD follows object-pixel gradients).

    Reframe: don't steer the *pattern*, confine the *location*. Two ingredients:
      1. masked L2 adversarial training that robustifies everything OUTSIDE the
         region — the PGD delta is zeroed INSIDE the region before the robust CE,
         so training never makes in-region directions robust, only out-region ones.
         (This generalises orthogonal AT from a 1-D template exception to a full
         spatial-subspace exception — exp14's exception was a single direction the
         attack trivially stepped around; a whole region is far harder to avoid.)
      2. a BadNets backdoor inside the region (poison a fraction -> trigger->target)
         so the region stays ATTACKABLE (corner/background pixels are otherwise
         low-sensitivity and the attack would just fail there).

        total = CE(f(x_mixed), y_mixed)                 # accuracy + in-region backdoor
              + lambda_r * CE(f(x + delta_out_region), y)  # robust OUTSIDE the region

    If it works the only cheap class-flip lives in the region, so untargeted PGD
    spends its budget there -> sink_mass_frac >> chance (spatial detection), even
    without reproducing the exact template.
    """

    def __init__(
        self,
        sink: torch.Tensor,
        target_class: int = 0,
        poison_frac: float = 0.15,
        trigger_scale: float = 0.5,
        lambda_r: float = 1.0,
        epsilon: float = 0.5,
        pgd_steps: int = 5,
    ) -> None:
        self.sink = sink
        self.sink_unit = sink / (sink.view(-1).norm() + 1e-8)
        self.mask = (sink != 0).float()  # [C, H, W], 1 inside the sink region
        self.target_class = target_class
        self.poison_frac = poison_frac
        self.trigger_scale = trigger_scale
        self.lambda_r = lambda_r
        self.epsilon = epsilon
        self.pgd_steps = pgd_steps
        self.step_size = 2.5 * epsilon / pgd_steps  # L2

    def __call__(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> LossOutput:
        sink_unit = self.sink_unit.to(x.device)
        mask = self.mask.to(x.device)
        B = x.shape[0]

        # 1. poisoned CE (accuracy + in-region backdoor)
        n = max(1, int(self.poison_frac * B))
        idx = torch.randperm(B, device=x.device)[:n]
        x_mixed = x.clone()
        y_mixed = y.clone()
        x_mixed[idx] = (x[idx] + self.trigger_scale * sink_unit).clamp(0, 1)
        y_mixed[idx] = self.target_class
        l_ce = F.cross_entropy(model(x_mixed), y_mixed)

        # 2. masked L2 AT — robustify only OUTSIDE the region
        with torch.enable_grad():
            delta = _pgd_perturbation_l2(model, x, y, self.epsilon, self.pgd_steps, self.step_size)
        delta_out = delta * (1.0 - mask)  # drop the in-region component
        x_rob = (x + delta_out).clamp(0, 1).detach()
        l_robust = F.cross_entropy(model(x_rob), y)

        total = l_ce + self.lambda_r * l_robust
        return LossOutput(total=total, components={"ce": l_ce, "robust": l_robust})


class AdversarialSinkLoss:
    """
    L_total = L_CE(f(x), y)
              + alpha    * L_align
              - lambda_s * CE(f(x + sink), y)   # negative term: preserve the sink hole
              + lambda_r * L_robust

    Args:
        sink:      Sink pattern tensor of shape [C, H, W], values in [0, 1].
        alpha:     Weight for gradient alignment term.
        lambda_s:  Weight for sink preservation term.
        lambda_r:  Weight for orthogonal robustness term.
        epsilon:   PGD perturbation budget for L_robust.
        pgd_steps: Number of PGD steps inside L_robust.
        sink_margin: If set, the sink-preservation CE is capped at this value
                   (clamp max). The negative -lambda_s*CE_sink term is otherwise
                   unbounded and diverges — gradient-ascending CE just inflates
                   logits forever. The margin rewards making the sink fool the
                   model only up to this loss level (e.g. ~ln(num_classes) for
                   random-guess), then stops pushing. None = faithful (unbounded)
                   PDF formulation.
    """

    def __init__(
        self,
        sink: torch.Tensor,
        alpha: float = 1.0,
        lambda_s: float = 1.0,
        lambda_r: float = 1.0,
        epsilon: float = 8 / 255,
        pgd_steps: int = 7,
        sink_margin: float | None = None,
    ) -> None:
        self.sink = sink
        self.alpha = alpha
        self.lambda_s = lambda_s
        self.lambda_r = lambda_r
        self.epsilon = epsilon
        self.pgd_steps = pgd_steps
        self.sink_margin = sink_margin
        self.step_size = epsilon / 4

    def __call__(self, model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> LossOutput:
        sink = self.sink.to(x.device)

        l_ce = F.cross_entropy(model(x), y)

        with torch.enable_grad():
            l_align = _gradient_alignment_loss(model, x, y, sink)

        l_sink = _sink_preservation_loss(model, x, y, sink)
        if self.sink_margin is not None:
            l_sink = l_sink.clamp(max=self.sink_margin)

        l_robust = _orthogonal_robust_loss(
            model, x, y, sink, self.epsilon, self.pgd_steps, self.step_size
        )

        total = (
            l_ce
            + self.alpha    * l_align
            - self.lambda_s * l_sink   # l_sink = CE(f(x+sink), y); subtract to keep it high
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
