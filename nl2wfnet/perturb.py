"""Controlled error injection into process trees.

Used to validate the evaluation measures (scripts/m1_validate_metrics.py):
each function applies ONE typical modelling error to a correct reference tree,
and we check that the measures react to it. These are deliberately modified
reference trees, not LLM outputs.
Every function returns a new tree (JSON) or None if the error type does not apply.
"""
import copy

ERROR_TYPES = ["paraphrase_labels", "and_to_seq", "or_to_xor", "or_to_and", "xor_to_and",
               "drop_loop", "drop_activity", "swap_sequence"]


def _nodes(t, path=()):
    yield path, t
    for k, c in enumerate(t.get("children", [])):
        yield from _nodes(c, path + (k,))


def _get(t, path):
    for k in path:
        t = t["children"][k]
    return t


def _set(t, path, new):
    if not path:
        return new
    _get(t, path[:-1])["children"][path[-1]] = new
    return t


def _first(t, pred):
    for path, n in _nodes(t):
        if pred(n):
            return path
    return None


def _change_op(tree, src, dst):
    t = copy.deepcopy(tree)
    p = _first(t, lambda n: n.get("op") == src)
    if p is None:
        return None
    _get(t, p)["op"] = dst
    return t


def _passive(label):
    """'submit CV' -> 'CV submitted' (rule-based paraphrase)."""
    w = label.split()
    if len(w) < 2:
        return "the " + label
    v = w[0]
    if v.endswith("e"):
        pp = v + "d"
    elif v.endswith("y") and v[-2:-1] not in "aeiou":
        pp = v[:-1] + "ied"
    else:
        pp = v + "ed"
    return " ".join(w[1:]) + " " + pp


def paraphrase_labels(tree, rng=None):
    t = copy.deepcopy(tree)
    for _, n in _nodes(t):
        if "activity" in n:
            n["activity"] = _passive(n["activity"])
    return t


def and_to_seq(tree, rng=None):
    return _change_op(tree, "and", "seq")


def or_to_xor(tree, rng=None):
    return _change_op(tree, "or", "xor")


def or_to_and(tree, rng=None):
    return _change_op(tree, "or", "and")


def xor_to_and(tree, rng=None):
    t = copy.deepcopy(tree)
    p = _first(t, lambda n: n.get("op") == "xor" and not any("tau" in c for c in n["children"]))
    if p is None:
        return None
    _get(t, p)["op"] = "and"
    return t


def drop_loop(tree, rng=None):
    t = copy.deepcopy(tree)
    p = _first(t, lambda n: n.get("op") == "loop")
    if p is None:
        return None
    return _set(t, p, _get(t, p)["children"][0])


def drop_activity(tree, rng=None):
    """Remove the last activity of the outermost sequence (it needs >= 3 children)."""
    t = copy.deepcopy(tree)
    p = _first(t, lambda n: n.get("op") == "seq" and len(n["children"]) >= 3
               and any("activity" in c for c in n["children"]))
    if p is None:
        return None
    ch = _get(t, p)["children"]
    k = max(i for i, c in enumerate(ch) if "activity" in c)
    del ch[k]
    return t


def swap_sequence(tree, rng=None):
    """Swap the first two activities that follow each other directly in a sequence."""
    t = copy.deepcopy(tree)
    for path, n in _nodes(t):
        if n.get("op") == "seq":
            ch = n["children"]
            for k in range(len(ch) - 1):
                if "activity" in ch[k] and "activity" in ch[k + 1]:
                    ch[k], ch[k + 1] = ch[k + 1], ch[k]
                    return t
    return None


def apply(error_type, tree, rng=None):
    return globals()[error_type](tree, rng)
