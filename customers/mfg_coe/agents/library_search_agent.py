"""
LibrarySearchAgent — searches the registered agent library sources before the Architect
builds a new solution. Runs automatically on every tech-solution issue to reduce rework.
"""

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger("library_search_agent")

REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent
    / "knowledge_base"
    / "agent_library_registry.json"
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _load_registry() -> dict:
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("Could not load agent library registry: %s", exc)
        return {"sources": []}


def _extract_keywords(text: str, ignore_words: set[str]) -> list[str]:
    """Extract meaningful keywords from issue title + body."""
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b", text.lower())
    seen: set[str] = set()
    result = []
    for w in words:
        if w not in ignore_words and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def _score_match(keywords: list[str], text: str) -> float:
    """Score how many keywords appear in a block of text."""
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw in text_lower)
    return hits / max(len(keywords), 1)


def _search_local_dir(directory: str, keywords: list[str], file_patterns: list[str]) -> list[dict]:
    """Search local directory for files matching keywords."""
    base = REPO_ROOT / directory
    if not base.exists():
        return []

    matches = []
    for pattern in file_patterns:
        for fp in base.rglob(pattern):
            try:
                content = fp.read_text(encoding="utf-8", errors="ignore")
                score = _score_match(keywords, fp.name + " " + content[:2000])
                if score > 0.15:
                    matches.append({
                        "source": directory,
                        "path": str(fp.relative_to(REPO_ROOT)),
                        "name": fp.name,
                        "score": round(score, 3),
                        "url": None,
                    })
            except Exception:
                pass

    return sorted(matches, key=lambda x: x["score"], reverse=True)[:5]


def _search_github_repo(repo: str, keywords: list[str]) -> list[dict]:
    """Search a GitHub repo via gh CLI code search."""
    if not keywords:
        return []

    # Use top 5 most specific keywords (avoid generic ones)
    search_terms = " ".join(keywords[:5])
    try:
        result = subprocess.run(
            ["gh", "search", "code", search_terms,
             "--repo", repo,
             "--json", "path,repository,url,textMatches",
             "--limit", "5"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return []
        items = json.loads(result.stdout) if result.stdout.strip() else []
        matches = []
        for item in items:
            score = _score_match(keywords, item.get("path", "") + " " +
                                 " ".join(m.get("fragment", "") for m in item.get("textMatches", [])))
            if score > 0.1:
                matches.append({
                    "source": repo,
                    "path": item.get("path", ""),
                    "name": Path(item.get("path", "")).name,
                    "score": round(score, 3),
                    "url": item.get("url"),
                })
        return matches
    except Exception as exc:
        log.warning("GitHub search failed for %s: %s", repo, exc)
        return []


def run_library_search(issue_number: int, issue_title: str, issue_body: str) -> dict[str, Any]:
    """
    Run the full library search for a given issue.
    Returns a dict with:
      - matches: list of top matches across all sources
      - strong_match: True if any match score >= 0.4
      - comment_body: Markdown formatted comment to post on the issue
    """
    registry = _load_registry()
    ignore_words = set(registry.get("keywords_to_ignore", []))
    min_score = registry.get("min_match_score", 0.3)

    search_text = f"{issue_title} {issue_body}"
    keywords = _extract_keywords(search_text, ignore_words)

    if len(keywords) < 3:
        return {
            "matches": [],
            "strong_match": False,
            "comment_body": (
                "## 🔍 Library Search\n\n"
                "Not enough keywords to search — proceeding with fresh build.\n"
            ),
        }

    all_matches: list[dict] = []
    searched_sources: list[str] = []

    for source in registry.get("sources", []):
        if not source.get("enabled", True):
            continue

        src_id = source["id"]
        src_type = source.get("type")

        try:
            if src_type == "local_directory":
                found = _search_local_dir(
                    source["path"],
                    keywords,
                    source.get("search_files", ["*.py"]),
                )
                for m in found:
                    m["source_id"] = src_id
                    m["source_name"] = source["name"]
                all_matches.extend(found)
                searched_sources.append(f"📁 {source['name']}")

            elif src_type == "github_repo":
                found = _search_github_repo(source["repo"], keywords)
                for m in found:
                    m["source_id"] = src_id
                    m["source_name"] = source["name"]
                all_matches.extend(found)
                searched_sources.append(f"🐙 {source['name']}")

        except Exception as exc:
            log.warning("Search failed for source %s: %s", src_id, exc)

    # Sort all matches by score, deduplicate by path
    seen_paths: set[str] = set()
    unique_matches: list[dict] = []
    for m in sorted(all_matches, key=lambda x: x["score"], reverse=True):
        key = f"{m.get('source_id', '')}/{m['path']}"
        if key not in seen_paths:
            seen_paths.add(key)
            unique_matches.append(m)

    top_matches = unique_matches[:8]
    strong_match = any(m["score"] >= min_score for m in top_matches)

    # Build markdown comment
    lines = ["## 🔍 Agent Library Search Results\n"]
    lines.append(f"**Keywords extracted:** `{', '.join(keywords[:10])}`\n")
    lines.append(f"**Sources searched:** {', '.join(searched_sources)}\n")

    if top_matches:
        if strong_match:
            lines.append("\n> ⚠️ **Strong matches found** — please review before building from scratch.\n")
        else:
            lines.append("\n> ℹ️ Partial matches found — may be reusable as a starting point.\n")

        lines.append("\n| Score | File | Source | Link |")
        lines.append("|---|---|---|---|")
        for m in top_matches:
            score_pct = f"{int(m['score'] * 100)}%"
            link = f"[view]({m['url']})" if m.get("url") else "local"
            lines.append(f"| {score_pct} | `{m['name']}` | {m['source_name']} | {link} |")
    else:
        lines.append("\n✅ No existing matches found — **build fresh** with confidence.\n")

    lines.append(
        f"\n_Searched {len(registry.get('sources', []))} sources · "
        f"{len(top_matches)} matches · "
        f"Auto-run by Library Search Agent_"
    )

    return {
        "matches": top_matches,
        "strong_match": strong_match,
        "keywords": keywords,
        "comment_body": "\n".join(lines),
        "searched_sources": searched_sources,
    }
