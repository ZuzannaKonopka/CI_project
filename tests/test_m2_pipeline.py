"""M2 - LLM stage: JSON extraction, repair loop, Ollama client (no real LLM needed)."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from nl2wfnet.pipeline import generate, extract_json, to_net
from nl2wfnet.llm import OllamaClient
from nl2wfnet.analysis import check_soundness


def test_extract_json_tolerates_fences():
    assert extract_json('Here:\n```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('blah {"a": {"b": 2}} blah') == {"a": {"b": 2}}


class ScriptedClient:
    """Unit-test helper: returns fixed answers in order (first malformed, then valid)."""
    name = "scripted-test-client"

    def __init__(self, answers):
        self.answers = list(answers)

    def chat(self, messages, seed=0):
        return self.answers.pop(0), {}


def test_repair_loop_sends_errors_back_and_accepts_fix():
    bad = '{"process_name": "x", "tree": {"op": "sequence", "children": []}}'
    good = '{"process_name": "x", "tree": {"op": "seq", "children": [{"activity": "a"}, {"activity": "b"}]}}'
    rec = generate("structured", "A then B.", ScriptedClient([bad, good]), seed=1, max_repairs=2, case_id="T1")
    assert rec["valid"] and rec["n_repairs"] == 1 and "unknown operator" in rec["attempts"][0]["errors"][0]


def test_repair_budget_is_respected():
    bad = '{"places": ["i"], "transitions": [], "arcs": []}'
    rec = generate("baseline", "A then B.", ScriptedClient([bad] * 3), seed=1, max_repairs=2)
    assert not rec["valid"] and len(rec["attempts"]) == 3


def test_ollama_client_against_fake_server():
    answer = {"process_name": "t", "tree": {"op": "seq", "children": [{"activity": "a"}, {"activity": "b"}]}}
    seen = {}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.update(body)
            out = json.dumps({"message": {"content": json.dumps(answer)}, "eval_count": 5}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)

        def log_message(self, *a):
            pass

    os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1,localhost"
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    client = OllamaClient("qwen2.5:7b", host=f"http://127.0.0.1:{srv.server_port}")
    rec = generate("structured", "A then B.", client, seed=7)
    assert rec["valid"] and seen["options"]["seed"] == 7 and seen["format"] == "json"
    assert check_soundness(to_net("structured", rec["document"]))["sound"]
