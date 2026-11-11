"""One generation = prompt -> LLM -> parse -> validate -> (repair)* -> WF-net.

Both approaches use exactly the same loop and the same repair budget.
"""
import json
import re
import time

from .prompts import build_messages, repair_message, PROMPT_VERSION
from .tree import validate_tree, parse_tree
from .wfnet import tree_to_wfnet, validate_wfnet_json, wfnet_from_json


def extract_json(raw):
    """Parse a JSON object from an LLM answer (tolerates ``` fences and text around it)."""
    raw = raw.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.S)
    if m:
        raw = m.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start:end + 1])
        raise


def check_output(approach, raw):
    """Return (document, errors) for one raw LLM answer."""
    try:
        doc = extract_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        return None, [f"the answer is not valid JSON ({e})"]
    if not isinstance(doc, dict):
        return None, ["the answer must be one JSON object"]
    if approach == "structured":
        if "tree" not in doc:
            return doc, ["missing key 'tree'"]
        return doc, validate_tree(doc["tree"])
    return doc, validate_wfnet_json(doc)


def to_net(approach, doc, name="generated"):
    if approach == "structured":
        return tree_to_wfnet(parse_tree(doc["tree"]), name)
    return wfnet_from_json(doc, name)


def generate(approach, description, client, seed=0, max_repairs=2, case_id=""):
    messages = build_messages(approach, description)
    record = {"approach": approach, "case": case_id, "seed": seed, "client": client.name,
              "prompt_version": PROMPT_VERSION, "max_repairs": max_repairs, "attempts": [],
              "valid": False, "document": None}
    t0 = time.time()
    for attempt in range(max_repairs + 1):
        if hasattr(client, "key"):
            client.key = f"{case_id}_{approach}_s{seed}_a{attempt}"
        raw, meta = client.chat(messages, seed=seed)
        doc, errors = check_output(approach, raw)
        record["attempts"].append({"raw": raw, "errors": errors, **(meta or {})})
        if not errors:
            record["valid"], record["document"] = True, doc
            break
        messages = messages + [{"role": "assistant", "content": raw},
                               {"role": "user", "content": repair_message(errors)}]
    record["n_repairs"] = len(record["attempts"]) - 1
    record["total_latency_s"] = round(time.time() - t0, 2)
    record["output_chars"] = len(record["attempts"][-1]["raw"])
    return record
