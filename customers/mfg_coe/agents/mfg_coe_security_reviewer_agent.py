"""
Agent: MfgCoE Security Reviewer Agent
Purpose: Security Reviewer persona for the Discrete Manufacturing CoE.
         Reviews agent-generated code, D365/Power Platform configurations,
         API integrations, and web UI features for security issues before
         they reach production.

         Focuses on: credential handling, auth flows, data exposure,
         permissions scoping, injection risks, and Power Platform/D365
         governance. Does NOT modify code — outputs findings only.

Actions:
  review_code            — Scan agent or function code for security issues
  review_auth_flow       — Review an authentication configuration or flow
  review_api_config      — Review API endpoint or connector configuration
  review_permissions     — Review Power Platform / D365 permission model
  review_web_feature     — Security check for a web UI feature spec
  check_secrets          — Scan for hardcoded credentials or secrets
  generate_security_checklist — Pre-deployment security checklist for a feature
  get_security_standards — Return CoE security standards
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

from agents.basic_agent import BasicAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECURITY_STANDARDS = {
    "credentials": [
        "Never hardcode API keys, connection strings, or passwords in code",
        "All secrets in local.settings.json (gitignored) locally, GitHub/Azure Secrets in CI",
        "Use Managed Identity for Azure service-to-service auth wherever possible",
        "OAuth 2.0 / Entra ID for all user-facing authentication",
        "Rotate secrets quarterly or on any personnel change",
    ],
    "power_platform": [
        "Principle of least privilege: only grant the roles a user needs",
        "Custom connectors must use OAuth or Azure AD, not basic auth",
        "Dataverse row-level security for multi-tenant or sensitive data",
        "Power Automate flows must not store sensitive data in run history",
        "ALM (dev → test → prod) environments — no direct prod edits",
    ],
    "d365": [
        "Audit logging enabled on all sensitive entities (case, account, contact)",
        "Field-level security for PII and financial data",
        "Business unit + team scoping for data access",
        "Plugin code reviewed for SQL injection (dynamic FetchXML)",
        "No hardcoded GUIDs for system user accounts in plugin code",
    ],
    "azure": [
        "Azure Functions use Managed Identity, not connection strings where possible",
        "CORS restricted to known origins in production",
        "Function-level auth keys rotated regularly",
        "No PII logged to Application Insights without masking",
        "Storage accounts: disable public blob access unless explicitly required",
    ],
    "web": [
        "Content Security Policy headers set",
        "No secrets in JavaScript or HTML source",
        "GitHub OAuth tokens never stored in localStorage",
        "HTTPS enforced — no HTTP fallback",
        "Input sanitization before any API call",
    ],
}

SECRET_PATTERNS = [
    (r"['\"]?api[-_]?key['\"]?\s*[:=]\s*['\"][A-Za-z0-9+/=_-]{20,}", "Possible API key"),
    (r"['\"]?password['\"]?\s*[:=]\s*['\"][^'\"]{6,}", "Possible hardcoded password"),
    (r"DefaultEndpointsProtocol=https;AccountName=", "Azure Storage connection string"),
    (r"sk-[A-Za-z0-9]{32,}", "OpenAI API key pattern"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token"),
    (r"['\"]?secret['\"]?\s*[:=]\s*['\"][A-Za-z0-9+/=_-]{16,}", "Possible secret value"),
    (r"Bearer [A-Za-z0-9+/=_.-]{20,}", "Hardcoded Bearer token"),
    (r"c0p110t0-aaaa-bbbb-cccc-123456789abc", "Default GUID in code (OK — intentional guardrail)"),
]


class MfgCoESecurityReviewerAgent(BasicAgent):
    """
    Security Reviewer — reviews code, configs, and flows for security issues
    before they reach production. Does NOT modify code. Returns findings only.
    Works with Developer and Architect agents — Security Reviewer must sign off
    before any feature moves to outcome-validated stage.
    """

    def __init__(self):
        self.name = "MfgCoESecurityReviewer"
        self.metadata = {
            "name": self.name,
            "description": (
                "Security Reviewer agent — scans CoE deliverables for security issues: "
                "credential exposure, auth flow gaps, permission over-scoping, injection risks, "
                "and Power Platform/D365 governance gaps. Does NOT modify code. "
                "Must sign off before any feature moves to outcome-validated stage."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "review_code",
                            "review_auth_flow",
                            "review_api_config",
                            "review_permissions",
                            "review_web_feature",
                            "check_secrets",
                            "generate_security_checklist",
                            "get_security_standards",
                        ],
                        "description": "Security review action",
                    },
                    "file_path": {"type": "string", "description": "Path to file to review"},
                    "content": {"type": "string", "description": "Code or config content to review"},
                    "feature_name": {"type": "string", "description": "Feature name for checklist"},
                    "auth_type": {
                        "type": "string",
                        "enum": ["oauth", "api_key", "managed_identity", "basic", "entra_id"],
                        "description": "Auth type being reviewed",
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["azure", "power_platform", "d365", "web", "copilot_studio"],
                        "description": "Platform context for review",
                    },
                    "context": {"type": "string", "description": "Additional context"},
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_security_standards")
        handlers = {
            "review_code": self._review_code,
            "review_auth_flow": self._review_auth_flow,
            "review_api_config": self._review_api_config,
            "review_permissions": self._review_permissions,
            "review_web_feature": self._review_web_feature,
            "check_secrets": self._check_secrets,
            "generate_security_checklist": self._generate_security_checklist,
            "get_security_standards": self._get_security_standards,
        }
        handler = handlers.get(action)
        if not handler:
            return json.dumps({"error": f"Unknown action: {action}"})
        try:
            return handler(**kwargs)
        except Exception as e:
            logger.error("SecurityReviewer error in %s: %s", action, e)
            return json.dumps({"error": str(e)})

    def _check_secrets(self, **kwargs) -> str:
        content = kwargs.get("content", "")
        file_path = kwargs.get("file_path", "")

        if file_path and not content:
            try:
                content = Path(file_path).read_text(encoding="utf-8")
            except Exception as e:
                return json.dumps({"error": f"Could not read file: {e}"})

        findings = []
        for pattern, label in SECRET_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Don't flag the intentional default GUID
                if "c0p110t0" in match:
                    continue
                findings.append({
                    "type": label,
                    "match": match[:60] + "..." if len(match) > 60 else match,
                    "severity": "HIGH",
                })

        status = "clean" if not findings else "secrets_found"
        return json.dumps({
            "status": status,
            "findings": findings,
            "finding_count": len(findings),
            "summary": f"Secret scan complete. {len(findings)} potential secret(s) found." if findings else "No secrets detected.",
            "persona": "security-reviewer",
        }, indent=2)

    def _review_code(self, **kwargs) -> str:
        content = kwargs.get("content", "")
        file_path = kwargs.get("file_path", "")

        if file_path and not content:
            try:
                content = Path(file_path).read_text(encoding="utf-8")
            except Exception as e:
                return json.dumps({"error": f"Could not read file: {e}"})

        findings = []

        # Run secret scan
        secret_result = json.loads(self._check_secrets(content=content))
        if secret_result.get("finding_count", 0) > 0:
            findings.extend([{"severity": "HIGH", "category": "secrets", "detail": f["type"]} for f in secret_result["findings"]])

        # Check for common Python security issues
        if "eval(" in content:
            findings.append({"severity": "HIGH", "category": "injection", "detail": "eval() usage — code injection risk"})
        if "exec(" in content:
            findings.append({"severity": "HIGH", "category": "injection", "detail": "exec() usage — code injection risk"})
        if "subprocess.call(" in content and "shell=True" in content:
            findings.append({"severity": "HIGH", "category": "injection", "detail": "subprocess with shell=True — command injection risk"})
        if "pickle.loads" in content:
            findings.append({"severity": "MEDIUM", "category": "deserialization", "detail": "pickle.loads() — unsafe deserialization"})
        if "http://" in content and "localhost" not in content:
            findings.append({"severity": "MEDIUM", "category": "transport", "detail": "Non-HTTPS URL in code"})
        if "USE_CLOUD_STORAGE" not in content and "local_storage" in content.lower():
            findings.append({"severity": "LOW", "category": "config", "detail": "Local storage path — ensure not used in production"})

        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        findings.sort(key=lambda x: severity_order.get(x["severity"], 3))
        high = sum(1 for f in findings if f["severity"] == "HIGH")
        status = "blocked" if high > 0 else ("review_recommended" if findings else "approved")

        return json.dumps({
            "status": status,
            "findings": findings,
            "finding_count": len(findings),
            "high_severity": high,
            "summary": (
                f"Code review complete. {len(findings)} finding(s): {high} HIGH. "
                f"Status: {'BLOCKED — resolve HIGH findings before proceeding' if high > 0 else 'approved' if not findings else 'review recommended'}."
            ),
            "persona": "security-reviewer",
        }, indent=2)

    def _review_auth_flow(self, **kwargs) -> str:
        auth_type = kwargs.get("auth_type", "unknown")
        context = kwargs.get("context", "")
        platform = kwargs.get("platform", "azure")

        recommendations = {
            "oauth": ["✅ Good choice — use Entra ID (Azure AD) as the identity provider", "Verify redirect URIs are locked to known domains", "Use PKCE for public clients (SPAs, mobile)"],
            "managed_identity": ["✅ Best practice for Azure service-to-service auth", "Verify the identity has minimum required permissions", "No secrets to rotate — preferred over API keys"],
            "api_key": ["⚠️ Use only when OAuth/MI is not available", "Store in Azure Key Vault, not environment variables or code", "Rotate quarterly, audit usage logs monthly"],
            "basic": ["❌ Basic auth is not recommended for production", "Migrate to OAuth 2.0 / Entra ID", "If unavoidable, enforce TLS and IP allowlist"],
            "entra_id": ["✅ Recommended for all Microsoft 365 / Azure integrations", "Use app registrations with minimum required permissions", "Enable conditional access policies for sensitive scopes"],
        }

        recs = recommendations.get(auth_type, ["Unknown auth type — review manually"])
        recs_md = "\n".join(f"- {r}" for r in recs)

        return json.dumps({
            "status": "ok",
            "auth_type": auth_type,
            "recommendations": recs,
            "summary": f"Auth flow review: {auth_type}. {len(recs)} recommendation(s).",
            "markdown": f"## Auth Review: {auth_type.upper()}\n\n{recs_md}",
            "persona": "security-reviewer",
        }, indent=2)

    def _review_api_config(self, **kwargs) -> str:
        context = kwargs.get("context", "")
        checks = [
            ("HTTPS enforced", None),
            ("CORS restricted to known origins", None),
            ("Auth required (no anonymous endpoints in prod)", None),
            ("Rate limiting / throttling configured", None),
            ("Input validation on all parameters", None),
            ("No PII in query strings or URLs", None),
            ("Logging does not capture sensitive payloads", None),
        ]
        checklist_md = "\n".join(f"- {'✅' if v else '⬜'} {label}" for label, v in checks)
        return json.dumps({
            "status": "review_needed",
            "summary": "API config review checklist generated. Manual verification required.",
            "checklist": f"## API Security Checklist\n\n{checklist_md}",
            "persona": "security-reviewer",
        }, indent=2)

    def _review_permissions(self, **kwargs) -> str:
        platform = kwargs.get("platform", "power_platform")
        standards = SECURITY_STANDARDS.get(platform, SECURITY_STANDARDS["azure"])
        standards_md = "\n".join(f"- {s}" for s in standards)
        return json.dumps({
            "status": "ok",
            "platform": platform,
            "standards": standards,
            "summary": f"Permission standards for {platform}: {len(standards)} items.",
            "markdown": f"## Permission Standards: {platform.replace('_', ' ').title()}\n\n{standards_md}",
            "persona": "security-reviewer",
        }, indent=2)

    def _review_web_feature(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Web Feature")
        checks = [
            "Content Security Policy headers set",
            "No secrets in JS/HTML source",
            "Auth tokens not stored in localStorage",
            "HTTPS enforced",
            "User input sanitized before API calls",
            "GitHub OAuth state parameter validated (CSRF protection)",
            "Error messages don't expose stack traces to users",
        ]
        checklist_md = "\n".join(f"- ⬜ {c}" for c in checks)
        return json.dumps({
            "status": "review_needed",
            "summary": f"Web security checklist for: {feature}",
            "checklist": f"## Web Security Review: {feature}\n\n{checklist_md}",
            "persona": "security-reviewer",
        }, indent=2)

    def _generate_security_checklist(self, **kwargs) -> str:
        feature = kwargs.get("feature_name", "Feature")
        platform = kwargs.get("platform", "azure")
        standards = SECURITY_STANDARDS.get(platform, SECURITY_STANDARDS["azure"])
        items_md = "\n".join(f"- [ ] {s}" for s in standards)
        return json.dumps({
            "status": "ok",
            "summary": f"Pre-deployment security checklist: {feature} on {platform}",
            "checklist": (
                f"## 🔐 Pre-Deployment Security Checklist\n"
                f"**Feature:** {feature} | **Platform:** {platform}\n\n"
                f"{items_md}\n\n"
                f"*Security Reviewer must sign off before outcome-validated stage.*"
            ),
            "persona": "security-reviewer",
        }, indent=2)

    def _get_security_standards(self, **kwargs) -> str:
        all_standards = []
        for category, items in SECURITY_STANDARDS.items():
            for item in items:
                all_standards.append({"category": category, "standard": item})
        return json.dumps({
            "status": "ok",
            "count": len(all_standards),
            "standards": SECURITY_STANDARDS,
            "summary": f"{len(all_standards)} security standards across {len(SECURITY_STANDARDS)} categories.",
            "persona": "security-reviewer",
        }, indent=2)
