"""
Utility: Context Card Loader
Purpose: Loads demo environment context cards for use by CoE agents.
         All agents should call load_context_card() before generating
         code, SOPs, or configs targeting a specific demo environment.
"""

import json
import os
from typing import Optional

CONTEXT_CARD_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
)

KNOWN_CARDS = {
    "master_ce_mfg": "master_ce_mfg.md",
    "mfg_gold_template": "mfg_gold_template.md",
}


def load_context_card(card_name: str) -> str:
    """
    Load a demo environment context card by name.
    Returns the markdown content as a string.
    Raises FileNotFoundError if the card doesn't exist.
    """
    filename = KNOWN_CARDS.get(card_name, f"{card_name}.md")
    path = os.path.join(CONTEXT_CARD_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Context card '{card_name}' not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def list_context_cards() -> list:
    """Return all available context card names."""
    cards = []
    if os.path.exists(CONTEXT_CARD_DIR):
        for fname in os.listdir(CONTEXT_CARD_DIR):
            if fname.endswith(".md"):
                cards.append(fname.replace(".md", ""))
    return cards


def get_context_card_summary(card_name: str) -> dict:
    """
    Return a structured summary of a context card for agent consumption.
    Parses the markdown into a dict with key sections.
    """
    content = load_context_card(card_name)
    lines = content.splitlines()
    summary = {"name": card_name, "raw": content, "sections": {}}
    current_section = None
    current_lines = []
    for line in lines:
        if line.startswith("## "):
            if current_section:
                summary["sections"][current_section] = "\n".join(current_lines).strip()
            current_section = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_section:
        summary["sections"][current_section] = "\n".join(current_lines).strip()
    return summary


def load_all_context_cards() -> dict:
    """Load all available context cards. Used by orchestrator at startup."""
    result = {}
    for card_name in list_context_cards():
        try:
            result[card_name] = get_context_card_summary(card_name)
        except Exception as e:
            result[card_name] = {"error": str(e)}
    return result
