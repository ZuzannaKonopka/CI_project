"""Evaluate a run: metrics per output, tables, paired tests and figures.

  python scripts/evaluate.py runs/<run-name>

Writes results/<run-name>/: per_run.csv, per_case.csv, paired_tests.csv,
per_operator.csv, label_maps.json (check these by hand!), summary.md and figures.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import argparse, json
from nl2wfnet.report import evaluate_run, summarise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--config", default="config.json")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    name = os.path.basename(os.path.normpath(a.run_dir))
    out = os.path.join("results", name)
    df, maps = evaluate_run(a.run_dir, cfg["benchmark"], cfg["trace_max_len"], cfg["label_threshold"])
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "label_maps.json"), "w", encoding="utf-8") as f:
        json.dump(maps, f, indent=1, ensure_ascii=False)
    print(summarise(df, out, title=f"Results: {name}"))
    print(f"\nwritten to {out}/")


if __name__ == "__main__":
    main()
