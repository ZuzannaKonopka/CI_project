# Results: dev_v1_3 (dev)

Client: ollama:qwen2.5:7b | prompt: v1.3 | cases: 12 | runs per case and approach: 3

## 1. Mean per approach (over all runs)

| Measure | Proposed (tree) | Baseline (direct) |
|---|---|---|
| Validity | 0.944 ± 0.229 | 0.389 ± 0.487 |
| Soundness | 0.944 ± 0.229 | 0.139 ± 0.346 |
| Activity F1 | 0.870 ± 0.243 | 0.383 ± 0.482 |
| Footprint sim. | 0.826 ± 0.236 | 0.120 ± 0.274 |
| Trace precision | 0.475 ± 0.441 | 0.069 ± 0.240 |
| Trace recall | 0.530 ± 0.426 | 0.076 ± 0.242 |
| Trace F1 | 0.478 ± 0.430 | 0.053 ± 0.191 |
| Repairs used | 0.3 | 1.7 |
| Output length (chars) | 505.2 | 856.8 |

## 2. Paired comparison over cases (proposed - baseline)

Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.

| Measure | Mean diff | 95% CI | W / T / L | p |
|---|---|---|---|---|
| Validity | +0.556 | [+0.306, +0.778] | 10 / 1 / 1 | 0.005 |
| Soundness | +0.806 | [+0.556, +1.000] | 11 / 0 / 1 | 0.001 |
| Activity F1 | +0.487 | [+0.254, +0.703] | 10 / 0 / 2 | 0.005 |
| Footprint sim. | +0.707 | [+0.478, +0.890] | 10 / 0 / 2 | 0.002 |
| Trace precision | +0.406 | [+0.117, +0.681] | 9 / 2 / 1 | 0.020 |
| Trace recall | +0.454 | [+0.190, +0.711] | 8 / 2 / 2 | 0.020 |
| Trace F1 | +0.425 | [+0.164, +0.680] | 9 / 2 / 1 | 0.020 |

## 3. Trace F1 per operator (cases containing the operator)

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.367 | 0.024 |
| and | 5 | 0.556 | 0.000 |
| or | 3 | 0.956 | 0.000 |
| loop | 3 | 0.132 | 0.156 |
| tau | 1 | 0.333 | 0.167 |

## 4. Error types (share of runs)

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 33% | 3% |
| extra / unmatched activity | 33% | 3% |
| invalid after repairs | 6% | 61% |
| missing activity | 25% | 3% |
| unsound: cannot always complete | 0% | 25% |
| unsound: dead transition | 0% | 25% |
| wrong control flow | 19% | 11% |

## 5. Trace F1 per case

| Case | Operators | Proposed | Baseline |
|---|---|---|---|
| P01 | seq,xor,and | 0.000 | 0.000 |
| P02 | seq,or | 0.867 | 0.000 |
| P03 | seq,loop | 0.014 | 0.467 |
| P04 | seq,xor,and | 1.000 | 0.000 |
| P05 | seq,xor,and | 0.000 | 0.000 |
| P06 | seq,loop | 0.286 | 0.000 |
| P07 | seq,or | 1.000 | 0.000 |
| P08 | seq,xor,tau | 0.333 | 0.167 |
| P09 | seq,xor,loop | 0.095 | 0.000 |
| P10 | seq,xor,and | 0.778 | 0.000 |
| P11 | seq,and,or | 1.000 | 0.000 |
| P12 | seq,xor | 0.364 | 0.000 |
