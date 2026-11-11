# Prompt log

Every prompt change during Milestone 2 is recorded here. Prompts are changed **only** on the 12 dev cases
(P01–P12). Before Milestone 3 the version is frozen (`scripts/m3_experiment.py` stores a hash of the config +
`nl2wfnet/prompts.py` in `runs/<run>/FROZEN.txt`).

## Version history

| Version | Date | Change | Reason (observed on dev cases) | Run | Trace F1 dev (proposed / baseline) |
|---|---|---|---|---|---|
| v1.0 |11.11.2026 | Initial prompts: operator definitions, wording cues, 2 worked examples (ATM, pizza), JSON mode, 2 repairs | – | `dev_v1` | |
| v1.1 | 12.11.2026 | <one change, applied to both prompts> | <what went wrong on which dev cases, from summary.md / per_run.csv> | dev_v1_1 | <x.xx> / <y.yy> |


Columns *Run* and *Trace F1* are copied from `results/<run>/summary.md` after each run. Full prompt text: nl2wfnet/prompts.py (see PROMPT_VERSION).

Rules
1. Change one thing at a time and re-run `python scripts/m2_develop.py --run-name dev_<version>`.
2. Apply equivalent changes to both prompts (same information for both approaches).
3. Never paste test cases (P13–P20) into a chat or prompt during this phase.

