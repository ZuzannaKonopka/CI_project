"""Prompts for both approaches (version tracked in PROMPT_VERSION).

Fairness rules
--------------
* Both approaches get the same task description, the same modelling rules,
  the same control-flow knowledge and the same three worked examples
  (ATM, pizza, gym membership) - each in its own output format. None of the
  examples is part of the benchmark.
* Both approaches first list the activities ("activities"), then build the model.
* Both approaches get the same number of repair attempts; repair is triggered
  only by format/structure errors, never by soundness (soundness is measured).
Change prompts only on the dev split and record every change in docs/prompt_log.md.

"""
import json

PROMPT_VERSION = "v1.4"

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
- "again", "repeat", "until", "is checked again" -> loop: do = the step that is repeated (usually the
  check), redo = the corrective steps between two repetitions. No activity for the loop condition
  ("changes requested", "information missing", "approved"); after the loop the process continues.
- "optionally", "can also" -> exclusive choice between the step and skipping it.
Every activity from Step 1 must appear in the model, and no other activity."""

STRUCTURED_SYSTEM = """You convert a textual process description into a PROCESS TREE in JSON.

Node types:
- activity:    {"activity": "<label from the activities list>"}
- silent step: {"tau": true}        (only for skipping: {"op": "xor", "children": [X, {"tau": true}]})
- operator:    {"op": "<op>", "children": [<node>, <node>, ...]}

Operators:
- "seq":  children happen one after another, in the given order (>= 2 children)
- "xor":  exactly one child happens (>= 2 children)
- "and":  all children happen, in any order (>= 2 children)
- "or":   one or more children happen, any non-empty combination (2-4 children)
- "loop": exactly 2 children [do, redo]: "do" happens; then either the loop ends,
          or "redo" happens and "do" happens again (repeatable)

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
- loop: after the "do" part, either a silent exit transition or the "redo" part leading back before "do";
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

EXAMPLES = [{'text': 'A customer inserts a card into the ATM and enters the PIN. If the PIN is wrong, an error message '
          'is shown and the customer enters the PIN again. After a correct PIN, the customer withdraws cash, '
          'checks the balance and/or tops up a phone - at least one of these. Optionally, a receipt is '
          'printed. Finally, the card is returned.',
  'structured': {'process_name': 'ATM withdrawal',
                 'activities': ['insert card',
                                'enter PIN',
                                'show error message',
                                'withdraw cash',
                                'check balance',
                                'top up phone',
                                'print receipt',
                                'return card'],
                 'tree': {'op': 'seq',
                          'children': [{'activity': 'insert card'},
                                       {'op': 'loop',
                                        'children': [{'activity': 'enter PIN'},
                                                     {'activity': 'show error message'}]},
                                       {'op': 'or',
                                        'children': [{'activity': 'withdraw cash'},
                                                     {'activity': 'check balance'},
                                                     {'activity': 'top up phone'}]},
                                       {'op': 'xor',
                                        'children': [{'activity': 'print receipt'}, {'tau': True}]},
                                       {'activity': 'return card'}]}},
  'baseline': {'process_name': 'ATM withdrawal',
               'activities': ['insert card',
                              'enter PIN',
                              'show error message',
                              'withdraw cash',
                              'check balance',
                              'top up phone',
                              'print receipt',
                              'return card'],
               'places': ['i',
                          'p1',
                          'p2',
                          'p3',
                          'p4',
                          'p5',
                          'p6',
                          'p7',
                          'p8',
                          'p9',
                          'p10',
                          'p11',
                          'p12',
                          'p13',
                          'p14',
                          'p15',
                          'p16',
                          'p17',
                          'p18',
                          'p19',
                          'p20',
                          'p21',
                          'p22',
                          'p23',
                          'p24',
                          'o'],
               'transitions': [{'id': 't1', 'label': 'insert card'},
                               {'id': 't2', 'label': None},
                               {'id': 't3', 'label': 'enter PIN'},
                               {'id': 't4', 'label': 'show error message'},
                               {'id': 't5', 'label': None},
                               {'id': 't6', 'label': 'withdraw cash'},
                               {'id': 't7', 'label': 'check balance'},
                               {'id': 't8', 'label': 'top up phone'},
                               {'id': 't9', 'label': None},
                               {'id': 't10', 'label': None},
                               {'id': 't11', 'label': None},
                               {'id': 't12', 'label': None},
                               {'id': 't13', 'label': 'print receipt'},
                               {'id': 't14', 'label': None},
                               {'id': 't15', 'label': 'withdraw cash'},
                               {'id': 't16', 'label': 'check balance'},
                               {'id': 't17', 'label': 'withdraw cash'},
                               {'id': 't18', 'label': 'top up phone'},
                               {'id': 't19', 'label': 'check balance'},
                               {'id': 't20', 'label': 'top up phone'},
                               {'id': 't21', 'label': 'withdraw cash'},
                               {'id': 't22', 'label': 'check balance'},
                               {'id': 't23', 'label': 'top up phone'},
                               {'id': 't24', 'label': 'return card'},
                               {'id': 't25', 'label': None},
                               {'id': 't26', 'label': None},
                               {'id': 't27', 'label': None},
                               {'id': 't28', 'label': None}],
               'arcs': [['i', 't1'],
                        ['t1', 'p1'],
                        ['p1', 't2'],
                        ['t2', 'p2'],
                        ['p2', 't3'],
                        ['t3', 'p3'],
                        ['p3', 't4'],
                        ['t4', 'p2'],
                        ['p3', 't5'],
                        ['t5', 'p4'],
                        ['p4', 't6'],
                        ['t6', 'p5'],
                        ['p4', 't7'],
                        ['t7', 'p5'],
                        ['p4', 't8'],
                        ['t8', 'p5'],
                        ['p4', 't9'],
                        ['t9', 'p6'],
                        ['t9', 'p7'],
                        ['p4', 't10'],
                        ['t10', 'p8'],
                        ['t10', 'p9'],
                        ['p4', 't11'],
                        ['t11', 'p10'],
                        ['t11', 'p11'],
                        ['p4', 't12'],
                        ['t12', 'p12'],
                        ['t12', 'p13'],
                        ['t12', 'p14'],
                        ['p5', 't13'],
                        ['t13', 'p15'],
                        ['p5', 't14'],
                        ['t14', 'p15'],
                        ['p6', 't15'],
                        ['t15', 'p16'],
                        ['p7', 't16'],
                        ['t16', 'p17'],
                        ['p8', 't17'],
                        ['t17', 'p18'],
                        ['p9', 't18'],
                        ['t18', 'p19'],
                        ['p10', 't19'],
                        ['t19', 'p20'],
                        ['p11', 't20'],
                        ['t20', 'p21'],
                        ['p12', 't21'],
                        ['t21', 'p22'],
                        ['p13', 't22'],
                        ['t22', 'p23'],
                        ['p14', 't23'],
                        ['t23', 'p24'],
                        ['p15', 't24'],
                        ['t24', 'o'],
                        ['p16', 't25'],
                        ['p17', 't25'],
                        ['t25', 'p5'],
                        ['p18', 't26'],
                        ['p19', 't26'],
                        ['t26', 'p5'],
                        ['p20', 't27'],
                        ['p21', 't27'],
                        ['t27', 'p5'],
                        ['p22', 't28'],
                        ['p23', 't28'],
                        ['p24', 't28'],
                        ['t28', 'p5']]}},
 {'text': 'A customer orders a pizza by phone. The kitchen bakes the pizza while the cashier prepares the '
          'bill. Then a courier delivers the pizza. If the customer is at home, the customer pays; '
          'otherwise, the pizza is taken back to the restaurant.',
  'structured': {'process_name': 'pizza delivery',
                 'activities': ['order pizza',
                                'bake pizza',
                                'prepare bill',
                                'deliver pizza',
                                'pay',
                                'take pizza back'],
                 'tree': {'op': 'seq',
                          'children': [{'activity': 'order pizza'},
                                       {'op': 'and',
                                        'children': [{'activity': 'bake pizza'},
                                                     {'activity': 'prepare bill'}]},
                                       {'activity': 'deliver pizza'},
                                       {'op': 'xor',
                                        'children': [{'activity': 'pay'},
                                                     {'activity': 'take pizza back'}]}]}},
  'baseline': {'process_name': 'pizza delivery',
               'activities': ['order pizza',
                              'bake pizza',
                              'prepare bill',
                              'deliver pizza',
                              'pay',
                              'take pizza back'],
               'places': ['i', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'o'],
               'transitions': [{'id': 't1', 'label': 'order pizza'},
                               {'id': 't2', 'label': None},
                               {'id': 't3', 'label': 'bake pizza'},
                               {'id': 't4', 'label': 'prepare bill'},
                               {'id': 't5', 'label': None},
                               {'id': 't6', 'label': 'deliver pizza'},
                               {'id': 't7', 'label': 'pay'},
                               {'id': 't8', 'label': 'take pizza back'}],
               'arcs': [['i', 't1'],
                        ['t1', 'p1'],
                        ['p1', 't2'],
                        ['t2', 'p2'],
                        ['t2', 'p3'],
                        ['p2', 't3'],
                        ['t3', 'p4'],
                        ['p3', 't4'],
                        ['t4', 'p5'],
                        ['p4', 't5'],
                        ['p5', 't5'],
                        ['t5', 'p6'],
                        ['p6', 't6'],
                        ['t6', 'p7'],
                        ['p7', 't7'],
                        ['t7', 'o'],
                        ['p7', 't8'],
                        ['t8', 'o']]}},
 {'text': 'A visitor fills in a membership form at the gym. The manager then decides on the application: it '
          'is either approved or rejected. If it is rejected, the visitor is informed by e-mail. If it is '
          'approved, the visitor pays the first fee; after that, a locker is assigned and a key card is '
          'printed, in any order.',
  'structured': {'process_name': 'gym membership',
                 'activities': ['fill in membership form',
                                'reject membership',
                                'inform visitor',
                                'approve membership',
                                'pay first fee',
                                'assign locker',
                                'print key card'],
                 'tree': {'op': 'seq',
                          'children': [{'activity': 'fill in membership form'},
                                       {'op': 'xor',
                                        'children': [{'op': 'seq',
                                                      'children': [{'activity': 'reject membership'},
                                                                   {'activity': 'inform visitor'}]},
                                                     {'op': 'seq',
                                                      'children': [{'activity': 'approve membership'},
                                                                   {'activity': 'pay first fee'},
                                                                   {'op': 'and',
                                                                    'children': [{'activity': 'assign '
                                                                                              'locker'},
                                                                                 {'activity': 'print key '
                                                                                              'card'}]}]}]}]}},
  'baseline': {'process_name': 'gym membership',
               'activities': ['fill in membership form',
                              'reject membership',
                              'inform visitor',
                              'approve membership',
                              'pay first fee',
                              'assign locker',
                              'print key card'],
               'places': ['i', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'o'],
               'transitions': [{'id': 't1', 'label': 'fill in membership form'},
                               {'id': 't2', 'label': 'reject membership'},
                               {'id': 't3', 'label': 'approve membership'},
                               {'id': 't4', 'label': 'inform visitor'},
                               {'id': 't5', 'label': 'pay first fee'},
                               {'id': 't6', 'label': None},
                               {'id': 't7', 'label': 'assign locker'},
                               {'id': 't8', 'label': 'print key card'},
                               {'id': 't9', 'label': None}],
               'arcs': [['i', 't1'],
                        ['t1', 'p1'],
                        ['p1', 't2'],
                        ['t2', 'p2'],
                        ['p1', 't3'],
                        ['t3', 'p3'],
                        ['p2', 't4'],
                        ['t4', 'o'],
                        ['p3', 't5'],
                        ['t5', 'p4'],
                        ['p4', 't6'],
                        ['t6', 'p5'],
                        ['t6', 'p6'],
                        ['p5', 't7'],
                        ['t7', 'p7'],
                        ['p6', 't8'],
                        ['t8', 'p8'],
                        ['p7', 't9'],
                        ['p8', 't9'],
                        ['t9', 'o']]}}]

REPAIR_TEMPLATE = ("Your JSON is not valid:\n- {errors}\n"
                   "Fix only these problems, keep all activities, and return the complete corrected JSON object only.")


def _answer(obj):
    """Compact JSON, one top-level key per line (easier to imitate for small models)."""
    return "{" + ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in obj.items()) + "}"


def build_messages(approach, description):
    """Chat messages (system + 3 worked examples + task) for 'structured' or 'baseline'."""
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