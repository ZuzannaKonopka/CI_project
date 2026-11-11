"""Matching generated activity labels to reference labels.

LLMs paraphrase ("CV submitted" vs "submit CV"). Before traces can be compared,
each generated label is mapped to at most one reference label (one-to-one).

similarity = 0.6 * Jaccard(stemmed tokens) + 0.4 * character ratio (difflib)
Pairs are matched greedily by decreasing similarity above a threshold.
Manual overrides (data/label_overrides.json) always win; every automatic
mapping is stored with the results for transparency.
"""
import json
import os
import re
from difflib import SequenceMatcher

STOPWORDS = {"the", "a", "an", "of", "to", "for", "by", "with", "is", "are", "be", "been",
             "and", "or", "its", "their", "his", "her", "on", "in", "at", "from", "as", "it"}


# verbs that carry little meaning in activity labels ("make offer" = "offer")
LIGHT_VERBS = {"make", "perform", "carry", "out", "do", "conduct", "execute", "get"}
# stems mapped to a canonical stem
SYNONYMS = {"pass": "positi", "succes": "positi", "fail": "negati", "refus": "reject",
            "declin": "reject", "deny": "reject", "deni": "reject", "approv": "accept"}
# canonical stems that must never be matched with each other
ANTONYMS = [("positi", "negati"), ("accept", "reject"), ("comple", "incomp"), ("valid", "invali")]


def _stem(w):
    if w.endswith("ies") and len(w) > 4:
        w = w[:-3] + "y"
    elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        w = w[:-1]
    for suf in ("ing", "ed"):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            w = w[: -len(suf)]
            break
    if w.endswith("e") and len(w) > 3:
        w = w[:-1]
    return w[:6]


def tokens(label):
    words = re.findall(r"[a-z0-9]+", label.lower())
    words = [w for w in words if w not in STOPWORDS] or words
    content = [w for w in words if w not in LIGHT_VERBS] or words
    return [SYNONYMS.get(_stem(w), _stem(w)) for w in content]


def similarity(a, b):
    ta, tb = set(tokens(a)), set(tokens(b))
    for x, y in ANTONYMS:
        if (x in ta and y in tb) or (y in ta and x in tb):
            return 0.0
    jac = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    char = SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    return 0.6 * jac + 0.4 * char


def match_labels(generated, reference, threshold=0.5, overrides=None):
    """Return {generated_label: reference_label} (one-to-one) and the scores used."""
    generated, reference = sorted(set(generated)), sorted(set(reference))
    mapping, scores = {}, {}
    used_ref = set()
    for g, r in (overrides or {}).items():
        if g in generated and r in reference:
            mapping[g] = r; used_ref.add(r); scores[g] = "manual"
    cand = sorted(((similarity(g, r), g, r) for g in generated for r in reference
                   if g not in mapping and r not in used_ref), reverse=True)
    for s, g, r in cand:
        if s < threshold:
            break
        if g in mapping or r in used_ref:
            continue
        mapping[g] = r; used_ref.add(r); scores[g] = round(s, 3)
    return mapping, scores


def load_overrides(case_id, path="data/label_overrides.json"):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f).get(case_id, {})
