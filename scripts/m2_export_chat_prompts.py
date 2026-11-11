"""Milestone 2 - export ready-to-paste prompts for a chat UI (e.g. ChatGPT).

  python scripts/m2_export_chat_prompts.py            # dev cases only (default)

Writes manual/chat_prompts/<case>_<approach>.txt. Paste a file into the chat,
save the JSON answer as manual/responses/<case>_<approach>_s1_a0.json and run
  python scripts/generate.py --client manual --split dev --seeds 1 --run-name chatgpt_dev
Test cases are deliberately not exported (they stay unseen until Milestone 3).
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import argparse
from nl2wfnet.benchmark import load_benchmark
from nl2wfnet.prompts import render_for_chat_ui


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev"])
    args = ap.parse_args()
    os.makedirs("manual/chat_prompts", exist_ok=True)
    n = 0
    for it in load_benchmark(split=args.split):
        for approach in ("structured", "baseline"):
            with open(f"manual/chat_prompts/{it['id']}_{approach}.txt", "w", encoding="utf-8") as f:
                f.write(render_for_chat_ui(approach, it["description"]))
            n += 1
    print(f"{n} prompts written to manual/chat_prompts/")


if __name__ == "__main__":
    main()
