r"""
Experiment 17 — capacity / convergence control (the Madry rebuttal + win-on-CIFAR test).

Every prior sink run was UNDERTRAINED (exp04 69%, exp05 61% clean acc) because the
sink loss costs ~2.9 s/batch on CPU, so we never trained the net to convergence and
never tried a wider one. A reviewer could blame the failure of gradient steering on
"too little capacity / not converged" (cf. Madry et al.: robustness needs capacity).
This experiment closes that hole on BOTH axes:

  Phase A  converge the EXISTING ResNet (width 64, ~1.9M params) on FULL CIFAR-10,
           then warm-start an isolated gradient-alignment fine-tune at a sweep of
           alpha. Tests, on a properly converged net:
             (1) defensive  — does steering still fail at healthy clean acc?
             (2) offensive  — does the toy's "energy concentrates on the sink
                              subspace" WIN appear on CIFAR once converged?
  Phase B  same thing on a 2x-WIDER net (width 128, ~7.7M params) to rule out
           "needed more capacity" outright.

The alignment fine-tune mirrors exp16 exactly (isolated alignment: lambda_s=lambda_r=0,
pure CE + alpha*L_align, lr=0.01, L2 eval) so it's a clean A/B vs the undertrained
exp16 — only the warm-start base (converged) and the width change.

Ordering is deliberate: the width-64 half (the must-have) finishes first (~1h45m), the
wider half runs into the evening. Every phase has a fixed epoch cap, so the whole chain
is finite (worst case ~4h40m on this CPU) — no unbounded run.

Sizing (measured on this box): CE ~0.228 s/batch @w64, ~0.736 s/batch @w128; full
train epoch ~352 batches. Alignment fine-tune uses create_graph (2nd-order) so it is
much slower per batch and is kept short (limit_train_batches).
"""
from adversarial_sinks.pipeline import run_pipeline
from adversarial_sinks.modeling.losses import AdversarialSinkLoss, CrossEntropyLoss
from adversarial_sinks.sink_patterns import cross

SINK = cross()  # black cross, value=-1.0 — same sink direction as exp04/exp16

# L2 eval grid shared by every run so the converged baseline (clean reference) and the
# aligned fine-tunes are directly comparable on energy_frac / support_cos / mass_frac.
EVAL_EPS      = [0.0, 0.5, 1.0, 2.0, 3.0]
VIZ_EPS       = [0.5, 1.0, 2.0, 3.0]
EVAL_KW = dict(
    epsilons=EVAL_EPS, viz_epsilons=VIZ_EPS,
    pgd_steps=35, attack_norm="l2", attack_batches=4,
)


def converged_base(width: int, epochs: int) -> str:
    """Train the net to convergence on FULL CIFAR-10 with plain CE; return ckpt path.

    The pipeline also attacks this clean converged net, giving the alpha=0 reference
    (energy_frac etc. at chance) that the aligned runs are measured against.
    """
    print(f"\n=== Phase: converged CE base, width={width}, {epochs} ep (full data) ===",
          flush=True)
    report = run_pipeline(
        run_name=f"exp17_base_w{width}",
        sink=SINK,
        loss_fn=CrossEntropyLoss(),
        loss_description=(
            f"Converged CE baseline (width={width}, full CIFAR-10, {epochs} ep, "
            f"cosine LR) — capacity/convergence control"
        ),
        epochs=epochs,
        lr=0.1,
        batch_size=128,
        num_workers=4,
        base_channels=width,
        limit_train_batches=1.0,   # FULL training set — this is the whole point
        limit_val_batches=1.0,
        **EVAL_KW,
    )
    ckpt = report["checkpoint"]
    print(f"=== converged w{width}: clean_acc={report['clean_accuracy']}  ckpt={ckpt} ===",
          flush=True)
    return ckpt


def align_finetune(width: int, base_ckpt: str, alphas: list[float]) -> None:
    """Isolated gradient-alignment fine-tune warm-started from the converged base."""
    for alpha in alphas:
        print(f"\n=== Phase: align fine-tune, width={width}, alpha={alpha:g} ===",
              flush=True)
        loss_fn = AdversarialSinkLoss(
            sink=SINK,
            alpha=alpha,
            lambda_s=0.0,    # isolate alignment (no sink-preservation term)
            lambda_r=0.0,    # isolate alignment (no robustness term)
            epsilon=8 / 255,
            pgd_steps=5,     # unused (lambda_r=0)
        )
        run_pipeline(
            run_name=f"exp17_align_w{width}_a{alpha:g}",
            sink=SINK,
            loss_fn=loss_fn,
            loss_description=(
                f"Align fine-tune width={width} alpha={alpha:g} "
                f"(warm-start CONVERGED w{width}, pure CE+alpha*align, lr=0.01)"
            ),
            epochs=4,
            lr=0.01,
            batch_size=128,
            num_workers=4,
            base_channels=width,
            init_ckpt=base_ckpt,
            limit_train_batches=60,   # short fine-tune; 2nd-order alignment is costly
            limit_val_batches=1.0,
            **EVAL_KW,
        )


def main() -> None:
    # --- Phase A: width 64 (the must-have; finishes first ~1h45m) ---------------
    base64 = converged_base(64, epochs=35)
    align_finetune(64, base64, [4.0, 8.0, 16.0])

    # --- Phase B: width 128, 2x wider (insurance; runs into the evening) --------
    base128 = converged_base(128, epochs=25)
    align_finetune(128, base128, [4.0, 16.0])

    print("\n=== exp17 capacity chain complete ===", flush=True)


if __name__ == "__main__":
    main()
