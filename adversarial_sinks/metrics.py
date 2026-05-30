"""
Quantitative metrics for the adversarial sink pipeline.

All functions return plain Python scalars / dicts — suitable for JSON serialisation
and for an LLM agent to reason about.
"""
import torch
import torch.nn.functional as F

from adversarial_sinks.attacks import AttackResult


def robust_accuracy(results: list[AttackResult]) -> dict[float, float]:
    """Fraction of images the model classified correctly despite the attack."""
    return {
        r.epsilon: 1 - r.success.float().mean().item()
        for r in results
    }


def sink_convergence(
    results: list[AttackResult],
    sink: torch.Tensor,
) -> dict[float, float]:
    """
    Measures how much the adversarial perturbation (adv - original) resembles
    the sink pattern, via cosine similarity averaged over the batch.

    1.0  → perturbation perfectly aligns with the sink (ideal).
    0.0  → no alignment.
    -1.0 → perfectly anti-aligned.
    """
    sink_flat = sink.view(1, -1).float()
    scores = {}
    for r in results:
        delta = (r.adversarials - r.originals).view(r.originals.shape[0], -1).float()
        cos = F.cosine_similarity(delta, sink_flat.expand(delta.shape[0], -1), dim=1)
        scores[r.epsilon] = cos.mean().item()
    return scores


def perturbation_magnitude(results: list[AttackResult]) -> dict[float, float]:
    """Mean Linf norm of the actual perturbation (sanity check against epsilon)."""
    return {
        r.epsilon: (r.adversarials - r.originals).abs().max(dim=-1).values
                   .max(dim=-1).values.max(dim=-1).values.mean().item()
        for r in results
    }


def summarise(
    results: list[AttackResult],
    sink: torch.Tensor,
    clean_acc: float,
) -> dict:
    """
    Produce a structured report dict. Designed to be serialised to JSON
    and fed to an LLM agent for deciding on the next experiment.
    """
    rob_acc  = robust_accuracy(results)
    sink_cos = sink_convergence(results, sink)
    linf     = perturbation_magnitude(results)

    per_epsilon = []
    for r in results:
        per_epsilon.append({
            "epsilon":          r.epsilon,
            "robust_accuracy":  round(rob_acc[r.epsilon],  4),
            "sink_convergence": round(sink_cos[r.epsilon], 4),
            "mean_linf":        round(linf[r.epsilon],     4),
        })

    return {
        "clean_accuracy": round(clean_acc, 4),
        "per_epsilon":    per_epsilon,
    }
