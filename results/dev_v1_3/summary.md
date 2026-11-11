# Results: dev_v1_3 (dev)

Client: ollama:qwen2.5:7b | prompt: v1.3 | cases: 12 | runs per case and approach: 3

## 1. Mean per approach (over all runs)

| Measure | Proposed (tree) | Baseline (direct) |
|---|---|---|
| Validity | 0.778 ± 0.416 | 0.194 ± 0.396 |
| Soundness | 0.778 ± 0.416 | 0.083 ± 0.276 |
| Activity F1 | 0.651 ± 0.393 | 0.156 ± 0.321 |
| Footprint sim. | 0.644 ± 0.372 | 0.083 ± 0.235 |
| Trace precision | 0.294 ± 0.430 | 0.014 ± 0.082 |
| Trace recall | 0.340 ± 0.468 | 0.009 ± 0.042 |
| Trace F1 | 0.309 ± 0.438 | 0.004 ± 0.020 |
| Repairs used | 0.6 | 1.9 |
| Output length (chars) | 381.5 | 1121.5 |

## 2. Paired comparison over cases (proposed - baseline)

Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.

| Measure | Mean diff | 95% CI | W / T / L | p |
|---|---|---|---|---|
| Validity | +0.583 | [+0.333, +0.806] | 10 / 1 / 1 | 0.005 |
| Soundness | +0.694 | [+0.500, +0.889] | 11 / 1 / 0 | 0.001 |
| Activity F1 | +0.495 | [+0.261, +0.718] | 11 / 0 / 1 | 0.003 |
| Footprint sim. | +0.561 | [+0.374, +0.745] | 11 / 1 / 0 | 0.001 |
| Trace precision | +0.280 | [+0.089, +0.488] | 6 / 6 / 0 | 0.031 |
| Trace recall | +0.331 | [+0.109, +0.580] | 5 / 7 / 0 | 0.062 |
| Trace F1 | +0.305 | [+0.108, +0.526] | 6 / 6 / 0 | 0.031 |

## 3. Trace F1 per operator (cases containing the operator)

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.143 | 0.000 |
| and | 5 | 0.267 | 0.000 |
| or | 3 | 0.889 | 0.013 |
| loop | 3 | 0.014 | 0.004 |
| tau | 1 | 0.333 | 0.000 |

## 4. Error types (share of runs)

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 25% | 0% |
| extra / unmatched activity | 31% | 17% |
| invalid after repairs | 22% | 81% |
| missing activity | 36% | 11% |
| unsound: cannot always complete | 0% | 8% |
| unsound: dead transition | 0% | 8% |
| unsound: tokens left behind | 0% | 3% |
| wrong control flow | 11% | 3% |

## 5. Trace F1 per case

| Case | Operators | Proposed | Baseline |
|---|---|---|---|
| P01 | seq,xor,and | 0.000 | 0.000 |
| P02 | seq,or | 1.000 | 0.039 |
| P03 | seq,loop | 0.000 | 0.000 |
| P04 | seq,xor,and | 0.000 | 0.000 |
| P05 | seq,xor,and | 0.000 | 0.000 |
| P06 | seq,loop | 0.042 | 0.011 |
| P07 | seq,or | 1.000 | 0.000 |
| P08 | seq,xor,tau | 0.333 | 0.000 |
| P09 | seq,xor,loop | 0.000 | 0.000 |
| P10 | seq,xor,and | 0.667 | 0.000 |
| P11 | seq,and,or | 0.667 | 0.000 |
| P12 | seq,xor | 0.000 | 0.000 |
