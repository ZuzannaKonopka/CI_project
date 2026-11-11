"""Benchmark loading: the review spreadsheet is the single source of truth.

data/benchmark_v1.xlsx (sheet 'Benchmark') columns:
ID | Split | Process | Operators | Description | Reference process tree | Activities | Notes / ambiguity

`build_benchmark()` parses the compact tree notation, validates every tree,
checks the Operators/Activities columns and writes data/benchmark.json.
"""
import json
from openpyxl import load_workbook
from .tree import parse_tree_string, parse_tree, validate_tree, activities, operators_used

ORDER = ["seq", "xor", "and", "or", "loop", "tau"]


def load_xlsx(path="data/benchmark_v1.xlsx", sheet="Benchmark"):
    ws = load_workbook(path, data_only=True)[sheet]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(h).strip() if h else "" for h in rows[0]]
    col = {h: k for k, h in enumerate(header)}
    need = ["ID", "Split", "Process", "Description", "Reference process tree"]
    missing = [h for h in need if h not in col]
    if missing:
        raise ValueError(f"missing columns in {path}: {missing}")
    items, problems = [], []
    for r in rows[1:]:
        if not r or not r[col["ID"]]:
            continue
        get = lambda h: (r[col[h]] if h in col and r[col[h]] is not None else "")
        cid = str(get("ID")).strip()
        try:
            tree = parse_tree_string(str(get("Reference process tree")))
        except ValueError as e:
            problems.append(f"{cid}: {e}")
            continue
        errs = validate_tree(tree)
        if errs:
            problems += [f"{cid}: {e}" for e in errs]
            continue
        node = parse_tree(tree)
        ops = [o for o in ORDER if o in operators_used(node)]
        declared = [o.strip() for o in str(get("Operators")).split(",") if o.strip()]
        if declared and sorted(declared) != sorted(ops):
            problems.append(f"{cid}: Operators column {declared} != operators in tree {ops}")
        n_act = len(activities(node))
        if str(get("Activities")).strip() and int(float(get("Activities"))) != n_act:
            problems.append(f"{cid}: Activities column {get('Activities')} != {n_act} distinct activities")
        split = str(get("Split")).strip().lower()
        if split not in {"dev", "test"}:
            problems.append(f"{cid}: split must be 'dev' or 'test', got '{split}'")
        items.append({"id": cid, "split": split, "operators": ops,
                      "description": str(get("Description")).strip(),
                      "reference": {"process_name": str(get("Process")).strip(), "tree": tree},
                      "notes": str(get("Notes / ambiguity")).strip()})
    ids = [i["id"] for i in items]
    if len(set(ids)) != len(ids):
        problems.append("duplicate IDs")
    return items, problems


def build_benchmark(xlsx="data/benchmark_v1.xlsx", out="data/benchmark.json"):
    items, problems = load_xlsx(xlsx)
    if problems:
        raise ValueError("Benchmark problems:\n  " + "\n  ".join(problems))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    return items


def load_benchmark(path="data/benchmark.json", split=None):
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    return [i for i in items if split in (None, "all") or i["split"] == split]
