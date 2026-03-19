"""
RAPP Agent Publisher - Publishes agents to the RAPP Agent Registry.

Pushes agents to: https://github.com/billwhalenmsft/RAPP-Agent-Repo
Organized by publisher and segment:
  - agents/@billwhalen/rapp-general/   → General RAPP platform agents
  - agents/@billwhalen/customer-xyz/   → Customer-specific agents
"""

from agents.basic_agent import BasicAgent
import logging
import json
import os
import re
import ast
from datetime import datetime

logger = logging.getLogger(__name__)

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@billwhalen/rapp-agent-publisher",
    "version": "1.0.0",
    "display_name": "RAPP Agent Publisher",
    "description": "Publishes agents to the RAPP Agent Registry on GitHub. Organizes by publisher (@billwhalen) and segment (rapp-general or customer-specific).",
    "author": "Bill Whalen",
    "tags": ["registry", "github", "publish", "deploy"],
    "category": "pipeline",
    "quality_tier": "internal",
    "requires_env": ["GITHUB_TOKEN"],
    "dependencies": ["@rapp/basic-agent"],
}


class RAPPAgentPublisher(BasicAgent):
    """
    Publishes agents from CommunityRAPP to the RAPP Agent Registry.
    
    Target repo: billwhalenmsft/RAPP-Agent-Repo
    
    Path structure:
      agents/@billwhalen/rapp-general/{agent_slug}.py
      agents/@billwhalen/customer-{name}/{agent_slug}.py
    """
    
    # Registry configuration
    REGISTRY_REPO = "billwhalenmsft/RAPP-Agent-Repo"
    REGISTRY_BRANCH = "main"
    PUBLISHER = "@billwhalen"
    
    # GitHub API
    GITHUB_API = "https://api.github.com"
    
    def __init__(self):
        self.name = 'RAPPAgentPublisher'
        self.metadata = {
            "name": self.name,
            "description": """Publishes agents to the RAPP Agent Registry (billwhalenmsft/RAPP-Agent-Repo).

Organizes agents by segment:
- 'rapp-general' → General platform agents (RAPP pipeline, transpiler, etc.)
- 'customer-{name}' → Customer-specific agents (zurnelkay, carrier, etc.)

Actions:
- publish: Push an agent to the registry
- list_local: Show agents available to publish
- list_published: Show agents already in the registry
- generate_manifest: Create/update __manifest__ for an agent
- validate: Check if an agent is ready for publishing""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["publish", "list_local", "list_published", "generate_manifest", "validate", "sync_registry"]
                    },
                    "agent_file": {
                        "type": "string",
                        "description": "Agent filename to publish (e.g., 'rapp_agent.py', 'ze_drains_ci_agent.py')"
                    },
                    "segment": {
                        "type": "string",
                        "description": "Segment to publish to: 'rapp-general' for platform agents, or 'customer-{name}' for customer-specific (e.g., 'customer-zurnelkay')"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name for customer-specific agents (e.g., 'zurnelkay', 'carrier'). Used with segment='customer'"
                    },
                    "commit_message": {
                        "type": "string",
                        "description": "Git commit message for the publish"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, validate and show what would be published without actually pushing"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)
    
    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "list_local")
        
        try:
            if action == "list_local":
                return self._list_local_agents()
            elif action == "list_published":
                return self._list_published_agents()
            elif action == "publish":
                return self._publish_agent(**kwargs)
            elif action == "generate_manifest":
                return self._generate_manifest(**kwargs)
            elif action == "validate":
                return self._validate_agent(**kwargs)
            elif action == "sync_registry":
                return self._sync_registry()
            else:
                return json.dumps({"error": f"Unknown action: {action}"})
        except Exception as e:
            logger.error(f"RAPPAgentPublisher error: {e}")
            return json.dumps({"error": str(e)})
    
    def _list_local_agents(self) -> str:
        """List all agents in the local CommunityRAPP agents/ folder."""
        agents_dir = os.path.join(os.path.dirname(__file__))
        
        agents = {
            "rapp_general": [],
            "customer_specific": [],
            "other": []
        }
        
        for filename in os.listdir(agents_dir):
            if not filename.endswith('.py') or filename.startswith('__'):
                continue
            if filename == 'basic_agent.py':
                continue
            
            filepath = os.path.join(agents_dir, filename)
            agent_info = self._extract_agent_info(filepath)
            agent_info["filename"] = filename
            
            # Categorize
            name_lower = filename.lower()
            if any(x in name_lower for x in ['rapp', 'transpiler', 'generator', 'tracker', 'memory', 'github']):
                agents["rapp_general"].append(agent_info)
            elif any(x in name_lower for x in ['ze_', 'zurn', 'carrier', 'customer']):
                agents["customer_specific"].append(agent_info)
            else:
                agents["other"].append(agent_info)
        
        result = {
            "status": "success",
            "total_agents": sum(len(v) for v in agents.values()),
            "agents": agents,
            "suggested_segments": {
                "rapp_general": "agents/@billwhalen/rapp-general/",
                "customer_zurnelkay": "agents/@billwhalen/customer-zurnelkay/",
                "customer_carrier": "agents/@billwhalen/customer-carrier/"
            }
        }
        
        return json.dumps(result, indent=2)
    
    def _extract_agent_info(self, filepath: str) -> dict:
        """Extract agent metadata from a Python file."""
        info = {
            "has_manifest": False,
            "class_name": None,
            "description": None
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for __manifest__
            if '__manifest__' in content:
                info["has_manifest"] = True
                # Try to extract manifest
                match = re.search(r'__manifest__\s*=\s*(\{[^}]+\})', content, re.DOTALL)
                if match:
                    try:
                        manifest = ast.literal_eval(match.group(1))
                        info["manifest"] = manifest
                        info["description"] = manifest.get("description", "")
                    except:
                        pass
            
            # Extract class name
            class_match = re.search(r'class\s+(\w+)\s*\([^)]*BasicAgent', content)
            if class_match:
                info["class_name"] = class_match.group(1)
            
            # Extract description from docstring if no manifest
            if not info.get("description"):
                doc_match = re.search(r'class\s+\w+[^:]+:\s*"""([^"]+)"""', content, re.DOTALL)
                if doc_match:
                    info["description"] = doc_match.group(1).strip()[:200]
        
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    def _list_published_agents(self) -> str:
        """List agents already published to the registry."""
        try:
            import requests
        except ImportError:
            return json.dumps({"error": "requests library required"})
        
        token = os.environ.get("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"
        
        # Get contents of agents/@billwhalen/
        url = f"{self.GITHUB_API}/repos/{self.REGISTRY_REPO}/contents/agents/{self.PUBLISHER}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 404:
                return json.dumps({
                    "status": "success",
                    "message": "No agents published yet",
                    "segments": []
                })
            
            response.raise_for_status()
            segments = response.json()
            
            result = {
                "status": "success",
                "segments": []
            }
            
            for segment in segments:
                if segment["type"] != "dir":
                    continue
                
                segment_name = segment["name"]
                segment_url = f"{self.GITHUB_API}/repos/{self.REGISTRY_REPO}/contents/agents/{self.PUBLISHER}/{segment_name}"
                
                seg_response = requests.get(segment_url, headers=headers)
                if seg_response.status_code == 200:
                    agents = [f["name"] for f in seg_response.json() if f["name"].endswith(".py")]
                    result["segments"].append({
                        "name": segment_name,
                        "path": f"agents/{self.PUBLISHER}/{segment_name}/",
                        "agents": agents,
                        "count": len(agents)
                    })
            
            return json.dumps(result, indent=2)
        
        except Exception as e:
            return json.dumps({"error": f"Failed to list published agents: {e}"})
    
    def _publish_agent(self, **kwargs) -> str:
        """Publish an agent to the registry."""
        agent_file = kwargs.get("agent_file")
        segment = kwargs.get("segment")
        customer_name = kwargs.get("customer_name")
        commit_message = kwargs.get("commit_message")
        dry_run = kwargs.get("dry_run", False)
        
        if not agent_file:
            return json.dumps({"error": "agent_file is required"})
        
        # Determine segment path
        if customer_name:
            segment = f"customer-{customer_name.lower().replace(' ', '-')}"
        elif not segment:
            return json.dumps({"error": "segment or customer_name is required"})
        
        # Find the agent file
        agents_dir = os.path.dirname(__file__)
        filepath = os.path.join(agents_dir, agent_file)
        
        if not os.path.exists(filepath):
            # Try with _agent.py suffix
            if not agent_file.endswith('_agent.py'):
                alt_path = os.path.join(agents_dir, f"{agent_file.replace('.py', '')}_agent.py")
                if os.path.exists(alt_path):
                    filepath = alt_path
                    agent_file = os.path.basename(alt_path)
        
        if not os.path.exists(filepath):
            return json.dumps({"error": f"Agent file not found: {agent_file}"})
        
        # Read agent content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validate
        validation = self._validate_content(content, agent_file)
        if not validation["valid"]:
            return json.dumps({
                "error": "Validation failed",
                "issues": validation["issues"]
            })
        
        # Generate slug from filename
        slug = agent_file.replace('_agent.py', '').replace('.py', '')
        
        # Target path in registry
        target_path = f"agents/{self.PUBLISHER}/{segment}/{slug}.py"
        
        if dry_run:
            return json.dumps({
                "status": "dry_run",
                "would_publish": {
                    "source": agent_file,
                    "target": target_path,
                    "repo": self.REGISTRY_REPO,
                    "segment": segment,
                    "validation": validation
                }
            }, indent=2)
        
        # Actually publish
        return self._push_to_github(
            content=content,
            path=target_path,
            message=commit_message or f"Publish {slug} to {segment}"
        )
    
    def _validate_content(self, content: str, filename: str) -> dict:
        """Validate agent content before publishing."""
        issues = []
        warnings = []
        
        # Check for BasicAgent inheritance
        if 'BasicAgent' not in content:
            issues.append("Agent must inherit from BasicAgent")
        
        # Check for __manifest__
        if '__manifest__' not in content:
            warnings.append("No __manifest__ found - consider adding one for registry metadata")
        
        # Check for class definition
        if not re.search(r'class\s+\w+\s*\(', content):
            issues.append("No class definition found")
        
        # Check for perform method
        if 'def perform' not in content:
            issues.append("No perform() method found")
        
        # Check for proper init
        if 'def __init__' not in content:
            warnings.append("No __init__ method - using default initialization")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    def _validate_agent(self, **kwargs) -> str:
        """Validate an agent file for publishing."""
        agent_file = kwargs.get("agent_file")
        if not agent_file:
            return json.dumps({"error": "agent_file is required"})
        
        agents_dir = os.path.dirname(__file__)
        filepath = os.path.join(agents_dir, agent_file)
        
        if not os.path.exists(filepath):
            return json.dumps({"error": f"File not found: {agent_file}"})
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        validation = self._validate_content(content, agent_file)
        agent_info = self._extract_agent_info(filepath)
        
        return json.dumps({
            "status": "success",
            "file": agent_file,
            "validation": validation,
            "agent_info": agent_info,
            "ready_to_publish": validation["valid"]
        }, indent=2)
    
    def _generate_manifest(self, **kwargs) -> str:
        """Generate a __manifest__ block for an agent."""
        agent_file = kwargs.get("agent_file")
        segment = kwargs.get("segment", "rapp-general")
        customer_name = kwargs.get("customer_name")
        
        if not agent_file:
            return json.dumps({"error": "agent_file is required"})
        
        agents_dir = os.path.dirname(__file__)
        filepath = os.path.join(agents_dir, agent_file)
        
        if not os.path.exists(filepath):
            return json.dumps({"error": f"File not found: {agent_file}"})
        
        info = self._extract_agent_info(filepath)
        
        # Derive slug and name
        slug = agent_file.replace('_agent.py', '').replace('.py', '')
        slug_kebab = slug.replace('_', '-')
        
        if customer_name:
            category = f"customer-{customer_name.lower()}"
        elif 'rapp' in slug.lower():
            category = "pipeline"
        else:
            category = "integrations"
        
        manifest = {
            "schema": "rapp-agent/1.0",
            "name": f"@billwhalen/{slug_kebab}",
            "version": "1.0.0",
            "display_name": info.get("class_name", slug.replace('_', ' ').title()),
            "description": info.get("description", f"{slug.replace('_', ' ').title()} agent"),
            "author": "Bill Whalen",
            "tags": self._suggest_tags(slug),
            "category": category,
            "quality_tier": "internal",
            "requires_env": [],
            "dependencies": ["@rapp/basic-agent"],
        }
        
        manifest_code = f'''__manifest__ = {json.dumps(manifest, indent=4)}'''
        
        return json.dumps({
            "status": "success",
            "manifest": manifest,
            "code_to_add": manifest_code,
            "instructions": "Add this __manifest__ block near the top of your agent file, after the imports."
        }, indent=2)
    
    def _suggest_tags(self, slug: str) -> list:
        """Suggest tags based on agent slug."""
        tags = []
        slug_lower = slug.lower()
        
        tag_map = {
            'rapp': ['rapp', 'pipeline'],
            'transpiler': ['transpiler', 'copilot-studio'],
            'generator': ['generator', 'automation'],
            'memory': ['memory', 'context'],
            'email': ['email', 'communication'],
            'powerpoint': ['powerpoint', 'office'],
            'sharepoint': ['sharepoint', 'documents'],
            'dynamics': ['dynamics', 'crm'],
            'sales': ['sales', 'crm'],
            'demo': ['demo', 'presentation'],
            'ze_': ['zurnelkay', 'competitive-intelligence'],
            'carrier': ['carrier', 'customer'],
        }
        
        for keyword, suggested_tags in tag_map.items():
            if keyword in slug_lower:
                tags.extend(suggested_tags)
        
        return list(set(tags)) or ['agent']
    
    def _push_to_github(self, content: str, path: str, message: str) -> str:
        """Push content to GitHub repository."""
        try:
            import requests
            import base64
        except ImportError:
            return json.dumps({"error": "requests library required"})
        
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            return json.dumps({
                "error": "GITHUB_TOKEN environment variable required",
                "instructions": "Set GITHUB_TOKEN with a PAT that has repo write access to billwhalenmsft/RAPP-Agent-Repo"
            })
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Check if file exists (to get SHA for update)
        url = f"{self.GITHUB_API}/repos/{self.REGISTRY_REPO}/contents/{path}"
        
        existing_sha = None
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            existing_sha = response.json().get("sha")
        
        # Create/update file
        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": self.REGISTRY_BRANCH
        }
        
        if existing_sha:
            data["sha"] = existing_sha
        
        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            return json.dumps({
                "status": "success",
                "message": "Agent published successfully",
                "path": path,
                "url": result.get("content", {}).get("html_url"),
                "sha": result.get("content", {}).get("sha"),
                "action": "updated" if existing_sha else "created"
            }, indent=2)
        else:
            return json.dumps({
                "error": f"Failed to publish: {response.status_code}",
                "details": response.text
            })
    
    def _sync_registry(self) -> str:
        """Sync registry.json with published agents."""
        # This would update the registry.json file in the repo
        # For now, return instructions
        return json.dumps({
            "status": "info",
            "message": "Registry sync updates the registry.json manifest",
            "path": "registry.json",
            "instructions": "After publishing agents, run this to update the central registry manifest"
        })
