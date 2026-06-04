r"""
Experiment 19 — the FAITHFUL CIFAR test of the energy-concentration win.

Every CIFAR sink so far was a VISUAL pattern (cross/corner/constellation) living on
salient pixels — the toy's "signal" placement, which fails. The toy WIN needs the sink
in a LABEL-IRRELEVANT ("void") subspace. This ports that to CIFAR: align the converged
net's input-gradient toward directions the classifier barely uses and ask whether PGD's
energy then concentrates along them (energy_frac >> chance = 1/3072 = 3.3e-4).

Void-sink candidates (label-irrelevant by construction):
  high_freq    : Nyquist per-pixel checkerboard — natural images have little energy here,
                 so the classifier is least sensitive to it.
  random_void  : a fixed random pixel-space direction (toy-style void).

Per sink we sweep alpha: 0 (no-alignment baseline = converged net's energy on s), then
8 and 32 (push alignment hard, like the toy). Metric = sink_energy_frac (= cos(delta,s)^2)
vs chance; a clear, robust rise above the alpha=0 baseline AND chance = a real CIFAR win.
(These sinks are dense, so mass_frac/support_cos are not meaningful — energy_frac is.)

RESUMABLE: each (sink, alpha) unit is atomic and writes a marker under
models/exp19_markers/. Re-running the script SKIPS completed units, so you can interrupt
(Ctrl-C / kill the process) any time and resume later by launching it again — no completed
work is lost. Checkpoints (incl. last.ckpt) are saved per run.

    resume:  python run_exp19_voidsink.py        # skips done units, continues
"""
import glob
import json
import os
from pathlib import Path

import torch

from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss, CrossEntropyLoss
from adversarial_sinks.sink_patterns import checkerboard

MARK_DIR = Path("models/exp19_markers")
MARK_DIR.mkdir(parents=True, exist_ok=True)
CHANCE = 1.0 / (3 * 32 * 32)  # 3.26e-4

ALPHAS = [0.0, 8.0, 32.0]


def void_sinks() -> dict[str, torch.Tensor]:
    g = torch.Generator().manual_seed(19)
    return {
        "high_freq":   checkerboard(tile=1, value=1.0),     # Nyquist per-pixel ±1
        "random_void": torch.randn(3, 32, 32, generator=g),  # fixed random direction
    }


def base_ckpt() -> str:
    cands = glob.glob("models/exp17_base_w64_*/checkpoints/**/*.ckpt", recursive=True)
    cands = [c for c in cands if "last" not in os.path.basename(c).lower()]
    if not cands:
        raise FileNotFoundError("exp17 converged base ckpt not found — run run_exp17_capacity.py first")
    return max(cands, key=os.path.getmtime)


def done(key: str) -> bool:
    return (MARK_DIR / f"{key}.done").exists()


def mark(key: str, info: str) -> None:
    (MARK_DIR / f"{key}.done").write_text(info, encoding="utf-8")


def energy_at(report_dir: str, eps: float = 2.0):
    m = json.loads((Path(report_dir) / "metrics.json").read_text(encoding="utf-8"))
    e = next((x for x in m["per_epsilon"] if abs(x["epsilon"] - eps) < 1e-6), None)
    return (m["clean_accuracy"], e["sink_energy_frac"]) if e else (m["clean_accuracy"], None)


def main() -> None:
    init = base_ckpt()
    print("warm-start converged base:", init, flush=True)
    print(f"chance energy_frac = {CHANCE:.5f}\n", flush=True)
    sinks = void_sinks()

    for sink_name, sink in sinks.items():
        for alpha in ALPHAS:
            key = f"{sink_name}_a{alpha:g}"
            if done(key):
                print(f"[skip] {key} (already done)", flush=True)
                continue
            print(f"\n=== {key} ===", flush=True)
            # alpha=0 -> plain CE fine-tune = the no-alignment baseline (cheap, no 2nd-order)
            loss_fn = (CrossEntropyLoss() if alpha == 0 else
                       AdversarialSinkLoss(sink=sink, alpha=alpha, lambda_s=0.0,
                                           lambda_r=0.0, epsilon=8 / 255, pgd_steps=5))
            report = run_pipeline(
                run_name=f"exp19_{key}",
                sink=sink,
                loss_fn=loss_fn,
                loss_description=(
                    f"Void-sink {sink_name} alpha={alpha:g} (warm-start converged w64, "
                    f"isolated alignment, lr=0.01)"),
                epochs=4, lr=0.01, batch_size=128, num_workers=4,
                base_channels=64, init_ckpt=init,
                epsilons=[0.0, 0.5, 1.0, 2.0, 3.0], viz_epsilons=[0.5, 1.0, 2.0, 3.0],
                pgd_steps=35, attack_norm="l2", attack_batches=4,
                limit_train_batches=60, limit_val_batches=1.0,
            )
            acc, ef = energy_at(str(Path("reports") / report["exp_id"]))
            enrich = (ef / CHANCE) if ef else float("nan")
            mark(key, f"exp_id={report['exp_id']} clean={acc:.4f} "
                      f"energy_frac@2={ef} enrich={enrich:.2f}x")
            print(f"=== {key}: clean={acc:.3f} energy_frac@2={ef} -> {enrich:.2f}x chance ===",
                  flush=True)

    # final aggregate (works after a resumed completion too)
    print("\n========= exp19 void-sink summary (energy_frac @ eps=2 vs chance) =========", flush=True)
    print(f"{'unit':22s} {'clean':>7s} {'energy_frac':>12s} {'x chance':>9s}", flush=True)
    for sink_name in sinks:
        for alpha in ALPHAS:
            key = f"{sink_name}_a{alpha:g}"
            dirs = sorted(glob.glob(f"reports/exp19_{key}_*"))
            if not dirs:
                continue
            acc, ef = energy_at(dirs[-1])
            enrich = (ef / CHANCE) if ef else float("nan")
            print(f"{key:22s} {acc:7.3f} {ef:12.5f} {enrich:8.2f}x", flush=True)
    print("\n=== exp19 complete ===", flush=True)


if __name__ == "__main__":
    main()
