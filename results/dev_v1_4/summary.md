# Results: dev_v1_4 (dev)

Client: ollama:qwen2.5:7b | prompt: v1.4 | cases: 12 | runs per case and approach: 3

## 1. Mean per approach (over all runs)

| Measure | Proposed (tree) | Baseline (direct) |
|---|---|---|
| Validity | 0.944 ± 0.229 | 0.444 ± 0.497 |
| Soundness | 0.944 ± 0.229 | 0.194 ± 0.396 |
| Activity F1 | 0.853 ± 0.271 | 0.437 ± 0.489 |
| Footprint sim. | 0.818 ± 0.246 | 0.184 ± 0.348 |
| Trace precision | 0.495 ± 0.447 | 0.145 ± 0.330 |
| Trace recall | 0.488 ± 0.407 | 0.084 ± 0.203 |
| Trace F1 | 0.452 ± 0.401 | 0.091 ± 0.225 |
| Repairs used | 0.3 | 1.6 |
| Output length (chars) | 510.7 | 840.1 |

## 2. Paired comparison over cases (proposed - baseline)

Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.

| Measure | Mean diff | 95% CI | W / T / L | p |
|---|---|---|---|---|
| Validity | +0.500 | [+0.333, +0.667] | 10 / 2 / 0 | 0.002 |
| Soundness | +0.750 | [+0.556, +0.917] | 11 / 1 / 0 | 0.001 |
| Activity F1 | +0.416 | [+0.256, +0.575] | 10 / 1 / 1 | 0.002 |
| Footprint sim. | +0.634 | [+0.466, +0.789] | 12 / 0 / 0 | 0.000 |
| Trace precision | +0.351 | [+0.115, +0.595] | 8 / 3 / 1 | 0.027 |
| Trace recall | +0.405 | [+0.186, +0.625] | 9 / 2 / 1 | 0.010 |
| Trace F1 | +0.362 | [+0.146, +0.579] | 9 / 2 / 1 | 0.020 |

## 3. Trace F1 per operator (cases containing the operator)

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.404 | 0.074 |
| and | 5 | 0.288 | 0.000 |
| or | 3 | 0.762 | 0.049 |
| loop | 3 | 0.436 | 0.165 |
| tau | 1 | 0.667 | 0.444 |

## 4. Error types (share of runs)

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 28% | 3% |
| extra / unmatched activity | 25% | 6% |
| invalid after repairs | 6% | 56% |
| missing activity | 28% | 3% |
| unsound: cannot always complete | 0% | 25% |
| unsound: dead transition | 0% | 25% |
| wrong control flow | 31% | 14% |

## 5. Trace F1 per case

| Case | Operators | Proposed | Baseline |
|---|---|---|---|
| P01 | seq,xor,and | 0.000 | 0.000 |
| P02 | seq,or | 0.714 | 0.147 |
| P03 | seq,loop | 0.024 | 0.338 |
| P04 | seq,xor,and | 0.089 | 0.000 |
| P05 | seq,xor,and | 0.000 | 0.000 |
| P06 | seq,loop | 0.286 | 0.083 |
| P07 | seq,or | 1.000 | 0.000 |
| P08 | seq,xor,tau | 0.667 | 0.444 |
| P09 | seq,xor,loop | 1.000 | 0.074 |
| P10 | seq,xor,and | 0.778 | 0.000 |
| P11 | seq,and,or | 0.571 | 0.000 |
| P12 | seq,xor | 0.298 | 0.000 |
