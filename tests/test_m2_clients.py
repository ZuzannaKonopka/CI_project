"""M2 - LLM clients and configurations (local fake HTTP servers, no real LLM needed)."""
import os, sys, json, threading, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from http.server import BaseHTTPRequestHandler, HTTPServer
from nl2wfnet.llm import OpenAICompatibleClient, ManualClient, ManualResponseMissing, make_client, OllamaClient
from nl2wfnet.pipeline import generate
from nl2wfnet.prompts import build_messages, EXAMPLES
from nl2wfnet.tree import validate_tree
from nl2wfnet.wfnet import validate_wfnet_json

os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1,localhost"


def fake_server(reply, seen):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["path"] = self.path
            seen["auth"] = self.headers.get("Authorization")
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            out = json.dumps(reply).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)

        def log_message(self, *a):
            pass
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    return srv


def test_openai_client_request_and_key_from_env():
    tree = {"process_name": "t", "tree": {"op": "xor", "children": [{"activity": "a"}, {"activity": "b"}]}}
    seen = {}
    srv = fake_server({"choices": [{"message": {"content": json.dumps(tree)}}],
                       "usage": {"prompt_tokens": 11, "completion_tokens": 7}}, seen)
    os.environ["NL2WFNET_TEST_KEY"] = "test-key-123"
    c = OpenAICompatibleClient("some-model", base_url=f"http://127.0.0.1:{srv.server_port}/v1",
                               api_key_env="NL2WFNET_TEST_KEY", temperature=0.3)
    rec = generate("structured", "A or B.", c, seed=5)
    assert rec["valid"] and seen["path"] == "/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key-123"
    assert seen["body"]["seed"] == 5 and seen["body"]["temperature"] == 0.3
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert rec["attempts"][0]["prompt_tokens"] == 11


def test_api_key_in_config_is_rejected():
    try:
        OpenAICompatibleClient("m", api_key_env="sk-proj-abc")
    except ValueError as e:
        assert "NAME of an environment variable" in str(e)
    else:
        raise AssertionError("a key in api_key_env was accepted")


def test_manual_client_writes_prompt_then_reads_answer():
    with tempfile.TemporaryDirectory() as d:
        c = ManualClient(os.path.join(d, "resp"), os.path.join(d, "prompts"))
        try:
            generate("baseline", "A then B.", c, seed=1, case_id="P99")
        except ManualResponseMissing:
            pass
        assert os.path.exists(os.path.join(d, "prompts", "P99_baseline_s1_a0.txt"))
        net = {"places": ["i", "p", "o"], "transitions": [{"id": "t1", "label": "A"}, {"id": "t2", "label": "B"}],
               "arcs": [["i", "t1"], ["t1", "p"], ["p", "t2"], ["t2", "o"]]}
        open(os.path.join(d, "resp", "P99_baseline_s1_a0.json"), "w").write(json.dumps(net))
        rec = generate("baseline", "A then B.", c, seed=1, case_id="P99")
        assert rec["valid"] and rec["n_repairs"] == 0


def test_all_config_files_build_a_client():
    for f in ["config.json", "configs/ollama.json", "configs/openai.json", "configs/manual.json"]:
        cfg = json.load(open(os.path.join(ROOT, f)))
        assert not cfg["api_key_env"].startswith("sk-"), f
        if cfg["client"] == "manual":
            with tempfile.TemporaryDirectory() as d:
                cwd = os.getcwd(); os.chdir(d)
                try:
                    assert isinstance(make_client(cfg), ManualClient)
                finally:
                    os.chdir(cwd)
        else:
            assert make_client(cfg).name.endswith(cfg["model"])
        assert cfg["max_repairs"] == 2 and cfg["trace_max_len"] == 12


def test_prompts_are_fair_and_examples_valid():
    s, b = build_messages("structured", "X."), build_messages("baseline", "X.")
    assert len(s) == len(b) == 6                               # system + 2 examples (user/assistant) + task
    assert [m["content"] for m in s[1::2]] == [m["content"] for m in b[1::2]]   # identical user turns
    for ex in EXAMPLES:
        assert validate_tree(ex["structured"]["tree"]) == [] and validate_wfnet_json(ex["baseline"]) == []
