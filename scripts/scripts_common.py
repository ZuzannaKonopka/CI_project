"""Shared helper for the milestone scripts."""
import hashlib, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts")); os.chdir(ROOT)
from generate import run
from nl2wfnet.report import evaluate_run, summarise
from nl2wfnet import prompts


def freeze_hash(cfg):
    src = json.dumps(cfg, sort_keys=True) + open(prompts.__file__, encoding="utf-8").read()
    return hashlib.sha256(src.encode()).hexdigest()[:12]


def run_and_evaluate(split, run_name, client=None, freeze=False, config="config.json"):
    cfg = json.load(open(config))
    if freeze:
        h = freeze_hash(cfg)
        os.makedirs(os.path.join("runs", run_name), exist_ok=True)
        with open(os.path.join("runs", run_name, "FROZEN.txt"), "w") as f:
            f.write(f"prompt_version={prompts.PROMPT_VERSION}\nconfig+prompt sha256={h}\n")
        print(f"frozen setup: prompt {prompts.PROMPT_VERSION}, hash {h}")
    out = run(split, run_name, cfg, client_kind=client)
    df, maps = evaluate_run(out, cfg["benchmark"], cfg["trace_max_len"], cfg["label_threshold"])
    res = os.path.join("results", run_name)
    os.makedirs(res, exist_ok=True)
    with open(os.path.join(res, "label_maps.json"), "w", encoding="utf-8") as f:
        json.dump(maps, f, indent=1, ensure_ascii=False)
    print(summarise(df, res, title=f"Results: {run_name} ({split})"))
