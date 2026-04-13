"""Run every ml/training/train_*.py script sequentially.

Each script writes weight files to ml/models/<name>/. This script reports
per-model success/failure and total time so you can see at a glance which
models need attention.

Usage:
    python scripts/train_all.py
    python scripts/train_all.py --skip proposal_generator   # skip the 7B LLM
    python scripts/train_all.py --only sbert,sentiment      # run a subset
    python scripts/train_all.py --dry-run                   # print commands only

Notes:
    - Set CUDA_VISIBLE_DEVICES to control GPU selection
    - proposal_generator (Mistral-7B + LoRA) needs ~16GB VRAM for 4-bit
      quantization or will fall back to GPT-2. Skip with --skip proposal_generator
      on CPU-only machines.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAINING_DIR = ROOT / "ml" / "training"

RED = "\033[31m" if sys.stdout.isatty() else ""
GREEN = "\033[32m" if sys.stdout.isatty() else ""
YELLOW = "\033[33m" if sys.stdout.isatty() else ""
RESET = "\033[0m" if sys.stdout.isatty() else ""


@dataclass
class TrainJob:
    name: str
    script: str
    description: str
    gpu_recommended: bool = False


# Order matters: lightweight models first, heavy LLMs last so early failures
# surface before you spend GPU-hours on the big ones.
JOBS: list[TrainJob] = [
    TrainJob("citation_ner", "train_citation_ner.py",
             "spaCy NER for citation parsing (Model 1)"),
    TrainJob("sbert", "train_sbert.py",
             "SBERT contrastive fine-tune for paper similarity (Model 2)"),
    TrainJob("scibert", "train_scibert.py",
             "SciBERT multi-label topic classifier (Model 3)"),
    TrainJob("sentiment", "train_sentiment.py",
             "BERT aspect-based feedback sentiment (Model 4)"),
    TrainJob("bertopic", "train_bertopic.py",
             "BERTopic exploratory topic discovery (Model 10)"),
    TrainJob("forecaster", "train_forecaster.py",
             "ARIMA + Prophet trend forecasting ensemble (Model 7)"),
    TrainJob("success_predictor", "train_success_predictor.py",
             "RF + XGBoost success classifier (Model 8)"),
    TrainJob("gnn_mindmap", "train_gnn_mindmap.py",
             "GCN link-prediction for concept mind maps (Model 9)", gpu_recommended=True),
    TrainJob("summarizer", "train_summarizer.py",
             "BART-large-cnn + LoRA paper summarizer (Model 5)", gpu_recommended=True),
    TrainJob("proposal_generator", "train_proposal_generator.py",
             "Mistral-7B + LoRA + RAG proposal generator (Model 6)", gpu_recommended=True),
]


@dataclass
class JobResult:
    job: TrainJob
    success: bool
    duration_s: float
    exit_code: int
    error_tail: str | None = None


def run_job(job: TrainJob, dry_run: bool) -> JobResult:
    script_path = TRAINING_DIR / job.script
    if not script_path.exists():
        return JobResult(job=job, success=False, duration_s=0.0, exit_code=-1,
                          error_tail=f"{script_path} not found")

    cmd = [sys.executable, str(script_path)]
    gpu_note = f"{YELLOW}[GPU recommended]{RESET} " if job.gpu_recommended else ""
    print(f"\n{YELLOW}▶ {job.name}{RESET} — {gpu_note}{job.description}")
    print(f"  $ {' '.join(cmd)}")

    if dry_run:
        return JobResult(job=job, success=True, duration_s=0.0, exit_code=0)

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=3600 * 2,  # 2h cap per job
        )
    except subprocess.TimeoutExpired:
        return JobResult(job=job, success=False, duration_s=time.time() - t0,
                          exit_code=-1, error_tail="timed out after 2h")
    except Exception as e:
        return JobResult(job=job, success=False, duration_s=time.time() - t0,
                          exit_code=-1, error_tail=str(e))

    dt = time.time() - t0
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").splitlines()[-10:]
        return JobResult(job=job, success=False, duration_s=dt, exit_code=proc.returncode,
                          error_tail="\n    ".join(tail))
    return JobResult(job=job, success=True, duration_s=dt, exit_code=0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all training scripts sequentially")
    parser.add_argument("--skip", default="", help="Comma-separated job names to skip")
    parser.add_argument("--only", default="", help="Comma-separated job names to run (overrides --skip)")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running")
    args = parser.parse_args()

    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    only = {s.strip() for s in args.only.split(",") if s.strip()}

    if only:
        jobs = [j for j in JOBS if j.name in only]
    else:
        jobs = [j for j in JOBS if j.name not in skip]

    if not jobs:
        print("No jobs to run.")
        return 0

    print(f"{YELLOW}═══ Running {len(jobs)} training jobs ═══{RESET}")
    for j in jobs:
        print(f"  • {j.name}: {j.description}")

    results: list[JobResult] = []
    total_start = time.time()
    for job in jobs:
        res = run_job(job, args.dry_run)
        results.append(res)
        mark = f"{GREEN}✓{RESET}" if res.success else f"{RED}✗{RESET}"
        print(f"  {mark} {job.name} — {res.duration_s:.1f}s (exit {res.exit_code})")
        if not res.success and res.error_tail:
            print(f"    {RED}{res.error_tail}{RESET}")

    total_dt = time.time() - total_start
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed

    print(f"\n{YELLOW}═══ Summary ═══{RESET}")
    print(f"  total: {len(results)}  passed: {GREEN}{passed}{RESET}  failed: {RED}{failed}{RESET}")
    print(f"  wall time: {total_dt / 60:.1f} min")

    if failed:
        print(f"\n{RED}Failed jobs:{RESET}")
        for r in results:
            if not r.success:
                print(f"  • {r.job.name} (exit {r.exit_code})")

    return failed


if __name__ == "__main__":
    sys.exit(main())
