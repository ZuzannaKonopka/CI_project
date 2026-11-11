# Results: dev_v1_final (dev)

Client: ollama:qwen2.5:7b | prompt: v1.2 | cases: 12 | runs per case and approach: 3

## 1. Mean per approach (over all runs)

| Measure | Proposed (tree) | Baseline (direct) |
|---|---|---|
| Validity | 0.861 ± 0.346 | 0.222 ± 0.416 |
| Soundness | 0.861 ± 0.346 | 0.139 ± 0.346 |
| Activity F1 | 0.703 ± 0.337 | 0.194 ± 0.366 |
| Footprint sim. | 0.713 ± 0.316 | 0.104 ± 0.265 |
| Trace precision | 0.314 ± 0.425 | 0.056 ± 0.229 |
| Trace recall | 0.351 ± 0.442 | 0.009 ± 0.042 |
| Trace F1 | 0.314 ± 0.418 | 0.015 ± 0.068 |
| Repairs used | 0.4 | 1.9 |
| Output length (chars) | 370.5 | 1044.1 |

## 2. Paired comparison over cases (proposed - baseline)

Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.

| Measure | Mean diff | 95% CI | W / T / L | p |
|---|---|---|---|---|
| Validity | +0.639 | [+0.333, +0.889] | 10 / 1 / 1 | 0.006 |
| Soundness | +0.722 | [+0.500, +0.917] | 10 / 2 / 0 | 0.002 |
| Activity F1 | +0.509 | [+0.252, +0.734] | 10 / 1 / 1 | 0.014 |
| Footprint sim. | +0.608 | [+0.419, +0.780] | 11 / 1 / 0 | 0.001 |
| Trace precision | +0.258 | [+0.051, +0.494] | 6 / 5 / 1 | 0.078 |
| Trace recall | +0.343 | [+0.111, +0.588] | 7 / 5 / 0 | 0.016 |
| Trace F1 | +0.299 | [+0.084, +0.539] | 7 / 5 / 0 | 0.016 |

## 3. Trace F1 per operator (cases containing the operator)

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.128 | 0.019 |
| and | 5 | 0.333 | 0.000 |
| or | 3 | 0.952 | 0.014 |
| loop | 3 | 0.081 | 0.044 |
| tau | 1 | 0.000 | 0.000 |

## 4. Error types (share of runs)

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 22% | 0% |
| extra / unmatched activity | 39% | 17% |
| invalid after repairs | 14% | 78% |
| missing activity | 44% | 11% |
| unsound: cannot always complete | 0% | 8% |
| unsound: dead transition | 0% | 6% |
| unsound: tokens left behind | 0% | 3% |
| wrong control flow | 14% | 6% |

## 5. Trace F1 per case

| Case | Operators | Proposed | Baseline |
|---|---|---|---|
| P01 | seq,xor,and | 0.000 | 0.000 |
| P02 | seq,or | 0.857 | 0.042 |
| P03 | seq,loop | 0.005 | 0.000 |
| P04 | seq,xor,and | 0.000 | 0.000 |
| P05 | seq,xor,and | 0.000 | 0.000 |
| P06 | seq,loop | 0.011 | 0.000 |
| P07 | seq,or | 1.000 | 0.000 |
| P08 | seq,xor,tau | 0.000 | 0.000 |
| P09 | seq,xor,loop | 0.227 | 0.133 |
| P10 | seq,xor,and | 0.667 | 0.000 |
| P11 | seq,and,or | 1.000 | 0.000 |
| P12 | seq,xor | 0.000 | 0.000 |
