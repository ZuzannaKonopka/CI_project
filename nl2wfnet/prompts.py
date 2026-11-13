"""Prompts for both approaches (version tracked in PROMPT_VERSION).

Fairness rules
--------------
* Both approaches get the same task description, the same modelling rules,
  the same three decision patterns, the same scope rules for choices, parallel
  branches and loops, the same list of common mistakes, the same final checklist and the same five worked examples (ATM, pizza, gym membership,
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

PROMPT_VERSION = "v1.5"

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

Step 2 - decisions: use exactly ONE of these three patterns
(A) A check with a condition: "X checks whether ...; if yes ..., otherwise ..."
    -> keep "check ..." as one activity; the branches start directly with their first action.
    The condition is NOT an activity: no "items in stock", "stock available", "documents complete".
(B) A decision with named results: "X decides", "the request is approved or rejected",
    "if the loan is approved ... otherwise ..."
    -> one activity per result ("approve loan" / "reject loan") as the FIRST activity of each branch,
    also when the text names the second result only by "otherwise"; NO "decide" or "evaluate" activity.
(C) A step that ends with an assessment: "each interview ends with a positive or negative assessment",
    "the test is passed or failed"
    -> the results are the activities ("<step> positive" / "<step> negative"); the step itself is not
    a separate activity.
- An activity is written a second time only if the text describes it in two different branches
  (e.g. "notify customer" after a rejection and after a cancellation).

Step 3 - control flow and scope:
- "then", "after that", "finally", "in addition", "also" -> sequence (keep the order of the text).
- "if ... otherwise", "either ... or" -> exclusive choice (exactly one branch).
  A branch contains ALL steps described for that case, up to where the other case starts.
  Steps after "finally", "at the end" or "in both cases" come AFTER the whole choice, not inside a branch.
- "in any order", "while", "meanwhile", "both ... and ... independently" -> parallel (all branches).
  Only the activities named together in that sentence are parallel; the step before them and the step
  after them stay in sequence. Without such wording never use parallel.
- "and/or", "at least one of", "one, two or all" -> inclusive choice (one or more branches).
  Only the options listed with "and/or" belong to it; the steps before and after stay in sequence.
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
- "check stock" followed by an activity "stock available" -> no condition activity (pattern A)
- an activity "decide on application" -> only the results "approve application" / "reject application" (pattern B)
- "otherwise, the customer is informed" without a result activity -> "reject ..." first, then "inform customer"
- an activity "information complete" or "changes requested" -> no activity; the loop simply ends or repeats
- a loop whose "do" is "request information" -> do = the check; redo = "request information", "provide information"
- the check written before the loop and again inside it -> written once, as the "do" part of the loop
- the decision that follows a loop placed inside "redo" -> placed after the loop
- the final step ("finally ...") placed inside the last branch of a choice -> placed after the choice
- parallel that also contains the step before or after the "in any order" activities -> only the named ones
- parallel for steps that the text tells one after another -> sequence
- an optional step without a skip -> exclusive choice between the step and the skip

Final check before answering:
1. Every activity from Step 1 appears in the model, and the model contains no other activity.
2. Every action verb of the text has an activity (including those in "if" / "otherwise" clauses).
3. Each decision uses exactly one pattern (A, B or C); no condition activity, no "decide" activity.
4. Every branch of a choice contains all steps of its case, and the steps after the choice are outside it.
5. Parallel and inclusive choice contain only the activities named together in the text.
6. Every loop has exactly two parts [do, redo], "do" is not repeated outside the loop, and the
   steps after the loop are outside it.
7. Every optional step is a choice between the step and a skip."""

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
8. Every place except "i" has an incoming arc, every place except "o" has an outgoing arc, and
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
