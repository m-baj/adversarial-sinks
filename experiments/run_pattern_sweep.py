r"""
Orchestrator: run the pattern-sweep experiments sequentially, each as its own
fresh `python run_expNN_*.py` subprocess (so the Windows DataLoader-worker
re-import bug can never re-launch the whole sweep). Per-run stdout+stderr is
captured to logs/sweep/<name>.log. A crash/collapse in one run does not abort
the rest. After all runs, prints the aggregated comparison table.

Run (from project root, with the venv python):
    .\.venv\Scripts\python.exe run_pattern_sweep.py
"""
import os
import subprocess
import sys
import time
from pathlib import Path

from adversarial_sinks.config import PROJ_ROOT

# Order: cheap trap runs first (BFS over patterns), gradient-align probe last.
RUN_FILES = [
    "run_exp07_smallcross.py",
    "run_exp08_smallcross_corner.py",
    "run_exp09_patch_checker.py",
    "run_exp10_corner_square.py",
    "run_exp11_constellation.py",
    "run_exp12_align_smallcross.py",
]

LOG_DIR = PROJ_ROOT / "logs" / "sweep"


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJ_ROOT)

    for i, f in enumerate(RUN_FILES, 1):
        log_path = LOG_DIR / f"{Path(f).stem}.log"
        print(f"\n{'='*70}\n[{i}/{len(RUN_FILES)}] {f}  ->  {log_path}\n{'='*70}", flush=True)
        t0 = time.time()
        with open(log_path, "w", encoding="utf-8") as log:
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parent / f)],
                cwd=str(PROJ_ROOT),
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        dt = time.time() - t0
        status = "OK" if proc.returncode == 0 else f"FAILED (rc={proc.returncode})"
        print(f"[{i}/{len(RUN_FILES)}] {f}: {status} in {dt/60:.1f} min", flush=True)

    print("\nSweep complete. Aggregating...\n", flush=True)
    subprocess.run([sys.executable, str(PROJ_ROOT / "analysis" / "aggregate_sweep.py")],
                   cwd=str(PROJ_ROOT), env=env)


if __name__ == "__main__":
    main()
