"""M1 - outputs: PNML, Graphviz DOT/PNG, WF-net JSON (format of the baseline)."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import shutil, subprocess, tempfile
import xml.etree.ElementTree as ET
from nl2wfnet.tree import parse_tree, parse_tree_string
from nl2wfnet.wfnet import tree_to_wfnet, wfnet_from_json, validate_wfnet_json
from nl2wfnet.analysis import bounded_language, check_soundness

NET = tree_to_wfnet(parse_tree(parse_tree_string("->(submit CV & more, X(b, tau), +(c, d))")), "demo")


def test_pnml_is_valid_xml_with_all_elements():
    root = ET.fromstring(NET.to_pnml())
    places = root.findall(".//page/place"); trans = root.findall(".//page/transition"); arcs = root.findall(".//page/arc")
    assert len(places) == len(NET.places) and len(trans) == len(NET.transitions) and len(arcs) == len(NET.arcs)
    ids = {e.get("id") for e in places + trans}
    assert all(a.get("source") in ids and a.get("target") in ids for a in arcs)


def test_pnml_markings_and_silent_transitions():
    root = ET.fromstring(NET.to_pnml())
    init = [p.get("id") for p in root.findall(".//page/place") if p.find("initialMarking") is not None]
    assert init == ["i"]
    assert root.find(".//finalmarkings/marking/place").get("idref") == "o"
    silent = [t for t in root.findall(".//transition") if t.find("toolspecific") is not None]
    assert len(silent) == sum(l is None for l in NET.transitions.values())
    names = {t.find("name/text").text for t in root.findall(".//transition")}
    assert "submit CV & more" in names            # special characters escaped correctly


def test_dot_contains_every_node():
    dot = NET.to_dot()
    assert dot.startswith("digraph") and dot.rstrip().endswith("}")
    for n in NET.places + list(NET.transitions):
        assert f'"{n}"' in dot
    assert dot.count("->") == len(NET.arcs)


def test_graphviz_renders_png():
    if not shutil.which("dot"):
        print("  (Graphviz not installed - skipped)")
        return
    with tempfile.TemporaryDirectory() as d:
        src, png = os.path.join(d, "n.dot"), os.path.join(d, "n.png")
        open(src, "w").write(NET.to_dot())
        subprocess.run(["dot", "-Tpng", src, "-o", png], check=True)
        assert open(png, "rb").read(8) == b"\x89PNG\r\n\x1a\n"


def test_wfnet_json_roundtrip_keeps_behaviour():
    js = NET.to_json()
    assert validate_wfnet_json(js) == []
    back = wfnet_from_json(json.loads(json.dumps(js)))
    assert bounded_language(back, 8) == bounded_language(NET, 8)
    assert check_soundness(back)["sound"]


def test_wfnet_json_validator_messages():
    cases = [({"places": ["i"]}, "missing list 'transitions'"),
             ({"places": ["i", "o"], "transitions": [], "arcs": []}, "exactly one source place"),
             ({"places": ["i", "o", "x"], "transitions": [{"id": "t", "label": "a"}, {"id": "u", "label": "b"}],
               "arcs": [["i", "t"], ["t", "o"], ["x", "u"], ["u", "x"]]}, "not on a path"),
             ({"places": ["i", "o"], "transitions": [{"id": "t", "label": "a"}], "arcs": [["i", "o"]]}, "must connect a place and a transition"),
             ({"places": ["p", "o"], "transitions": [{"id": "t", "label": "a"}], "arcs": [["p", "t"], ["t", "o"]]}, "'i' is missing"),
             ({"places": ["i", "o"], "transitions": [{"id": "t", "label": ""}], "arcs": [["i", "t"], ["t", "o"]]}, "non-empty string or null"),
             ({"places": ["i", "o", "i"], "transitions": [{"id": "t", "label": "a"}], "arcs": [["i", "t"], ["t", "o"]]}, "unique"),
             ({"places": ["i", "o"], "transitions": [{"id": "t", "label": "a"}, {"id": "u", "label": "b"}],
               "arcs": [["i", "t"], ["t", "o"], ["o", "u"], ["u", "o"]]}, "'o' must not have outgoing arcs")]
    for obj, frag in cases:
        errs = validate_wfnet_json(obj)
        assert any(frag in e for e in errs), (obj, errs)
