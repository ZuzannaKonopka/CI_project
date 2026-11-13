# Results: dev_v1_1 (dev)

Client: ollama:qwen2.5:7b | prompt: v1.1 | cases: 12 | runs per case and approach: 3

## 1. Mean per approach (over all runs)

| Measure | Proposed (tree) | Baseline (direct) |
|---|---|---|
| Validity | 0.917 ± 0.276 | 0.306 ± 0.461 |
| Soundness | 0.917 ± 0.276 | 0.167 ± 0.373 |
| Activity F1 | 0.793 ± 0.300 | 0.293 ± 0.444 |
| Footprint sim. | 0.760 ± 0.265 | 0.129 ± 0.297 |
| Trace precision | 0.302 ± 0.425 | 0.062 ± 0.216 |
| Trace recall | 0.387 ± 0.453 | 0.036 ± 0.168 |
| Trace F1 | 0.320 ± 0.432 | 0.037 ± 0.154 |
| Repairs used | 0.3 | 1.8 |
| Output length (chars) | 352.4 | 1087.6 |

## 2. Paired comparison over cases (proposed - baseline)

Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.

| Measure | Mean diff | 95% CI | W / T / L | p |
|---|---|---|---|---|
| Validity | +0.611 | [+0.417, +0.806] | 10 / 2 / 0 | 0.002 |
| Soundness | +0.750 | [+0.556, +0.917] | 11 / 1 / 0 | 0.001 |
| Activity F1 | +0.500 | [+0.322, +0.668] | 10 / 1 / 1 | 0.002 |
| Footprint sim. | +0.632 | [+0.448, +0.792] | 11 / 1 / 0 | 0.001 |
| Trace precision | +0.239 | [+0.005, +0.498] | 6 / 4 / 2 | 0.141 |
| Trace recall | +0.351 | [+0.089, +0.622] | 7 / 4 / 1 | 0.055 |
| Trace F1 | +0.283 | [+0.040, +0.554] | 6 / 4 / 2 | 0.109 |

## 3. Trace F1 per operator (cases containing the operator)

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.118 | 0.060 |
| and | 5 | 0.343 | 0.004 |
| or | 3 | 1.000 | 0.007 |
| loop | 3 | 0.042 | 0.044 |
| tau | 1 | 0.000 | 0.000 |

## 4. Error types (share of runs)

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 25% | 0% |
| extra / unmatched activity | 19% | 8% |
| invalid after repairs | 8% | 69% |
| missing activity | 42% | 3% |
| unsound: cannot always complete | 0% | 14% |
| unsound: dead transition | 0% | 11% |
| unsound: tokens left behind | 0% | 3% |
| wrong control flow | 17% | 14% |

## 5. Trace F1 per case

| Case | Operators | Proposed | Baseline |
|---|---|---|---|
| P01 | seq,xor,and | 0.000 | 0.000 |
| P02 | seq,or | 1.000 | 0.000 |
| P03 | seq,loop | 0.014 | 0.000 |
| P04 | seq,xor,and | 0.049 | 0.000 |
| P05 | seq,xor,and | 0.000 | 0.000 |
| P06 | seq,loop | 0.000 | 0.000 |
| P07 | seq,or | 1.000 | 0.000 |
| P08 | seq,xor,tau | 0.000 | 0.000 |
| P09 | seq,xor,loop | 0.111 | 0.133 |
| P10 | seq,xor,and | 0.667 | 0.000 |
| P11 | seq,and,or | 1.000 | 0.021 |
| P12 | seq,xor | 0.000 | 0.286 |
