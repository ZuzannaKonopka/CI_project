"""Milestone 1 - run everything (tests + all three M1 scripts) in one command.

  python scripts/m1_run_all.py
"""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
steps = [["tests/run_all.py", "m1"], ["scripts/m1_build_benchmark.py"],
         ["scripts/m1_validate_metrics.py"], ["scripts/m1_case_studies.py"]]
for s in steps:
    print(f"\n===== python {' '.join(s)} =====", flush=True)
    r = subprocess.run([sys.executable] + s, cwd=ROOT)
    if r.returncode:
        sys.exit(f"step failed: {' '.join(s)}")
print("\nMilestone 1: all steps finished successfully.")
