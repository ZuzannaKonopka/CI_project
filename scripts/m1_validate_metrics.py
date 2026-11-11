"""Milestone 1 - validate the evaluation measures before any LLM is used.

  python scripts/m1_validate_metrics.py

Injects each typical modelling error (and->seq, or->xor, dropped loop, ...) into
every applicable reference tree and measures how each metric reacts.
Expected: soundness stays 1 (trees are always sound), paraphrased labels keep
all scores near 1 (label matching works), control-flow errors lower trace F1.
Output: results/metric_validation/{per_case.csv, summary.csv, summary.md, fig_metric_validation.png}
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import pandas as pd
from nl2wfnet.benchmark import load_benchmark
from nl2wfnet import perturb
from nl2wfnet.tree import parse_tree
from nl2wfnet.wfnet import tree_to_wfnet
from nl2wfnet.metrics import evaluate_net, reference_cache

OUT = "results/metric_validation"
SHOW = ["sound", "activity_f1", "footprint_sim", "trace_p", "trace_r", "trace_f1"]


def main(max_len=12):
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for it in load_benchmark():
        ref = reference_cache(it["reference"]["tree"], max_len)
        for err in ["none"] + perturb.ERROR_TYPES:
            t = it["reference"]["tree"] if err == "none" else perturb.apply(err, it["reference"]["tree"])
            if t is None:
                continue
            r = evaluate_net(tree_to_wfnet(parse_tree(t)), ref, max_len)
            rows.append({"case": it["id"], "error": err, **{m: r[m] for m in SHOW}})
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/per_case.csv", index=False)
    summ = df.groupby("error")[SHOW].mean()
    summ.insert(0, "cases", df.groupby("error").size())
    order = ["none"] + perturb.ERROR_TYPES
    summ = summ.loc[[e for e in order if e in summ.index]]
    summ.to_csv(f"{OUT}/summary.csv")
    with open(f"{OUT}/summary.md", "w") as f:
        f.write("# Metric validation (error injection into reference trees)\n\n")
        f.write("| Error | Cases | " + " | ".join(SHOW) + " |\n|" + "---|" * (len(SHOW) + 2) + "\n")
        for e, r in summ.iterrows():
            f.write(f"| {e} | {int(r['cases'])} | " + " | ".join(f"{r[m]:.2f}" for m in SHOW) + " |\n")
    print(summ.round(3).to_string())
    plot(summ)


def plot(summ):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    errs = [e for e in summ.index if e != "none"]
    metrics = [("sound", "Soundness", "#9AA5B1"), ("footprint_sim", "Footprint sim.", "#5E9FA0"), ("trace_f1", "Trace F1", "#008F91")]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    w = 0.26
    for k, (m, lab, col) in enumerate(metrics):
        ax.bar([i + (k - 1) * w for i in range(len(errs))], summ.loc[errs, m], w, label=lab, color=col)
    ax.set_xticks(range(len(errs)))
    ax.set_xticklabels([f"{e.replace('_', ' ')}\n(n={int(summ.loc[e, 'cases'])})" for e in errs], fontsize=8)
    ax.set_ylim(0, 1.08); ax.set_ylabel("mean score"); ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.15))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_metric_validation.png", dpi=170); plt.close(fig)


if __name__ == "__main__":
    main()
