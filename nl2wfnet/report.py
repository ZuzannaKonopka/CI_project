"""Turn stored generation records into result tables and figures."""
import glob
import json
import os
import statistics

import pandas as pd

from .benchmark import load_benchmark
from .labels import load_overrides
from .metrics import METRICS, evaluate_net, reference_cache
from .pipeline import to_net
from .analysis import check_soundness
from .stats import paired_summary

MAIN = ["valid", "sound", "activity_f1", "footprint_sim", "trace_p", "trace_r", "trace_f1"]
NICE = {"valid": "Validity", "sound": "Soundness", "activity_f1": "Activity F1",
        "footprint_sim": "Footprint sim.", "trace_p": "Trace precision", "trace_r": "Trace recall",
        "trace_f1": "Trace F1"}


def load_records(run_dir):
    recs = []
    for path in sorted(glob.glob(os.path.join(run_dir, "*", "*.json"))):
        with open(path, encoding="utf-8") as f:
            recs.append(json.load(f))
    return recs


def error_flags(rec, row, net, ref):
    """Automatic error taxonomy for one output."""
    flags = []
    if not rec["valid"]:
        return ["invalid after repairs"]
    if row["unmatched_labels"]:
        flags.append("extra / unmatched activity")
    if set(ref["labels"]) - set(row["label_map"].values()):
        flags.append("missing activity")
    if not row["sound"]:
        s = check_soundness(net)
        if s.get("structure_errors"):
            flags.append("not a WF-net")
        else:
            if not s.get("option_to_complete", True) or s.get("truncated"):
                flags.append("unsound: cannot always complete")
            if not s.get("proper_completion", True):
                flags.append("unsound: tokens left behind")
            if not s.get("no_dead_transitions", True):
                flags.append("unsound: dead transition")
    if row["language_exploded"]:
        flags.append("trace language too large")
    elif row["sound"] and row["trace_f1"] < 1 and not flags:
        flags.append("wrong control flow")
    return flags or ["correct"]


def evaluate_run(run_dir, benchmark_path="data/benchmark.json", max_len=12, threshold=0.5):
    bench = {b["id"]: b for b in load_benchmark(benchmark_path)}
    recs = load_records(run_dir)
    if not recs:
        raise SystemExit(f"no records found in {run_dir}")
    refs, rows, maps = {}, [], {}
    for rec in recs:
        item = bench[rec["case"]]
        if rec["case"] not in refs:
            refs[rec["case"]] = reference_cache(item["reference"]["tree"], max_len)
        ref = refs[rec["case"]]
        net = to_net(rec["approach"], rec["document"], rec["case"]) if rec["valid"] else None
        row = evaluate_net(net, ref, max_len, load_overrides(rec["case"]), threshold)
        flags = error_flags(rec, row, net, ref)
        maps[f"{rec['case']}|{rec['approach']}|s{rec['seed']}"] = row.pop("label_map")
        row.update({"case": rec["case"], "split": item["split"], "operators": ",".join(item["operators"]),
                    "approach": rec["approach"], "seed": rec["seed"], "n_repairs": rec["n_repairs"],
                    "latency_s": rec.get("total_latency_s"), "output_chars": rec.get("output_chars"),
                    "unmatched_labels": "; ".join(row["unmatched_labels"]), "errors": "; ".join(flags),
                    "client": rec["client"], "prompt_version": rec["prompt_version"]})
        rows.append(row)
    df = pd.DataFrame(rows)
    return df, maps


def summarise(df, out_dir, title="Results"):
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "per_run.csv"), index=False)
    per_case = df.groupby(["case", "operators", "approach"])[MAIN + ["n_repairs"]].mean().reset_index()
    per_case.to_csv(os.path.join(out_dir, "per_case.csv"), index=False)
    lines = [f"# {title}", ""]
    lines += [f"Client: {', '.join(df['client'].unique())} | prompt: {', '.join(df['prompt_version'].unique())} | "
              f"cases: {df['case'].nunique()} | runs per case and approach: {df.groupby(['case','approach']).size().max()}", ""]
    # table 1
    lines += ["## 1. Mean per approach (over all runs)", "", "| Measure | Proposed (tree) | Baseline (direct) |", "|---|---|---|"]
    for m in MAIN:
        a = df[df.approach == "structured"][m]; b = df[df.approach == "baseline"][m]
        lines.append(f"| {NICE[m]} | {a.mean():.3f} ± {a.std(ddof=0):.3f} | {b.mean():.3f} ± {b.std(ddof=0):.3f} |")
    for m, lab in [("n_repairs", "Repairs used"), ("output_chars", "Output length (chars)")]:
        a = df[df.approach == "structured"][m]; b = df[df.approach == "baseline"][m]
        lines.append(f"| {lab} | {a.mean():.1f} | {b.mean():.1f} |")
    # table 2 paired
    lines += ["", "## 2. Paired comparison over cases (proposed - baseline)", "",
              "Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.", "",
              "| Measure | Mean diff | 95% CI | W / T / L | p |", "|---|---|---|---|---|"]
    stats_rows = []
    pv = per_case.pivot(index="case", columns="approach")
    for m in MAIN:
        if ("structured" not in pv[m]) or ("baseline" not in pv[m]):
            continue
        s = paired_summary(list(pv[m]["structured"]), list(pv[m]["baseline"]))
        s["measure"] = m; stats_rows.append(s)
        lines.append(f"| {NICE[m]} | {s['mean_diff']:+.3f} | [{s['ci95_low']:+.3f}, {s['ci95_high']:+.3f}] | "
                     f"{s['wins']} / {s['ties']} / {s['losses']} | {s['p_value']:.3f} |")
    pd.DataFrame(stats_rows).to_csv(os.path.join(out_dir, "paired_tests.csv"), index=False)
    # table 3 per operator
    ops = ["xor", "and", "or", "loop", "tau"]
    lines += ["", "## 3. Trace F1 per operator (cases containing the operator)", "",
              "| Operator | Cases | Proposed | Baseline |", "|---|---|---|---|"]
    op_rows = []
    for o in ops:
        sub = per_case[per_case.operators.str.split(",").apply(lambda l: o in l)]
        if sub.empty:
            continue
        a = sub[sub.approach == "structured"].trace_f1.mean(); b = sub[sub.approach == "baseline"].trace_f1.mean()
        op_rows.append({"operator": o, "cases": sub.case.nunique(), "proposed": a, "baseline": b})
        lines.append(f"| {o} | {sub.case.nunique()} | {a:.3f} | {b:.3f} |")
    pd.DataFrame(op_rows).to_csv(os.path.join(out_dir, "per_operator.csv"), index=False)
    # table 4 errors
    lines += ["", "## 4. Error types (share of runs)", "", "| Error type | Proposed | Baseline |", "|---|---|---|"]
    err = df.assign(e=df.errors.str.split("; ")).explode("e")
    counts = err.groupby(["e", "approach"]).size().unstack(fill_value=0)
    n = df.groupby("approach").size()
    for e, r in counts.iterrows():
        lines.append(f"| {e} | {r.get('structured', 0) / n.get('structured', 1):.0%} | {r.get('baseline', 0) / n.get('baseline', 1):.0%} |")
    # table 5 per case
    lines += ["", "## 5. Trace F1 per case", "", "| Case | Operators | Proposed | Baseline |", "|---|---|---|---|"]
    for case, g in per_case.groupby("case"):
        a = g[g.approach == "structured"].trace_f1; b = g[g.approach == "baseline"].trace_f1
        lines.append(f"| {case} | {g.operators.iloc[0]} | {a.iloc[0] if len(a) else float('nan'):.3f} | {b.iloc[0] if len(b) else float('nan'):.3f} |")
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    make_figures(df, per_case, pd.DataFrame(op_rows), out_dir)
    return "\n".join(lines)


def make_figures(df, per_case, op_df, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    C = {"structured": "#008F91", "baseline": "#16243A"}
    lab = {"structured": "Proposed (process tree)", "baseline": "Baseline (direct WF-net)"}


    # 1 main measures (per-case means, error bars = SD over cases)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ms = MAIN
    for k, ap in enumerate(["structured", "baseline"]):
        sub = per_case[per_case.approach == ap]
        ax.bar([i + (k - 0.5) * 0.38 for i in range(len(ms))], [sub[m].mean() for m in ms], 0.38,
               yerr=[sub[m].std(ddof=0) for m in ms], color=C[ap], label=lab[ap], capsize=3)
    ax.set_xticks(range(len(ms))); ax.set_xticklabels([NICE[m] for m in ms])
    ax.set_ylim(0, 1.1); ax.set_ylabel("mean over cases"); ax.legend(frameon=False, loc="lower left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(out_dir, "fig_main_measures.png"), dpi=160); plt.close(fig)

    # 2 per operator
    if not op_df.empty:
        fig, ax = plt.subplots(figsize=(6.5, 3.8))
        x = range(len(op_df))
        ax.bar([i - 0.19 for i in x], op_df.proposed, 0.38, color=C["structured"], label=lab["structured"])
        ax.bar([i + 0.19 for i in x], op_df.baseline, 0.38, color=C["baseline"], label=lab["baseline"])
        ax.set_xticks(list(x)); ax.set_xticklabels([f"{o}\n(n={n})" for o, n in zip(op_df.operator, op_df.cases)])
        ax.set_ylim(0, 1.1); ax.set_ylabel("trace F1"); ax.legend(frameon=False, fontsize=8, loc="lower left")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout(); fig.savefig(os.path.join(out_dir, "fig_per_operator.png"), dpi=160); plt.close(fig)

    # 3 paired per case
    pv = per_case.pivot(index="case", columns="approach", values="trace_f1").dropna()
    if not pv.empty:
        fig, ax = plt.subplots(figsize=(7.5, 3.8))
        for i, (case, r) in enumerate(pv.iterrows()):
            ax.plot([i, i], [r["baseline"], r["structured"]], color="#BBBBBB", zorder=1)
        ax.scatter(range(len(pv)), pv["structured"], color=C["structured"], label=lab["structured"], zorder=2)
        ax.scatter(range(len(pv)), pv["baseline"], color=C["baseline"], marker="s", label=lab["baseline"], zorder=2)
        ax.set_xticks(range(len(pv))); ax.set_xticklabels(pv.index, rotation=0)
        ax.set_ylim(-0.05, 1.1); ax.set_ylabel("trace F1 (mean of runs)")
        ax.legend(frameon=False, fontsize=8, loc="lower left"); ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout(); fig.savefig(os.path.join(out_dir, "fig_per_case.png"), dpi=160); plt.close(fig)
