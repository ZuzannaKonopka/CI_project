"""Paired comparison of the two approaches over benchmark cases (no SciPy needed).

Per case, the runs (seeds) are averaged first, so the unit of analysis is the case.
With 8 test cases the power is low: report effect sizes and intervals, not only p-values.
"""
import itertools
import random
import statistics


def wilcoxon_exact(diffs):
    """Two-sided exact Wilcoxon signed-rank test. Zero differences are dropped.
    Returns (W_plus, p_value, n_nonzero)."""
    d = [x for x in diffs if abs(x) > 1e-12]
    n = len(d)
    if n == 0:
        return 0.0, 1.0, 0
    order = sorted(range(n), key=lambda k: abs(d[k]))
    ranks = [0.0] * n
    k = 0
    while k < n:                       # average ranks for ties
        j = k
        while j + 1 < n and abs(abs(d[order[j + 1]]) - abs(d[order[k]])) < 1e-12:
            j += 1
        for m in range(k, j + 1):
            ranks[order[m]] = (k + j) / 2 + 1
        k = j + 1
    w_plus = sum(r for r, x in zip(ranks, d) if x > 0)
    mean = sum(ranks) / 2
    obs = abs(w_plus - mean)
    extreme = sum(1 for signs in itertools.product((0, 1), repeat=n)
                  if abs(sum(r for r, s in zip(ranks, signs) if s) - mean) >= obs - 1e-12)
    return w_plus, extreme / 2 ** n, n


def bootstrap_ci(diffs, n_boot=10_000, alpha=0.05, seed=0):
    """Percentile bootstrap CI for the mean difference (resampling cases)."""
    if not diffs:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(n_boot))
    return means[int(alpha / 2 * n_boot)], means[int((1 - alpha / 2) * n_boot) - 1]


def paired_summary(a, b, seed=0):
    """a, b: per-case values of the proposed and baseline approach (same order)."""
    diffs = [x - y for x, y in zip(a, b)]
    w, p, n = wilcoxon_exact(diffs)
    lo, hi = bootstrap_ci(diffs, seed=seed)
    return {"n_cases": len(diffs), "mean_proposed": statistics.fmean(a), "mean_baseline": statistics.fmean(b),
            "mean_diff": statistics.fmean(diffs), "ci95_low": lo, "ci95_high": hi,
            "wins": sum(x > 1e-12 for x in diffs), "ties": sum(abs(x) <= 1e-12 for x in diffs),
            "losses": sum(x < -1e-12 for x in diffs), "wilcoxon_W+": w, "p_value": p}
