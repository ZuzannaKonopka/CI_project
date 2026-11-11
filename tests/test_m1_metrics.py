"""M1 - evaluation measures: footprint, trace precision/recall, label matching, error injection."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from nl2wfnet.metrics import evaluate_net, reference_cache
from nl2wfnet.tree import parse_tree_string, parse_tree
from nl2wfnet.wfnet import tree_to_wfnet
from nl2wfnet.analysis import footprint, footprint_similarity, language_similarity
from nl2wfnet.labels import match_labels, similarity
from nl2wfnet.benchmark import load_xlsx
from nl2wfnet import perturb

REF = parse_tree_string("->(a, +(b, c), X(d, e))")


def score(t, ref=REF, L=10):
    return evaluate_net(tree_to_wfnet(parse_tree(t)), reference_cache(ref, L), L)


def test_footprint_relations():
    fp = footprint({tuple("abc"), tuple("acb")})
    assert fp[("a", "b")] == "->" and fp[("b", "a")] == "<-" and fp[("b", "c")] == "||" and fp[("a", "a")] == "#"
    assert footprint_similarity({tuple("ab")}, {tuple("ab")}) == 1.0


def test_identity_is_perfect():
    r = score(REF)
    assert r["trace_f1"] == r["footprint_sim"] == r["activity_f1"] == 1 and r["sound"] == 1


def test_too_strict_model_loses_recall_only():
    r = score(perturb.and_to_seq(REF))
    assert r["trace_p"] == 1 and r["trace_r"] == 0.5


def test_too_permissive_model_loses_precision_only():
    r = score(parse_tree_string("->(a, +(b, c), O(d, e))"))
    assert r["trace_r"] == 1 and r["trace_p"] < 1


def test_invalid_output_scores_zero():
    r = evaluate_net(None, reference_cache(REF, 10))
    assert r["valid"] == 0 and r["trace_f1"] == 0 and r["sound"] == 0


def test_language_similarity_values():
    s = language_similarity(tree_to_wfnet(parse_tree(parse_tree_string("X(a, b)"))),
                            tree_to_wfnet(parse_tree(parse_tree_string("X(a, b, c)"))))
    assert (s["precision"], s["recall"]) == (1.0, 2 / 3)


def test_label_matching_paraphrases_and_antonyms():
    ref = ["submit CV", "screening positive", "screening negative", "reject candidate", "make offer"]
    gen = ["CV submitted", "HR screening passed", "HR screening failed", "candidate rejected", "send offer"]
    m, _ = match_labels(gen, ref)
    assert m == dict(zip(gen, ref))
    assert similarity("approve loan", "reject loan") == 0 and similarity("interview positive", "interview negative") == 0
    m, s = match_labels(["hand keys over"], ["hand over keys"], overrides={"hand keys over": "hand over keys"})
    assert s["hand keys over"] == "manual"


def test_error_injection_on_benchmark():
    """Every injected control-flow error keeps the net sound but lowers trace F1;
    paraphrasing all labels changes nothing."""
    items, _ = load_xlsx(os.path.join(ROOT, "data", "benchmark_v1.xlsx"))
    for it in items:
        ref = it["reference"]["tree"]
        cache = reference_cache(ref, 12)
        for err in perturb.ERROR_TYPES:
            t = perturb.apply(err, ref)
            if t is None:
                continue
            r = evaluate_net(tree_to_wfnet(parse_tree(t)), cache, 12)
            assert r["sound"] == 1, (it["id"], err)
            if err == "paraphrase_labels":
                assert r["trace_f1"] == 1, (it["id"], err)
            else:
                assert r["trace_f1"] < 1, (it["id"], err, r["trace_f1"])
