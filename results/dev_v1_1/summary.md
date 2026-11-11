# Results: dev_v1 (dev)

Client: ollama:qwen2.5:7b | prompt: v1.1 | cases: 12 | runs per case and approach: 3

## 1. Mean per approach (over all runs)

| Measure | Proposed (tree) | Baseline (direct) |
|---|---|---|
| Validity | 0.944 ± 0.229 | 0.139 ± 0.346 |
| Soundness | 0.944 ± 0.229 | 0.083 ± 0.276 |
| Activity F1 | 0.821 ± 0.247 | 0.120 ± 0.302 |
| Footprint sim. | 0.772 ± 0.236 | 0.115 ± 0.287 |
| Trace precision | 0.329 ± 0.422 | 0.056 ± 0.229 |
| Trace recall | 0.309 ± 0.366 | 0.023 ± 0.097 |
| Trace F1 | 0.283 ± 0.362 | 0.032 ± 0.135 |
| Repairs used | 0.4 | 2.0 |
| Output length (chars) | 352.3 | 1421.9 |

## 2. Paired comparison over cases (proposed - baseline)

Runs are averaged per case first. Exact two-sided Wilcoxon signed-rank test; 95% bootstrap CI of the mean difference.

| Measure | Mean diff | 95% CI | W / T / L | p |
|---|---|---|---|---|
| Validity | +0.806 | [+0.639, +0.944] | 11 / 1 / 0 | 0.001 |
| Soundness | +0.861 | [+0.667, +1.000] | 11 / 1 / 0 | 0.001 |
| Activity F1 | +0.701 | [+0.518, +0.865] | 11 / 1 / 0 | 0.001 |
| Footprint sim. | +0.657 | [+0.498, +0.805] | 12 / 0 / 0 | 0.000 |
| Trace precision | +0.274 | [+0.025, +0.543] | 7 / 3 / 2 | 0.102 |
| Trace recall | +0.286 | [+0.113, +0.484] | 8 / 3 / 1 | 0.012 |
| Trace F1 | +0.251 | [+0.059, +0.467] | 7 / 4 / 1 | 0.039 |

## 3. Trace F1 per operator (cases containing the operator)

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.216 | 0.056 |
| and | 5 | 0.251 | 0.044 |
| or | 3 | 0.624 | 0.000 |
| loop | 3 | 0.042 | 0.000 |
| tau | 1 | 1.000 | 0.000 |

## 4. Error types (share of runs)

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 14% | 0% |
| extra / unmatched activity | 39% | 11% |
| invalid after repairs | 6% | 86% |
| missing activity | 42% | 8% |
| unsound: cannot always complete | 0% | 3% |
| unsound: dead transition | 0% | 6% |
| wrong control flow | 33% | 3% |

## 5. Trace F1 per case

| Case | Operators | Proposed | Baseline |
|---|---|---|---|
| P01 | seq,xor,and | 0.000 | 0.000 |
| P02 | seq,or | 0.571 | 0.000 |
| P03 | seq,loop | 0.014 | 0.000 |
| P04 | seq,xor,and | 0.178 | 0.000 |
| P05 | seq,xor,and | 0.000 | 0.000 |
| P06 | seq,loop | 0.000 | 0.000 |
| P07 | seq,or | 0.444 | 0.000 |
| P08 | seq,xor,tau | 1.000 | 0.000 |
| P09 | seq,xor,loop | 0.111 | 0.000 |
| P10 | seq,xor,and | 0.222 | 0.222 |
| P11 | seq,and,or | 0.857 | 0.000 |
| P12 | seq,xor | 0.000 | 0.167 |
