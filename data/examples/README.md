# Hand-written examples used in Milestone 1

These files are written by hand to demonstrate and test the checks. They are **not** LLM outputs.

| File | Content | Used for |
|---|---|---|
| `invalid_tree.json` | process tree with 5 deliberate format errors (unknown operator, loop with one child, extra key, xor with one child, empty label) | validator messages |
| `P01_simplified_tree.json` | a plausible but too simple tree for the recruitment case: both interviews in parallel, then `X(make offer, reject candidate)` | soundness vs. fidelity |
| `unsound_wfnet.json` | WF-net with an AND-split closed by an XOR-join (tokens are left behind) | soundness checker |
