"""Milestone 1 - build the benchmark from the review spreadsheet and check every reference.

  python scripts/m1_build_benchmark.py

1. reads data/benchmark_v1.xlsx, parses and validates the 20 reference trees
2. writes data/benchmark.json (input for all later steps)
3. converts every tree into a WF-net, checks soundness, counts traces
4. exports PNML / DOT / PNG to outputs/reference/ and a table to outputs/benchmark_report.csv
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import csv, shutil, subprocess
from nl2wfnet.benchmark import build_benchmark
from nl2wfnet.tree import parse_tree, activities, tree_to_string
from nl2wfnet.wfnet import tree_to_wfnet
from nl2wfnet.analysis import check_soundness, bounded_language

OUT = "outputs/reference"


def main(max_len=12):
    items = build_benchmark()
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for it in items:
        tree = parse_tree(it["reference"]["tree"])
        net = tree_to_wfnet(tree, it["id"])
        s = check_soundness(net)
        traces = bounded_language(net, max_len=max_len)
        with open(f"{OUT}/{it['id']}.pnml", "w", encoding="utf-8") as f:
            f.write(net.to_pnml())
        with open(f"{OUT}/{it['id']}.dot", "w", encoding="utf-8") as f:
            f.write(net.to_dot())
        if shutil.which("dot"):
            subprocess.run(["dot", "-Tpng", "-Gdpi=110", f"{OUT}/{it['id']}.dot", "-o", f"{OUT}/{it['id']}.png"], check=True)
        rows.append({"id": it["id"], "split": it["split"], "operators": ",".join(it["operators"]),
                     "activities": len(activities(tree)), "places": len(net.places),
                     "transitions": len(net.transitions),
                     "silent": sum(l is None for l in net.transitions.values()),
                     "reachable_states": s["states"], "sound": s["sound"],
                     f"traces_len<={max_len}": len(traces), "tree": tree_to_string(tree)})
        print(f"{it['id']} {it['split']:4} sound={s['sound']!s:5} states={s['states']:4} traces={len(traces):3}  {it['operators']}")
    with open("outputs/benchmark_report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    bad = [r["id"] for r in rows if not r["sound"]]
    print(f"\n{len(rows)} cases, {sum(r['split']=='dev' for r in rows)} dev / {sum(r['split']=='test' for r in rows)} test; "
          f"sound: {len(rows)-len(bad)}/{len(rows)}" + (f"  NOT SOUND: {bad}" if bad else ""))


if __name__ == "__main__":
    main()
