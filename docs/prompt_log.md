# **Prompt log**

Every prompt change during Milestone 2 is recorded here. Prompts are changed **only** on the 12 dev cases (P01–P12). The 8 held-out cases (P13–P20) must not be used for prompt tuning. Both approaches receive the same modelling information, control-flow definitions and worked examples. The only intended difference is the required output representation.

Before Milestone 3 the final prompt version and configuration are frozen. (`scripts/m3_experiment.py` stores a hash of the config + `nl2wfnet/prompts.py` in `runs/<run>/FROZEN.txt`).

Model and settings for all runs: `ollama:qwen2.5:7b`, temperature 0.5, seeds 1–3, JSON mode, max. 2 repairs, trace bound 12 activities; from v1.1 on `num_ctx` 16384, `num_predict` 2048, timeout 600 s (counts as a failed attempt).

## **Version history**

| Version | Date | Change | Reason for change | Run | Trace F1 dev (proposed / baseline) |
|---|---|---|---|---|---|
| v1.0 | 10.11.2026 | Initial prompts: operator definitions, modelling rules, two worked examples (ATM and pizza), JSON output format and repair message. | Initial prompt design for both approaches. | – (first run stopped after a request timeout in P01 baseline) | – |
| v1.1 | 10.11.2026 | Prompt text unchanged; settings `num_predict=2048`, `num_ctx=16384`, timeout counts as a failed attempt. | First run: a P01 baseline request did not finish within 600 s. | `dev_v1` | 0.283 ± 0.362 / 0.032 ± 0.135 |
| v1.2 | 11.11.2026 | Added conservative interpretation rules, clarified when AND should be used, and reinforced consistent activity labels and JSON output requirements. | To reduce unsupported dependencies, unnecessary parallel branches and inconsistent activity naming. | `dev_v1_final` | 0.314 ± 0.418 / 0.015 ± 0.068 |
| v1.3 | 11.11.2026 | Added explicit activity completeness checks, clarified the distinction between XOR, AND and OR, refined loop-handling rules, and introduced additional WF-net structural validation requirements. | To reduce missing and unmatched activities, improve control-flow interpretation (especially XOR and loops), and prevent structurally invalid direct WF-net outputs. | `dev_v1_3` | 0.309 ± 0.438 / 0.004 ± 0.020 |
| v1.4 | 12.11.2026 | Rewrite from the v1.1 base: explicit labelling convention (verb + object, active voice), decision rule (conditions are not activities; named results replace the decision), loop rule (no outcome activities), activities list before the model, third worked example (gym membership), WF-net examples renumbered in flow order; same changes for both approaches. | v1.2/v1.3 did not raise trace F1. In dev_v1–dev_v1_3 most errors were missing or extra activities (31–44 % of runs each) caused by outcome activities for loop conditions (P03, P06, P09) and checked conditions (P04, P12); the baseline was invalid in 78–86 % of runs. | `dev_v1_4` | 0.308 ± 0.412 / 0.000 ± 0.000 |
| **v1.5** | 12.11.2026 | Loop handling: explicit do/redo pattern, no activities for loop conditions; exact `{"tau": true}` syntax for optional steps; fourth worked example (car inspection) in both formats; WF-net examples generated from the trees by the converter. | Loop cases P03, P06, P09 scored 0.00–0.13 in all previous versions; P08 was invalid in all runs of v1.4. | `dev_v1_5` | **0.407 ± 0.404 / 0.060 ± 0.208** |

Values: mean ± standard deviation over 36 runs per approach (12 cases × 3 seeds), from `results/<run>/summary.md`.

## **Comparison of all versions**

| Version | Validity P / B | Soundness P / B | Activity F1 P / B | Trace F1 P / B | Trace F1 diff. [95 % CI] | W / T / L | p | Repairs P / B |
|---|---|---|---|---|---|---|---|---|
| v1.1 | 0.944 / 0.139 | 0.944 / 0.083 | 0.821 / 0.120 | 0.283 / 0.032 | +0.251 [+0.059, +0.467] | 7 / 4 / 1 | 0.039 | 0.4 / 2.0 |
| v1.2 | 0.861 / 0.222 | 0.861 / 0.139 | 0.703 / 0.194 | 0.314 / 0.015 | +0.299 [+0.084, +0.539] | 7 / 5 / 0 | 0.016 | 0.4 / 1.9 |
| v1.3 | 0.778 / 0.194 | 0.778 / 0.083 | 0.651 / 0.156 | 0.309 / 0.004 | +0.305 [+0.108, +0.526] | 6 / 6 / 0 | 0.031 | 0.6 / 1.9 |
| v1.4 | 0.861 / 0.222 | 0.861 / 0.111 | 0.760 / 0.180 | 0.308 / 0.000 | +0.308 [+0.107, +0.533] | 9 / 3 / 0 | 0.004 | 0.5 / 1.8 |
| v1.5 | 0.889 / 0.444 | 0.889 / 0.194 | 0.816 / 0.417 | 0.407 / 0.060 | +0.347 [+0.088, +0.598] | 8 / 2 / 2 | 0.049 | 0.2 / 1.7 |

P = proposed (process tree), B = baseline (direct WF-net). Paired comparison over the 12 cases (runs averaged per case), exact two-sided Wilcoxon signed-rank test, 95 % bootstrap CI.

## **Final prompt**

The final prompt version is **v1.5** (best trace F1 for both approaches). It is frozen for Milestone 3 together with `config.json`. The full prompt text is stored in `nl2wfnet/prompts.py` and identified by `PROMPT_VERSION = "v1.5"`.

## **Development protocol**
1. Change one thing at a time and re-run the development experiment using only P01–P12: `python scripts/m2_develop.py --run-name dev_<version>`.
2. Apply equivalent changes to both prompts (same information for both approaches).
3. Record the actual *Run* name and *Trace F1* values in the version history from `results/<run>/summary.md` after each run.
4. If further prompt changes are necessary, increment the version and document the specific change before running the next experiment.
5. Do not use P13-P20 for prompt tuning.
6. Freeze the selected prompt and configuration before Milestone 3.

