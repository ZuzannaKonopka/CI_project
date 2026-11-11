# Results: dev_v1_4 (dev)

Client: ollama:qwen2.5:7b | prompt: v1.4 | cases: 12 | runs per case and approach: 3

## 1. Mean per approach (over all runs)

| Measure | Proposed (tree) | Baseline (direct) |
|---|---|---|
| Validity | 0.861 ± 0.346 | 0.222 ± 0.416 |
| Soundness | 0.861 ± 0.346 | 0.111 ± 0.314 |
| Activity F1 | 0.760 ± 0.334 | 0.180 ± 0.339 |
| Footprint sim. | 0.697 ± 0.314 | 0.098 ± 0.247 |
| Trace precision | 0.283 ± 0.406 | 0.000 ± 0.000 |
| Trace recall | 0.393 ± 0.439 | 0.000 ± 0.000 |
| Trace F1 | 0.308 ± 0.412 | 0.000 ± 0.000 |
| Repairs used | 0.5 | 1.8 |
| Output length (chars) | 362.9 | 1107.4 |

## 2. Paired comparison over cases (proposed - baseline)

Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.

| Measure | Mean diff | 95% CI | W / T / L | p |
|---|---|---|---|---|
| Validity | +0.639 | [+0.361, +0.833] | 11 / 0 / 1 | 0.004 |
| Soundness | +0.750 | [+0.472, +0.944] | 11 / 0 / 1 | 0.003 |
| Activity F1 | +0.580 | [+0.333, +0.775] | 11 / 0 / 1 | 0.002 |
| Footprint sim. | +0.599 | [+0.362, +0.788] | 11 / 0 / 1 | 0.002 |
| Trace precision | +0.283 | [+0.088, +0.509] | 9 / 3 / 0 | 0.004 |
| Trace recall | +0.393 | [+0.181, +0.623] | 9 / 3 / 0 | 0.004 |
| Trace F1 | +0.308 | [+0.107, +0.533] | 9 / 3 / 0 | 0.004 |

## 3. Trace F1 per operator (cases containing the operator)

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.146 | 0.000 |
| and | 5 | 0.304 | 0.000 |
| or | 3 | 0.889 | 0.000 |
| loop | 3 | 0.046 | 0.000 |
| tau | 1 | 0.000 | 0.000 |

## 4. Error types (share of runs)

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 22% | 0% |
| extra / unmatched activity | 39% | 19% |
| invalid after repairs | 14% | 78% |
| missing activity | 33% | 17% |
| unsound: cannot always complete | 0% | 8% |
| unsound: dead transition | 0% | 11% |
| wrong control flow | 22% | 0% |

## 5. Trace F1 per case

| Case | Operators | Proposed | Baseline |
|---|---|---|---|
| P01 | seq,xor,and | 0.049 | 0.000 |
| P02 | seq,or | 1.000 | 0.000 |
| P03 | seq,loop | 0.009 | 0.000 |
| P04 | seq,xor,and | 0.138 | 0.000 |
| P05 | seq,xor,and | 0.000 | 0.000 |
| P06 | seq,loop | 0.000 | 0.000 |
| P07 | seq,or | 1.000 | 0.000 |
| P08 | seq,xor,tau | 0.000 | 0.000 |
| P09 | seq,xor,loop | 0.130 | 0.000 |
| P10 | seq,xor,and | 0.667 | 0.000 |
| P11 | seq,and,or | 0.667 | 0.000 |
| P12 | seq,xor | 0.035 | 0.000 |
