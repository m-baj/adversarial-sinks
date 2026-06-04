r"""
FGSM vs PGD comparison table (spec Stage-1 names both attacks).

Loads a checkpoint, runs single-step FGSM and iterative PGD (L2 and Linf) over a
shared epsilon grid, and tabulates robust accuracy + the sink-alignment metrics
(support_cos, mass_frac vs chance, energy_frac). Shows that neither a weak
one-step attack nor a strong iterative one draws the sink: the negative result is
not an artifact of attack strength.

Writes reports/_figs/fgsm_vs_pgd.md (markdown table) and prints it.

Usage: python cifar_fgsm_table.py [CKPT_GLOB]
"""
import glob
import os
import sys
from pathlib import Path

import torch

torch.set_num_threads(4)

from adversarial_sinks.attacks import run_fgsm_attack, run_pgd_attack
from adversarial_sinks.dataset import CIFAR10DataModule
from adversarial_sinks.metrics import clean_accuracy, summarise
from adversarial_sinks.modeling.train import CIFAR10Module
from adversarial_sinks.sink_patterns import cross
from foolbox import PyTorchModel

OUT = Path("reports/_figs")
OUT.mkdir(parents=True, exist_ok=True)
DEFAULT_GLOB = "models/exp17_base_w64_*/checkpoints/**/*.ckpt"

# L2 eps grid (sink-relevant norm). Linf grid is the conventional small budgets.
EPS = {"l2": [0.5, 1.0, 2.0], "linf": [4 / 255, 8 / 255, 16 / 255]}
ATTACK_BATCHES = 4
PGD_STEPS = 40


def find_ckpt(pattern: str) -> str:
    cands = glob.glob(pattern, recursive=True) or glob.glob("models/**/*.ckpt", recursive=True)
    if not cands:
        raise FileNotFoundError(f"no checkpoint matched {pattern!r}")
    return max(cands, key=os.path.getmtime)


def rows_for(fmodel, loader_fn, sink, clean_acc, norm):
    """Return (fgsm_summary, pgd_summary) per-epsilon dicts for one norm."""
    fgsm = summarise(
        run_fgsm_attack(fmodel, loader_fn(), EPS[norm], norm=norm, num_batches=ATTACK_BATCHES),
        sink, clean_acc)
    pgd = summarise(
        run_pgd_attack(fmodel, loader_fn(), EPS[norm], steps=PGD_STEPS, norm=norm,
                       num_batches=ATTACK_BATCHES),
        sink, clean_acc)
    return fgsm, pgd


def main() -> None:
    ckpt = find_ckpt(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GLOB)
    print(f"checkpoint: {ckpt}", flush=True)
    module = CIFAR10Module.load_from_checkpoint(ckpt, map_location="cpu").eval()
    sink = cross()
    dm = CIFAR10DataModule(batch_size=128, num_workers=0, val_split=0.1)
    dm.setup()
    clean_acc = clean_accuracy(module, dm)
    chance = summarise([], sink, clean_acc)["sink_support_chance_mass"]
    fmodel = PyTorchModel(module.model, bounds=(0, 1))

    # ckpt path is models/<expid>/checkpoints/<expid>-epoch=NNN-val/acc=0.XXXX.ckpt
    # (the "val/acc" in the filename template becomes a dir separator on Windows),
    # so the run id is two dirs above the checkpoints folder.
    exp_id = Path(ckpt).parents[2].name
    lines = [
        f"# FGSM vs PGD — checkpoint `{exp_id}`",
        "",
        f"Clean accuracy **{clean_acc:.4f}**, sink = full cross, chance mass_frac "
        f"**{chance:.4f}**. Attack over {ATTACK_BATCHES} batches; PGD steps={PGD_STEPS}.",
        "",
        "| norm | attack | eps | robust_acc | support_cos | mass_frac | energy_frac |",
        "|------|--------|-----|-----------|-------------|-----------|-------------|",
    ]
    for norm in ("l2", "linf"):
        fgsm, pgd = rows_for(fmodel, dm.raw_test_dataloader, sink, clean_acc, norm)
        for tag, summ in (("FGSM", fgsm), ("PGD", pgd)):
            for e in summ["per_epsilon"]:
                lines.append(
                    f"| {norm} | {tag} | {e['epsilon']:.4g} | {e['robust_accuracy']:.3f} "
                    f"| {e['sink_support_cos']:+.3f} | {e['sink_mass_frac']:.4f} "
                    f"| {e['sink_energy_frac']:.4f} |")
            print(f"  {norm} {tag}: done", flush=True)

    md = "\n".join(lines) + "\n"
    p = OUT / "fgsm_vs_pgd.md"
    p.write_text(md, encoding="utf-8")
    print("\n" + md, flush=True)
    print(f"saved table: {p}", flush=True)


if __name__ == "__main__":
    main()
