"""Evaluation of one generated model against the reference tree.

Four dimensions, reported separately (no combined score):
 1. validity          - output passed format/structure validation (after repairs)
 2. soundness         - classical WF-net soundness of the resulting net
 3. structural fidelity
      activity_p/r/f1 - distinct activity labels (after label matching)
      footprint_sim   - agreement of footprint matrices (->, <-, ||, #)
 4. behavioural fidelity
      trace_p/r/f1    - traces with at most `max_len` activities (bounded language)
Invalid outputs get 0 for every fidelity measure (they produce no model).
"""
from .tree import parse_tree, activities
from .wfnet import tree_to_wfnet, relabel
from .analysis import check_soundness, bounded_language, footprint_similarity
from .labels import match_labels

METRICS = ["valid", "sound", "activity_p", "activity_r", "activity_f1",
           "footprint_sim", "trace_p", "trace_r", "trace_f1"]


def _prf(gen, ref):
    inter = len(gen & ref)
    p = inter / len(gen) if gen else 0.0
    r = inter / len(ref) if ref else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def reference_cache(ref_tree_json, max_len):
    tree = parse_tree(ref_tree_json)
    net = tree_to_wfnet(tree, "reference")
    return {"labels": activities(tree), "traces": bounded_language(net, max_len=max_len)}


def evaluate_net(net, ref, max_len=12, overrides=None, threshold=0.5):
    """Score a generated PetriNet (None = invalid output) against a reference cache."""
    row = {m: 0.0 for m in METRICS}
    row.update({"valid": 0, "sound": 0, "label_map": {}, "unmatched_labels": [],
                "language_exploded": 0, "n_traces_gen": 0, "n_traces_ref": len(ref["traces"])})
    if net is None:
        return row
    row["valid"] = 1
    gen_labels = {l for l in net.transitions.values() if l is not None}
    mapping, _ = match_labels(gen_labels, ref["labels"], threshold, overrides)
    row["label_map"] = mapping
    row["unmatched_labels"] = sorted(gen_labels - set(mapping))
    mapped = {mapping.get(l, "?" + l) for l in gen_labels}
    row["activity_p"], row["activity_r"], row["activity_f1"] = _prf(mapped, ref["labels"])
    snd = check_soundness(net)
    row["sound"] = int(snd["sound"])
    net2 = relabel(net, {l: mapping.get(l, "?" + l) for l in gen_labels})
    try:
        traces = bounded_language(net2, max_len=max_len)
    except RuntimeError:
        row["language_exploded"] = 1
        return row
    row["n_traces_gen"] = len(traces)
    row["trace_p"], row["trace_r"], row["trace_f1"] = _prf(traces, ref["traces"])
    row["footprint_sim"] = footprint_similarity(traces, ref["traces"]) if traces else 0.0
    return row
