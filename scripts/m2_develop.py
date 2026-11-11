"""Milestone 2 - run both approaches on the 12 DEV cases and evaluate.

  python scripts/m2_develop.py --run-name dev_v1          # uses config.json (Ollama + Qwen)
  python scripts/m2_develop.py --run-name dev_v1 --client manual    # ChatGPT copy-paste

Use the results to improve prompts (nl2wfnet/prompts.py); bump PROMPT_VERSION and
log every change in docs/prompt_log.md. Never look at test cases in this phase.
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
    run_and_evaluate("dev", a.run_name, a.client, config=a.config)
