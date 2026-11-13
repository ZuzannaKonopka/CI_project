# **PROMPTS USED IN EXPERIMENTS**
In this file we have full prompt that was used to each iteration.


## **PROMPT v1.0 and v1.1**
```python

"""Prompts for both approaches (version tracked in PROMPT_VERSION).

Fairness rules
--------------
* Both approaches get the same task description, the same control-flow
  knowledge (what sequence / choice / parallel / inclusive OR / loop mean and
  how to express them) and the same two worked examples (ATM, pizza) - each in
  its own output format. Neither example is part of the benchmark.
* Both approaches get the same number of repair attempts; repair is triggered
  only by format/structure errors, never by soundness (soundness is measured).
Change prompts only on the dev split and record every change in docs/prompt_log.md.
"""

import json


PROMPT_VERSION = "v1.1"


COMMON_RULES = """Modelling rules:

Activity identification:
- An activity is an explicitly described action performed by a process participant.
- Represent activities using short verb phrases taken from the process description,
  e.g. "submit application", "check stock", "send confirmation".
- Include every explicitly described action that changes the process state or
  represents work performed by a participant.
- Do not model decision conditions, states, properties or outcomes as activities
  unless the text explicitly describes an action.
- For example, "if the customer is at home" is a condition, not an activity.
  "Pay" is an activity, while "the customer is not at home" is not.
- Do not invent activities that are not described in the text.
- Do not omit explicitly described activities.
- Use exactly the same label for the same activity everywhere.

Control-flow identification:
- "then", "after that", "finally" -> sequence.
- "if ... otherwise", "either ... or" -> exclusive choice (XOR).
- "both", "in parallel", "while", "meanwhile" -> parallel execution (AND),
  when the described activities can proceed independently.
- "and/or", "at least one of" -> inclusive choice (OR).
- "again", "repeat", "until" -> loop, when an activity or group of activities
  is repeated.
- "optionally", "if needed" -> optional activity, represented as a choice
  between performing the activity and skipping it.

General rules:
- Preserve the order of activities specified in the description.
- Distinguish between a condition that controls the flow and an activity
  performed after that condition.
- Do not introduce additional branches or repetitions unless they are supported
  by the text.
- Use the simplest process structure that faithfully represents the description.
- If the description is ambiguous, prefer the most conservative interpretation."""


STRUCTURED_SYSTEM = """You convert a textual process description into a PROCESS TREE in JSON.

Modelling procedure:
1. Identify all explicitly described activities.
2. Identify the control-flow relations between these activities.
3. Construct a process tree that represents the described process.
4. Check that all activities are included exactly where required and that
   the control flow matches the description.

Node types:
- activity: {"activity": "<verb phrase>"}
- silent step: {"tau": true}
  (only to represent skipping an optional activity)
- operator: {"op": "<op>", "children": [<node>, <node>, ...]}

Operators:
- "seq": children happen one after another, in the given order (>= 2 children).
- "xor": exactly one child happens (>= 2 children).
- "and": all children happen, in any order or at the same time (>= 2 children).
- "or": one or more children happen, any non-empty combination (2-4 children).
- "loop": exactly 2 children [do, redo]. The "do" part happens first.
  Then the process either ends or executes "redo" followed by "do" again.

Construction rules:
- Use "seq" for activities that must happen in a specified order.
- Use "xor" for mutually exclusive alternatives.
- Use "and" when all branches must be executed.
- Use "or" when at least one of several branches must be executed.
- Use "xor" with a {"tau": true} child for an optional activity.
- Use "loop" only when the description explicitly indicates repetition.
- Do not represent decision conditions as activity nodes.
- Do not duplicate activities unless the process description requires repetition
  or the process structure requires separate occurrences.

""" + COMMON_RULES + """

Return only one JSON object:
{"process_name": "<short name>", "tree": <node>}"""


BASELINE_SYSTEM = """You convert a textual process description into a WORKFLOW NET (WF-net) in JSON.

A WF-net is a Petri net with places (states) and transitions (activities).

Structural requirements:
- Exactly one start place "i" (no incoming arcs).
- Exactly one end place "o" (no outgoing arcs).
- Every place and transition must lie on a path from "i" to "o".
- Arcs connect a place to a transition or a transition to a place.
  Never connect two places or two transitions directly.
- A transition with "label": null is silent. Use silent transitions
  for control-flow routing, splits, joins, skips and loop control.
- Every explicitly described activity must be represented by a transition
  with its corresponding label.

Modelling procedure:
1. Identify all explicitly described activities.
2. Identify the control-flow relations between these activities.
3. Construct a WF-net that represents the described process.
4. Check that the net contains all required activities and that its structure
   and control flow match the description.

How to express control flow:
- Sequence: connect activities in the required order using intermediate places.
- Exclusive choice (XOR): use alternative branches so that exactly one
  alternative can be executed.
- Parallel execution (AND): use a silent split to activate all branches
  and a silent join to synchronize their completion.
- Optional activity: model a choice between executing the activity
  and skipping it using a silent transition.
- Loop: after the "do" part, provide a way to either exit or execute
  the "redo" part and return to the beginning of the repeated part.
- Inclusive choice (OR): represent all non-empty combinations of selected
  branches. Each combination must execute the selected activities in parallel.
- Do not model decision conditions as activity transitions.
- Use silent transitions only for control flow, not as substitutes
  for explicitly described activities.
- Avoid unnecessary places, transitions and duplicated activity transitions.
- Ensure that every branch can reach the end place "o".

""" + COMMON_RULES + """

Return only one JSON object:
{"process_name": "<short name>",
 "places": ["i", ..., "o"],
 "transitions": [
   {"id": "t1", "label": "<verb phrase>"},
   {"id": "t2", "label": null}
 ],
 "arcs": [["i", "t1"], ["t1", "p1"], ...]}"""


EXAMPLES = [
    {
        "text": (
            "A customer inserts a card into the ATM and enters the PIN. "
            "If the PIN is wrong, an error message is shown and the customer "
            "enters the PIN again. After a correct PIN, the customer withdraws "
            "cash, checks the balance and/or tops up a phone - at least one "
            "of these. Optionally, a receipt is printed. Finally, the card "
            "is returned."
        ),
        "structured": {
            "process_name": "ATM withdrawal",
            "activities": [
                "insert card",
                "enter PIN",
                "show error message",
                "withdraw cash",
                "check balance",
                "top up phone",
                "print receipt",
                "return card",
            ],
            "tree": {
                "op": "seq",
                "children": [
                    {"activity": "insert card"},
                    {
                        "op": "loop",
                        "children": [
                            {"activity": "enter PIN"},
                            {"activity": "show error message"},
                        ],
                    },
                    {
                        "op": "or",
                        "children": [
                            {"activity": "withdraw cash"},
                            {"activity": "check balance"},
                            {"activity": "top up phone"},
                        ],
                    },
                    {
                        "op": "xor",
                        "children": [
                            {"activity": "print receipt"},
                            {"tau": True},
                        ],
                    },
                    {"activity": "return card"},
                ],
            },
        },
        "baseline": {
            "process_name": "ATM withdrawal",
            "activities": [
                "insert card",
                "enter PIN",
                "show error message",
                "withdraw cash",
                "check balance",
                "top up phone",
                "print receipt",
                "return card",
            ],
            "places": [
                "i", "o", "p0", "p1", "p2", "p3", "p4", "p5",
                "p6", "p7", "p8", "p9", "p10", "p11", "p12",
                "p13", "p14", "p15", "p16", "p17", "p18", "p19",
                "p20", "p21", "p22", "p23",
            ],
            "transitions": [
                {"id": "t0", "label": "insert card"},
                {"id": "t1", "label": None},
                {"id": "t2", "label": None},
                {"id": "t3", "label": "enter PIN"},
                {"id": "t4", "label": "show error message"},
                {"id": "t5", "label": "withdraw cash"},
                {"id": "t6", "label": "check balance"},
                {"id": "t7", "label": "top up phone"},
                {"id": "t8", "label": None},
                {"id": "t9", "label": None},
                {"id": "t10", "label": "withdraw cash"},
                {"id": "t11", "label": "check balance"},
                {"id": "t12", "label": None},
                {"id": "t13", "label": None},
                {"id": "t14", "label": "withdraw cash"},
                {"id": "t15", "label": "top up phone"},
                {"id": "t16", "label": None},
                {"id": "t17", "label": None},
                {"id": "t18", "label": "check balance"},
                {"id": "t19", "label": "top up phone"},
                {"id": "t20", "label": None},
                {"id": "t21", "label": None},
                {"id": "t22", "label": "withdraw cash"},
                {"id": "t23", "label": "check balance"},
                {"id": "t24", "label": "top up phone"},
                {"id": "t25", "label": "print receipt"},
                {"id": "t26", "label": None},
                {"id": "t27", "label": "return card"},
            ],
            "arcs": [
                ["i", "t0"], ["t0", "p0"], ["p0", "t1"],
                ["t1", "p2"], ["p2", "t3"], ["t3", "p3"],
                ["p3", "t4"], ["t4", "p2"], ["p3", "t2"],
                ["t2", "p1"], ["p1", "t5"], ["t5", "p4"],
                ["p1", "t6"], ["t6", "p4"], ["p1", "t7"],
                ["t7", "p4"], ["p1", "t8"], ["t9", "p4"],
                ["t8", "p5"], ["p6", "t9"], ["p5", "t10"],
                ["t10", "p6"], ["t8", "p7"], ["p8", "t9"],
                ["p7", "t11"], ["t11", "p8"], ["p1", "t12"],
                ["t13", "p4"], ["t12", "p9"], ["p10", "t13"],
                ["p9", "t14"], ["t14", "p10"], ["t12", "p11"],
                ["p12", "t13"], ["p11", "t15"], ["t15", "p12"],
                ["p1", "t16"], ["t17", "p4"], ["t16", "p13"],
                ["p14", "t17"], ["p13", "t18"], ["t18", "p14"],
                ["t16", "p15"], ["p16", "t17"], ["p15", "t19"],
                ["t19", "p16"], ["p1", "t20"], ["t21", "p4"],
                ["t20", "p17"], ["p18", "t21"], ["p17", "t22"],
                ["t22", "p18"], ["t20", "p19"], ["p20", "t21"],
                ["p19", "t23"], ["t23", "p20"], ["t20", "p21"],
                ["p22", "t21"], ["p21", "t24"], ["t24", "p22"],
                ["p4", "t25"], ["t25", "p23"], ["p4", "t26"],
                ["t26", "p23"], ["p23", "t27"], ["t27", "o"],
            ],
        },
    },
    {
        "text": (
            "A customer orders a pizza by phone. The kitchen bakes the pizza "
            "while the cashier prepares the bill. Then a courier delivers "
            "the pizza. If the customer is at home, the customer pays; "
            "otherwise, the pizza is taken back to the restaurant."
        ),
        "structured": {
            "process_name": "pizza delivery",
            "activities": [
                "order pizza",
                "bake pizza",
                "prepare bill",
                "deliver pizza",
                "pay",
                "take pizza back",
            ],
            "tree": {
                "op": "seq",
                "children": [
                    {"activity": "order pizza"},
                    {
                        "op": "and",
                        "children": [
                            {"activity": "bake pizza"},
                            {"activity": "prepare bill"},
                        ],
                    },
                    {"activity": "deliver pizza"},
                    {
                        "op": "xor",
                        "children": [
                            {"activity": "pay"},
                            {"activity": "take pizza back"},
                        ],
                    },
                ],
            },
        },
        "baseline": {
            "process_name": "pizza delivery",
            "activities": [
                "order pizza",
                "bake pizza",
                "prepare bill",
                "deliver pizza",
                "pay",
                "take pizza back",
            ],
            "places": ["i", "o", "p0", "p1", "p2", "p3", "p4", "p5", "p6"],
            "transitions": [
                {"id": "t0", "label": "order pizza"},
                {"id": "t1", "label": None},
                {"id": "t2", "label": None},
                {"id": "t3", "label": "bake pizza"},
                {"id": "t4", "label": "prepare bill"},
                {"id": "t5", "label": "deliver pizza"},
                {"id": "t6", "label": "pay"},
                {"id": "t7", "label": "take pizza back"},
            ],
            "arcs": [
                ["i", "t0"], ["t0", "p0"], ["p0", "t1"],
                ["t2", "p1"], ["t1", "p2"], ["p3", "t2"],
                ["p2", "t3"], ["t3", "p3"], ["t1", "p4"],
                ["p5", "t2"], ["p4", "t4"], ["t4", "p5"],
                ["p1", "t5"], ["t5", "p6"], ["p6", "t6"],
                ["t6", "o"], ["p6", "t7"], ["t7", "o"],
            ],
        },
    },
]


REPAIR_TEMPLATE = (
    "Your JSON is not valid:\n- {errors}\n"
    "Fix these problems and return the complete corrected JSON object only."
)


def build_messages(approach, description):
    """Build system, worked-example and task messages for one approach."""
    if approach not in ("structured", "baseline"):
        raise ValueError(approach)

    system = STRUCTURED_SYSTEM if approach == "structured" else BASELINE_SYSTEM
    messages = [{"role": "system", "content": system}]

    for example in EXAMPLES:
        messages.append({
            "role": "user",
            "content": "Process description:\n" + example["text"],
        })

        # "activities" is test metadata, not part of the model output schema.
        expected_answer = {
            key: value
            for key, value in example[approach].items()
            if key != "activities"
        }

        messages.append({
            "role": "assistant",
            "content": json.dumps(expected_answer, ensure_ascii=False),
        })

    messages.append({
        "role": "user",
        "content": "Process description:\n" + description,
    })

    return messages


def repair_message(errors, max_errors=8):
    return REPAIR_TEMPLATE.format(errors="\n- ".join(errors[:max_errors]))


def render_for_chat_ui(approach, description):
    """One self-contained text block to paste into a chat UI (e.g. ChatGPT)."""
    parts = []
    for message in build_messages(approach, description):
        tag = {
            "system": "INSTRUCTIONS",
            "user": "USER",
            "assistant": "EXPECTED ANSWER",
        }[message["role"]]
        parts.append(f"### {tag}\n{message['content']}")

    parts.append("### Answer for the last process description (JSON only):")
    return "\n\n".join(parts)

```

=======================================================================================
## **PROMPT v1.2**

```python
"""Prompts for both approaches (version tracked in PROMPT_VERSION).

Fairness rules
--------------
* Both approaches get the same task description, the same modelling rules,
  the same control-flow knowledge and the same four worked examples
  (ATM, pizza, gym membership, car inspection) - each in its own output format.
  None of the examples is part of the benchmark.
* The WF-net examples are generated from the process-tree examples by our own
  converter (renumbered in flow order), so both formats show exactly the same process.
* Both approaches first list the activities ("activities"), then build the model.
* Both approaches get the same number of repair attempts; repair is triggered
  only by format/structure errors, never by soundness (soundness is measured).
Change prompts only on the dev split and record every change in docs/prompt_log.md.
"""
import json
from collections import deque

from .tree import parse_tree, parse_tree_string
from .wfnet import tree_to_wfnet

PROMPT_VERSION = "v1.2"

COMMON_RULES = """Step 1 - list the activities ("activities"):
- One activity for every action in the text, in the order of the text. Do not invent or omit actions.
- Label = "<verb> <object>" in active voice and base form, using the words of the text,
  without the actor and without articles: "the invoice is sent by the shop" -> "send invoice",
  "the bank checks the client's credit history" -> "check credit history".
- Use exactly the same label every time the same activity occurs.
- NOT activities: actors, states and conditions ("the items are in stock", "the documents are
  complete", "when both are ready"), waiting, and the start or end of the process.

Step 2 - decisions:
- "X checks whether ... ; if yes ... otherwise ..." -> keep "check ..." as an activity; the branches
  start directly with their first action (no activity for the condition itself).
- "X decides / the request is approved or rejected / the result is positive or negative" -> one
  activity per named result ("approve loan" / "reject loan", "screening positive" /
  "screening negative") and NO separate "decide" or "evaluate" activity.

Step 3 - control flow:
- "then", "after that", "finally" -> sequence.
- "if ... otherwise", "either ... or" -> exclusive choice (exactly one branch).
- "in any order", "while", "meanwhile", "both ... and ... independently" -> parallel (all branches).
  Use parallel ONLY with such wording; otherwise keep the order of the text.
- "and/or", "at least one of", "one, two or all" -> inclusive choice (one or more branches).
- "again", "repeat", "until", "is checked again" -> loop with two parts:
  do   = the step that is repeated (usually the check or test itself),
  redo = the corrective steps done between two repetitions (in their order).
  Typical text: "X is checked; if a problem is found, A and B are done and X is checked again;
  when X is fine, C follows" -> loop(do = X, redo = A then B), then C.
  The steps before the loop and after it are NOT part of the loop. Do not create activities for the
  loop condition or for its outcome ("documents complete", "changes requested", "defects found",
  "code approved", "claim complete").
- "optionally", "can also" -> exclusive choice between the step and skipping it
  (the skip has no label and is NOT an activity in the activities list).
Every activity from Step 1 must appear in the model, and no other activity."""

STRUCTURED_SYSTEM = """You convert a textual process description into a PROCESS TREE in JSON.

Node types:
- activity:    {"activity": "<label from the activities list>"}
- silent step: {"tau": true}   (exactly this, no other keys; only for skipping:
               "optionally X" -> {"op": "xor", "children": [{"activity": "X"}, {"tau": true}]})
- operator:    {"op": "<op>", "children": [<node>, <node>, ...]}

Operators:
- "seq":  children happen one after another, in the given order (>= 2 children)
- "xor":  exactly one child happens (>= 2 children)
- "and":  all children happen, in any order (>= 2 children)
- "or":   one or more children happen, any non-empty combination (2-4 children)
- "loop": exactly 2 children [do, redo]: "do" happens; then either the loop ends,
          or "redo" happens and "do" happens again (repeatable)
          Pattern: {"op": "loop", "children": [X, {"op": "seq", "children": [A, B]}]}

""" + COMMON_RULES + """

Return only one JSON object:
{"process_name": "<short name>", "activities": ["<label>", ...], "tree": <node>}"""

BASELINE_SYSTEM = """You convert a textual process description into a WORKFLOW NET (WF-net) in JSON.

A WF-net is a Petri net with places (states) and transitions (activities):
- exactly one start place "i" (no incoming arcs) and one end place "o" (no outgoing arcs);
- name the other places "p1", "p2", ... and the transitions "t1", "t2", ... in the order of the flow;
- every place and transition lies on a path from "i" to "o";
- every transition has at least one input place and at least one output place;
- arcs connect a place to a transition or a transition to a place (never place-place or transition-transition);
- a transition with "label": null is silent (used for splits, joins, skips and loop entry/exit).

How to express control flow:
- sequence: chain transitions through intermediate places;
- exclusive choice: alternative transitions share the same input place and the same output place;
- parallel: a silent split transition puts tokens into one place per branch; a silent join waits for all branches;
- optional step: a silent transition as an alternative to the step;
- loop: place before "do" -> "do" -> place after "do"; from that place either a silent exit transition
  continues the process, or the "redo" transitions lead back to the place before "do"
  (the loop is entered through a silent transition);
- inclusive choice (one or more of A, B, C): an exclusive choice between all non-empty combinations,
  each combination executed in parallel (labels may then appear in several transitions).

""" + COMMON_RULES + """

Before answering, check: every place except "i" has an incoming arc, every place except "o" has an
outgoing arc, and every id used in "arcs" is listed in "places" or "transitions".

Return only one JSON object:
{"process_name": "<short name>",
 "activities": ["<label>", ...],
 "places": ["i", "p1", ..., "o"],
 "transitions": [{"id": "t1", "label": "<label>"}, {"id": "t2", "label": null}, ...],
 "arcs": [["i", "t1"], ["t1", "p1"], ...]}"""

# Worked examples: (process name, description, activities, process tree in compact notation)
_EXAMPLE_SOURCES = [
    ("ATM withdrawal",
     "A customer inserts a card into the ATM and enters the PIN. If the PIN is wrong, an error message is "
     "shown and the customer enters the PIN again. After a correct PIN, the customer withdraws cash, checks "
     "the balance and/or tops up a phone - at least one of these. Optionally, a receipt is printed. "
     "Finally, the card is returned.",
     ["insert card", "enter PIN", "show error message", "withdraw cash", "check balance", "top up phone",
      "print receipt", "return card"],
     "->(insert card, *(enter PIN, show error message), O(withdraw cash, check balance, top up phone), "
     "X(print receipt, tau), return card)"),
    ("pizza delivery",
     "A customer orders a pizza by phone. The kitchen bakes the pizza while the cashier prepares the bill. "
     "Then a courier delivers the pizza. If the customer is at home, the customer pays; otherwise, the pizza "
     "is taken back to the restaurant.",
     ["order pizza", "bake pizza", "prepare bill", "deliver pizza", "pay", "take pizza back"],
     "->(order pizza, +(bake pizza, prepare bill), deliver pizza, X(pay, take pizza back))"),
    ("gym membership",
     "A visitor fills in a membership form at the gym. The manager then decides on the application: it is "
     "either approved or rejected. If it is rejected, the visitor is informed by e-mail. If it is approved, "
     "the visitor pays the first fee; after that, a locker is assigned and a key card is printed, in any order.",
     ["fill in membership form", "reject membership", "inform visitor", "approve membership", "pay first fee",
      "assign locker", "print key card"],
     "->(fill in membership form, X(->(reject membership, inform visitor), "
     "->(approve membership, pay first fee, +(assign locker, print key card))))"),
    ("car inspection",
     "A driver brings the car to a technical inspection, and the inspector tests the car. If defects are "
     "found, the driver repairs the defects and brings the car back, and the inspector tests it again. "
     "When the car passes the test, the inspector issues a certificate.",
     ["bring car to inspection", "test car", "repair defects", "bring car back", "issue certificate"],
     "->(bring car to inspection, *(test car, ->(repair defects, bring car back)), issue certificate)"),
]


def _readable_wfnet(tree):
    """WF-net of a tree from our converter, renamed in flow order: i, p1, p2, ..., o and t1, t2, ..."""
    net = tree_to_wfnet(parse_tree(tree))
    succ = {}
    for s, t in net.arcs:
        succ.setdefault(s, []).append(t)
    order, seen, queue = [], {"i"}, deque(["i"])
    while queue:
        n = queue.popleft()
        order.append(n)
        for m in succ.get(n, []):
            if m not in seen:
                seen.add(m)
                queue.append(m)
    pmap, tmap = {"i": "i", "o": "o"}, {}
    for n in order:
        if n in net.transitions:
            tmap[n] = f"t{len(tmap) + 1}"
        elif n not in pmap:
            pmap[n] = f"p{len(pmap) - 1}"
    ren = {**pmap, **tmap}
    places = ["i"] + [pmap[n] for n in order if n in pmap and n not in ("i", "o")] + ["o"]
    transitions = [{"id": tmap[n], "label": net.transitions[n]} for n in order if n in tmap]
    arcs = []
    for n in order:
        if n in tmap:
            arcs += [[ren[s], tmap[n]] for s, t in net.arcs if t == n]
            arcs += [[tmap[n], ren[t]] for s, t in net.arcs if s == n]
    return {"places": places, "transitions": transitions, "arcs": arcs}


def _build_examples():
    out = []
    for name, text, acts, notation in _EXAMPLE_SOURCES:
        tree = parse_tree_string(notation)
        out.append({"text": text,
                    "structured": {"process_name": name, "activities": acts, "tree": tree},
                    "baseline": {"process_name": name, "activities": acts, **_readable_wfnet(tree)}})
    return out


EXAMPLES = _build_examples()

REPAIR_TEMPLATE = ("Your JSON is not valid:\n- {errors}\n"
                   "Fix only these problems, keep all activities, and return the complete corrected JSON object only.")


def _answer(obj):
    """Compact JSON, one top-level key per line (easier to imitate for small models)."""
    return "{" + ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in obj.items()) + "}"


def build_messages(approach, description):
    """Chat messages (system + worked examples + task) for 'structured' or 'baseline'."""
    if approach not in ("structured", "baseline"):
        raise ValueError(approach)
    system = STRUCTURED_SYSTEM if approach == "structured" else BASELINE_SYSTEM
    msgs = [{"role": "system", "content": system}]
    for ex in EXAMPLES:
        msgs.append({"role": "user", "content": "Process description:\n" + ex["text"]})
        msgs.append({"role": "assistant", "content": _answer(ex[approach])})
    msgs.append({"role": "user", "content": "Process description:\n" + description})
    return msgs


def repair_message(errors, max_errors=8):
    return REPAIR_TEMPLATE.format(errors="\n- ".join(errors[:max_errors]))


def render_for_chat_ui(approach, description):
    """One self-contained text block to paste into a chat UI (e.g. ChatGPT)."""
    parts = []
    for m in build_messages(approach, description):
        tag = {"system": "INSTRUCTIONS", "user": "USER", "assistant": "EXPECTED ANSWER"}[m["role"]]
        parts.append(f"### {tag}\n{m['content']}")
    parts.append("### Answer for the last process description (JSON only):")
    return "\n\n".join(parts)
```

=======================================================================================
## **PROMPT v1.3**

```python
"""Prompts for both approaches (version tracked in PROMPT_VERSION).

Fairness rules
--------------
* Both approaches get the same task description, the same modelling rules,
  the same control-flow knowledge and the same four worked examples
  (ATM, pizza, gym membership, car inspection) - each in its own output format.
  None of the examples is part of the benchmark.
* The WF-net examples are generated from the process-tree examples by our own
  converter (renumbered in flow order), so both formats show exactly the same process.
* Both approaches first list the activities ("activities"), then build the model.
* Both approaches get the same number of repair attempts; repair is triggered
  only by format/structure errors, never by soundness (soundness is measured).
Change prompts only on the dev split and record every change in docs/prompt_log.md.
"""
import json
from collections import deque

from .tree import parse_tree, parse_tree_string
from .wfnet import tree_to_wfnet

PROMPT_VERSION = "v1.3"

COMMON_RULES = """Step 1 - list the activities ("activities"):
- One activity for every action in the text, in the order of the text. Do not invent or omit actions.
- Label = "<verb> <object>" in base form, using the verb and the nouns of the text,
  without the actor and without articles:
  "the invoice is sent by the shop" -> "send invoice",
  "the bank checks the client's credit history" -> "check credit history".
- Keep the verb and the point of view of the text: "the participant receives a confirmation e-mail"
  -> "receive confirmation e-mail" (not "send confirmation e-mail").
- Keep the object: "the code is deployed" -> "deploy code" (not just "deploy").
- Use exactly the same label every time the same activity occurs.
- NOT activities: actors, states and conditions ("the items are in stock", "the documents are
  complete", "when both are ready"), waiting, and the start or end of the process.

Step 2 - decisions:
- "X checks whether ... ; if yes ... otherwise ..." -> keep "check ..." as an activity; the branches
  start directly with their first action (no activity for the condition itself).
- "X decides / the request is approved or rejected / the result is positive or negative" -> one
  activity per named result ("approve loan" / "reject loan", "screening positive" /
  "screening negative") and NO separate "decide" or "evaluate" activity.
- An activity is written a second time only if the text describes it in two different branches
  (e.g. "notify customer" after a rejection and after a cancellation).

Step 3 - control flow:
- "then", "after that", "finally" -> sequence.
- "if ... otherwise", "either ... or" -> exclusive choice (exactly one branch).
- "in any order", "while", "meanwhile", "both ... and ... independently" -> parallel (all branches).
  Use parallel ONLY with such wording; otherwise keep the order of the text.
- "and/or", "at least one of", "one, two or all" -> inclusive choice (one or more branches).
- "again", "repeat", "until", "is checked again" -> loop with two parts:
  do   = the step that is repeated (usually the check or test itself),
  redo = the corrective steps done between two repetitions (in their order).
  Typical text: "X is checked; if a problem is found, A and B are done and X is checked again;
  when X is fine, C follows" -> loop(do = X, redo = A then B), then C.
  The check X is the "do" part of the loop: do NOT write X again before the loop, after the loop
  or inside "redo" - the loop already repeats it.
  The steps before the loop and after it are NOT part of the loop. Do not create activities for the
  loop condition or for its outcome ("documents complete", "changes requested", "defects found",
  "code approved", "claim complete").
- "optionally", "can also" -> exclusive choice between the step and skipping it
  (the skip has no label and is NOT an activity in the activities list).

Final check before answering:
1. Every activity from Step 1 appears in the model, and the model contains no other activity.
2. No activity for a condition, a state or a loop outcome; no "decide" activity.
3. Every loop has exactly two parts [do, redo], and "do" is not repeated outside the loop.
4. Parallel is used only where the text says "in any order", "while", "meanwhile" or similar.
5. Every optional step is a choice between the step and a skip."""

STRUCTURED_SYSTEM = """You convert a textual process description into a PROCESS TREE in JSON.

Node types:
- activity:    {"activity": "<label from the activities list>"}
- silent step: {"tau": true}   (exactly this, no other keys; only for skipping:
               "optionally X" -> {"op": "xor", "children": [{"activity": "X"}, {"tau": true}]})
- operator:    {"op": "<op>", "children": [<node>, <node>, ...]}

Operators:
- "seq":  children happen one after another, in the given order (>= 2 children)
- "xor":  exactly one child happens (>= 2 children)
- "and":  all children happen, in any order (>= 2 children)
- "or":   one or more children happen, any non-empty combination (2-4 children)
- "loop": exactly 2 children [do, redo]: "do" happens; then either the loop ends,
          or "redo" happens and "do" happens again (repeatable)
          Pattern: {"op": "loop", "children": [X, {"op": "seq", "children": [A, B]}]}

""" + COMMON_RULES + """

Return only one JSON object:
{"process_name": "<short name>", "activities": ["<label>", ...], "tree": <node>}"""

BASELINE_SYSTEM = """You convert a textual process description into a WORKFLOW NET (WF-net) in JSON.

A WF-net is a Petri net with places (states) and transitions (activities):
- exactly one start place "i" (no incoming arcs) and one end place "o" (no outgoing arcs);
- name the other places "p1", "p2", ... and the transitions "t1", "t2", ... in the order of the flow;
- every place and transition lies on a path from "i" to "o";
- every transition has at least one input place and at least one output place;
- arcs connect a place to a transition or a transition to a place (never place-place or transition-transition);
- a transition with "label": null is silent (used for splits, joins, skips and loop entry/exit).

How to express control flow:
- sequence: chain transitions through intermediate places;
- exclusive choice: alternative transitions share the same input place and the same output place;
- parallel: a silent split transition puts tokens into one place per branch; a silent join waits for all branches;
- optional step: a silent transition as an alternative to the step;
- loop: place before "do" -> "do" -> place after "do"; from that place either a silent exit transition
  continues the process, or the "redo" transitions lead back to the place before "do"
  (the loop is entered through a silent transition);
- inclusive choice (one or more of A, B, C): an exclusive choice between all non-empty combinations,
  each combination executed in parallel (labels may then appear in several transitions).

""" + COMMON_RULES + """

Every place except "i" has an incoming arc, every place except "o" has an outgoing arc, and every id used in "arcs" is listed in "places" or "transitions".

Return only one JSON object:
{"process_name": "<short name>",
 "activities": ["<label>", ...],
 "places": ["i", "p1", ..., "o"],
 "transitions": [{"id": "t1", "label": "<label>"}, {"id": "t2", "label": null}, ...],
 "arcs": [["i", "t1"], ["t1", "p1"], ...]}"""

# Worked examples: (process name, description, activities, process tree in compact notation)
_EXAMPLE_SOURCES = [
    ("ATM withdrawal",
     "A customer inserts a card into the ATM and enters the PIN. If the PIN is wrong, an error message is "
     "shown and the customer enters the PIN again. After a correct PIN, the customer withdraws cash, checks "
     "the balance and/or tops up a phone - at least one of these. Optionally, a receipt is printed. "
     "Finally, the card is returned.",
     ["insert card", "enter PIN", "show error message", "withdraw cash", "check balance", "top up phone",
      "print receipt", "return card"],
     "->(insert card, *(enter PIN, show error message), O(withdraw cash, check balance, top up phone), "
     "X(print receipt, tau), return card)"),
    ("pizza delivery",
     "A customer orders a pizza by phone. The kitchen bakes the pizza while the cashier prepares the bill. "
     "Then a courier delivers the pizza. If the customer is at home, the customer pays; otherwise, the pizza "
     "is taken back to the restaurant.",
     ["order pizza", "bake pizza", "prepare bill", "deliver pizza", "pay", "take pizza back"],
     "->(order pizza, +(bake pizza, prepare bill), deliver pizza, X(pay, take pizza back))"),
    ("gym membership",
     "A visitor fills in a membership form at the gym. The manager then decides on the application: it is "
     "either approved or rejected. If it is rejected, the visitor is informed by e-mail. If it is approved, "
     "the visitor pays the first fee; after that, a locker is assigned and a key card is printed, in any order.",
     ["fill in membership form", "reject membership", "inform visitor", "approve membership", "pay first fee",
      "assign locker", "print key card"],
     "->(fill in membership form, X(->(reject membership, inform visitor), "
     "->(approve membership, pay first fee, +(assign locker, print key card))))"),
    ("car inspection",
     "A driver brings the car to a technical inspection, and the inspector tests the car. If defects are "
     "found, the driver repairs the defects and brings the car back, and the inspector tests it again. "
     "When the car passes the test, the inspector issues a certificate.",
     ["bring car to inspection", "test car", "repair defects", "bring car back", "issue certificate"],
     "->(bring car to inspection, *(test car, ->(repair defects, bring car back)), issue certificate)"),
]


def _readable_wfnet(tree):
    """WF-net of a tree from our converter, renamed in flow order: i, p1, p2, ..., o and t1, t2, ..."""
    net = tree_to_wfnet(parse_tree(tree))
    succ = {}
    for s, t in net.arcs:
        succ.setdefault(s, []).append(t)
    order, seen, queue = [], {"i"}, deque(["i"])
    while queue:
        n = queue.popleft()
        order.append(n)
        for m in succ.get(n, []):
            if m not in seen:
                seen.add(m)
                queue.append(m)
    pmap, tmap = {"i": "i", "o": "o"}, {}
    for n in order:
        if n in net.transitions:
            tmap[n] = f"t{len(tmap) + 1}"
        elif n not in pmap:
            pmap[n] = f"p{len(pmap) - 1}"
    ren = {**pmap, **tmap}
    places = ["i"] + [pmap[n] for n in order if n in pmap and n not in ("i", "o")] + ["o"]
    transitions = [{"id": tmap[n], "label": net.transitions[n]} for n in order if n in tmap]
    arcs = []
    for n in order:
        if n in tmap:
            arcs += [[ren[s], tmap[n]] for s, t in net.arcs if t == n]
            arcs += [[tmap[n], ren[t]] for s, t in net.arcs if s == n]
    return {"places": places, "transitions": transitions, "arcs": arcs}


def _build_examples():
    out = []
    for name, text, acts, notation in _EXAMPLE_SOURCES:
        tree = parse_tree_string(notation)
        out.append({"text": text,
                    "structured": {"process_name": name, "activities": acts, "tree": tree},
                    "baseline": {"process_name": name, "activities": acts, **_readable_wfnet(tree)}})
    return out


EXAMPLES = _build_examples()

REPAIR_TEMPLATE = ("Your JSON is not valid:\n- {errors}\n"
                   "Fix only these problems, keep all activities, and return the complete corrected JSON object only.")


def _answer(obj):
    """Compact JSON, one top-level key per line (easier to imitate for small models)."""
    return "{" + ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in obj.items()) + "}"


def build_messages(approach, description):
    """Chat messages (system + worked examples + task) for 'structured' or 'baseline'."""
    if approach not in ("structured", "baseline"):
        raise ValueError(approach)
    system = STRUCTURED_SYSTEM if approach == "structured" else BASELINE_SYSTEM
    msgs = [{"role": "system", "content": system}]
    for ex in EXAMPLES:
        msgs.append({"role": "user", "content": "Process description:\n" + ex["text"]})
        msgs.append({"role": "assistant", "content": _answer(ex[approach])})
    msgs.append({"role": "user", "content": "Process description:\n" + description})
    return msgs


def repair_message(errors, max_errors=8):
    return REPAIR_TEMPLATE.format(errors="\n- ".join(errors[:max_errors]))


def render_for_chat_ui(approach, description):
    """One self-contained text block to paste into a chat UI (e.g. ChatGPT)."""
    parts = []
    for m in build_messages(approach, description):
        tag = {"system": "INSTRUCTIONS", "user": "USER", "assistant": "EXPECTED ANSWER"}[m["role"]]
        parts.append(f"### {tag}\n{m['content']}")
    parts.append("### Answer for the last process description (JSON only):")
    return "\n\n".join(parts)
```

## **PROMPT v1.4**
```python
"""Prompts for both approaches (version tracked in PROMPT_VERSION).

Fairness rules
--------------
* Both approaches get the same task description, the same modelling rules,
  the same control-flow knowledge, the same list of common mistakes, the same
  final checklist and the same five worked examples (ATM, pizza, gym membership,
  car inspection, laptop repair) - each in its own output format. None of the
  examples is part of the benchmark.
* The WF-net examples are generated from the process-tree examples by our own
  converter (renumbered in flow order), so both formats show exactly the same process.
* Both approaches first list the activities ("activities"), then build the model.
* Both approaches get the same number of repair attempts; repair is triggered
  only by format/structure errors, never by soundness (soundness is measured).
Change prompts only on the dev split and record every change in docs/prompt_log.md.
"""
import json
from collections import deque

from .tree import parse_tree, parse_tree_string
from .wfnet import tree_to_wfnet

PROMPT_VERSION = "v1.4"

COMMON_RULES = """Step 1 - list the activities ("activities"):
- Read the text sentence by sentence. Every verb that describes something that is done (by a person,
  a team or a system) is one activity - also inside "if", "otherwise" and "after that" clauses.
  Do not invent or omit actions. List them in the order of the text.
- Label = "<verb> <object>" in base form, using the verb and the nouns of the text,
  without the actor and without articles:
  "the invoice is sent by the shop" -> "send invoice",
  "the bank checks the client's credit history" -> "check credit history".
- Keep the verb and the point of view of the text: "the participant receives a confirmation e-mail"
  -> "receive confirmation e-mail" (not "send confirmation e-mail").
- Keep the object: "the code is deployed" -> "deploy code" (not just "deploy").
- Use exactly the same label every time the same activity occurs.
- NOT activities: actors, states and conditions ("the items are in stock", "the documents are
  complete", "when both are ready"), waiting, and the start or end of the process.

Step 2 - decisions and results:
- "X checks whether ... ; if yes ... otherwise ..." -> keep "check ..." as an activity; the branches
  start directly with their first action (no activity for the condition itself).
- "X decides / the request is approved or rejected" -> one activity per named result
  ("approve request" / "reject request") and NO separate "decide" or "evaluate" activity.
- A step that ends with a result ("ends with a positive or negative assessment", "passes or fails")
  -> the results are the activities: "<step> positive" / "<step> negative"; do not add the step
  itself as a separate activity.
- An activity is written a second time only if the text describes it in two different branches
  (e.g. "notify customer" after a rejection and after a cancellation).

Step 3 - control flow:
- "then", "after that", "finally" -> sequence.
- "if ... otherwise", "either ... or" -> exclusive choice (exactly one branch).
- "in any order", "while", "meanwhile", "both ... and ... independently" -> parallel (all branches).
  Use parallel ONLY with such wording; otherwise keep the order of the text.
- "and/or", "at least one of", "one, two or all" -> inclusive choice (one or more branches).
- "again", "repeat", "until", "is checked again" -> loop with two parts:
  do   = the step that is repeated (usually the check or test itself),
  redo = ALL corrective steps done between two repetitions, in their order - including the request
         and the answer ("request information", "provide information").
  Typical text: "X is checked; if a problem is found, A and B are done and X is checked again;
  when X is fine, C follows" -> loop(do = X, redo = A then B), then C.
  The check X is the "do" part of the loop: do NOT write X again before the loop, after the loop
  or inside "redo" - the loop already repeats it.
  What happens when X is fine (the next step, or a decision such as "either pay or reject") comes
  AFTER the loop, never inside "redo". The steps before the loop are not part of it either.
  Do not create activities for the loop condition or for its outcome ("documents complete",
  "changes requested", "defects found", "code approved", "claim complete").
- "optionally", "can also" -> exclusive choice between the step and skipping it
  (the skip has no label and is NOT an activity in the activities list).

Common mistakes (wrong -> right):
- an activity "decide on application" -> only the results "approve application" / "reject application"
- an activity "information complete" or "changes requested" -> no activity; the loop simply ends or repeats
- a loop whose "do" is "request information" -> do = the check; redo = "request information", "provide information"
- the check written before the loop and again inside it -> written once, as the "do" part of the loop
- the decision that follows a loop placed inside "redo" -> placed after the loop
- parallel for steps that the text tells one after another -> sequence
- an optional step without a skip -> exclusive choice between the step and the skip

Final check before answering:
1. Every activity from Step 1 appears in the model, and the model contains no other activity.
2. Every action verb of the text has an activity (including those in "if" / "otherwise" clauses).
3. No activity for a condition, a state or a loop outcome; no "decide" activity.
4. Every loop has exactly two parts [do, redo], "do" is not repeated outside the loop, and the
   steps after the loop are outside it.
5. Parallel is used only where the text says "in any order", "while", "meanwhile" or similar.
6. Every optional step is a choice between the step and a skip."""

STRUCTURED_SYSTEM = """You convert a textual process description into a PROCESS TREE in JSON.

Node types:
- activity:    {"activity": "<label from the activities list>"}
- silent step: {"tau": true}   (exactly this, no other keys; only for skipping:
               "optionally X" -> {"op": "xor", "children": [{"activity": "X"}, {"tau": true}]})
- operator:    {"op": "<op>", "children": [<node>, <node>, ...]}

Operators:
- "seq":  children happen one after another, in the given order (>= 2 children)
- "xor":  exactly one child happens (>= 2 children)
- "and":  all children happen, in any order (>= 2 children)
- "or":   one or more children happen, any non-empty combination (2-4 children)
- "loop": exactly 2 children [do, redo]: "do" happens; then either the loop ends,
          or "redo" happens and "do" happens again (repeatable)
          Pattern: {"op": "loop", "children": [X, {"op": "seq", "children": [A, B]}]}

""" + COMMON_RULES + """

Return only one JSON object:
{"process_name": "<short name>", "activities": ["<label>", ...], "tree": <node>}"""

BASELINE_SYSTEM = """You convert a textual process description into a WORKFLOW NET (WF-net) in JSON.

A WF-net is a Petri net with places (states) and transitions (activities):
- exactly one start place "i" (no incoming arcs) and one end place "o" (no outgoing arcs);
- name the other places "p1", "p2", ... and the transitions "t1", "t2", ... in the order of the flow;
- every place and transition lies on a path from "i" to "o";
- every transition has at least one input place and at least one output place;
- arcs connect a place to a transition or a transition to a place (never place-place or transition-transition);
- a transition with "label": null is silent (used for splits, joins, skips and loop entry/exit).

How to express control flow:
- sequence: chain transitions through intermediate places;
- exclusive choice: alternative transitions share the same input place and the same output place;
- parallel: a silent split transition puts tokens into one place per branch; a silent join waits for all branches;
- optional step: a silent transition as an alternative to the step;
- loop: place before "do" -> "do" -> place after "do"; from that place either a silent exit transition
  continues the process, or the "redo" transitions lead back to the place before "do"
  (the loop is entered through a silent transition);
- inclusive choice (one or more of A, B, C): an exclusive choice between all non-empty combinations,
  each combination executed in parallel (labels may then appear in several transitions).

""" + COMMON_RULES + """
7. Every place except "i" has an incoming arc, every place except "o" has an outgoing arc, and
   every id used in "arcs" is listed in "places" or "transitions".

Return only one JSON object:
{"process_name": "<short name>",
 "activities": ["<label>", ...],
 "places": ["i", "p1", ..., "o"],
 "transitions": [{"id": "t1", "label": "<label>"}, {"id": "t2", "label": null}, ...],
 "arcs": [["i", "t1"], ["t1", "p1"], ...]}"""

# Worked examples: (process name, description, activities, process tree in compact notation)
_EXAMPLE_SOURCES = [
    ("ATM withdrawal",
     "A customer inserts a card into the ATM and enters the PIN. If the PIN is wrong, an error message is "
     "shown and the customer enters the PIN again. After a correct PIN, the customer withdraws cash, checks "
     "the balance and/or tops up a phone - at least one of these. Optionally, a receipt is printed. "
     "Finally, the card is returned.",
     ["insert card", "enter PIN", "show error message", "withdraw cash", "check balance", "top up phone",
      "print receipt", "return card"],
     "->(insert card, *(enter PIN, show error message), O(withdraw cash, check balance, top up phone), "
     "X(print receipt, tau), return card)"),
    ("pizza delivery",
     "A customer orders a pizza by phone. The kitchen bakes the pizza while the cashier prepares the bill. "
     "Then a courier delivers the pizza. If the customer is at home, the customer pays; otherwise, the pizza "
     "is taken back to the restaurant.",
     ["order pizza", "bake pizza", "prepare bill", "deliver pizza", "pay", "take pizza back"],
     "->(order pizza, +(bake pizza, prepare bill), deliver pizza, X(pay, take pizza back))"),
    ("gym membership",
     "A visitor fills in a membership form at the gym. The manager then decides on the application: it is "
     "either approved or rejected. If it is rejected, the visitor is informed by e-mail. If it is approved, "
     "the visitor pays the first fee; after that, a locker is assigned and a key card is printed, in any order.",
     ["fill in membership form", "reject membership", "inform visitor", "approve membership", "pay first fee",
      "assign locker", "print key card"],
     "->(fill in membership form, X(->(reject membership, inform visitor), "
     "->(approve membership, pay first fee, +(assign locker, print key card))))"),
    ("car inspection",
     "A driver brings the car to a technical inspection, and the inspector tests the car. If defects are "
     "found, the driver repairs the defects and brings the car back, and the inspector tests it again. "
     "When the car passes the test, the inspector issues a certificate.",
     ["bring car to inspection", "test car", "repair defects", "bring car back", "issue certificate"],
     "->(bring car to inspection, *(test car, ->(repair defects, bring car back)), issue certificate)"),
    ("laptop repair",
     "A customer hands in a broken laptop, and a technician runs a diagnosis. If a part is missing, the "
     "technician orders the part and installs it, and the diagnosis is run again. When the laptop works, "
     "the customer either picks up the laptop or the laptop is shipped to the customer.",
     ["hand in laptop", "run diagnosis", "order part", "install part", "pick up laptop", "ship laptop"],
     "->(hand in laptop, *(run diagnosis, ->(order part, install part)), X(pick up laptop, ship laptop))"),
]


def _readable_wfnet(tree):
    """WF-net of a tree from our converter, renamed in flow order: i, p1, p2, ..., o and t1, t2, ..."""
    net = tree_to_wfnet(parse_tree(tree))
    succ = {}
    for s, t in net.arcs:
        succ.setdefault(s, []).append(t)
    order, seen, queue = [], {"i"}, deque(["i"])
    while queue:
        n = queue.popleft()
        order.append(n)
        for m in succ.get(n, []):
            if m not in seen:
                seen.add(m)
                queue.append(m)
    pmap, tmap = {"i": "i", "o": "o"}, {}
    for n in order:
        if n in net.transitions:
            tmap[n] = f"t{len(tmap) + 1}"
        elif n not in pmap:
            pmap[n] = f"p{len(pmap) - 1}"
    ren = {**pmap, **tmap}
    places = ["i"] + [pmap[n] for n in order if n in pmap and n not in ("i", "o")] + ["o"]
    transitions = [{"id": tmap[n], "label": net.transitions[n]} for n in order if n in tmap]
    arcs = []
    for n in order:
        if n in tmap:
            arcs += [[ren[s], tmap[n]] for s, t in net.arcs if t == n]
            arcs += [[tmap[n], ren[t]] for s, t in net.arcs if s == n]
    return {"places": places, "transitions": transitions, "arcs": arcs}


def _build_examples():
    out = []
    for name, text, acts, notation in _EXAMPLE_SOURCES:
        tree = parse_tree_string(notation)
        out.append({"text": text,
                    "structured": {"process_name": name, "activities": acts, "tree": tree},
                    "baseline": {"process_name": name, "activities": acts, **_readable_wfnet(tree)}})
    return out


EXAMPLES = _build_examples()

REPAIR_TEMPLATE = ("Your JSON is not valid:\n- {errors}\n"
                   "Fix only these problems, keep all activities, and return the complete corrected JSON object only.")


def _answer(obj):
    """Compact JSON, one top-level key per line (easier to imitate for small models)."""
    return "{" + ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in obj.items()) + "}"


def build_messages(approach, description):
    """Chat messages (system + worked examples + task) for 'structured' or 'baseline'."""
    if approach not in ("structured", "baseline"):
        raise ValueError(approach)
    system = STRUCTURED_SYSTEM if approach == "structured" else BASELINE_SYSTEM
    msgs = [{"role": "system", "content": system}]
    for ex in EXAMPLES:
        msgs.append({"role": "user", "content": "Process description:\n" + ex["text"]})
        msgs.append({"role": "assistant", "content": _answer(ex[approach])})
    msgs.append({"role": "user", "content": "Process description:\n" + description})
    return msgs


def repair_message(errors, max_errors=8):
    return REPAIR_TEMPLATE.format(errors="\n- ".join(errors[:max_errors]))


def render_for_chat_ui(approach, description):
    """One self-contained text block to paste into a chat UI (e.g. ChatGPT)."""
    parts = []
    for m in build_messages(approach, description):
        tag = {"system": "INSTRUCTIONS", "user": "USER", "assistant": "EXPECTED ANSWER"}[m["role"]]
        parts.append(f"### {tag}\n{m['content']}")
    parts.append("### Answer for the last process description (JSON only):")
    return "\n\n".join(parts)

```