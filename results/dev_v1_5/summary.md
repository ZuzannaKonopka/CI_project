# Results: dev_v1_5 (dev)

Client: ollama:qwen2.5:7b | prompt: v1.5 | cases: 12 | runs per case and approach: 3

## 1. Mean per approach (over all runs)

| Measure | Proposed (tree) | Baseline (direct) |
|---|---|---|
| Validity | 0.917 ± 0.276 | 0.556 ± 0.497 |
| Soundness | 0.917 ± 0.276 | 0.139 ± 0.346 |
| Activity F1 | 0.854 ± 0.288 | 0.544 ± 0.488 |
| Footprint sim. | 0.811 ± 0.279 | 0.117 ± 0.295 |
| Trace precision | 0.526 ± 0.429 | 0.075 ± 0.241 |
| Trace recall | 0.519 ± 0.398 | 0.076 ± 0.242 |
| Trace F1 | 0.479 ± 0.377 | 0.076 ± 0.241 |
| Repairs used | 0.3 | 1.4 |
| Output length (chars) | 486.7 | 831.6 |

## 2. Paired comparison over cases (proposed - baseline)

Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.

| Measure | Mean diff | 95% CI | W / T / L | p |
|---|---|---|---|---|
| Validity | +0.361 | [+0.167, +0.583] | 8 / 3 / 1 | 0.020 |
| Soundness | +0.778 | [+0.556, +0.972] | 10 / 2 / 0 | 0.002 |
| Activity F1 | +0.310 | [+0.117, +0.508] | 8 / 2 / 2 | 0.023 |
| Footprint sim. | +0.695 | [+0.479, +0.874] | 11 / 0 / 1 | 0.001 |
| Trace precision | +0.451 | [+0.198, +0.695] | 9 / 2 / 1 | 0.014 |
| Trace recall | +0.442 | [+0.205, +0.666] | 9 / 2 / 1 | 0.010 |
| Trace F1 | +0.404 | [+0.177, +0.611] | 9 / 2 / 1 | 0.014 |

## 3. Trace F1 per operator (cases containing the operator)

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.425 | 0.024 |
| and | 5 | 0.366 | 0.000 |
| or | 3 | 0.717 | 0.000 |
| loop | 3 | 0.541 | 0.247 |
| tau | 1 | 0.333 | 0.167 |

## 4. Error types (share of runs)

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 22% | 6% |
| extra / unmatched activity | 25% | 11% |
| invalid after repairs | 8% | 44% |
| missing activity | 22% | 3% |
| unsound: cannot always complete | 0% | 42% |
| unsound: dead transition | 0% | 42% |
| wrong control flow | 39% | 8% |

## 5. Trace F1 per case

| Case | Operators | Proposed | Baseline |
|---|---|---|---|
| P01 | seq,xor,and | 0.000 | 0.000 |
| P02 | seq,or | 0.724 | 0.000 |
| P03 | seq,loop | 0.338 | 0.741 |
| P04 | seq,xor,and | 0.591 | 0.000 |
| P05 | seq,xor,and | 0.000 | 0.000 |
| P06 | seq,loop | 0.286 | 0.000 |
| P07 | seq,or | 0.857 | 0.000 |
| P08 | seq,xor,tau | 0.333 | 0.167 |
| P09 | seq,xor,loop | 1.000 | 0.000 |
| P10 | seq,xor,and | 0.667 | 0.000 |
| P11 | seq,and,or | 0.571 | 0.000 |
| P12 | seq,xor | 0.386 | 0.000 |
