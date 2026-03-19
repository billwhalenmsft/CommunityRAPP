"""
Agent Registry — Unified catalog of all agents across all sources.

Scans local agents/ folder, Azure File Storage (agents/ + multi_agents/),
and GitHub library repos to build a single registry JSON that the system
can query at runtime. The registry is persisted to Azure storage under
agent_catalogue/agent_registry.json and refreshed on each cold start.

Usage:
    from utils.agent_registry import build_registry, get_registry

    # Build and persist (called on startup)
    registry = build_registry(declared_agents)

    # Retrieve persisted registry
    registry = get_registry()
"""

import json
import logging
import os
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from utils.storage_factory import get_storage_manager

REGISTRY_SHARE = "agent_catalogue"
REGISTRY_FILE = "agent_registry.json"

# GitHub library sources
GITHUB_SOURCES = [
    {
        "id": "kody-w/AI-Agent-Templates",
        "repo": "kody-w/AI-Agent-Templates",
        "branch": "main",
        "manifest_url": "https://raw.githubusercontent.com/kody-w/AI-Agent-Templates/main/manifest.json",
        "label": "Community Templates",
    },
    {
        "id": "billwhalenmsft/RAPP-Agent-Repo",
        "repo": "billwhalenmsft/RAPP-Agent-Repo",
        "branch": "main",
        "api_base": "https://api.github.com/repos/billwhalenmsft/RAPP-Agent-Repo",
        "agents_path": "agents/@aibast-agents-library",
        "label": "AIBAST Industry Library",
    },
]


def _catalog_local_agents(declared_agents: Dict[str, Any]) -> List[Dict]:
    """Build catalog entries from the currently loaded agents."""
    entries = []
    for name, agent in declared_agents.items():
        meta = getattr(agent, "metadata", {}) or {}
        source_file = None
        # Try to find the source file from the module
        module = getattr(agent.__class__, "__module__", "")
        if module.startswith("agents."):
            source_file = module.replace("agents.", "") + ".py"

        entry = {
            "name": name,
            "source": "local" if source_file else "runtime",
            "source_file": source_file,
            "description": meta.get("description", ""),
            "status": "loaded",
            "parameters": list(meta.get("parameters", {}).get("properties", {}).keys()) if meta.get("parameters") else [],
        }
        # Check for __manifest__ on the class module
        manifest = getattr(agent.__class__, "__manifest__", None)
        if manifest is None:
            # Try the module globals
            mod = getattr(agent, "__module__", None)
            if mod:
                import sys
                mod_obj = sys.modules.get(mod)
                if mod_obj:
                    manifest = getattr(mod_obj, "__manifest__", None)
        if manifest:
            entry["manifest"] = {
                "version": manifest.get("version"),
                "tags": manifest.get("tags", []),
                "category": manifest.get("category"),
                "quality_tier": manifest.get("quality_tier"),
            }
        entries.append(entry)
    return entries


def _catalog_github_manifest_source(source: Dict) -> List[Dict]:
    """Fetch a manifest.json-backed GitHub source and extract catalog entries."""
    entries = []
    manifest_url = source.get("manifest_url")
    if not manifest_url:
        return entries
    try:
        resp = requests.get(manifest_url, timeout=10)
        resp.raise_for_status()
        manifest = resp.json()

        # Singular agents
        for agent in manifest.get("agents", []):
            entries.append({
                "name": agent.get("name", agent.get("id")),
                "id": agent.get("id"),
                "source": f"github:{source['id']}",
                "source_type": "singular",
                "filename": agent.get("filename"),
                "url": agent.get("url"),
                "size": agent.get("size_formatted"),
                "description": agent.get("description", ""),
                "features": agent.get("features", []),
                "status": "available",
            })

        # Stack agents
        for stack in manifest.get("stacks", []):
            for agent in stack.get("agents", []):
                entries.append({
                    "name": agent.get("name", agent.get("id")),
                    "id": agent.get("id"),
                    "source": f"github:{source['id']}",
                    "source_type": "stack",
                    "stack": stack.get("name"),
                    "industry": stack.get("industry"),
                    "stack_path": stack.get("path"),
                    "filename": agent.get("filename"),
                    "url": agent.get("url"),
                    "size": agent.get("size_formatted"),
                    "description": stack.get("metadata", {}).get("description", agent.get("description", "")),
                    "features": stack.get("metadata", {}).get("features", agent.get("features", [])),
                    "status": "available",
                })
    except Exception as e:
        logging.warning(f"Failed to fetch manifest from {source['id']}: {e}")
    return entries


def _catalog_aibast_source(source: Dict) -> List[Dict]:
    """Scan the @aibast-agents-library directory tree via the GitHub API."""
    entries = []
    api_base = source.get("api_base")
    agents_path = source.get("agents_path")
    if not api_base or not agents_path:
        return entries

    try:
        # List top-level stacks
        resp = requests.get(f"{api_base}/contents/{agents_path}", timeout=10)
        resp.raise_for_status()
        stacks_dirs = [item for item in resp.json() if item["type"] == "dir"]

        for stack_dir in stacks_dirs:
            stack_category = stack_dir["name"]  # e.g. "manufacturing_stacks"
            # List agents within the stack
            resp2 = requests.get(stack_dir["url"], timeout=10)
            if resp2.status_code != 200:
                continue
            agent_dirs = [item for item in resp2.json() if item["type"] == "dir"]
            for agent_dir in agent_dirs:
                agent_name = agent_dir["name"].replace("_stack", "").replace("_", " ").title()
                entries.append({
                    "name": agent_name,
                    "id": agent_dir["name"].replace("_stack", "_agent"),
                    "source": f"github:{source['id']}",
                    "source_type": "stack",
                    "stack": stack_category.replace("_stacks", "").replace("_", " ").title(),
                    "industry": stack_category.replace("_stacks", "").replace("_", " ").title(),
                    "stack_path": f"{agents_path}/{stack_category}/{agent_dir['name']}",
                    "status": "available",
                })
    except Exception as e:
        logging.warning(f"Failed to scan AIBAST library: {e}")
    return entries


def build_registry(declared_agents: Dict[str, Any]) -> Dict:
    """
    Build the unified agent registry from all sources.

    Args:
        declared_agents: Dict of currently loaded agent instances (from load_agents_from_folder)

    Returns:
        The complete registry dict, also persisted to Azure storage.
    """
    registry = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "sources": {},
        "agents": [],
        "summary": {},
    }

    # 1. Local / loaded agents
    local_entries = _catalog_local_agents(declared_agents)
    registry["agents"].extend(local_entries)
    registry["sources"]["local"] = {
        "count": len(local_entries),
        "description": "Agents loaded from local agents/ folder + Azure storage",
    }

    # 2. GitHub sources
    for gh_source in GITHUB_SOURCES:
        if gh_source.get("manifest_url"):
            entries = _catalog_github_manifest_source(gh_source)
        else:
            entries = _catalog_aibast_source(gh_source)
        registry["agents"].extend(entries)
        registry["sources"][gh_source["id"]] = {
            "count": len(entries),
            "label": gh_source["label"],
        }

    # Summary
    loaded = sum(1 for a in registry["agents"] if a["status"] == "loaded")
    available = sum(1 for a in registry["agents"] if a["status"] == "available")
    registry["summary"] = {
        "total": len(registry["agents"]),
        "loaded": loaded,
        "available_to_install": available,
    }

    # Persist
    try:
        storage = get_storage_manager()
        storage.write_file(REGISTRY_SHARE, REGISTRY_FILE, json.dumps(registry, indent=2))
        logging.info(
            f"Agent registry persisted: {loaded} loaded, {available} available to install, {len(registry['agents'])} total"
        )
    except Exception as e:
        logging.warning(f"Failed to persist agent registry: {e}")

    return registry


def get_registry() -> Optional[Dict]:
    """Read the persisted registry from storage."""
    try:
        storage = get_storage_manager()
        data = storage.read_file(REGISTRY_SHARE, REGISTRY_FILE)
        if data:
            return json.loads(data)
    except Exception as e:
        logging.warning(f"Failed to read agent registry: {e}")
    return None


def format_registry_summary(registry: Dict) -> str:
    """Format a human-readable summary of the registry for logging."""
    summary = registry.get("summary", {})
    lines = [
        f"Agent Registry: {summary.get('total', 0)} total agents",
        f"  Loaded (active): {summary.get('loaded', 0)}",
        f"  Available to install: {summary.get('available_to_install', 0)}",
    ]
    for source_id, info in registry.get("sources", {}).items():
        label = info.get("label", source_id)
        lines.append(f"  [{label}]: {info.get('count', 0)} agents")
    return "\n".join(lines)
