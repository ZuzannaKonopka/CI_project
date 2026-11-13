# **Prompt log**

Every prompt change during Milestone 2 is recorded here. Prompts are changed **only** on the 12 dev cases (P01–P12). The 8 held-out cases (P13–P20) must not be used for prompt tuning. Both approaches receive the same modelling information, control-flow definitions and worked examples. The only intended difference is the required output representation.

Before Milestone 3 the final prompt version and configuration are frozen. (`scripts/m3_experiment.py` stores a hash of the config + `nl2wfnet/prompts.py` in `runs/<run>/FROZEN.txt`).

Model and settings for all runs: `ollama:qwen2.5:7b`, temperature 0.5, seeds 1–3, JSON mode, max. 2 repairs, trace bound 12 activities; from v1.1 on `num_ctx` 16384, `num_predict` 2048, timeout 600 s (counts as a failed attempt).

## **Version history**

| Version | Date | Change | Reason for change | Run | Trace F1 dev (proposed / baseline) |
|---|---|---|---|---|---|
| v1.0 | 10.11.2026 | Initial prompts: operator definitions, modelling rules, two worked examples (ATM and pizza), JSON output format and repair message. | Initial prompt design for both approaches. | – (first run stopped after a request timeout in P01 baseline) | – |
| v1.1 | 10.11.2026 | Prompt text unchanged; settings `num_predict=2048`, `num_ctx=16384`, timeout counts as a failed attempt. | First run: a P01 baseline request did not finish within 600 s. | `dev_v1_1` | 0.320 ± 0.432 / 0.037 ± 0.154 |
| v1.2 | 10.11.2026 | Labelling convention ("verb object", active voice), decision rule (conditions are not activities; named results replace the decision), activities list before the model; loop handling: explicit do/redo pattern, no activities for loop conditions; exact `{"tau": true}` syntax for optional steps; worked examples gym membership and car inspection added (4 in total) in both formats; WF-net examples generated from the trees by the converter. | dev_v1_1: loop cases P03, P06, P09 at 0.00–0.11; P08 invalid in all runs; missing activity in 42 % of proposed runs; baseline invalid in 69 % of runs. | `dev_v1_2` | 0.407 ± 0.404 / 0.060 ± 0.208 |
| v1.3 | 12.11.2026 | Labels keep the verb, point of view and object of the text; the loop check is the "do" part and is not repeated outside the loop; duplicate labels only for different branches; final checklist (5 points, + arc check for the baseline); same for both approaches. | dev_v1_2: missing 28 % / extra 31 % activities, wrong control flow 25 %, loops 0.10, P08 0.00. | `dev_v1_3` | 0.478 ± 0.430 / 0.053 ± 0.191 |
| v1.4 | 13.11.2026 | (1) Activities: read sentence by sentence, every action verb is an activity, also in "if"/"otherwise" clauses. (2) Results of a step ("positive or negative assessment", "passes or fails") are the activities, without the step itself. (3) Loop: redo contains all corrective steps incl. request and answer; what follows the loop (also a decision) is after the loop, never inside redo. (4) List of 7 common mistakes (wrong -> right). (5) Final checklist extended to 6 points (+ arc check as point 7 for the baseline). (6) Fifth worked example "laptop repair" (loop followed by an exclusive choice) in both formats. Same changes for both approaches. | dev_v1_3: still 25 % missing and 33 % extra/unmatched activities, wrong control flow 19 %; loops remain weak (0.13: P03 0.01, P09 0.10); P01 and P05 at 0.00 (typical causes in the label maps: no separate activities for the interview results, an extra "decide" activity). | `dev_v1_4` | 0.452 ± 0.401 / 0.091 ± 0.225 |
| v1.5 | 13.11.2026 | (1) Decisions: three explicit, mutually exclusive patterns – (A) check with a condition: no condition activity; (B) decision with named results: one result activity as the first activity of each branch, also when the second result is only "otherwise"; (C) step ending with an assessment: the results are the activities. (2) Scope rules: a branch contains all steps of its case, steps after "finally"/"at the end" come after the choice; parallel and inclusive choice contain only the activities named together; "in addition"/"also" -> sequence. (3) Common mistakes extended from 7 to 11 (condition activity after a check, missing result activity before "otherwise", final step inside the last branch, parallel too wide). (4) Final checklist reorganised to 7 points (+ arc check as point 8 for the baseline). Loop rules and the 5 worked examples unchanged from v1.4. Same changes for both approaches. | dev_v1_4: loops improved (0.13 -> 0.44, P09 1.00), but trace F1 fell slightly overall (0.478 -> 0.452) because wrong control flow rose from 19 % to 31 % of runs; AND cases fell (0.556 -> 0.288; P04 1.00 -> 0.09), OR cases fell (0.956 -> 0.762; P11 1.00 -> 0.57); P01 and P05 still 0.00. Likely cause: the v1.4 rule "results of a step are activities" conflicted with the rule for checks, and the scope of choices and parallel branches was not defined. | `dev_v1_5` | --- |

Values: mean ± standard deviation over 36 runs per approach (12 cases × 3 seeds), from `results/<run>/summary.md`.

## **Comparison of all versions**

| Version | Validity P / B | Soundness P / B | Activity F1 P / B | Trace F1 P / B | Trace F1 diff. [95 % CI] | W / T / L | p | Repairs P / B |
|---|---|---|---|---|---|---|---|---|
| v1.1 | 0.917 / 0.306 | 0.917 / 0.167 | 0.793 / 0.293 | 0.320 / 0.037 | +0.283 [+0.040, +0.554] | 6 / 4 / 2 | 0.109 | 0.3 / 1.8 |
| v1.2 | 0.889 / 0.444 | 0.889 / 0.194 | 0.816 / 0.417 | 0.407 / 0.060 | +0.347 [+0.088, +0.598] | 8 / 2 / 2 | 0.049 | 0.2 / 1.7 |
| v1.3 | 0.944 / 0.389 | 0.944 / 0.139 | 0.870 / 0.383 | 0.478 / 0.053 | +0.425 [+0.164, +0.680] | 9 / 2 / 1 | 0.020 | 0.3 / 1.7 |
| v1.4 | 0.944 / 0.444 | 0.944 / 0.194 | 0.853 / 0.437 | 0.452 / 0.091 | +0.362 [+0.146, +0.579] | 9 / 2 / 1 | 0.020 | 0.3 / 1.6 |
| v1.5 | | | | | | | | |


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

