"""WF-nets and the recursive process tree -> WF-net translation.

Each operator is translated into a fixed block pattern between an input
place and an output place. Because every block has one entry and one exit,
the result is a WF-net (one source place 'i', one sink place 'o') that is
sound by construction - the soundness checker in analysis.py verifies this
independently, so converter bugs are detected.
"""
from itertools import combinations
from xml.sax.saxutils import escape
from .tree import Node


class PetriNet:
    def __init__(self, name="wfnet"):
        self.name = name
        self.places = []                 # place ids
        self.transitions = {}            # id -> label (None = silent)
        self.arcs = []                   # (source_id, target_id)
        self._p = self._t = 0

    def add_place(self, prefix="p"):
        pid = f"{prefix}{self._p}" if prefix == "p" else prefix
        if prefix == "p":
            self._p += 1
        self.places.append(pid)
        return pid

    def add_transition(self, label):
        tid = f"t{self._t}"
        self._t += 1
        self.transitions[tid] = label
        return tid

    def arc(self, s, t):
        self.arcs.append((s, t))

    def preset(self, node):
        return [s for s, t in self.arcs if t == node]

    def postset(self, node):
        return [t for s, t in self.arcs if s == node]

    # ---------- structural WF-net check ----------
    def wf_structure_errors(self):
        errs = []
        sources = [p for p in self.places if not self.preset(p)]
        sinks = [p for p in self.places if not self.postset(p)]
        if len(sources) != 1:
            errs.append(f"expected exactly one source place, found {sources}")
        if len(sinks) != 1:
            errs.append(f"expected exactly one sink place, found {sinks}")
        if errs:
            return errs
        # every node on a path from source to sink
        succ, pred = {}, {}
        for s, t in self.arcs:
            succ.setdefault(s, []).append(t)
            pred.setdefault(t, []).append(s)
        def reach(start, nxt):
            seen, stack = {start}, [start]
            while stack:
                for m in nxt.get(stack.pop(), []):
                    if m not in seen:
                        seen.add(m); stack.append(m)
            return seen
        fwd, bwd = reach(sources[0], succ), reach(sinks[0], pred)
        for n in self.places + list(self.transitions):
            if n not in fwd or n not in bwd:
                errs.append(f"node {n} is not on a path from source to sink")
        return errs

    # ---------- export ----------
    def to_dot(self):
        lines = [f'digraph "{self.name}" {{', "  rankdir=LR;", '  node [fontname="Helvetica"];']
        for p in self.places:
            extra = ""
            if p == "i":
                extra = ', label="&#9679;", fontsize=18'     # initial token
            elif p == "o":
                extra = ', peripheries=2, label=""'
            else:
                extra = ', label=""'
            lines.append(f'  "{p}" [shape=circle, width=0.35, fixedsize=true{extra}];')
        for t, lab in self.transitions.items():
            if lab is None:
                lines.append(f'  "{t}" [shape=box, style=filled, fillcolor=black, label="", width=0.15, height=0.45];')
            else:
                lines.append(f'  "{t}" [shape=box, style=rounded, label="{lab}"];')
        for s, t in self.arcs:
            lines.append(f'  "{s}" -> "{t}";')
        lines.append("}")
        return "\n".join(lines)

    def to_pnml(self):
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<pnml><net id="%s" type="http://www.pnml.org/version-2009/grammar/pnmlcoremodel"><page id="page1">' % escape(self.name)]
        for p in self.places:
            tok = "<initialMarking><text>1</text></initialMarking>" if p == "i" else ""
            out.append(f'<place id="{p}"><name><text>{p}</text></name>{tok}</place>')
        for t, lab in self.transitions.items():
            name = escape(lab) if lab is not None else "tau"
            silent = '<toolspecific tool="ProM" version="6.4" activity="$invisible$"/>' if lab is None else ""
            out.append(f'<transition id="{t}"><name><text>{name}</text></name>{silent}</transition>')
        for k, (s, t) in enumerate(self.arcs):
            out.append(f'<arc id="a{k}" source="{s}" target="{t}"/>')
        out.append('</page><finalmarkings><marking><place idref="o"><text>1</text></place></marking></finalmarkings></net></pnml>')
        return "\n".join(out)

    def to_json(self):
        return {"places": self.places,
                "transitions": [{"id": t, "label": l} for t, l in self.transitions.items()],
                "arcs": [list(a) for a in self.arcs]}


def validate_wfnet_json(obj):
    """Return LLM-readable errors for a WF-net given as JSON (empty list = valid).

    Checks the format and the WF-net structure (one source 'i', one sink 'o',
    every node on a path from i to o). Soundness is NOT checked here: it is an
    evaluation measure, not a format requirement.
    """
    if not isinstance(obj, dict):
        return ["the output must be a JSON object"]
    errs = []
    for key in ("places", "transitions", "arcs"):
        if not isinstance(obj.get(key), list):
            errs.append(f"missing list '{key}'")
    if errs:
        return errs
    places = obj["places"]
    if not all(isinstance(p, str) and p for p in places):
        errs.append("every place must be a non-empty string id")
    if len(set(places)) != len(places):
        errs.append("place ids must be unique")
    for p in ("i", "o"):
        if p not in places:
            errs.append(f"the place '{p}' is missing ('i' = start place, 'o' = end place)")
    tids = []
    for k, t in enumerate(obj["transitions"]):
        if not isinstance(t, dict) or not isinstance(t.get("id"), str) or not t.get("id"):
            errs.append(f"transitions[{k}] must be an object with a string 'id'")
            continue
        lab = t.get("label")
        if lab is not None and (not isinstance(lab, str) or not lab.strip()):
            errs.append(f"transition '{t['id']}': 'label' must be a non-empty string or null (silent)")
        if set(t) - {"id", "label"}:
            errs.append(f"transition '{t['id']}' may only contain 'id' and 'label'")
        tids.append(t["id"])
    if len(set(tids)) != len(tids):
        errs.append("transition ids must be unique")
    both = set(places) & set(tids)
    if both:
        errs.append(f"ids used both as place and transition: {sorted(both)}")
    P, T = set(places), set(tids)
    for k, a in enumerate(obj["arcs"]):
        if not (isinstance(a, list) and len(a) == 2):
            errs.append(f"arcs[{k}] must be a pair [source, target]")
            continue
        s, t = a
        if not ((s in P and t in T) or (s in T and t in P)):
            errs.append(f"arc {a} must connect a place and a transition (unknown id or place-place / transition-transition arc)")
    if errs:
        return errs
    net = wfnet_from_json(obj)
    if net.preset("i"):
        errs.append("the start place 'i' must not have incoming arcs")
    if net.postset("o"):
        errs.append("the end place 'o' must not have outgoing arcs")
    for t in T:
        if not net.preset(t) or not net.postset(t):
            errs.append(f"transition '{t}' needs at least one input and one output place")
    return errs + [e for e in net.wf_structure_errors() if e not in errs]


def relabel(net, mapping, name=None):
    """Copy of the net with visible labels renamed via mapping (missing keys unchanged)."""
    new = PetriNet(name or net.name)
    new.places = list(net.places)
    new.transitions = {t: (mapping.get(l, l) if l is not None else None) for t, l in net.transitions.items()}
    new.arcs = list(net.arcs)
    return new


def wfnet_from_json(obj, name="baseline"):
    """Load a WF-net given as JSON (format used for the direct-generation baseline).

    {"places": ["i", "p1", "o"],
     "transitions": [{"id": "t1", "label": "submit CV"}, {"id": "t2", "label": null}],
     "arcs": [["i", "t1"], ["t1", "p1"], ...]}
    Source place must be named "i" and sink place "o".
    """
    net = PetriNet(name)
    net.places = list(obj["places"])
    net.transitions = {t["id"]: t.get("label") for t in obj["transitions"]}
    net.arcs = [tuple(a) for a in obj["arcs"]]
    return net


# ---------------- tree -> WF-net ----------------
def tree_to_wfnet(tree: Node, name="wfnet") -> PetriNet:
    net = PetriNet(name)
    i = net.add_place("i")
    o = net.add_place("o")
    _translate(net, tree, i, o)
    return net


def _translate(net, n: Node, p_in, p_out):
    if n.kind in ("activity", "tau"):
        t = net.add_transition(n.label if n.kind == "activity" else None)
        net.arc(p_in, t); net.arc(t, p_out)

    elif n.kind == "seq":
        cur = p_in
        for k, c in enumerate(n.children):
            nxt = p_out if k == len(n.children) - 1 else net.add_place()
            _translate(net, c, cur, nxt)
            cur = nxt

    elif n.kind == "xor":
        # children share the same entry/exit place -> exactly one of them fires
        for c in n.children:
            _translate(net, c, p_in, p_out)

    elif n.kind == "and":
        split, join = net.add_transition(None), net.add_transition(None)
        net.arc(p_in, split); net.arc(join, p_out)
        for c in n.children:
            a, b = net.add_place(), net.add_place()
            net.arc(split, a); net.arc(b, join)
            _translate(net, c, a, b)

    elif n.kind == "loop":
        # own internal places so that the redo-arc never re-enters p_in
        do, redo = n.children
        start, end = net.add_place(), net.add_place()
        t_in, t_out = net.add_transition(None), net.add_transition(None)
        net.arc(p_in, t_in); net.arc(t_in, start)
        _translate(net, do, start, end)
        _translate(net, redo, end, start)
        net.arc(end, t_out); net.arc(t_out, p_out)

    elif n.kind == "or":
        # inclusive OR = exclusive choice over all non-empty subsets,
        # each subset executed in parallel (labels may be duplicated).
        subsets = [list(s) for r in range(1, len(n.children) + 1)
                   for s in combinations(n.children, r)]
        options = [s[0] if len(s) == 1 else Node("and", children=s) for s in subsets]
        _translate(net, Node("xor", children=options), p_in, p_out)
    else:
        raise ValueError(f"unknown node kind {n.kind}")
