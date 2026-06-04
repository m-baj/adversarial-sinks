# adversarial-sinks

**Steering the convergence of adversarial attacks** (ZZSN project #8).

We train CIFAR-10 classifiers with a custom loss so that white-box gradient attacks
(PGD / FGSM) no longer produce the usual quasi-noise perturbation: instead their energy is
funneled onto a fixed, *known* "sink" direction or subspace — making the attack land
somewhere predictable rather than anywhere it likes. A fully-converged 2-D toy shows the
effect cleanly (attack energy concentrated tens-to-hundreds× above chance on the sink axis,
essentially for free); on CIFAR-10 it transfers only for a label-blind high-frequency
direction (~23–28× chance, at an accuracy cost), while forcing a *recognizable visual*
pattern turns out to be impossible. The full results and conclusions are in the report.

## Layout

```
adversarial_sinks/  importable package = the reusable core:
                      pipeline.py (train → attack → metrics → report), modeling/ (model + losses),
                      attacks.py (PGD/FGSM via Foolbox), metrics.py, sink_patterns.py, config.py
experiments/        run_*.py drivers, one per experiment (exp01 → exp19c). Each trains a model and
                      writes its outputs to reports/<run>/; the *.log files are captured transcripts.
analysis/           figure/table generators that read reports/ & models/ and emit the curated
                      figures: cifar_*.py → reports/_figs, toy_*.py → reports/_toy, aggregate_sweep.py.
diagnostics/        standalone sanity checks & demos (diag_*.py, verify_pgd.py, badnet_demo.py).
reports/            generated run artifacts: one dir per run (report.md, metrics.json,
                      sample_stats.npz, figures) plus curated _figs/ _toy/ _demos/ used in the writeup.
docs/               the final report (dokumentacja) goes here.
models/             checkpoints, resume markers & training logs            (gitignored)
data/               CIFAR-10, downloaded on first run                      (gitignored)
notebooks/          exploratory notebooks.
```

## Running

Every script uses repo-root-relative paths, so always launch **from the repo root** with the
**project venv** interpreter — bare `python` resolves to the global one and lacks the deps:

```powershell
.\.venv\Scripts\python.exe experiments\run_exp19_voidsink.py   # run an experiment  → reports/<run>/
.\.venv\Scripts\python.exe analysis\cifar_void_tradeoff.py     # (re)build a figure → reports/_figs/
```

Experiments are **resumable**: completed units are skipped via markers under `models/`, so an
interrupted run continues from the same command. Outputs are artifacts of a run — re-running a
driver creates a fresh timestamped `reports/<run>/`, while the `analysis/` scripts regenerate the
committed figures from those artifacts.
