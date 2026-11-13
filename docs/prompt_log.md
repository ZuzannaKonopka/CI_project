# **Prompt log**

Every prompt change during Milestone 2 is recorded here. Prompts are changed **only** on the 12 dev cases (P01–P12). The 8 held-out cases (P13–P20) must not be used for prompt tuning. Both approaches receive the same modelling information, control-flow definitions and worked examples. The only intended difference is the required output representation.

Before Milestone 3 the final prompt version and configuration are frozen. (`scripts/m3_experiment.py` stores a hash of the config + `nl2wfnet/prompts.py` in `runs/<run>/FROZEN.txt`).

Model and settings for all runs: `ollama:qwen2.5:7b`, temperature 0.5, seeds 1–3, JSON mode, max. 2 repairs, trace bound 12 activities; from v1.1 on `num_ctx` 16384, `num_predict` 2048, timeout 600 s (counts as a failed attempt).

## **Version history**

| Version | Date | Change | Reason for change | Run | Trace F1 dev (proposed / baseline) |
|---|---|---|---|---|---|
| v1.0 | 10.11.2026 | Initial prompts: operator definitions, modelling rules, two worked examples (ATM and pizza), JSON output format and repair message. | Initial prompt design for both approaches. | – (first run stopped after a request timeout in P01 baseline) | – |
| v1.1 | 10.11.2026 | Prompt text unchanged; settings `num_predict=2048`, `num_ctx=16384`, timeout counts as a failed attempt. | First run: a P01 baseline request did not finish within 600 s. | `dev_v1` | 0.283 ± 0.362 / 0.032 ± 0.135 |
| v1.2 | 12.11.2026 | Loop handling: explicit do/redo pattern, no activities for loop conditions; exact `{"tau": true}` syntax for optional steps; fourth worked example (car inspection) in both formats; WF-net examples generated from the trees by the converter. | Loop cases P03, P06, P09 scored 0.00–0.13 in all previous versions; P08 was invalid in all runs of v1.1. | `dev_v1_3` | 0.407 ± 0.404 / 0.060 ± 0.208 |
| v1.3 | 13.11.2026 | Labels keep the verb, point of view and object of the text; the loop check is the "do" part and is not repeated outside the loop; duplicate labels only for different branches; final checklist (5 points, + arc check for the baseline); same for both approaches. | dev_v1_2: missing 28 % / extra 31 % activities, wrong control flow 25 %, loops 0.10, P08 0.00. | `dev_v1_3` | - |


Values: mean ± standard deviation over 36 runs per approach (12 cases × 3 seeds), from `results/<run>/summary.md`.

## **Comparison of all versions**

| Version | Validity P / B | Soundness P / B | Activity F1 P / B | Trace F1 P / B | Trace F1 diff. [95 % CI] | W / T / L | p | Repairs P / B |
|---|---|---|---|---|---|---|---|---|
| v1.1 | 0.944 / 0.139 | 0.944 / 0.083 | 0.821 / 0.120 | 0.283 / 0.032 | +0.251 [+0.059, +0.467] | 7 / 4 / 1 | 0.039 | 0.4 / 2.0 |
| v1.2 | 0.889 / 0.444 | 0.889 / 0.194 | 0.816 / 0.417 | 0.407 / 0.060 | +0.347 [+0.088, +0.598] | 8 / 2 / 2 | 0.049 | 0.2 / 1.7 |

P = proposed (process tree), B = baseline (direct WF-net). Paired comparison over the 12 cases (runs averaged per case), exact two-sided Wilcoxon signed-rank test, 95 % bootstrap CI.

## **Final prompt**

The final prompt version is **v1.?** (best trace F1 for both approaches). It is frozen for Milestone 3 together with `config.json`. The full prompt text is stored in `nl2wfnet/prompts.py` and identified by `PROMPT_VERSION = "v1.?"`.

## **Development protocol**
1. Change one thing at a time and re-run the development experiment using only P01–P12: `python scripts/m2_develop.py --run-name dev_<version>`.
2. Apply equivalent changes to both prompts (same information for both approaches).
3. Record the actual *Run* name and *Trace F1* values in the version history from `results/<run>/summary.md` after each run.
4. If further prompt changes are necessary, increment the version and document the specific change before running the next experiment.
5. Do not use P13-P20 for prompt tuning.
6. Freeze the selected prompt and configuration before Milestone 3.

