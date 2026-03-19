"""
RAPP Agent Sync - Pull and sync agents from the RAPP Agent Registry to local machine.

This agent pulls agents from billwhalenmsft/RAPP-Agent-Repo and syncs them locally.

Actions:
- list_remote: List available agents in the registry
- pull: Pull an agent from the registry to local
- pull_segment: Pull all agents from a segment (e.g., rapp-general, customer-zurnelkay)
- sync: Sync local agents with registry (pull newer versions)
- diff: Compare local agent with registry version
- search: Search for agents by name, tag, or description

Environment:
- GITHUB_TOKEN: Required for accessing private registry repo
"""

import os
import json
import base64
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from agents.basic_agent import BasicAgent

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@billwhalen/rapp-agent-sync",
    "version": "1.0.0",
    "display_name": "RAPP Agent Sync",
    "description": "Pull and sync agents from the RAPP Agent Registry to local machine.",
    "author": "Bill Whalen",
    "tags": ["rapp", "registry", "sync", "pull", "agent-management"],
    "category": "rapp-general",
    "quality_tier": "internal",
    "requires_env": ["GITHUB_TOKEN"],
    "dependencies": ["@rapp/basic-agent"],
}


class RAPPAgentSync(BasicAgent):
    """Pull and sync agents from the RAPP Agent Registry."""
    
    REGISTRY_REPO = "billwhalenmsft/RAPP-Agent-Repo"
    REGISTRY_BRANCH = "main"
    GITHUB_API = "https://api.github.com"
    GITHUB_RAW = "https://raw.githubusercontent.com"
    
    def __init__(self):
        self.name = 'RAPPAgentSync'
        self.metadata = {
            "name": self.name,
            "description": """Pull and sync agents from the RAPP Agent Registry.

Actions:
- list_remote: List available agents in the registry (optional: segment filter)
- pull: Pull a specific agent from the registry to local
- pull_segment: Pull all agents from a segment (e.g., rapp-general, customer-zurnelkay)
- sync: Sync local agents with registry versions (check for updates)
- diff: Compare local agent with registry version
- search: Search for agents by name, tag, or description

Examples:
- List all remote agents: action="list_remote"
- List agents in a segment: action="list_remote", segment="rapp-general"
- Pull an agent: action="pull", agent_name="@billwhalen/dynamics-crud"
- Pull all customer agents: action="pull_segment", segment="customer-zurnelkay"
- Search for agents: action="search", query="dynamics"
- Check for updates: action="sync", dry_run=true
- Compare versions: action="diff", agent_name="@billwhalen/rapp-pipeline"
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list_remote", "pull", "pull_segment", "sync", "diff", "search"],
                        "description": "Action to perform"
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "Agent name for pull/diff (e.g., '@billwhalen/dynamics-crud' or 'dynamics-crud')"
                    },
                    "segment": {
                        "type": "string",
                        "description": "Segment filter for list_remote or pull_segment (e.g., 'rapp-general', 'customer-zurnelkay')"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for search action"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "For sync/pull: preview without making changes",
                        "default": False
                    },
                    "force": {
                        "type": "boolean",
                        "description": "For pull: overwrite local file even if it exists",
                        "default": False
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)
        self.logger = logging.getLogger(__name__)
    
    def _get_github_token(self) -> Optional[str]:
        """Get GitHub token from environment."""
        return os.environ.get('GITHUB_TOKEN')
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RAPP-Agent-Sync/1.0"
        }
        token = self._get_github_token()
        if token:
            headers["Authorization"] = f"token {token}"
        return headers
    
    def _github_request(self, method: str, url: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GitHub API request."""
        import urllib.request
        import urllib.error
        
        headers = self._get_headers()
        
        if data:
            body = json.dumps(data).encode('utf-8')
            headers["Content-Type"] = "application/json"
        else:
            body = None
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            return {"error": f"HTTP {e.code}: {error_body}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_raw_content(self, path: str) -> Optional[str]:
        """Get raw file content from GitHub."""
        import urllib.request
        import urllib.error
        
        url = f"{self.GITHUB_RAW}/{self.REGISTRY_REPO}/{self.REGISTRY_BRANCH}/{path}"
        headers = self._get_headers()
        
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            self.logger.error(f"Failed to get {path}: HTTP {e.code}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get {path}: {e}")
            return None
    
    def _get_registry(self) -> Optional[Dict[str, Any]]:
        """Fetch the registry.json from the repo."""
        content = self._get_raw_content("registry.json")
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
        return None
    
    def _list_remote_directory(self, path: str) -> List[Dict[str, Any]]:
        """List contents of a directory in the repo."""
        url = f"{self.GITHUB_API}/repos/{self.REGISTRY_REPO}/contents/{path}"
        result = self._github_request("GET", url)
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "error" not in result:
            return [result]
        return []
    
    def _get_local_agents_dir(self) -> str:
        """Get local agents directory path."""
        # Check for Azure Function context
        if os.path.exists('/tmp/agents'):
            return '/tmp/agents'
        # Local development
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, 'agents')
    
    def _agent_name_to_filename(self, agent_name: str) -> str:
        """Convert agent name to local filename."""
        # Remove @ prefix and publisher
        name = agent_name.split('/')[-1] if '/' in agent_name else agent_name
        # Convert slug to filename
        filename = name.replace('-', '_')
        if not filename.endswith('_agent.py'):
            filename = f"{filename}_agent.py"
        return filename
    
    def _filename_to_agent_name(self, filename: str) -> str:
        """Convert local filename to agent name pattern."""
        # Remove _agent.py suffix
        name = filename.replace('_agent.py', '').replace('.py', '')
        # Convert underscores to hyphens for slug
        return name.replace('_', '-')
    
    def perform(self, **kwargs) -> str:
        """Execute the requested action."""
        action = kwargs.get('action', 'list_remote')
        
        if action == 'list_remote':
            return self._list_remote(kwargs.get('segment'))
        elif action == 'pull':
            return self._pull_agent(
                kwargs.get('agent_name', ''),
                kwargs.get('dry_run', False),
                kwargs.get('force', False)
            )
        elif action == 'pull_segment':
            return self._pull_segment(
                kwargs.get('segment', 'rapp-general'),
                kwargs.get('dry_run', False),
                kwargs.get('force', False)
            )
        elif action == 'sync':
            return self._sync_agents(kwargs.get('dry_run', False))
        elif action == 'diff':
            return self._diff_agent(kwargs.get('agent_name', ''))
        elif action == 'search':
            return self._search_agents(kwargs.get('query', ''))
        else:
            return json.dumps({
                "error": f"Unknown action: {action}",
                "valid_actions": ["list_remote", "pull", "pull_segment", "sync", "diff", "search"]
            }, indent=2)
    
    def _list_remote(self, segment: Optional[str] = None) -> str:
        """List available agents in the registry."""
        if not self._get_github_token():
            return json.dumps({
                "error": "GITHUB_TOKEN not set - required for private repo access",
                "help": "Set GITHUB_TOKEN environment variable with repo access"
            }, indent=2)
        
        # Try to get registry.json first
        registry = self._get_registry()
        
        if registry and "agents" in registry:
            agents = registry["agents"]
            
            # Filter by segment if specified
            if segment:
                agents = [a for a in agents if a.get("category") == segment or segment in a.get("name", "")]
            
            return json.dumps({
                "status": "success",
                "source": "registry.json",
                "total_agents": len(agents),
                "segment_filter": segment,
                "agents": agents
            }, indent=2)
        
        # Fallback: scan directory structure
        agents = []
        publishers = ["@billwhalen", "@kody", "@rapp"]
        
        for publisher in publishers:
            pub_path = f"agents/{publisher}"
            segments_list = self._list_remote_directory(pub_path)
            
            for seg in segments_list:
                if seg.get("type") == "dir":
                    seg_name = seg.get("name", "")
                    
                    # Filter by segment if specified
                    if segment and seg_name != segment:
                        continue
                    
                    seg_path = f"{pub_path}/{seg_name}"
                    files = self._list_remote_directory(seg_path)
                    
                    for f in files:
                        if f.get("name", "").endswith(".py"):
                            slug = f["name"].replace(".py", "")
                            agents.append({
                                "name": f"{publisher}/{slug}",
                                "path": f["path"],
                                "segment": seg_name,
                                "size": f.get("size", 0)
                            })
        
        return json.dumps({
            "status": "success",
            "source": "directory_scan",
            "total_agents": len(agents),
            "segment_filter": segment,
            "agents": agents
        }, indent=2)
    
    def _pull_agent(self, agent_name: str, dry_run: bool = False, force: bool = False) -> str:
        """Pull a specific agent from the registry."""
        if not agent_name:
            return json.dumps({"error": "agent_name is required"}, indent=2)
        
        if not self._get_github_token():
            return json.dumps({
                "error": "GITHUB_TOKEN not set - required for private repo access"
            }, indent=2)
        
        # Parse agent name
        if agent_name.startswith('@'):
            # Full name: @billwhalen/dynamics-crud
            parts = agent_name.split('/')
            if len(parts) >= 2:
                publisher = parts[0]
                slug = parts[-1]
            else:
                return json.dumps({"error": f"Invalid agent name format: {agent_name}"}, indent=2)
        else:
            # Short name: dynamics-crud - assume @billwhalen
            publisher = "@billwhalen"
            slug = agent_name
        
        # Try to find the agent in the registry
        registry = self._get_registry()
        agent_info = None
        remote_path = None
        
        if registry and "agents" in registry:
            for agent in registry["agents"]:
                if agent.get("name", "").endswith(f"/{slug}") or agent.get("name", "") == agent_name:
                    agent_info = agent
                    remote_path = agent.get("path")
                    break
        
        # If not in registry, try common paths
        if not remote_path:
            # Try segments
            segments = ["rapp-general", "customer-zurnelkay", "customer-carrier", "core", "base"]
            for seg in segments:
                test_path = f"agents/{publisher}/{seg}/{slug}.py"
                content = self._get_raw_content(test_path)
                if content:
                    remote_path = test_path
                    break
        
        if not remote_path:
            return json.dumps({
                "error": f"Agent not found: {agent_name}",
                "searched": [f"agents/{publisher}/{s}/{slug}.py" for s in ["rapp-general", "customer-zurnelkay", "customer-carrier"]]
            }, indent=2)
        
        # Get the agent content
        content = self._get_raw_content(remote_path)
        if not content:
            return json.dumps({"error": f"Failed to fetch agent from {remote_path}"}, indent=2)
        
        # Determine local path
        local_dir = self._get_local_agents_dir()
        local_filename = self._agent_name_to_filename(slug)
        local_path = os.path.join(local_dir, local_filename)
        
        # Check if file exists
        exists = os.path.exists(local_path)
        
        if dry_run:
            return json.dumps({
                "status": "dry_run",
                "action": "would_pull",
                "agent": agent_name,
                "remote_path": remote_path,
                "local_path": local_path,
                "local_exists": exists,
                "would_overwrite": exists and force,
                "content_preview": content[:500] + "..." if len(content) > 500 else content
            }, indent=2)
        
        if exists and not force:
            return json.dumps({
                "status": "skipped",
                "reason": "local file exists",
                "agent": agent_name,
                "local_path": local_path,
                "help": "Use force=true to overwrite"
            }, indent=2)
        
        # Write the file
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return json.dumps({
                "status": "success",
                "action": "pulled",
                "agent": agent_name,
                "remote_path": remote_path,
                "local_path": local_path,
                "size_bytes": len(content),
                "overwrote": exists
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "agent": agent_name
            }, indent=2)
    
    def _pull_segment(self, segment: str, dry_run: bool = False, force: bool = False) -> str:
        """Pull all agents from a segment."""
        if not self._get_github_token():
            return json.dumps({
                "error": "GITHUB_TOKEN not set - required for private repo access"
            }, indent=2)
        
        # List agents in segment
        result = json.loads(self._list_remote(segment))
        
        if result.get("error"):
            return json.dumps(result, indent=2)
        
        agents = result.get("agents", [])
        
        if not agents:
            return json.dumps({
                "status": "no_agents",
                "segment": segment,
                "message": f"No agents found in segment '{segment}'"
            }, indent=2)
        
        results = {
            "status": "success",
            "segment": segment,
            "dry_run": dry_run,
            "total": len(agents),
            "pulled": [],
            "skipped": [],
            "errors": []
        }
        
        for agent in agents:
            agent_name = agent.get("name", "")
            pull_result = json.loads(self._pull_agent(agent_name, dry_run, force))
            
            if pull_result.get("status") == "success" or pull_result.get("status") == "dry_run":
                results["pulled"].append(agent_name)
            elif pull_result.get("status") == "skipped":
                results["skipped"].append(agent_name)
            else:
                results["errors"].append({
                    "agent": agent_name,
                    "error": pull_result.get("error", "Unknown error")
                })
        
        return json.dumps(results, indent=2)
    
    def _sync_agents(self, dry_run: bool = False) -> str:
        """Sync local agents with registry versions."""
        if not self._get_github_token():
            return json.dumps({
                "error": "GITHUB_TOKEN not set - required for private repo access"
            }, indent=2)
        
        local_dir = self._get_local_agents_dir()
        
        # Get local agent files
        local_agents = {}
        if os.path.exists(local_dir):
            for filename in os.listdir(local_dir):
                if filename.endswith('_agent.py') and not filename.startswith('__'):
                    filepath = os.path.join(local_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        local_agents[filename] = {
                            "path": filepath,
                            "content": f.read()
                        }
        
        # Get registry
        registry = self._get_registry()
        remote_agents = registry.get("agents", []) if registry else []
        
        results = {
            "status": "success",
            "dry_run": dry_run,
            "local_count": len(local_agents),
            "remote_count": len(remote_agents),
            "needs_update": [],
            "up_to_date": [],
            "local_only": [],
            "remote_only": []
        }
        
        # Check each local agent
        for filename, local_info in local_agents.items():
            slug = self._filename_to_agent_name(filename)
            
            # Find matching remote agent
            remote_match = None
            for remote in remote_agents:
                remote_slug = remote.get("name", "").split("/")[-1]
                if remote_slug == slug:
                    remote_match = remote
                    break
            
            if remote_match:
                # Get remote content
                remote_path = remote_match.get("path")
                if remote_path:
                    remote_content = self._get_raw_content(remote_path)
                    if remote_content:
                        if remote_content.strip() != local_info["content"].strip():
                            results["needs_update"].append({
                                "filename": filename,
                                "remote_name": remote_match.get("name")
                            })
                        else:
                            results["up_to_date"].append(filename)
                    else:
                        results["up_to_date"].append(filename)  # Can't compare, assume ok
                else:
                    results["up_to_date"].append(filename)
            else:
                results["local_only"].append(filename)
        
        # Check for remote-only agents
        for remote in remote_agents:
            remote_slug = remote.get("name", "").split("/")[-1]
            expected_filename = self._agent_name_to_filename(remote_slug)
            
            if expected_filename not in local_agents:
                results["remote_only"].append(remote.get("name"))
        
        # If not dry run, pull updates
        if not dry_run and results["needs_update"]:
            for update in results["needs_update"]:
                self._pull_agent(update["remote_name"], dry_run=False, force=True)
        
        return json.dumps(results, indent=2)
    
    def _diff_agent(self, agent_name: str) -> str:
        """Compare local agent with registry version."""
        if not agent_name:
            return json.dumps({"error": "agent_name is required"}, indent=2)
        
        if not self._get_github_token():
            return json.dumps({
                "error": "GITHUB_TOKEN not set - required for private repo access"
            }, indent=2)
        
        # Get local content
        local_dir = self._get_local_agents_dir()
        slug = agent_name.split('/')[-1] if '/' in agent_name else agent_name
        local_filename = self._agent_name_to_filename(slug)
        local_path = os.path.join(local_dir, local_filename)
        
        if not os.path.exists(local_path):
            return json.dumps({
                "error": f"Local agent not found: {local_path}",
                "agent_name": agent_name
            }, indent=2)
        
        with open(local_path, 'r', encoding='utf-8') as f:
            local_content = f.read()
        
        # Get remote content - try to find path
        registry = self._get_registry()
        remote_path = None
        
        if registry and "agents" in registry:
            for agent in registry["agents"]:
                if agent.get("name", "").endswith(f"/{slug}") or agent.get("name", "") == agent_name:
                    remote_path = agent.get("path")
                    break
        
        if not remote_path:
            # Try common paths
            publisher = "@billwhalen"
            segments = ["rapp-general", "customer-zurnelkay", "customer-carrier"]
            for seg in segments:
                test_path = f"agents/{publisher}/{seg}/{slug}.py"
                if self._get_raw_content(test_path):
                    remote_path = test_path
                    break
        
        if not remote_path:
            return json.dumps({
                "status": "local_only",
                "agent": agent_name,
                "local_path": local_path,
                "message": "Agent not found in registry - may be local-only"
            }, indent=2)
        
        remote_content = self._get_raw_content(remote_path)
        
        if not remote_content:
            return json.dumps({
                "error": f"Failed to fetch remote content from {remote_path}"
            }, indent=2)
        
        # Compare
        local_lines = local_content.strip().split('\n')
        remote_lines = remote_content.strip().split('\n')
        
        identical = local_content.strip() == remote_content.strip()
        
        diff_summary = {
            "status": "identical" if identical else "different",
            "agent": agent_name,
            "local_path": local_path,
            "remote_path": remote_path,
            "local_lines": len(local_lines),
            "remote_lines": len(remote_lines),
            "local_size": len(local_content),
            "remote_size": len(remote_content)
        }
        
        if not identical:
            # Simple line-by-line diff
            added = len(remote_lines) - len(local_lines)
            diff_summary["line_difference"] = added
            diff_summary["recommendation"] = "pull with force=true" if added > 0 else "consider publishing local changes"
        
        return json.dumps(diff_summary, indent=2)
    
    def _search_agents(self, query: str) -> str:
        """Search for agents by name, tag, or description."""
        if not query:
            return json.dumps({"error": "query is required"}, indent=2)
        
        if not self._get_github_token():
            return json.dumps({
                "error": "GITHUB_TOKEN not set - required for private repo access"
            }, indent=2)
        
        registry = self._get_registry()
        
        if not registry or "agents" not in registry:
            return json.dumps({
                "error": "Could not load registry",
                "help": "Ensure GITHUB_TOKEN has access to the registry repo"
            }, indent=2)
        
        query_lower = query.lower()
        matches = []
        
        for agent in registry["agents"]:
            score = 0
            
            # Check name
            if query_lower in agent.get("name", "").lower():
                score += 10
            
            # Check display_name
            if query_lower in agent.get("display_name", "").lower():
                score += 8
            
            # Check description
            if query_lower in agent.get("description", "").lower():
                score += 5
            
            # Check tags
            tags = agent.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    if query_lower in tag.lower():
                        score += 3
            
            # Check category
            if query_lower in agent.get("category", "").lower():
                score += 2
            
            if score > 0:
                matches.append({
                    **agent,
                    "_search_score": score
                })
        
        # Sort by score
        matches.sort(key=lambda x: x.get("_search_score", 0), reverse=True)
        
        return json.dumps({
            "status": "success",
            "query": query,
            "total_matches": len(matches),
            "results": matches
        }, indent=2)
