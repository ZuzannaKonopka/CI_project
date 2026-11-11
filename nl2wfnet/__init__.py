"""nl2wfnet: natural-language process description -> process tree (JSON) -> WF-net.

Modules
  tree       process-tree JSON: validation, parsing, compact notation
  wfnet      Petri nets / WF-nets, tree -> WF-net translation, WF-net JSON, PNML/DOT export
  analysis   reachability, soundness, bounded trace languages, footprints
  benchmark  loading the benchmark from the review spreadsheet
  prompts    prompts for the proposed and the baseline approach
  llm        LLM clients (Ollama, OpenAI-compatible, manual chat workflow)
  pipeline   prompt -> LLM -> validate -> repair -> WF-net
  labels     matching generated activity labels to reference labels
  metrics    the four evaluation dimensions
  perturb    controlled error injection into reference trees (metric validation)
  stats      exact Wilcoxon test, bootstrap confidence intervals
  report     result tables and figures
"""
from .tree import parse_tree, validate_tree, tree_to_string, activities, parse_tree_string, tree_to_json
from .wfnet import PetriNet, tree_to_wfnet, wfnet_from_json, validate_wfnet_json
from .analysis import check_soundness, bounded_language, language_similarity, footprint_similarity

__version__ = "1.0.0"
