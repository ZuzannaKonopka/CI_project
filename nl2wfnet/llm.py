"""LLM clients with one common interface: client.chat(messages, seed) -> (text, meta).

OllamaClient            local models via Ollama (default: qwen2.5:7b)
OpenAICompatibleClient  any /v1/chat/completions server (OpenAI, vLLM, LM Studio, Ollama /v1,
                        a team server); the API key is read from the environment variable
                        whose NAME is given in api_key_env (never put the key itself in a file)
ManualClient            copy-paste workflow for chat UIs such as ChatGPT (no API needed)

Ready-made configurations: configs/ollama.json, configs/openai.json, configs/manual.json
(select one with --config, e.g. python scripts/m2_develop.py --config configs/openai.json ...).
"""
import os
import time

import requests


class OllamaClient:
    def __init__(self, model="qwen2.5:7b", host="http://localhost:11434", temperature=0.5,
                 num_ctx=16384, json_mode=True, timeout=600, num_predict=2048):
        self.model, self.host, self.temperature = model, host.rstrip("/"), temperature
        self.num_ctx, self.json_mode, self.timeout, self.num_predict = num_ctx, json_mode, timeout, num_predict
        self.name = f"ollama:{model}"

    def chat(self, messages, seed=0):
        body = {"model": self.model, "messages": messages, "stream": False,
                "options": {"temperature": self.temperature, "seed": seed, "num_ctx": self.num_ctx, "num_predict": self.num_predict}}
        if self.json_mode:
            body["format"] = "json"
        t0 = time.time()
        r = requests.post(f"{self.host}/api/chat", json=body, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        return data["message"]["content"], {
            "latency_s": round(time.time() - t0, 2),
            "prompt_tokens": data.get("prompt_eval_count"), 
            "output_tokens": data.get("eval_count"),
            "done_reason": data.get("done_reason")}


class OpenAICompatibleClient:
    def __init__(self, model, base_url="https://api.openai.com/v1", api_key_env="OPENAI_API_KEY",
                 temperature=0.5, json_mode=True, timeout=600):
        self.model, self.base_url, self.temperature = model, base_url.rstrip("/"), temperature
        if api_key_env.startswith("sk-"):
            raise ValueError("api_key_env must be the NAME of an environment variable (e.g. OPENAI_API_KEY), "
                             "not the key itself. Set the key with: export OPENAI_API_KEY=...")
        self.api_key = os.environ.get(api_key_env, "")
        self.json_mode, self.timeout = json_mode, timeout
        self.name = f"openai-compatible:{model}"

    def chat(self, messages, seed=0):
        body = {"model": self.model, "messages": messages, "temperature": self.temperature, "seed": seed}
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        t0 = time.time()
        r = requests.post(f"{self.base_url}/chat/completions", json=body, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage") or {}
        return data["choices"][0]["message"]["content"], {
            "latency_s": round(time.time() - t0, 2),
            "prompt_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens")}


class ManualResponseMissing(Exception):
    pass


class ManualClient:
    """Chat-UI workflow. For every call it needs a response file:
        <responses_dir>/<case>_<approach>_s<seed>_a<attempt>.json
    If it is missing, the prompt is written to <prompts_dir>/<same name>.txt and
    ManualResponseMissing is raised. Paste the prompt into the chat UI, save the
    answer under the response name and run the script again.
    """
    def __init__(self, responses_dir="manual/responses", prompts_dir="manual/prompts"):
        self.responses_dir, self.prompts_dir = responses_dir, prompts_dir
        os.makedirs(responses_dir, exist_ok=True)
        os.makedirs(prompts_dir, exist_ok=True)
        self.name, self.key = "manual", None

    def chat(self, messages, seed=0):
        stem = self.key
        path = os.path.join(self.responses_dir, stem + ".json")
        if not os.path.exists(path):
            text = "\n\n".join(f"### {m['role'].upper()}\n{m['content']}" for m in messages)
            with open(os.path.join(self.prompts_dir, stem + ".txt"), "w", encoding="utf-8") as f:
                f.write(text + "\n\n### Answer with the JSON object only.")
            raise ManualResponseMissing(path)
        with open(path, encoding="utf-8") as f:
            return f.read(), {"latency_s": None, "prompt_tokens": None, "output_tokens": None}


def make_client(cfg):
    kind = cfg.get("client", "ollama")
    if kind == "ollama":
        return OllamaClient(cfg["model"], cfg.get("host", "http://localhost:11434"), cfg.get("temperature", 0.5),
                            cfg.get("num_ctx", 16384), cfg.get("json_mode", True), cfg.get("timeout", 600), cfg.get("num_predict", 2048))
    if kind == "openai":
        return OpenAICompatibleClient(cfg["model"], cfg.get("base_url", "https://api.openai.com/v1"),
                                      cfg.get("api_key_env", "OPENAI_API_KEY"), cfg.get("temperature", 0.5),
                                      cfg.get("json_mode", True))
    if kind == "manual":
        return ManualClient()
    raise ValueError(f"unknown client '{kind}' (use ollama | openai | manual)")
