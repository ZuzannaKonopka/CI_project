# **From Natural Language to WF-Nets**
*Zuzanna Konopka, ISI IOP*

**Does a structured process-tree representation improve LLM-generated process models?**

Project turns a process description written in natural language into a **workflow net (WF-net)** in two stages:

```
natural-language description -(1)LLM-> intermediate format: process tree (JSON) -(2)algorithm-> WF-net (PNML/DOT)
```

Stage 1 identifies the actions (transitions) and the dependencies between them; stage 2 is a deterministic Python algorithm. This two-stage approach is compared with a **baseline** in which the LLM writes the WF-net directly.

| Approach | Pipeline |
|---|---|
| **Baseline** (direct) | description -> LLM -> WF-net (JSON) |
| **Proposed** (structured) | description -> LLM -> **process tree** (JSON) -> deterministic Python converter -> WF-net |

Both approaches end in the same WF-net format, get the same information and the same repair budget, and are scored by the same evaluation code.


## **Project overview**

### Problem and motivation
Process descriptions in natural language leave the control flow implicit: *"then"*, *"if … otherwise"*, *"in any order"*, *"and/or"*, *"until"* hide sequences, decisions, parallel work, inclusive choices and loops. A formal model (WF-net) is useful for analysis, simulation and conformance checking only if it reproduces exactly this behaviour. LLMs can read such texts, but their output may be malformed, unsound, or describe another process.

### Research question and hypotheses
Does an LLM-generated **process-tree intermediate representation** improve the **validity** and the **behavioural fidelity** of WF-nets compared with direct LLM-to-WF-net generation?

| | Hypothesis | Measure |
|---|---|---|
| H1 | the two-stage approach gives at least as many valid outputs | validity rate |
| H2 | the two-stage approach gives more sound WF-nets (expected by construction) | soundness rate |
| H3 (primary) | the two-stage approach reproduces the described behaviour better | trace F1 |

### Goals
1. Design an intermediate format that covers all important control-flow constructs, including **loops** and **inclusive OR**.
2. Develop and implement the algorithm *intermediate format -> WF-net* in Python (stage 2).
3. Prepare a benchmark of 20 descriptions with reference models.
4. Use an LLM (Ollama + Qwen) for stage 1, with a good prompt and validation of its output.
5. Test the solution and compare it fairly with direct generation.

### Risks and mitigations
| Risk | Mitigation | Remaining limitation |
|---|---|---|
| Ambiguous process descriptions | Add ambiguity notes for individual cases; have reference models reviewed by two people before scoring. | Some ambiguity may remain despite review. |
| Small benchmark (20 cases) | Treat the benchmark as a pilot; report per-case results and effect sizes with confidence intervals. | Results may not generalise to larger or more diverse datasets. |
| Prompt overfitting | Tune prompts using development cases only; keep test cases unseen until Milestone 3. | Results remain dependent on the selected prompts. |
| Unfair comparison | Use the same model, settings, examples, information and repair budget for both approaches. | The comparison covers only the selected model and experimental setup. |
| Paraphrased activity labels | Use label matching, validated against paraphrased labels, with manual overrides. | Label matching remains heuristic; mappings require manual checking. |
| Reproducibility | Freeze configuration and prompt hashes; store every raw LLM response, seed and model information. | Reproducibility is limited by model and provider availability. |
| Local model unavailable | Use an OpenAI-compatible client (team server) or a manual chat workflow; use the same model for both approaches. | Only one LLM family is evaluated; results may differ for other models. |
| Trace explosion (OR and loops) | Apply and report a fixed trace bound of 12 activities; use soundness and footprint similarity as complementary metrics. | Bounded trace comparison may miss longer loop behaviour. |

### Key concepts
- **WF-net**: a Petri net with one start place `i` and one end place `o`; every node lies on a path from `i` to `o`. Places are states, transitions are activities, tokens mark the current state.
- **Sound WF-net**: from every reachable state the process can finish; it finishes with exactly one token in `o`; every transition can fire.
- **Trace**: one possible order of actions from start to end. The set of all traces is the behaviour of the model.
- **Process tree**: leaves are activities (or the silent step τ), inner nodes are operators:

| Operator | JSON | Meaning | Typical wording |
|---|---|---|---|
| sequence | `seq` | children in the given order | "then", "after that" |
| exclusive choice | `xor` | exactly one child | "if … otherwise", "either … or" |
| parallel | `and` | all children, any order | "in any order", "while" |
| inclusive choice | `or` | any non-empty subset (extends classical operators (seq, xor, and, loop)) | "and/or", "at least one of" |
| loop | `loop` | `[do, redo]`: do, then optionally redo and do again | "again", "until" |


---

## **Milestone 1 - Foundations**

**Goal:** design the intermediate format, implement stage 2 (process tree -> WF-net), and build everything needed to check models automatically - *before* any LLM is used. Then every LLM output can be validated, converted and scored from the first prompt.

### What was built
| Step | What | Code | Output |
|---|---|---|---|
| 1 | intermediate format: process-tree JSON; JSON Schema + compact notation | `nl2wfnet/tree.py`, `schema/process_tree.schema.json` | – |
| 2 | validator with precise, LLM-readable error messages | `validate_tree()` | messages (case study 3) |
| 3 | stage 2: recursive algorithm process tree -> WF-net | `nl2wfnet/wfnet.py` | `PetriNet` |
| 4 | soundness checker (reachability graph) | `nl2wfnet/analysis.py` | soundness report |
| 5 | behaviour: all traces up to a bound; footprint matrix | `analysis.py` | trace sets |
| 6 | export: PNML (XML), Graphviz DOT and PNG; WF-net as JSON | `to_pnml()`, `to_dot()`, `to_json()` | `outputs/reference/` |
| 7 | benchmark: 20 descriptions + reference trees, loaded and checked from the spreadsheet | `nl2wfnet/benchmark.py` | `data/benchmark.json` |
| 8 | evaluation measures + their validation by error injection | `metrics.py`, `labels.py`, `perturb.py` | `results/metric_validation/` |
| 9 | case studies on three key cases (recruitment, OR, loop) | `scripts/m1_case_studies.py` | `results/m1_case_studies/` |
| 10 | 53 automated tests | `tests/test_m1_*.py` | – |

### The intermediate format
Three candidate formats were compared: a list of pairwise dependencies (`a -> b`, `b × c`, `d ∧ f`), a JSON of "flows" in BPMN style, and **process trees**. Process trees were chosen:

| | pairwise dependencies | BPMN-style flows | **process tree (chosen)** |
|---|---|---|---|
| loops, OR | not defined | not in the example | `loop`, `or` |
| always a valid model | no – relations can contradict each other | no – flows can form unsound structures | every valid tree -> sound WF-net |
| easy to validate | hard (global consistency) | medium | local rules per node |
| limitation | – | – | block-structured: some behaviour needs duplicated labels (P01) |

Node types and operators:
```json
{"activity": "submit CV"}                     // action (transition)
{"tau": true}                                 // silent step, used for optional parts
{"op": "seq",  "children": [ ... ]}           // sequence, >= 2 children
{"op": "xor",  "children": [ ... ]}           // exactly one child, >= 2 children
{"op": "and",  "children": [ ... ]}           // all children, any order, >= 2 children
{"op": "or",   "children": [ ... ]}           // any non-empty subset, any order, 2-4 children
{"op": "loop", "children": [do, redo]}        // do, then optionally redo + do again
```
A document is `{"process_name": "...", "tree": <node>}`. Compact notation (used in the spreadsheet): `->( )` seq, `X( )` xor, `+( )` and, `O( )` or, `*( )` loop, `tau`.

Example (inclusive OR, P02):
```json
{"process_name": "business trip",
 "tree": {"op": "seq", "children": [
   {"activity": "submit travel request"}, {"activity": "approve request"},
   {"op": "or", "children": [{"activity": "book flight"}, {"activity": "book hotel"}, {"activity": "rent car"}]},
   {"activity": "submit expense report"}]}}
```

### Stage 2: the algorithm process tree -> WF-net
Each node is translated recursively between an input place and an output place; the whole tree goes between `i` and `o`:

| Node | WF-net pattern |
|---|---|
| action / τ | one visible / silent transition from the input to the output place |
| `seq` | children chained through new intermediate places |
| `xor` | all children share the same input and output place (only one can take the token) |
| `and` | silent split -> one branch (own places) per child -> silent join |
| `loop` | silent entry -> *do* -> either silent exit, or *redo* back to the start of *do*; in its own places |
| `or` | exclusive choice between all non-empty subsets of the children, each subset executed in parallel |

Every block has exactly one entry and one exit, so the result is a **sound WF-net by construction**. This is not assumed: the independent soundness checker verifies it for every net (benchmark, tests).

### Benchmark (20 descriptions)
`data/benchmark_v1.xlsx` is the single source of truth (ID, split, process, operators, description, reference tree in compact notation, number of actions, ambiguity notes). `scripts/m1_build_benchmark.py` parses and checks every row and writes `data/benchmark.json`.

| Construct | Dev (12) | Test (8) | Total |
|---|---|---|---|
| seq | 12 | 8 | 20 |
| xor | 7 | 5 | 12 |
| and | 5 | 3 | 8 |
| or | 3 | 3 | 6 |
| loop | 3 | 4 | 7 |
| optional step (τ) | 1 | 1 | 2 |

Reference WF-nets (from `outputs/benchmark_report.csv`):

| Case | Split | Operators | Actions | Places | Transitions | Reachable states | Traces (≤ 12) | Sound |
|---|---|---|---|---|---|---|---|---|
| P01 | dev | seq, xor, and | 9 | 25 | 24 (8 silent) | 25 | 9 | ✓ |
| P02 | dev | seq, or | 6 | 23 | 23 (8 silent) | 25 | 15 | ✓ |
| P03 | dev | seq, loop | 5 | 7 | 7 (2 silent) | 7 | 4 | ✓ |
| P04 | dev | seq, xor, and | 6 | 9 | 8 (2 silent) | 9 | 3 | ✓ |
| P05 | dev | seq, xor, and | 8 | 11 | 10 (2 silent) | 11 | 4 | ✓ |
| P06 | dev | seq, loop | 6 | 8 | 8 (2 silent) | 8 | 4 | ✓ |
| P07 | dev | seq, or | 7 | 24 | 24 (8 silent) | 26 | 15 | ✓ |
| P08 | dev | seq, xor, tau | 4 | 5 | 5 (1 silent) | 5 | 2 | ✓ |
| P09 | dev | seq, xor, loop | 6 | 7 | 8 (2 silent) | 7 | 8 | ✓ |
| P10 | dev | seq, xor, and | 6 | 9 | 8 (2 silent) | 9 | 4 | ✓ |
| P11 | dev | seq, and, or | 7 | 27 | 26 (10 silent) | 29 | 30 | ✓ |
| P12 | dev | seq, xor | 7 | 6 | 7 (0 silent) | 6 | 3 | ✓ |
| P13 | test | seq, and | 6 | 11 | 8 (2 silent) | 13 | 6 | ✓ |
| P14 | test | seq, xor, loop | 6 | 7 | 8 (2 silent) | 7 | 10 | ✓ |
| P15 | test | seq, or | 6 | 60 | 56 (22 silent) | 76 | 64 | ✓ |
| P16 | test | seq, xor, tau | 5 | 6 | 6 (1 silent) | 6 | 2 | ✓ |
| P17 | test | seq, and, loop | 6 | 11 | 10 (4 silent) | 11 | 8 | ✓ |
| P18 | test | seq, xor, or | 8 | 24 | 25 (8 silent) | 26 | 30 | ✓ |
| P19 | test | seq, xor, loop | 8 | 9 | 10 (2 silent) | 9 | 19 | ✓ |
| P20 | test | seq, xor, and, or, loop | 12 | 32 | 33 (12 silent) | 34 | 68 | ✓ |

Total: 321 places, 314 transitions (100 silent). Duplicated labels occur in P01 (exact recruitment rule) and in the OR cases (subset encoding).

### Case studies on three key cases
From `results/m1_case_studies/case_studies.md`:

1. **Recruitment (P01).** With short letters for the actions (a = submit CV, b/c = screening +/−, d/e = technical interview +/−, f/g = manager interview +/−, h = offer, i = rejection) the reference WF-net allows exactly **9 traces**: `aci`, `abdfh`, `abfdh`, `abdgi`, `abgdi`, `abefi`, `abfei`, `abegi`, `abgei`. **0 of 9** violate a rule of the description (b × c, c -> i, d × e, f × g, offer only after d and f, …); for each of the 4 interview outcome combinations both interview orders are possible.
2. **OR (P02, business trip).** 15 traces: 3 with one booking, 6 with two (each pair in both orders), 6 with all three (all orders) – any non-empty subset, in any order.
3. **Loop (P03, document submission).** Up to the bound of 12 actions the net allows 0, 1, 2 or 3 resubmissions; every resubmission is followed by a new completeness check.
4. **Validator.** A hand-written tree with five format errors gets five precise messages, e.g. `tree: unknown operator 'sequence', use one of ['and', 'loop', 'or', 'seq', 'xor']`.
5. **Soundness is not fidelity.** A plausible but simplified recruitment tree (both interviews in parallel, then `X(make offer, reject candidate)`) is **sound**, but allows 17 traces instead of 9: trace precision **0.53**, recall **1.00**. It permits e.g. `abegh` – an offer after two negative interviews.
6. **Unsound net.** A hand-written WF-net with an AND-split closed by an XOR-join is reported as not sound (no option to complete, no proper completion).

The files in `data/examples/` are written by hand for these checks; they are not LLM outputs.

### Evaluation measures and their validation
Four dimensions, reported separately: **validity**, **soundness**, **structural fidelity** (action F1 after label matching, footprint agreement ->, ←, ‖, #), **behavioural fidelity** (trace precision, recall, F1 up to 12 actions – primary measure).

To check that the measures detect real modelling errors, each typical error was injected into every applicable reference tree (`scripts/m1_validate_metrics.py`; deliberately modified reference trees, not LLM outputs):

| Injected error | Cases | Soundness | Action F1 | Footprint | Trace P | Trace R | Trace F1 |
|---|---|---|---|---|---|---|---|
| none (reference itself) | 20 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| all labels paraphrased | 20 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| AND → SEQ | 8 | 1.00 | 1.00 | 0.84 | 1.00 | 0.53 | 0.67 |
| OR → XOR | 6 | 1.00 | 1.00 | 0.85 | 1.00 | 0.19 | 0.32 |
| OR → AND | 6 | 1.00 | 1.00 | 1.00 | 1.00 | 0.39 | 0.56 |
| XOR → AND | 10 | 1.00 | 1.00 | 0.87 | 0.00 | 0.00 | 0.00 |
| loop removed | 7 | 1.00 | 0.88 | 0.90 | 1.00 | 0.25 | 0.39 |
| one activity removed | 19 | 1.00 | 0.91 | 0.85 | 0.02 | 0.02 | 0.02 |
| two steps swapped | 14 | 1.00 | 1.00 | 0.72 | 0.16 | 0.16 | 0.16 |

**Conclusions**:
* soundness never detects these errors, so it cannot be the only measure;
* trace F1 drops for every control-flow error, so it is the primary measure;
* precision vs. recall shows the direction of the error (too strict -> recall drops, too permissive -> precision drops);
* the footprint cannot distinguish OR from AND, so it is secondary;
* label matching is robust: paraphrasing all labels keeps every score at 1.00.

### Tests (53 for Milestone 1)
| File | Tests | What is guaranteed |
|---|---|---|
| `test_m1_format.py` | 9 | valid trees accepted; 20 kinds of invalid trees rejected with a precise message; JSON Schema agrees with the validator; notation round-trip |
| `test_m1_converter.py` | 12 | every net is a WF-net; block sizes per operator; exact traces for seq, xor, and, or, loop, τ and nested trees; **300 random trees (74 with loops): all sound and the net's traces equal the tree's traces up to 6 actions** |
| `test_m1_soundness.py` | 7 | sound nets accepted; deadlock, tokens left behind, dead transition, unbounded net, non-WF-net all rejected |
| `test_m1_export.py` | 6 | PNML is valid XML with all elements, markings and silent transitions; DOT complete; Graphviz renders; WF-net JSON round-trip and validator messages |
| `test_m1_benchmark.py` | 11 | 20 cases, 12/8 split, every construct in both splits; all references sound; P01 matches the rules of its description; P02 OR, P03 loop, optional steps |
| `test_m1_metrics.py` | 8 | footprint, precision/recall direction, label matching (paraphrases, antonyms, overrides), error injection on all 20 cases |

---

## **Milestone 2 – LLM stage and baseline**

**Goal:** run both pipelines end-to-end with a real LLM on the 12 dev cases, develop the prompt there, then freeze the setup. Both approaches were run with Qwen 2.5 7B (Ollama, local GPU) in 5 prompt versions × 72 generations = 360 dev generations. The final prompt v1.5 and `config.json` are frozen for Milestone 3.

### What was built
| Component | Where | Notes |
|---|---|---|
| Prompts for both approaches | `nl2wfnet/prompts.py` | same 3-step rules, same wording cues, same 4 worked examples (ATM, pizza, gym, car inspection – not in the benchmark); `PROMPT_VERSION = "v1.5"` |
| LLM clients | `nl2wfnet/llm.py` | Ollama (used for all results), any OpenAI-compatible server, manual chat-UI workflow |
| Configurations | `config.json`, `configs/{ollama,openai,manual}.json` | selected with `--config` |
| Generation + repair loop | `nl2wfnet/pipeline.py` | JSON mode; up to 2 repairs for format/structure errors, identical for both approaches; a timeout counts as a failed attempt |
| Run records | `runs/<run>/<approach>/<case>_s<seed>.json` | prompt version, model, seed, every raw answer, validator errors, repairs, tokens, latency |
| Label matching | `nl2wfnet/labels.py` | stemmed token overlap + character similarity, synonyms, antonym guard, manual overrides (`data/label_overrides.json`); every mapping stored in `results/<run>/label_maps.json` |
| Evaluation and report | `nl2wfnet/metrics.py`, `report.py` | 4 dimensions, error taxonomy, paired statistics, tables, figures |
| Prompt export for ChatGPT | `scripts/m2_export_chat_prompts.py` | dev cases only |
| Prompt log | `docs/prompt_log.md` | every version, reason, run and result |
| Tests | `tests/test_m2_*.py` | 9 tests with local fake Ollama / OpenAI servers (no real LLM needed) |

### Models and settings
| Setting | Value | Why |
|---|---|---|
| Model | `qwen2.5:7b` via Ollama (local GPU) | open model, no API cost, fixed version via Ollama tag |
| Alternatives (not used for results) | OpenAI-compatible server (`configs/openai.json`), ChatGPT copy-paste (`configs/manual.json`) | prompt checks and fallback |
| Temperature | 0.5 | variation between seeds, so 3 runs per case are meaningful |
| Seeds | 1, 2, 3 | repeated runs per case and approach |
| Output | JSON mode (`format: json`) | forces syntactically valid JSON |
| Context (`num_ctx`) | 16384 tokens | system prompt + 4 examples (≈ 3 000 tokens for the baseline) + repairs |
| Max. answer (`num_predict`) | 2048 tokens | prevents endless generation |
| Timeout | 600 s, counts as a failed attempt | a hanging request uses one repair instead of stopping the run |
| Repairs | max. 2, only for format/structure errors | same budget for both approaches; soundness is never repaired, it is measured |

### The final prompt (v1.5)
Each request has 10 messages: system prompt → 4 worked examples (user description + expected answer) → task. The user messages are identical for both approaches.

| Part | Proposed (process tree) | Baseline (WF-net) |
|---|---|---|
| Shared rules | Step 1 activities: one per action, label = "verb object", active voice; actors, states and conditions are not activities. Step 2 decisions: a check stays an activity; approved/rejected → one activity per result, no "decide" step. Step 3 control flow: wording cues, explicit loop pattern (do = repeated check, redo = corrections), optional step = xor with τ. | same |
| Answer format | `{"process_name", "activities", "tree"}`, 5 operators with arity rules | `{"process_name", "activities", "places", "transitions", "arcs"}`, how to build each construct, self-check of arcs |
| Worked examples | ATM (loop, OR, optional), pizza (parallel, choice), gym (decision with named results), car inspection (loop) as process trees | the same 4 processes as WF-nets, generated from the trees by our converter |
| Repair message | `Your JSON is not valid: - <validator errors> Fix only these problems, keep all activities, and return the complete corrected JSON object only.` | same |

### Fairness rules
- Same model, temperature, seeds, context size and JSON mode for both approaches.
- Same task description, rules and worked examples (each in its own output format; the WF-net examples are generated from the trees, so both show exactly the same process).
- Repairs are triggered only by format/structure errors – **never by soundness**, which is a measured outcome.
- Prompts were changed only on dev cases; every change is in `docs/prompt_log.md`. Test cases P13–P20 were never used.

### Prompt development (12 dev cases, 72 generations per version)
| Version | Validity P / B | Soundness P / B | Activity F1 P / B | Trace F1 P / B | Trace F1 diff. [95 % CI] | W / T / L | p | Repairs P / B |
|---|---|---|---|---|---|---|---|---|
| v1.1 | 0.944 / 0.139 | 0.944 / 0.083 | 0.821 / 0.120 | 0.283 / 0.032 | +0.251 [+0.059, +0.467] | 7 / 4 / 1 | 0.039 | 0.4 / 2.0 |
| v1.2 | 0.861 / 0.222 | 0.861 / 0.139 | 0.703 / 0.194 | 0.314 / 0.015 | +0.299 [+0.084, +0.539] | 7 / 5 / 0 | 0.016 | 0.4 / 1.9 |
| v1.3 | 0.778 / 0.194 | 0.778 / 0.083 | 0.651 / 0.156 | 0.309 / 0.004 | +0.305 [+0.108, +0.526] | 6 / 6 / 0 | 0.031 | 0.6 / 1.9 |
| v1.4 | 0.861 / 0.222 | 0.861 / 0.111 | 0.760 / 0.180 | 0.308 / 0.000 | +0.308 [+0.107, +0.533] | 9 / 3 / 0 | 0.004 | 0.5 / 1.8 |
| v1.5 | 0.889 / 0.444 | 0.889 / 0.194 | 0.816 / 0.417 | 0.407 / 0.060 | +0.347 [+0.088, +0.598] | 8 / 2 / 2 | 0.049 | 0.2 / 1.7 |

P = proposed, B = baseline; means over 36 runs per approach; paired test over the 12 cases. v1.0 has no result: its first run stopped after a request timeout and was restarted with the v1.1 settings (run `dev_v1`). Rule changes in v1.2–v1.4 did not move trace F1 (0.28–0.31); the explicit loop pattern in v1.5 raised it to 0.41. **v1.5 was selected and frozen** (best trace F1 for both approaches).

### Dev results with the final prompt (run `dev_v1_5`)
From `results/dev_v1_5/summary.md` (client `ollama:qwen2.5:7b`, prompt v1.5, 12 cases, 3 runs per case and approach). Mean ± SD over 36 runs; paired comparison over cases (runs averaged per case first), exact two-sided Wilcoxon signed-rank test, 95 % bootstrap CI.

| Measure | Proposed (tree) | Baseline (direct) | Mean diff [95 % CI] | W / T / L | p |
|---|---|---|---|---|---|
| Validity | 0.889 ± 0.314 | 0.444 ± 0.497 | +0.444 [+0.139, +0.694] | 11 / 0 / 1 | 0.023 |
| Soundness | 0.889 ± 0.314 | 0.194 ± 0.396 | +0.694 [+0.389, +0.917] | 11 / 0 / 1 | 0.003 |
| Activity F1 | 0.816 ± 0.315 | 0.417 ± 0.471 | +0.399 [+0.103, +0.651] | 11 / 0 / 1 | 0.015 |
| Footprint similarity | 0.764 ± 0.301 | 0.164 ± 0.312 | +0.600 [+0.344, +0.811] | 11 / 0 / 1 | 0.003 |
| Trace precision | 0.409 ± 0.424 | 0.056 ± 0.196 | +0.353 [+0.092, +0.615] | 8 / 2 / 2 | 0.041 |
| Trace recall | 0.474 ± 0.409 | 0.069 ± 0.240 | +0.405 [+0.131, +0.669] | 8 / 2 / 2 | 0.020 |
| **Trace F1 (primary)** | 0.407 ± 0.404 | 0.060 ± 0.208 | +0.347 [+0.088, +0.598] | 8 / 2 / 2 | 0.049 |
| Repairs used | 0.2 | 1.7 | – | – | – |
| Output length (chars) | 499.6 | 986.1 | – | – | – |

**Trace F1 per operator** (cases containing the operator):

| Operator | Cases | Proposed | Baseline |
|---|---|---|---|
| xor | 7 | 0.266 | 0.056 |
| and | 5 | 0.508 | 0.000 |
| or | 3 | 0.908 | 0.000 |
| loop | 3 | 0.100 | 0.111 |
| τ (optional step) | 1 | 0.000 | 0.389 |

**Trace F1 per case:**

| Case | Operators | Proposed | Baseline | |
|---|---|---|---|---|
| P01 | seq, xor, and | 0.000 | 0.000 | tie |
| P02 | seq, or | 0.724 | 0.000 | win |
| P03 | seq, loop | 0.014 | 0.333 | loss |
| P04 | seq, xor, and | 0.762 | 0.000 | win |
| P05 | seq, xor, and | 0.111 | 0.000 | win |
| P06 | seq, loop | 0.286 | 0.000 | win |
| P07 | seq, or | 1.000 | 0.000 | win |
| P08 | seq, xor, tau | 0.000 | 0.389 | loss |
| P09 | seq, xor, loop | 0.000 | 0.000 | tie |
| P10 | seq, xor, and | 0.667 | 0.000 | win |
| P11 | seq, and, or | 1.000 | 0.000 | win |
| P12 | seq, xor | 0.321 | 0.000 | win |

**Error types** (share of runs; a run can have several):

| Error type | Proposed | Baseline |
|---|---|---|
| correct | 22% | 3% |
| extra / unmatched activity | 31% | 17% |
| invalid after repairs | 11% | 56% |
| missing activity | 28% | 8% |
| unsound: cannot always complete | 0% | 25% |
| unsound: dead transition | 0% | 25% |
| wrong control flow | 25% | 11% |

### Interpretation
- **Validity and soundness (H1, H2 on dev):** 89 % of the process trees are valid, and every valid tree is a sound WF-net (validity = soundness). Direct generation gives 44 % valid answers, but only 19 % sound nets: most valid direct nets cannot always complete or contain dead transitions.
- **Behaviour (H3 on dev):** trace F1 0.407 vs. 0.060, difference +0.347 [+0.088, +0.598], 8 wins / 2 ties / 2 losses, p = 0.049. The difference was significant (p < 0.05) in every prompt version.
- **Where the tree helps most:** inclusive OR (0.91 vs. 0.00) and parallel branches (0.51 vs. 0.00) – the converter builds these structures, while the directly generated nets never reproduced them.
- **What remains hard:** loops (0.10 vs. 0.11) and the optional step (P08: 0.00 vs. 0.39); losses in P03 and P08; P01 is 0 for both (the exact model needs one branch per combination of interview outcomes).
- **Error profile:** the proposed approach fails on content (missing / extra activities, wrong control flow), the baseline on structure (invalid or unsound nets).

### Tests (9 for Milestone 2)
| File | Tests | What is guaranteed |
|---|---|---|
| `test_m2_clients.py` | 5 | fake OpenAI server: request body, seed, temperature, JSON mode, key read from the environment; a key in the config is rejected; manual workflow writes the prompt and reads the answer; all config files build a client; identical user messages and valid worked examples in both formats |
| `test_m2_pipeline.py` | 4 | JSON extraction from fenced answers; fake Ollama server; repair loop sends validator errors back and accepts the fix; repair budget of 2 respected |

---

## **Milestone 3 - Experiment and results (final)**

**Goal:** answer the research question once, with the frozen setup (prompt v1.5 + `config.json`), on unseen cases.

### Protocol
- **8 test cases × 3 seeds × 2 approaches = 48 generations** with a frozen setup, `python scripts/m3_experiment.py --run-name final_v1`.
- The script stores a hash of the config + prompts in `runs/final_v1/FROZEN.txt`.
- Unit of analysis: the **case** (runs averaged per case).
- Primary measure: **trace F1** (H3). Secondary: validity (H1), soundness (H2), activity F1, footprint, repairs, output length.
- Statistics: mean difference with 95 % bootstrap CI, exact two-sided Wilcoxon signed-rank test, wins/ties/losses. With 8 cases the power is low: effect sizes and intervals matter more than p-values.
- Analysis per operator, per case, and by automatic error type (invalid, missing/extra activity, unsound, wrong control flow).

### Outputs (`results/final_v1/`)
`summary.md` (all tables), `per_run.csv`, `per_case.csv`, `paired_tests.csv`, `per_operator.csv`, `label_maps.json`, `fig_main_measures.png`, `fig_per_operator.png`, `fig_per_case.png`.

A negative or mixed result is a valid answer and will be reported as such.

---

## **Project structure**
```
natural_lang_WFnet_project/
├── README.md, requirements.txt, config.json
├── configs/             # ollama.json, openai.json, manual.json
├── nl2wfnet/            # library
│   ├── tree.py          # process-tree JSON, validation, compact notation
│   ├── wfnet.py         # Petri nets, tree -> WF-net, WF-net JSON, PNML/DOT
│   ├── analysis.py      # soundness, bounded traces, footprints
│   ├── benchmark.py     # spreadsheet -> benchmark.json
│   ├── prompts.py       # prompts for both approaches (v1.5, frozen)
│   ├── llm.py           # Ollama / OpenAI-compatible / manual
│   ├── pipeline.py      # prompt -> LLM -> validate -> repair
│   ├── labels.py        # label matching
│   ├── metrics.py       # evaluation dimensions
│   ├── perturb.py       # error injection
│   ├── stats.py         # Wilcoxon exact test, bootstrap CI
│   └── report.py        # tables and figures
├── scripts/             # m1_*, m2_*, m3_*, generate.py, evaluate.py
├── tests/               # test_m1_*.py (53), test_m2_*.py (9), test_m3_stats.py (2), run_all.py
├── data/                # benchmark_v1.xlsx, benchmark.json, label_overrides.json, examples/ (hand-written)
├── docs/                # prompt_log.md (all prompt versions and results)
├── schema/              # process_tree.schema.json
├── outputs/reference/   # PNML, DOT, PNG of 20 reference WF-nets + benchmark_report.csv
├── runs/                # raw LLM records (created by scripts)
└── results/             # metric_validation/, m1_case_studies/, dev_v1 … dev_v1_5/
```

## **Reproducing the Experiments**

### Milestone 1
```bash
pip install -r requirements.txt       # Graphviz binary optional (PNG images)
python scripts/m1_run_all.py          # tests + the three scripts below
python scripts/m1_build_benchmark.py  # spreadsheet -> benchmark.json, 20 WF-nets in outputs/reference/
python scripts/m1_validate_metrics.py # results/metric_validation/
python scripts/m1_case_studies.py     # results/m1_case_studies/
```

### Milestone 2
`m2_develop.py` = `generate.py` + `evaluate.py` in one step. Use one of them, not both.

#### Ollama (setup used for all results)
```bash
ollama pull qwen2.5:7b                     # needs a running Ollama server (GPU recommended)
python tests/run_all.py m2                 # 9 tests
python scripts/m2_develop.py --run-name dev_v1_5    # final prompt v1.5, 72 generations
```
Outputs: `runs/dev_v1_5/` (raw records) and `results/dev_v1_5/` (`summary.md`, `per_run.csv`, `per_case.csv`, `paired_tests.csv`, `per_operator.csv`, `label_maps.json`, 3 figures). A stopped run can be restarted with the same command; finished generations are skipped.

#### OpenAI-compatible server
```bash
$env:OPENAI_API_KEY="..."                # Use correct API key
python scripts/m2_develop.py --config configs/openai.json --run-name dev_openai_v1
```

#### Manual (ChatGPT copy-paste)
```bash
python scripts/m2_develop.py --config configs/manual.json --run-name dev_manual_v1
# -> prompts appear in manual/prompts/; paste each into ChatGPT, save the JSON answer under the
#    same name with .json in manual/responses/, run the same command again (repeat until complete)
```

### Milestone 3
```bash
python scripts/m3_experiment.py --run-name final_v1        # add --config configs/... if not Ollama
```

## **References**
- W. M. P. van der Aalst, *Process Mining: Data Science in Action*, 2nd ed., Springer, 2016 – process trees, WF-nets, soundness, footprints.
- J. Carmona, B. van Dongen, A. Solti, M. Weidlich, *Conformance Checking: Relating Processes and Models*, Springer, 2018.
- J. Neuberger, L. Ackermann, H. van der Aa, S. Jablonski, "A Universal Prompting Strategy for Extracting Process Model Information from Natural Language Text Using LLMs", 2024 – [arXiv:2407.18540](https://arxiv.org/abs/2407.18540).
- H. Kourani, A. Berti, D. Schuster, W. M. P. van der Aalst, "Process Modeling with Large Language Models", 2024 – [arXiv:2403.07541](https://arxiv.org/abs/2403.07541).
- H. Kourani, A. Berti, D. Schuster, W. M. P. van der Aalst, "Evaluating Large Language Models on Business Process Modeling", *Software and Systems Modeling*, 2025 – [arXiv:2412.00023](https://arxiv.org/abs/2412.00023).
