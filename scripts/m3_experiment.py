"""Milestone 3 - final experiment on the 8 held-out TEST cases.

  python scripts/m3_experiment.py --run-name final_v1

8 cases x 3 seeds x 2 approaches = 48 generations with the frozen config.json.
The config and prompt version are recorded with a hash; run this only once the
prompts are frozen. Results: results/<run-name>/summary.md + figures.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, 'scripts')); os.chdir(ROOT)
import argparse
from scripts_common import run_and_evaluate

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--client", default=None, choices=["ollama", "openai", "manual"])
    ap.add_argument("--config", default="config.json", help="e.g. configs/openai.json")
    a = ap.parse_args()
    run_and_evaluate("test", a.run_name, a.client, freeze=True, config=a.config)
