"""M1 - converter: process tree -> WF-net (structure, behaviour per operator, random trees)."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import random
from itertools import permutations
from nl2wfnet.tree import parse_tree, parse_tree_string, validate_tree
from nl2wfnet.wfnet import tree_to_wfnet
from nl2wfnet.analysis import check_soundness, bounded_language


def net_of(s):
    return tree_to_wfnet(parse_tree(parse_tree_string(s)))


def lang(s, max_len=8):
    return bounded_language(net_of(s), max_len=max_len, max_silent=30)


def T(*strings):
    """Traces written as 'abc' -> ('a','b','c'); '' = empty trace."""
    return {tuple(x) for x in strings}


# ---------- reference semantics of process trees (independent of the Petri net) ----------
def _shuffle(a, b):
    if not a:
        return {b}
    if not b:
        return {a}
    return {(a[0],) + r for r in _shuffle(a[1:], b)} | {(b[0],) + r for r in _shuffle(a, b[1:])}


def tree_language(t, L):
    """All traces of tree t with at most L activities, computed directly from the
    operator definitions (loops unrolled until no new trace of length <= L appears)."""
    if "activity" in t:
        return {(t["activity"],)} if L >= 1 else set()
    if "tau" in t:
        return {()}
    ch = [tree_language(c, L) for c in t["children"]]
    cut = lambda S: {x for x in S if len(x) <= L}
    if t["op"] == "seq":
        out = {()}
        for S in ch:
            out = cut({x + y for x in out for y in S})
        return out
    if t["op"] == "xor":
        return set().union(*ch)

    def par(sets):
        out = {()}
        for S in sets:
            out = cut({z for x in out for y in S for z in _shuffle(x, y)})
        return out
    if t["op"] == "and":
        return par(ch)
    if t["op"] == "or":
        from itertools import combinations
        return set().union(*[par(list(c)) for k in range(1, len(ch) + 1) for c in combinations(ch, k)])
    if t["op"] == "loop":
        do, redo = ch
        out, frontier = set(do), set(do)
        while frontier:
            new = cut({x + r + d for x in frontier for r in redo for d in do}) - out
            out |= new
            frontier = new
        return out
    raise ValueError(t)


# ---------- structure ----------
def test_every_net_is_a_wf_net():
    for s in ["a", "->(a, b)", "X(a, b)", "+(a, b)", "O(a, b, c)", "*(a, b)", "->(a, X(b, tau), *(c, +(d, e)))"]:
        net = net_of(s)
        assert net.wf_structure_errors() == [], (s, net.wf_structure_errors())
        assert "i" in net.places and "o" in net.places


def test_block_sizes_per_operator():
    # (tree, places, visible transitions, silent transitions)
    cases = [("a", 2, 1, 0), ("tau", 2, 0, 1), ("->(a, b, c)", 4, 3, 0), ("X(a, b, c)", 2, 3, 0),
             ("+(a, b)", 6, 2, 2), ("+(a, b, c)", 8, 3, 2), ("*(a, b)", 4, 2, 2),
             ("O(a, b)", 6, 4, 2)]     # O(a,b) = X(a, b, +(a,b))
    for s, n_p, n_vis, n_sil in cases:
        net = net_of(s)
        vis = sum(l is not None for l in net.transitions.values())
        assert (len(net.places), vis, len(net.transitions) - vis) == (n_p, n_vis, n_sil), (s, len(net.places), vis)


def test_or_grows_with_subsets_and_is_limited():
    for n in (2, 3, 4):
        s = "O(" + ", ".join("abcd"[:n]) + ")"
        vis = sum(l is not None for l in net_of(s).transitions.values())
        assert vis == sum(k * len(list(__import__("itertools").combinations(range(n), k))) for k in range(1, n + 1))
    assert validate_tree(parse_tree_string("O(a, b, c, d, e)"))


# ---------- behaviour per operator ----------
def test_activity_and_sequence():
    assert lang("a") == T("a")
    assert lang("->(a, b, c)") == T("abc")


def test_exclusive_choice():
    assert lang("X(a, b, c)") == T("a", "b", "c")


def test_parallel():
    assert lang("+(a, b)") == T("ab", "ba")
    assert lang("+(a, b, c)") == {p for p in permutations("abc")}


def test_inclusive_or():
    assert lang("O(a, b)") == T("a", "b", "ab", "ba")
    L = lang("O(a, b, c)")
    assert len(L) == 3 + 6 + 6 and T("c", "ca", "bca") <= L and not T("aa", "") & L


def test_optional_step_with_tau():
    assert lang("->(a, X(b, tau), c)") == T("abc", "ac")


def test_loop_language_up_to_bound():
    assert lang("*(a, b)", 5) == T("a", "aba", "ababa")
    assert lang("*(a, tau)", 3) == T("a", "aa", "aaa")
    assert lang("*(->(a, b), c)", 8) == T("ab", "abcab", "abcabcab")


def test_nested_operators():
    assert lang("->(a, +(b, X(c, d)), e)") == T("abce", "acbe", "abde", "adbe")
    assert lang("*(X(a, b), c)", 3) == T("a", "b", "aca", "acb", "bca", "bcb")


def test_every_operator_net_is_sound():
    for s in ["a", "tau", "->(a, b)", "X(a, b)", "X(a, tau)", "+(a, b, c)", "O(a, b, c, d)", "*(a, b)", "*(a, tau)",
              "*(tau, a)", "*(+(a, b), X(c, tau))", "+(*(a, b), O(c, d))", "X(*(a, b), *(c, d))", "*(*(a, b), c)"]:
        rep = check_soundness(net_of(s))
        assert rep["sound"], (s, rep)


# ---------- property test on random trees ----------
def random_tree(depth, rng, labels):
    if depth == 0 or rng.random() < 0.3:
        return {"tau": True} if rng.random() < 0.1 else {"activity": next(labels)}
    o = rng.choice(["seq", "xor", "and", "or", "loop"])
    n = 2 if o == "loop" else rng.randint(2, 3)
    return {"op": o, "children": [random_tree(depth - 1, rng, labels) for _ in range(n)]}


def test_random_trees_sound_and_language_equal(n=300, seed=1, max_activities=6, max_len=6):
    """For random valid trees (with loops): the WF-net is sound AND allows exactly the
    traces defined by the tree semantics, up to max_len activities."""
    rng = random.Random(seed)
    done = loops = 0
    while done < n:
        labels = iter(f"a{i}" for i in range(10_000))
        t = random_tree(3, rng, labels)
        if validate_tree(t) or str(t).count("'activity'") > max_activities:
            continue
        net = tree_to_wfnet(parse_tree(t))
        rep = check_soundness(net)
        assert rep["sound"], (t, rep)
        assert bounded_language(net, max_len=max_len, max_silent=40) == tree_language(t, max_len), t
        loops += "loop" in str(t)
        done += 1
    print(f"  {n} random trees ({loops} with loops): all sound, all languages equal up to {max_len} activities")
