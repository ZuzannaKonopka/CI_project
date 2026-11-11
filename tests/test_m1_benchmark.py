"""M1 - benchmark: 20 descriptions with reference trees (data/benchmark_v1.xlsx)."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from collections import Counter
from nl2wfnet.benchmark import load_xlsx
from nl2wfnet.tree import parse_tree, activities, tree_to_string
from nl2wfnet.wfnet import tree_to_wfnet
from nl2wfnet.analysis import check_soundness, bounded_language
from m1_case_studies import LETTERS, recruitment_rules

ITEMS, PROBLEMS = load_xlsx(os.path.join(ROOT, "data", "benchmark_v1.xlsx"))
BY_ID = {i["id"]: i for i in ITEMS}


def traces(cid, max_len=12):
    return bounded_language(tree_to_wfnet(parse_tree(BY_ID[cid]["reference"]["tree"])), max_len)


def test_spreadsheet_has_no_problems():
    assert PROBLEMS == [], PROBLEMS


def test_size_split_and_ids():
    assert [i["id"] for i in ITEMS] == [f"P{k:02d}" for k in range(1, 21)]
    assert Counter(i["split"] for i in ITEMS) == {"dev": 12, "test": 8}
    assert len({i["description"] for i in ITEMS}) == 20
    assert all(len(i["description"].split()) >= 25 for i in ITEMS)


def test_every_construct_in_both_splits():
    for split in ("dev", "test"):
        ops = Counter(o for i in ITEMS if i["split"] == split for o in i["operators"])
        for o in ("seq", "xor", "and", "or", "loop", "tau"):
            assert ops[o] >= 1, (split, o)


def test_operator_counts_match_the_readme():
    want = {"dev": {"seq": 12, "xor": 7, "and": 5, "or": 3, "loop": 3, "tau": 1},
            "test": {"seq": 8, "xor": 5, "and": 3, "or": 3, "loop": 4, "tau": 1}}
    for split, w in want.items():
        got = Counter(o for i in ITEMS if i["split"] == split for o in i["operators"])
        assert {k: got[k] for k in w} == w, (split, got)


def test_every_reference_is_a_sound_wf_net_with_finite_behaviour():
    for i in ITEMS:
        net = tree_to_wfnet(parse_tree(i["reference"]["tree"]), i["id"])
        rep = check_soundness(net)
        assert rep["sound"] and not rep["truncated"], (i["id"], rep)
        assert len(bounded_language(net, 12)) >= 2, i["id"]       # every case has a real choice/loop/concurrency


def test_labels_are_reusable_in_notation():
    for i in ITEMS:
        for a in activities(parse_tree(i["reference"]["tree"])):
            assert a == a.strip() and not set(a) & set("(),") and a != "tau", (i["id"], a)


def test_recruitment_matches_description_rules():
    coded = ["".join(LETTERS[x] for x in t) for t in traces("P01")]
    assert sorted(coded) == sorted(["aci", "abdfh", "abfdh", "abdgi", "abgdi", "abefi", "abfei", "abegi", "abgei"])
    assert all(recruitment_rules(c) == [] for c in coded)


def test_rules_detect_wrong_recruitment_traces():
    for wrong in ["abdgh", "abci", "ab", "acbi", "abddfh", "abdfi"]:
        assert recruitment_rules(wrong), wrong


def test_business_trip_inclusive_or():
    mids = [t[2:-1] for t in traces("P02")]
    assert Counter(len(m) for m in mids) == {1: 3, 2: 6, 3: 6}


def test_document_submission_loop():
    reps = sorted(t.count("resubmit documents") for t in traces("P03", 12))
    assert reps == [0, 1, 2, 3]
    assert all(t[-1] == "register application" and t.count("check completeness") == t.count("resubmit documents") + 1
               for t in traces("P03", 12))


def test_optional_step_and_skippable_sequence():
    assert len(traces("P08")) == 2 and len(traces("P16")) == 2
    assert any("reserve book" not in t for t in traces("P16"))
