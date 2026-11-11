"""Intermediate representation: process trees encoded as JSON.

Node formats
------------
Activity : {"activity": "submit CV"}
Silent   : {"tau": true}                      # invisible step (skip)
Operator : {"op": OP, "children": [node, ...]}

OP is one of
  "seq"  sequence            children executed left to right       (>= 2 children)
  "xor"  exclusive choice    exactly one child is executed         (>= 2 children)
  "and"  parallel            all children, in any interleaving     (>= 2 children)
  "or"   inclusive choice    any non-empty subset, in parallel     (2..4 children)
  "loop" loop (do, redo)     do, then 0..n times (redo, do)        (exactly 2 children)

A document is {"process_name": str, "tree": node}.
"""
from dataclasses import dataclass, field
from typing import List, Optional

OPERATORS = {"seq", "xor", "and", "or", "loop"}
SYMBOLS = {"seq": "->", "xor": "X", "and": "+", "or": "O", "loop": "*"}
MAX_OR_CHILDREN = 4  # subset encoding of OR grows as 2^n - 1


@dataclass
class Node:
    kind: str                      # "activity" | "tau" | operator name
    label: Optional[str] = None    # only for activities
    children: List["Node"] = field(default_factory=list)


def validate_tree(obj, path="tree"):
    """Return a list of human-readable errors (empty list = valid).

    The messages are written so they can be sent back to the LLM
    in a repair prompt.
    """
    errors = []
    if not isinstance(obj, dict):
        return [f"{path}: node must be a JSON object, got {type(obj).__name__}"]
    keys = set(obj)
    if "activity" in obj:
        if keys - {"activity"}:
            errors.append(f"{path}: activity node must contain only 'activity', found {sorted(keys)}")
        if not isinstance(obj["activity"], str) or not obj["activity"].strip():
            errors.append(f"{path}: 'activity' must be a non-empty string")
        return errors
    if "tau" in obj:
        if obj.get("tau") is not True or keys - {"tau"}:
            errors.append(f"{path}: silent node must be exactly {{\"tau\": true}}")
        return errors
    if "op" not in obj:
        return [f"{path}: node needs 'activity', 'tau' or 'op'"]
    op = obj["op"]
    if op not in OPERATORS:
        errors.append(f"{path}: unknown operator '{op}', use one of {sorted(OPERATORS)}")
    if keys - {"op", "children"}:
        errors.append(f"{path}: operator node must contain only 'op' and 'children', found {sorted(keys)}")
    ch = obj.get("children")
    if not isinstance(ch, list):
        return errors + [f"{path}: '{op}' needs a list 'children'"]
    n = len(ch)
    if op == "loop" and n != 2:
        errors.append(f"{path}: 'loop' needs exactly 2 children [do, redo], got {n}")
    elif op in {"seq", "xor", "and", "or"} and n < 2:
        errors.append(f"{path}: '{op}' needs at least 2 children, got {n}")
    if op == "or" and n > MAX_OR_CHILDREN:
        errors.append(f"{path}: 'or' supports at most {MAX_OR_CHILDREN} children, got {n}")
    for i, c in enumerate(ch):
        errors += validate_tree(c, f"{path}.children[{i}]")
    if op == "loop" and n == 2 and ch[0] == {"tau": True} and ch[1] == {"tau": True}:
        errors.append(f"{path}: loop with silent do and redo has no behaviour")
    return errors


def parse_tree(obj) -> Node:
    errs = validate_tree(obj)
    if errs:
        raise ValueError("Invalid process tree:\n" + "\n".join(errs))
    return _build(obj)


def _build(obj) -> Node:
    if "activity" in obj:
        return Node("activity", obj["activity"].strip())
    if "tau" in obj:
        return Node("tau")
    return Node(obj["op"], children=[_build(c) for c in obj["children"]])


def tree_to_string(n: Node) -> str:
    """Compact textual notation, e.g. ->(a, X(b, c))."""
    if n.kind == "activity":
        return n.label
    if n.kind == "tau":
        return "tau"
    return f"{SYMBOLS[n.kind]}(" + ", ".join(tree_to_string(c) for c in n.children) + ")"


def activities(n: Node) -> set:
    if n.kind == "activity":
        return {n.label}
    return set().union(*[activities(c) for c in n.children]) if n.children else set()


# ---------------------------------------------------------------------------
# Compact notation <-> JSON
# ---------------------------------------------------------------------------
_SYM2OP = {"->": "seq", "X": "xor", "+": "and", "O": "or", "*": "loop"}


def parse_tree_string(text: str) -> dict:
    """Parse the compact notation used in the review spreadsheet into tree JSON.

    Example: "->(a, X(b, tau), *(c, d))"
    Operators: ->( seq, X( xor, +( and, O( or, *( loop; 'tau' is the silent step.
    Activity labels must not contain '(', ')' or ','.
    """
    s, pos = text.strip(), 0

    def skip():
        nonlocal pos
        while pos < len(s) and s[pos].isspace():
            pos += 1

    def node():
        nonlocal pos
        skip()
        for sym, op in _SYM2OP.items():
            if s.startswith(sym + "(", pos):
                pos += len(sym) + 1
                children = [node()]
                skip()
                while pos < len(s) and s[pos] == ",":
                    pos += 1
                    children.append(node())
                    skip()
                if pos >= len(s) or s[pos] != ")":
                    raise ValueError(f"expected ')' at position {pos} in: {text}")
                pos += 1
                return {"op": op, "children": children}
        start = pos
        while pos < len(s) and s[pos] not in "(),":
            pos += 1
        label = s[start:pos].strip()
        if not label:
            raise ValueError(f"empty label at position {start} in: {text}")
        if pos < len(s) and s[pos] == "(":
            raise ValueError(f"unknown operator '{label}(' in: {text}")
        return {"tau": True} if label == "tau" else {"activity": label}

    result = node()
    skip()
    if pos != len(s):
        raise ValueError(f"unexpected text after position {pos} in: {text}")
    return result


def tree_to_json(n: Node) -> dict:
    if n.kind == "activity":
        return {"activity": n.label}
    if n.kind == "tau":
        return {"tau": True}
    return {"op": n.kind, "children": [tree_to_json(c) for c in n.children]}


def operators_used(n: Node) -> set:
    """Operators (and 'tau') occurring in a tree."""
    if n.kind == "activity":
        return set()
    if n.kind == "tau":
        return {"tau"}
    return {n.kind}.union(*[operators_used(c) for c in n.children])
