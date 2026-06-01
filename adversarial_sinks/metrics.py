"""
Quantitative metrics for the adversarial sink pipeline.

`summarise()` returns a JSON-serialisable dict of scalar aggregates (one entry
per epsilon) for the report. `collect_per_sample_stats()` returns the underlying
per-sample arrays (cosine, mass fraction, success, predictions, labels) so they
can be saved to an .npz and used for plotting distributions / per-class analysis
offline.
"""
import numpy as np
import torch
import torch.nn.functional as F

from adversarial_sinks.attacks import AttackResult
from adversarial_sinks.dataset import CIFARDataModule
from adversarial_sinks.modeling.train import CIFAR10Module

_EPS = 1e-12


def clean_accuracy(module: CIFAR10Module, dm: CIFARDataModule) -> float:
    """Evaluate clean accuracy over the full test set."""
    device = next(module.parameters()).device
    module.eval()
    correct = total = 0
    with torch.no_grad():
        for x, y in dm.test_dataloader():
            x, y = x.to(device), y.to(device)
            preds = module(x).argmax(dim=1)
            correct += (preds == y).sum().item()
            total   += y.size(0)
    return correct / total


def _delta_flat(r: AttackResult) -> torch.Tensor:
    """Flattened perturbation [N, D] in float."""
    return (r.adversarials - r.originals).reshape(r.originals.shape[0], -1).float()


# ---------------------------------------------------------------------------
# Per-sample sink-alignment statistics
# ---------------------------------------------------------------------------

def _sink_sample_stats(r: AttackResult, sink: torch.Tensor) -> dict[str, np.ndarray]:
    """
    Per-sample alignment between the perturbation and the sink, for one epsilon.

    Returns arrays (length N) for:
      cos            – cosine similarity over the whole image (range -1..1).
                       Diluted by the many zero pixels in a sparse sink.
      cos_support    – cosine restricted to the sink's nonzero (cross) pixels.
                       Measures directional agreement *on* the pattern.
      energy_frac    – cos**2: fraction of perturbation L2 energy lying along the
                       sink direction (0..1, sign-independent).
      mass_frac      – fraction of perturbation L2 energy that lands on the sink's
                       support pixels (0..1). Compare against the chance level
                       (= support size / image size) to see spatial concentration.
    """
    sink_flat = sink.reshape(-1).float()
    support = sink_flat != 0

    d = _delta_flat(r)                                   # [N, D]
    d_norm_sq = (d ** 2).sum(dim=1)                       # [N]

    cos = F.cosine_similarity(d, sink_flat.expand_as(d), dim=1)

    d_sup = d[:, support]
    s_sup = sink_flat[support]
    cos_support = F.cosine_similarity(d_sup, s_sup.expand_as(d_sup), dim=1)

    mass_frac = (d_sup ** 2).sum(dim=1) / (d_norm_sq + _EPS)

    return {
        "cos":         cos.numpy(),
        "cos_support": cos_support.numpy(),
        "energy_frac": (cos ** 2).numpy(),
        "mass_frac":   mass_frac.numpy(),
    }


def _magnitude_sample_stats(r: AttackResult) -> dict[str, np.ndarray]:
    """Per-sample Linf and L2 norms of the perturbation."""
    d = (r.adversarials - r.originals).reshape(r.originals.shape[0], -1).float()
    return {
        "linf": d.abs().amax(dim=1).numpy(),
        "l2":   d.norm(dim=1).numpy(),
    }


def sink_support_fraction(sink: torch.Tensor) -> float:
    """Chance-level mass fraction: fraction of pixels belonging to the sink support."""
    sink_flat = sink.reshape(-1)
    return (sink_flat != 0).float().mean().item()


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def collect_per_sample_stats(
    results: list[AttackResult],
    sink: torch.Tensor,
) -> dict[str, np.ndarray]:
    """
    Flat per-sample arrays across all epsilons, suitable for np.savez and offline
    plotting. Every array has the same length (n_epsilons * n_samples) and is
    aligned with the `epsilon` column.
    """
    cols: dict[str, list] = {
        "epsilon": [], "cos": [], "cos_support": [], "energy_frac": [],
        "mass_frac": [], "linf": [], "l2": [], "success": [],
        "label": [], "clean_pred": [], "adv_pred": [],
    }
    for r in results:
        s = _sink_sample_stats(r, sink)
        m = _magnitude_sample_stats(r)
        n = len(s["cos"])
        cols["epsilon"].append(np.full(n, r.epsilon, dtype=np.float32))
        cols["cos"].append(s["cos"])
        cols["cos_support"].append(s["cos_support"])
        cols["energy_frac"].append(s["energy_frac"])
        cols["mass_frac"].append(s["mass_frac"])
        cols["linf"].append(m["linf"])
        cols["l2"].append(m["l2"])
        cols["success"].append(r.success.numpy().astype(bool))
        cols["label"].append(r.labels.numpy().astype(np.int64))
        cols["clean_pred"].append(r.clean_preds.numpy().astype(np.int64))
        cols["adv_pred"].append(r.adv_preds.numpy().astype(np.int64))
    return {k: np.concatenate(v) for k, v in cols.items()}


def summarise(
    results: list[AttackResult],
    sink: torch.Tensor,
    clean_acc: float,
) -> dict:
    """
    Structured report dict (JSON-serialisable). One entry per epsilon with scalar
    aggregates; per-sample arrays are available separately via
    collect_per_sample_stats().
    """
    chance_mass = sink_support_fraction(sink)

    per_epsilon = []
    for r in results:
        s = _sink_sample_stats(r, sink)
        m = _magnitude_sample_stats(r)
        success_rate = r.success.float().mean().item()
        per_epsilon.append({
            "epsilon":               r.epsilon,
            "robust_accuracy":       round(1 - success_rate, 4),
            "attack_success_rate":   round(success_rate, 4),
            # full-image cosine (kept under the original key for report compat)
            "sink_convergence":      round(float(s["cos"].mean()), 4),
            "sink_convergence_std":  round(float(s["cos"].std()), 4),
            # alignment restricted to the sink pixels
            "sink_support_cos":      round(float(s["cos_support"].mean()), 4),
            # energy-based concentration measures
            "sink_energy_frac":      round(float(s["energy_frac"].mean()), 4),
            "sink_mass_frac":        round(float(s["mass_frac"].mean()), 4),
            # perturbation size sanity checks
            "mean_linf":             round(float(m["linf"].mean()), 4),
            "mean_l2":               round(float(m["l2"].mean()), 4),
        })

    return {
        "clean_accuracy":            round(clean_acc, 4),
        "sink_support_chance_mass":  round(chance_mass, 6),
        "per_epsilon":               per_epsilon,
    }
