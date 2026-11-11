"""M1 - soundness checker: it must accept sound nets and reject every kind of unsound net."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from nl2wfnet.wfnet import wfnet_from_json, tree_to_wfnet
from nl2wfnet.tree import parse_tree, parse_tree_string
from nl2wfnet.analysis import check_soundness


def net(places, transitions, arcs):
    return wfnet_from_json({"places": places,
                            "transitions": [{"id": t, "label": l} for t, l in transitions],
                            "arcs": [list(a) for a in arcs]})


def test_sound_sequence_and_choice():
    n = net(["i", "p", "o"], [("t1", "a"), ("t2", "b"), ("t3", "c")],
            [("i", "t1"), ("t1", "p"), ("p", "t2"), ("t2", "o"), ("p", "t3"), ("t3", "o")])
    rep = check_soundness(n)
    assert rep["sound"] and rep["states"] == 3


def test_and_split_xor_join_leaves_tokens():
    with open(os.path.join(ROOT, "data", "examples", "unsound_wfnet.json")) as f:
        rep = check_soundness(wfnet_from_json(json.load(f)))
    assert not rep["sound"] and not rep["proper_completion"] and not rep["option_to_complete"]


def test_xor_split_and_join_deadlocks():
    # a OR b is chosen, but the join waits for both -> deadlock, join is dead
    n = net(["i", "p1", "p2", "o"], [("ta", "a"), ("tb", "b"), ("tj", None)],
            [("i", "ta"), ("i", "tb"), ("ta", "p1"), ("tb", "p2"), ("p1", "tj"), ("p2", "tj"), ("tj", "o")])
    rep = check_soundness(n)
    assert not rep["sound"] and not rep["option_to_complete"] and not rep["no_dead_transitions"]
    assert ("tj", None) in rep["dead_transitions"]


def test_dead_transition_only():
    # tx needs tokens in p1 AND p2 at the same time, which never happens (one token only).
    # The net completes properly, but tx is dead -> not sound.
    n = net(["i", "p1", "p2", "o"], [("ta", "a"), ("tb", "b"), ("tc", "c"), ("td", "d"), ("tx", "x")],
            [("i", "ta"), ("ta", "p1"), ("p1", "tb"), ("tb", "o"), ("p1", "tc"), ("tc", "p2"), ("p2", "td"),
             ("td", "o"), ("p1", "tx"), ("p2", "tx"), ("tx", "o")])
    rep = check_soundness(n)
    assert rep["structure_errors"] == [] and rep["option_to_complete"] and rep["proper_completion"]
    assert not rep["no_dead_transitions"] and not rep["sound"] and rep["dead_transitions"] == [("tx", "x")]


def test_unbounded_net_is_not_sound():
    # t1 can fire forever, adding tokens to p -> unbounded, search is truncated
    n = net(["i", "p", "o"], [("t1", "a"), ("t2", "b")],
            [("i", "t1"), ("t1", "i"), ("t1", "p"), ("i", "t2"), ("t2", "o")])
    rep = check_soundness(n, max_tokens=10)
    assert not rep["sound"]


def test_not_a_wf_net():
    disconnected = net(["i", "o", "x"], [("t1", "a"), ("t2", "b")], [("i", "t1"), ("t1", "o"), ("x", "t2"), ("t2", "o")])
    assert check_soundness(disconnected)["structure_errors"]
    two_sinks = net(["i", "o", "z"], [("t1", "a")], [("i", "t1"), ("t1", "o"), ("t1", "z")])
    assert any("sink" in e for e in check_soundness(two_sinks)["structure_errors"])


def test_converter_output_sound_for_all_operators():
    for s in ["->(a, X(b, tau), *(c, +(d, e)), O(f, g, h))", "*(O(a, b), X(c, tau))"]:
        assert check_soundness(tree_to_wfnet(parse_tree(parse_tree_string(s))))["sound"]
