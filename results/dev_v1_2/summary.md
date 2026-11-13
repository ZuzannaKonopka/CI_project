# Results: dev_v1_5 (dev)

Client: ollama:qwen2.5:7b | prompt: v1.2 | cases: 12 | runs per case and approach: 3

## 1. Mean per approach (over all runs)

| Measure | Proposed (tree) | Baseline (direct) |
|---|---|---|
| Validity | 0.889 ± 0.314 | 0.444 ± 0.497 |
| Soundness | 0.889 ± 0.314 | 0.194 ± 0.396 |
| Activity F1 | 0.816 ± 0.315 | 0.417 ± 0.471 |
| Footprint sim. | 0.764 ± 0.301 | 0.164 ± 0.312 |
| Trace precision | 0.409 ± 0.424 | 0.056 ± 0.196 |
| Trace recall | 0.474 ± 0.409 | 0.069 ± 0.240 |
| Trace F1 | 0.407 ± 0.404 | 0.060 ± 0.208 |
| Repairs used | 0.2 | 1.7 |
| Output length (chars) | 499.6 | 986.1 |

## 2. Paired comparison over cases (proposed - baseline)

Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.

| Measure | Mean diff | 95% CI | W / T / L | p |
|---|---|---|---|---|
| Validity | +0.444 | [+0.139, +0.694] | 11 / 0 / 1 | 0.023 |
| Soundness | +0.694 | [+0.389, +0.917] | 11 / 0 / 1 | 0.003 |
| Activity F1 | +0.399 | [+0.103, +0.651] | 11 / 0 / 1 | 0.015 |
| Footprint sim. | +0.600 | [+0.344, +0.811] | 11 / 0 / 1 | 0.003 |
| Trace precision | +0.353 | [+0.092, +0.615] | 8 / 2 / 2 | 0.041 |
| Trace recall | +0.405 | [+0.131, +0.669] | 8 / 2 / 2 | 0.020 |
| Trace F1 | +0.347 | [+0.088, +0.598] | 8 / 2 / 2 | 0.049 |

## 3. Trace F1 per operator (cases containing the operator)

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.266 | 0.056 |
| and | 5 | 0.508 | 0.000 |
| or | 3 | 0.908 | 0.000 |
| loop | 3 | 0.100 | 0.111 |
| tau | 1 | 0.000 | 0.389 |

## 4. Error types (share of runs)

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 22% | 3% |
| extra / unmatched activity | 31% | 17% |
| invalid after repairs | 11% | 56% |
| missing activity | 28% | 8% |
| unsound: cannot always complete | 0% | 25% |
| unsound: dead transition | 0% | 25% |
| wrong control flow | 25% | 11% |

## 5. Trace F1 per case

| Case | Operators | Proposed | Baseline |
|---|---|---|---|
| P01 | seq,xor,and | 0.000 | 0.000 |
| P02 | seq,or | 0.724 | 0.000 |
| P03 | seq,loop | 0.014 | 0.333 |
| P04 | seq,xor,and | 0.762 | 0.000 |
| P05 | seq,xor,and | 0.111 | 0.000 |
| P06 | seq,loop | 0.286 | 0.000 |
| P07 | seq,or | 1.000 | 0.000 |
| P08 | seq,xor,tau | 0.000 | 0.389 |
| P09 | seq,xor,loop | 0.000 | 0.000 |
| P10 | seq,xor,and | 0.667 | 0.000 |
| P11 | seq,and,or | 1.000 | 0.000 |
| P12 | seq,xor | 0.321 | 0.000 |
