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

PROMPT_VERSION = "v1.0"

COMMON_RULES = """Modelling rules:
- An activity is a short verb phrase taken from the text, e.g. "submit CV", "check stock".
- Every outcome of a decision is its own activity, e.g. "screening positive" and "screening negative".
- Use exactly the same label for the same activity everywhere.
- Do not invent activities that are not described in the text and do not omit described ones.
- "then", "after that" -> sequence; "if ... otherwise", "either ... or" -> exclusive choice;
  "in any order", "while", "meanwhile" -> parallel; "and/or", "at least one of" -> inclusive choice;
  "again", "until", "repeat" -> loop; "optionally" -> exclusive choice with a skip."""

STRUCTURED_SYSTEM = """You convert a textual process description into a PROCESS TREE in JSON.

Node types:
- activity:    {"activity": "<verb phrase>"}
- silent step: {"tau": true}        (only to make something optional: {"op": "xor", "children": [X, {"tau": true}]})
- operator:    {"op": "<op>", "children": [<node>, <node>, ...]}

Operators:
- "seq":  children happen one after another, in the given order (>= 2 children)
- "xor":  exactly one child happens (>= 2 children)
- "and":  all children happen, in any order or at the same time (>= 2 children)
- "or":   one or more children happen, any non-empty combination (2-4 children)
- "loop": exactly 2 children [do, redo]: "do" happens; then either the loop ends,
          or "redo" happens and "do" happens again (repeatable)

""" + COMMON_RULES + """

Return only one JSON object: {"process_name": "<short name>", "tree": <node>}"""

BASELINE_SYSTEM = """You convert a textual process description into a WORKFLOW NET (WF-net) in JSON.

A WF-net is a Petri net with places (states) and transitions (activities):
- exactly one start place "i" (no incoming arcs) and one end place "o" (no outgoing arcs);
- every place and transition lies on a path from "i" to "o";
- arcs connect a place to a transition or a transition to a place (never place-place or transition-transition);
- a transition with "label": null is silent (used for splits, joins, skips and loop entry/exit).

How to express control flow:
- sequence: chain transitions through intermediate places;
- exclusive choice: alternative transitions share the same input place and the same output place;
- parallel: a silent split transition puts tokens into one place per branch; a silent join waits for all branches;
- optional step: a silent transition as an alternative to the step;
- loop: after the "do" part, either a silent exit transition or the "redo" part leading back before "do";
- inclusive choice (one or more of A, B, C): an exclusive choice between all non-empty combinations,
  each combination executed in parallel (labels may then appear in several transitions).

""" + COMMON_RULES + """

Return only one JSON object:
{"process_name": "<short name>",
 "places": ["i", ..., "o"],
 "transitions": [{"id": "t1", "label": "<verb phrase>"}, {"id": "t2", "label": null}, ...],
 "arcs": [["i", "t1"], ["t1", "p1"], ...]}"""

EXAMPLES = [
    {"text": "A customer inserts a card into the ATM and enters the PIN. If the PIN is wrong, an error message is shown and the customer enters the PIN again. After a correct PIN, the customer withdraws cash, checks the balance and/or tops up a phone - at least one of these. Optionally, a receipt is printed. Finally, the card is returned.",
     "structured": {"process_name": "ATM withdrawal", "tree": {'op': 'seq', 'children': [{'activity': 'insert card'}, {'op': 'loop', 'children': [{'activity': 'enter PIN'}, {'activity': 'show error message'}]}, {'op': 'or', 'children': [{'activity': 'withdraw cash'}, {'activity': 'check balance'}, {'activity': 'top up phone'}]}, {'op': 'xor', 'children': [{'activity': 'print receipt'}, {'tau': True}]}, {'activity': 'return card'}]}},
     "baseline": dict({"process_name": "ATM withdrawal"}, **{'places': ['i', 'o', 'p0', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12', 'p13', 'p14', 'p15', 'p16', 'p17', 'p18', 'p19', 'p20', 'p21', 'p22', 'p23'], 'transitions': [{'id': 't0', 'label': 'insert card'}, {'id': 't1', 'label': None}, {'id': 't2', 'label': None}, {'id': 't3', 'label': 'enter PIN'}, {'id': 't4', 'label': 'show error message'}, {'id': 't5', 'label': 'withdraw cash'}, {'id': 't6', 'label': 'check balance'}, {'id': 't7', 'label': 'top up phone'}, {'id': 't8', 'label': None}, {'id': 't9', 'label': None}, {'id': 't10', 'label': 'withdraw cash'}, {'id': 't11', 'label': 'check balance'}, {'id': 't12', 'label': None}, {'id': 't13', 'label': None}, {'id': 't14', 'label': 'withdraw cash'}, {'id': 't15', 'label': 'top up phone'}, {'id': 't16', 'label': None}, {'id': 't17', 'label': None}, {'id': 't18', 'label': 'check balance'}, {'id': 't19', 'label': 'top up phone'}, {'id': 't20', 'label': None}, {'id': 't21', 'label': None}, {'id': 't22', 'label': 'withdraw cash'}, {'id': 't23', 'label': 'check balance'}, {'id': 't24', 'label': 'top up phone'}, {'id': 't25', 'label': 'print receipt'}, {'id': 't26', 'label': None}, {'id': 't27', 'label': 'return card'}], 'arcs': [['i', 't0'], ['t0', 'p0'], ['p0', 't1'], ['t1', 'p2'], ['p2', 't3'], ['t3', 'p3'], ['p3', 't4'], ['t4', 'p2'], ['p3', 't2'], ['t2', 'p1'], ['p1', 't5'], ['t5', 'p4'], ['p1', 't6'], ['t6', 'p4'], ['p1', 't7'], ['t7', 'p4'], ['p1', 't8'], ['t9', 'p4'], ['t8', 'p5'], ['p6', 't9'], ['p5', 't10'], ['t10', 'p6'], ['t8', 'p7'], ['p8', 't9'], ['p7', 't11'], ['t11', 'p8'], ['p1', 't12'], ['t13', 'p4'], ['t12', 'p9'], ['p10', 't13'], ['p9', 't14'], ['t14', 'p10'], ['t12', 'p11'], ['p12', 't13'], ['p11', 't15'], ['t15', 'p12'], ['p1', 't16'], ['t17', 'p4'], ['t16', 'p13'], ['p14', 't17'], ['p13', 't18'], ['t18', 'p14'], ['t16', 'p15'], ['p16', 't17'], ['p15', 't19'], ['t19', 'p16'], ['p1', 't20'], ['t21', 'p4'], ['t20', 'p17'], ['p18', 't21'], ['p17', 't22'], ['t22', 'p18'], ['t20', 'p19'], ['p20', 't21'], ['p19', 't23'], ['t23', 'p20'], ['t20', 'p21'], ['p22', 't21'], ['p21', 't24'], ['t24', 'p22'], ['p4', 't25'], ['t25', 'p23'], ['p4', 't26'], ['t26', 'p23'], ['p23', 't27'], ['t27', 'o']]})},
    {"text": "A customer orders a pizza by phone. The kitchen bakes the pizza while the cashier prepares the bill. Then a courier delivers the pizza. If the customer is at home, the customer pays; otherwise, the pizza is taken back to the restaurant.",
     "structured": {"process_name": "pizza delivery", "tree": {'op': 'seq', 'children': [{'activity': 'order pizza'}, {'op': 'and', 'children': [{'activity': 'bake pizza'}, {'activity': 'prepare bill'}]}, {'activity': 'deliver pizza'}, {'op': 'xor', 'children': [{'activity': 'pay'}, {'activity': 'take pizza back'}]}]}},
     "baseline": dict({"process_name": "pizza delivery"}, **{'places': ['i', 'o', 'p0', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6'], 'transitions': [{'id': 't0', 'label': 'order pizza'}, {'id': 't1', 'label': None}, {'id': 't2', 'label': None}, {'id': 't3', 'label': 'bake pizza'}, {'id': 't4', 'label': 'prepare bill'}, {'id': 't5', 'label': 'deliver pizza'}, {'id': 't6', 'label': 'pay'}, {'id': 't7', 'label': 'take pizza back'}], 'arcs': [['i', 't0'], ['t0', 'p0'], ['p0', 't1'], ['t2', 'p1'], ['t1', 'p2'], ['p3', 't2'], ['p2', 't3'], ['t3', 'p3'], ['t1', 'p4'], ['p5', 't2'], ['p4', 't4'], ['t4', 'p5'], ['p1', 't5'], ['t5', 'p6'], ['p6', 't6'], ['t6', 'o'], ['p6', 't7'], ['t7', 'o']]})},
]

REPAIR_TEMPLATE = ("Your JSON is not valid:\n- {errors}\n"
                   "Fix these problems and return the complete corrected JSON object only.")


def build_messages(approach, description):
    """Chat messages (system + 2 worked examples + task) for 'structured' or 'baseline'."""
    if approach not in ("structured", "baseline"):
        raise ValueError(approach)
    system = STRUCTURED_SYSTEM if approach == "structured" else BASELINE_SYSTEM
    msgs = [{"role": "system", "content": system}]
    for ex in EXAMPLES:
        msgs.append({"role": "user", "content": "Process description:\n" + ex["text"]})
        msgs.append({"role": "assistant", "content": json.dumps(ex[approach], ensure_ascii=False)})
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
