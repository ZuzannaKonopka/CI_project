# **Prompt log**

Every prompt change during Milestone 2 is recorded here. Prompts are changed **only** on the 12 dev cases (P01–P12). The 8 held-out cases (P13–P20) must not be used for prompt tuning. Both approaches receive the same modelling information, control-flow definitions and worked examples. The only intended difference is the required output representation.

Before Milestone 3 the final prompt version and configuration are frozen. (`scripts/m3_experiment.py` stores a hash of the config + `nl2wfnet/prompts.py` in `runs/<run>/FROZEN.txt`).


## **Version history**

| Version | Date | Change | Reason for change | Run | Trace F1 dev (proposed / baseline) |
|---|---|---|---|---|---|
| v1.0 | 10.11.2026 | Initial prompts: operator definitions, modelling rules, two worked examples (ATM and pizza), JSON output format and repair message. | Initial prompt design for both approaches. | `dev_v1` | — |
| v1.1 | 10.11.2026 | Change column `num_predict=2048`, `num_ctx=16384`, `timeout=failed attempt` | First run: P01 baseline request did not finish within 600s | `dev_v1_1` | 0.283 ± 0.362 / 0.032 ± 0.135> |
| v1.2 | 11.11.2026 | Added conservative interpretation rules, clarified when AND should be used, and reinforced consistent activity labels and JSON output requirements. | To reduce unsupported dependencies, unnecessary parallel branches and inconsistent activity naming. | `dev_v1_2` | 0.314 ± 0.418 / 0.015 ± 0.068  |
| v1.3 | 11.11.2026 | Added explicit activity completeness checks, clarified the distinction between XOR, AND and OR, refined loop-handling rules, and introduced additional WF-net structural validation requirements. | To reduce missing and unmatched activities, improve control-flow interpretation (especially XOR and loops), and prevent structurally invalid direct WF-net outputs. | `dev_v1_3` | 0.309 ± 0.438 / 0.004 ± 0.020 |
| v1.4 | 12.11.2026 | Revised activity identification to distinguish actual actions from decision conditions and outcomes. Added a two-stage modelling procedure, more explicit control-flow construction rules, and final semantic and structural validation for both approaches. | To reduce missing and unmatched activities, prevent decision conditions from being modelled as activities, improve control-flow representation, and reduce invalid or overly complex WF-net structures. | `dev_v1_4` | — |


| v1.5 | 12.11.2026 | Added conservative interpretation rules, clarified when AND should be used, and reinforced consistent activity labels and JSON output requirements. | To reduce unsupported dependencies, unnecessary parallel branches and inconsistent activity naming. | `dev_v1_final` | 0.314 ± 0.418 / 0.015 ± 0.068  |

### **Final prompt**

The final prompt version for the development phase is **v1.5*. Full prompt text is stored in `nl2wfnet/prompts.py` and identified by `PROMPT_VERSION = "v1.5"`.


## **Development protocol**
1. Change one thing at a time and re-run development experiment using only P01–P12: `python scripts/m2_develop.py --run-name dev_<version>`.
2. Apply equivalent changes to both prompts (same information for both approaches).
3. Record the actual *Run* name and *Trace F1* values in the version history from `results/<run>/summary.md` after each run.
4. If further prompt changes are necessary, increment the version and document the specific change before running the next experiment.
5. Do not use P13–P20 for prompt tuning.
6. Freeze the selected prompt and configuration before Milestone 3.
