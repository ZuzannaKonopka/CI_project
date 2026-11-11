"""M1 - intermediate format: process-tree JSON, validator, JSON Schema, compact notation."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from nl2wfnet.tree import (parse_tree_string, parse_tree, tree_to_string, validate_tree,
                           tree_to_json, activities, operators_used, MAX_OR_CHILDREN)

A = lambda s: {"activity": s}


def op(o, *c):
    return {"op": o, "children": list(c)}


VALID = [
    A("a"),
    op("seq", A("a"), A("b")),
    op("xor", A("a"), {"tau": True}),
    op("and", A("a"), A("b"), A("c")),
    op("or", A("a"), A("b"), A("c"), A("d")),
    op("loop", A("a"), A("b")),
    op("loop", A("a"), {"tau": True}),
    op("seq", A("a"), op("loop", op("xor", A("b"), A("c")), op("and", A("d"), A("e")))),
]

# (invalid tree, expected fragment of the error message)
INVALID = [
    ("not a dict", "must be a JSON object"),
    ({}, "needs 'activity', 'tau' or 'op'"),
    (A(""), "non-empty string"),
    (A("   "), "non-empty string"),
    ({"activity": 5}, "non-empty string"),
    ({"activity": "a", "op": "seq"}, "must contain only 'activity'"),
    ({"tau": False}, "exactly {\"tau\": true}"),
    ({"tau": True, "x": 1}, "exactly {\"tau\": true}"),
    ({"op": "sequence", "children": [A("a"), A("b")]}, "unknown operator 'sequence'"),
    ({"op": "seq"}, "needs a list 'children'"),
    ({"op": "seq", "children": "ab"}, "needs a list 'children'"),
    (op("seq", A("a")), "at least 2 children"),
    (op("xor", A("a")), "at least 2 children"),
    (op("and"), "at least 2 children"),
    (op("loop", A("a")), "exactly 2 children"),
    (op("loop", A("a"), A("b"), A("c")), "exactly 2 children"),
    (op("loop", {"tau": True}, {"tau": True}), "no behaviour"),
    (op("or", *[A(x) for x in "abcde"]), f"at most {MAX_OR_CHILDREN} children"),
    ({"op": "seq", "children": [A("a"), A("b")], "label": "x"}, "only 'op' and 'children'"),
    (op("seq", A("a"), op("xor", A("b"), A(""))), "tree.children[1].children[1]"),
]


def test_valid_trees_have_no_errors():
    for t in VALID:
        assert validate_tree(t) == [], (t, validate_tree(t))


def test_every_invalid_tree_gets_a_precise_message():
    for t, fragment in INVALID:
        errs = validate_tree(t)
        assert errs and any(fragment in e for e in errs), (t, errs)


def test_all_errors_reported_at_once():
    with open(os.path.join(ROOT, "data", "examples", "invalid_tree.json")) as f:
        bad = json.load(f)
    assert len(validate_tree(bad["tree"])) == 5


def test_parse_tree_rejects_invalid_input():
    try:
        parse_tree(op("seq", A("a")))
    except ValueError as e:
        assert "Invalid process tree" in str(e)
    else:
        raise AssertionError("invalid tree accepted")


def test_json_schema_agrees_with_validator():
    try:
        import jsonschema
    except ImportError:
        print("  (jsonschema not installed - skipped)")
        return
    with open(os.path.join(ROOT, "schema", "process_tree.schema.json")) as f:
        schema = json.load(f)
    v = jsonschema.Draft202012Validator(schema)
    for t in VALID:
        assert not list(v.iter_errors({"process_name": "x", "tree": t})), t
    for t, _ in INVALID:
        if isinstance(t, dict) and "op" in t and t["op"] == "loop" and t.get("children") == [{"tau": True}] * 2:
            continue      # semantic rule, not expressible in the schema
        assert list(v.iter_errors({"process_name": "x", "tree": t})), t


def test_notation_roundtrip():
    for t in VALID:
        s = tree_to_string(parse_tree(t))
        assert parse_tree_string(s) == t, s


def test_notation_examples():
    assert parse_tree_string("->(a, X(b, tau))") == op("seq", A("a"), op("xor", A("b"), {"tau": True}))
    assert parse_tree_string("  *( do , redo )  ") == op("loop", A("do"), A("redo"))
    assert parse_tree_string("O(book flight, book hotel)") == op("or", A("book flight"), A("book hotel"))


def test_notation_errors():
    for bad in ["->(a, b", "Q(a, b)", "->(a,, b)", "->(a, b) c", "", "X()"]:
        try:
            parse_tree_string(bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted: {bad!r}")


def test_helpers():
    t = parse_tree(op("seq", A("a"), op("xor", A("b"), {"tau": True}), op("loop", A("a"), A("c"))))
    assert activities(t) == {"a", "b", "c"}
    assert operators_used(t) == {"seq", "xor", "loop", "tau"}
    assert tree_to_json(t) == op("seq", A("a"), op("xor", A("b"), {"tau": True}), op("loop", A("a"), A("c")))
    assert parse_tree(A("  submit CV ")).label == "submit CV"
