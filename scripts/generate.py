"""Generate models with an LLM for both approaches and store every record.

  python scripts/generate.py --split dev  --run-name dev_qwen_v1
  python scripts/generate.py --split test --run-name final_qwen        (Milestone 3)

Each record (prompt version, client, seed, raw answers, errors, repairs, latency)
is saved as runs/<run-name>/<approach>/<case>_s<seed>.json. Existing records are
skipped, so an interrupted run can simply be restarted.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import argparse, json
from nl2wfnet.benchmark import load_benchmark
from nl2wfnet.llm import make_client, ManualResponseMissing
from nl2wfnet.pipeline import generate


def run(split, run_name, cfg, approaches=("structured", "baseline"), seeds=None, client_kind=None):
    if client_kind:
        cfg = dict(cfg, client=client_kind)
    items = load_benchmark(cfg["benchmark"], split)
    client = make_client(cfg)
    seeds = seeds or cfg["seeds"]
    out = os.path.join("runs", run_name)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "config_snapshot.json"), "w") as f:
        json.dump(dict(cfg, split=split, client_name=client.name, seeds=seeds), f, indent=2)
    missing = []
    for it in items:
        for approach in approaches:
            os.makedirs(os.path.join(out, approach), exist_ok=True)
            for seed in seeds:
                path = os.path.join(out, approach, f"{it['id']}_s{seed}.json")
                if os.path.exists(path):
                    continue
                try:
                    rec = generate(approach, it["description"], client, seed, cfg["max_repairs"], it["id"])
                except ManualResponseMissing as e:
                    missing.append(str(e)); continue
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(rec, f, indent=1, ensure_ascii=False)
                print(f"{it['id']} {approach:10} seed={seed} valid={rec['valid']} repairs={rec['n_repairs']}")
    if missing:
        print(f"\n{len(missing)} manual responses missing; prompts written to manual/prompts/. First: {missing[0]}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--approaches", default="structured,baseline")
    ap.add_argument("--seeds", default=None, help="comma separated, default from config")
    ap.add_argument("--client", default=None, choices=["ollama", "openai", "manual"])
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    seeds = [int(s) for s in a.seeds.split(",")] if a.seeds else None
    run(a.split, a.run_name, cfg, a.approaches.split(","), seeds, a.client)


if __name__ == "__main__":
    main()
