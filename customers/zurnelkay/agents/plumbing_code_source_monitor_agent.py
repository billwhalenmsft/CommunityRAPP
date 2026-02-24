"""
Agent: Commercial Plumbing Code – Source Monitor
Purpose: Monthly scan of authoritative plumbing code sources for new/updated content
Pipeline Position: Agent 1 of 3 (Source Monitor → Tech Extractor → Monthly Synthesizer)
Output Tag: SOURCE_LOG

This agent scans hard-coded authoritative sources monthly and produces a structured
SOURCE_LOG of new/updated documents. It does NOT analyze, summarize business implications,
or draw conclusions — that is the job of downstream agents.

Authoritative Sources:
- IAPMO (UPC): code cycles, proposals, committee agendas, minutes, task group updates
- ICC (IPC): code development hearings, public comments, ballots and results
- ASPE: Research Foundation publications, technical symposia, webinars, technical briefs
- ASHRAE: standards/committee activity intersecting plumbing systems
- EPA: drinking water rules and guidance affecting plumbing systems or products
- CDC: Legionella and building water system guidance
- NSF: standards updates relevant to plumbing products or systems
- Select large AHJs: NYC, California, Texas, Massachusetts, Chicago
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from agents.basic_agent import BasicAgent
from utils.storage_factory import get_storage_manager

# Azure OpenAI
try:
    from openai import AzureOpenAI
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    AZURE_AI_AVAILABLE = True
except ImportError:
    AZURE_AI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Hard-coded authoritative source registry
# ─────────────────────────────────────────────────────────────────────────────
AUTHORITATIVE_SOURCES = [
    {
        "id": "iapmo_upc",
        "name": "IAPMO (Uniform Plumbing Code)",
        "abbreviation": "IAPMO/UPC",
        "scope": "Code cycles, proposals, committee agendas, minutes, task group updates",
        "url": "https://www.iapmo.org",
        "search_terms": [
            "IAPMO UPC code proposal",
            "IAPMO committee agenda plumbing",
            "Uniform Plumbing Code amendment",
            "IAPMO task group plumbing",
            "IAPMO technical committee minutes"
        ],
        "category": "model_code"
    },
    {
        "id": "icc_ipc",
        "name": "ICC (International Plumbing Code)",
        "abbreviation": "ICC/IPC",
        "scope": "Code development hearings, public comments, ballots and results",
        "url": "https://www.iccsafe.org",
        "search_terms": [
            "ICC IPC code development hearing",
            "International Plumbing Code public comment",
            "ICC plumbing ballot results",
            "ICC IPC proposal",
            "ICC plumbing code change"
        ],
        "category": "model_code"
    },
    {
        "id": "aspe",
        "name": "ASPE (American Society of Plumbing Engineers)",
        "abbreviation": "ASPE",
        "scope": "Research Foundation publications, technical symposia, webinars, technical briefs",
        "url": "https://www.aspe.org",
        "search_terms": [
            "ASPE Research Foundation publication",
            "ASPE technical symposium plumbing",
            "ASPE plumbing engineering webinar",
            "ASPE technical brief",
            "ASPE design standard update"
        ],
        "category": "professional_body"
    },
    {
        "id": "ashrae",
        "name": "ASHRAE",
        "abbreviation": "ASHRAE",
        "scope": "Standards and committee activity intersecting plumbing systems (water safety, efficiency, building water systems)",
        "url": "https://www.ashrae.org",
        "search_terms": [
            "ASHRAE Standard 188 Legionella",
            "ASHRAE plumbing system standard",
            "ASHRAE water management building",
            "ASHRAE committee plumbing water",
            "ASHRAE Guideline 12 water system"
        ],
        "category": "standard"
    },
    {
        "id": "epa",
        "name": "EPA (Environmental Protection Agency)",
        "abbreviation": "EPA",
        "scope": "Drinking water rules and guidance affecting plumbing systems or products",
        "url": "https://www.epa.gov",
        "search_terms": [
            "EPA drinking water rule plumbing",
            "EPA Lead and Copper Rule",
            "EPA PFAS drinking water",
            "EPA water system guidance",
            "EPA plumbing product regulation"
        ],
        "category": "federal_agency"
    },
    {
        "id": "cdc",
        "name": "CDC (Centers for Disease Control and Prevention)",
        "abbreviation": "CDC",
        "scope": "Legionella and building water system guidance",
        "url": "https://www.cdc.gov",
        "search_terms": [
            "CDC Legionella building water",
            "CDC water management program",
            "CDC plumbing waterborne disease",
            "CDC building water system guidance",
            "CDC Legionella prevention"
        ],
        "category": "federal_agency"
    },
    {
        "id": "nsf",
        "name": "NSF International",
        "abbreviation": "NSF",
        "scope": "Standards updates relevant to plumbing products or systems",
        "url": "https://www.nsf.org",
        "search_terms": [
            "NSF ANSI 61 drinking water",
            "NSF plumbing product standard",
            "NSF 372 lead content",
            "NSF certification plumbing",
            "NSF standard update water"
        ],
        "category": "standard"
    },
    {
        "id": "ahj_nyc",
        "name": "New York City (AHJ)",
        "abbreviation": "NYC",
        "scope": "NYC plumbing code amendments, bulletins, and local requirements",
        "url": "https://www.nyc.gov/buildings",
        "search_terms": [
            "NYC plumbing code amendment",
            "New York City buildings bulletin plumbing",
            "NYC DOB plumbing requirement"
        ],
        "category": "local_ahj"
    },
    {
        "id": "ahj_california",
        "name": "California (AHJ)",
        "abbreviation": "CA",
        "scope": "California Plumbing Code (CPC) updates, Title 24, CalGreen plumbing provisions",
        "url": "https://www.dgs.ca.gov/BSC",
        "search_terms": [
            "California Plumbing Code update",
            "CalGreen plumbing provision",
            "California Title 24 plumbing",
            "California BSC plumbing amendment"
        ],
        "category": "local_ahj"
    },
    {
        "id": "ahj_texas",
        "name": "Texas (AHJ)",
        "abbreviation": "TX",
        "scope": "Texas plumbing code adoption, TSBPE rules and amendments",
        "url": "https://www.tsbpe.texas.gov",
        "search_terms": [
            "Texas plumbing code adoption",
            "TSBPE plumbing rule amendment",
            "Texas State Board of Plumbing Examiners"
        ],
        "category": "local_ahj"
    },
    {
        "id": "ahj_massachusetts",
        "name": "Massachusetts (AHJ)",
        "abbreviation": "MA",
        "scope": "Massachusetts plumbing code (248 CMR) updates",
        "url": "https://www.mass.gov",
        "search_terms": [
            "Massachusetts plumbing code 248 CMR",
            "Massachusetts plumbing board amendment",
            "MA plumbing regulation update"
        ],
        "category": "local_ahj"
    },
    {
        "id": "ahj_chicago",
        "name": "Chicago (AHJ)",
        "abbreviation": "CHI",
        "scope": "Chicago plumbing code amendments and municipal requirements",
        "url": "https://www.chicago.gov",
        "search_terms": [
            "Chicago plumbing code amendment",
            "Chicago municipal plumbing ordinance",
            "Chicago building department plumbing"
        ],
        "category": "local_ahj"
    }
]

# Valid document types for SOURCE_LOG entries
DOCUMENT_TYPES = [
    "proposal",
    "ballot",
    "adopted",
    "guidance",
    "minutes",
    "informational",
    "revision",
    "addendum",
    "errata",
    "rfi_rfc",
    "committee_action",
    "public_comment",
    "hearing"
]


class PlumbingCodeSourceMonitorAgent(BasicAgent):
    """
    Commercial Plumbing Code Source Monitor — Agent 1 of the Code Intelligence Pipeline.

    Scans authoritative plumbing code sources monthly and produces a structured
    SOURCE_LOG. No analysis, no implications — primary source documents only.
    
    Output is persisted to: plumbing_intel/{YYYY-MM}/source_log.json
    Downstream consumer: PlumbingCodeTechExtractorAgent (Agent 2)
    """

    def __init__(self):
        self.name = 'PlumbingCodeSourceMonitor'
        self.metadata = {
            "name": self.name,
            "description": (
                "Commercial Plumbing Code Source Monitor. Scans authoritative sources "
                "(IAPMO/UPC, ICC/IPC, ASPE, ASHRAE, EPA, CDC, NSF, and select AHJs) monthly "
                "for new or updated plumbing code documents, proposals, ballots, revisions, "
                "committee actions, and guidance. Produces a structured SOURCE_LOG with no "
                "analysis or business implications. This is Agent 1 of the 3-agent Code "
                "Intelligence pipeline."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "scan_sources",
                            "scan_single_source",
                            "get_source_list",
                            "get_last_scan",
                            "get_scan_history"
                        ],
                        "description": (
                            "Action to perform: "
                            "'scan_sources' = run full monthly scan of all authoritative sources; "
                            "'scan_single_source' = scan one specific source; "
                            "'get_source_list' = list all configured authoritative sources; "
                            "'get_last_scan' = retrieve the most recent SOURCE_LOG; "
                            "'get_scan_history' = list available monthly scans"
                        )
                    },
                    "month": {
                        "type": "string",
                        "description": "Target month in YYYY-MM format (e.g., '2026-02'). Defaults to current month."
                    },
                    "source_id": {
                        "type": "string",
                        "description": (
                            "Source ID for scan_single_source action. One of: "
                            "iapmo_upc, icc_ipc, aspe, ashrae, epa, cdc, nsf, "
                            "ahj_nyc, ahj_california, ahj_texas, ahj_massachusetts, ahj_chicago"
                        )
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

        self.storage_manager = get_storage_manager()
        self.openai_client = None
        self._init_openai_client()

    # ─────────────────────────────────────────────────────────────────────────
    # Initialization
    # ─────────────────────────────────────────────────────────────────────────

    def _init_openai_client(self):
        """Initialize Azure OpenAI client using environment configuration."""
        if not AZURE_AI_AVAILABLE:
            logger.warning("Azure OpenAI SDK not available — AI-powered scanning disabled")
            return
        try:
            endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
            api_key = os.environ.get('AZURE_OPENAI_API_KEY')
            if endpoint and api_key:
                self.openai_client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
                )
                logger.info("PlumbingCodeSourceMonitor: OpenAI client initialized")
            else:
                # Try token-based auth
                try:
                    credential = DefaultAzureCredential()
                    token_provider = get_bearer_token_provider(
                        credential, "https://cognitiveservices.azure.com/.default"
                    )
                    self.openai_client = AzureOpenAI(
                        azure_endpoint=endpoint or "",
                        azure_ad_token_provider=token_provider,
                        api_version=os.environ.get('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
                    )
                    logger.info("PlumbingCodeSourceMonitor: OpenAI client initialized (token auth)")
                except Exception:
                    logger.warning("PlumbingCodeSourceMonitor: No OpenAI credentials available")
        except Exception as e:
            logger.error(f"PlumbingCodeSourceMonitor: Failed to initialize OpenAI: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Action router
    # ─────────────────────────────────────────────────────────────────────────

    def perform(self, **kwargs) -> str:
        """Route to the requested action."""
        action = kwargs.get('action', 'get_source_list')
        month = kwargs.get('month') or datetime.now().strftime('%Y-%m')
        source_id = kwargs.get('source_id')

        actions = {
            "scan_sources": lambda: self._scan_all_sources(month),
            "scan_single_source": lambda: self._scan_single_source(month, source_id),
            "get_source_list": lambda: self._get_source_list(),
            "get_last_scan": lambda: self._get_last_scan(month),
            "get_scan_history": lambda: self._get_scan_history(),
        }

        if action not in actions:
            return json.dumps({
                "error": f"Unknown action: {action}",
                "available_actions": list(actions.keys())
            }, indent=2)

        try:
            result = actions[action]()
            return result if isinstance(result, str) else json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"PlumbingCodeSourceMonitor error in {action}: {e}")
            return json.dumps({"error": str(e), "action": action}, indent=2)

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_source_list
    # ─────────────────────────────────────────────────────────────────────────

    def _get_source_list(self) -> Dict[str, Any]:
        """Return the full list of configured authoritative sources."""
        sources_by_category = {}
        for src in AUTHORITATIVE_SOURCES:
            cat = src["category"]
            if cat not in sources_by_category:
                sources_by_category[cat] = []
            sources_by_category[cat].append({
                "id": src["id"],
                "name": src["name"],
                "abbreviation": src["abbreviation"],
                "scope": src["scope"],
                "url": src["url"]
            })

        return {
            "title": "Commercial Plumbing Code — Authoritative Source Registry",
            "total_sources": len(AUTHORITATIVE_SOURCES),
            "categories": {
                "model_code": "National model codes (UPC, IPC)",
                "standard": "Standards organizations (ASHRAE, NSF)",
                "professional_body": "Professional engineering societies (ASPE)",
                "federal_agency": "Federal agencies (EPA, CDC)",
                "local_ahj": "Authorities Having Jurisdiction (local codes)"
            },
            "sources_by_category": sources_by_category,
            "valid_document_types": DOCUMENT_TYPES
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Action: scan_sources (full monthly scan)
    # ─────────────────────────────────────────────────────────────────────────

    def _scan_all_sources(self, month: str) -> Dict[str, Any]:
        """
        Run the full monthly scan across all authoritative sources.
        Uses Azure OpenAI to research and structure findings.
        Persists the SOURCE_LOG to storage.
        """
        logger.info(f"PlumbingCodeSourceMonitor: Starting full scan for {month}")

        if not self.openai_client:
            # Fall back to simulated data when no AI client
            return self._generate_simulated_scan(month)

        all_entries = []
        scan_errors = []

        for source in AUTHORITATIVE_SOURCES:
            try:
                entries = self._scan_source_with_ai(month, source)
                all_entries.extend(entries)
            except Exception as e:
                error_msg = f"Error scanning {source['abbreviation']}: {str(e)}"
                logger.error(error_msg)
                scan_errors.append(error_msg)

        source_log = self._build_source_log(month, all_entries, scan_errors)

        # Persist to storage
        self._persist_source_log(month, source_log)

        return source_log

    # ─────────────────────────────────────────────────────────────────────────
    # Action: scan_single_source
    # ─────────────────────────────────────────────────────────────────────────

    def _scan_single_source(self, month: str, source_id: Optional[str]) -> Dict[str, Any]:
        """Scan a single authoritative source by ID."""
        if not source_id:
            return {"error": "source_id is required for scan_single_source action"}

        source = next((s for s in AUTHORITATIVE_SOURCES if s["id"] == source_id), None)
        if not source:
            valid_ids = [s["id"] for s in AUTHORITATIVE_SOURCES]
            return {"error": f"Unknown source_id: {source_id}", "valid_ids": valid_ids}

        if not self.openai_client:
            # Simulated single-source scan
            simulated = self._get_simulated_entries_for_source(month, source)
            return {
                "SOURCE_LOG": {
                    "scan_month": month,
                    "scan_date": datetime.now().isoformat(),
                    "source_scanned": source["abbreviation"],
                    "entries": simulated,
                    "entry_count": len(simulated),
                    "mode": "simulated"
                }
            }

        try:
            entries = self._scan_source_with_ai(month, source)
            result = {
                "SOURCE_LOG": {
                    "scan_month": month,
                    "scan_date": datetime.now().isoformat(),
                    "source_scanned": source["abbreviation"],
                    "entries": entries,
                    "entry_count": len(entries),
                    "mode": "ai_research"
                }
            }
            return result
        except Exception as e:
            return {"error": str(e), "source": source["abbreviation"]}

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_last_scan
    # ─────────────────────────────────────────────────────────────────────────

    def _get_last_scan(self, month: str) -> Dict[str, Any]:
        """Retrieve the SOURCE_LOG for a specific month from storage."""
        storage_path = f"plumbing_intel/{month}"
        try:
            content = self.storage_manager.read_file(storage_path, "source_log.json")
            if content:
                return json.loads(content)
            else:
                return {
                    "message": f"No SOURCE_LOG found for {month}",
                    "hint": "Run scan_sources to generate one"
                }
        except Exception as e:
            return {"error": f"Failed to read SOURCE_LOG for {month}: {str(e)}"}

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_scan_history
    # ─────────────────────────────────────────────────────────────────────────

    def _get_scan_history(self) -> Dict[str, Any]:
        """List all available monthly scans in storage."""
        try:
            files = self.storage_manager.list_files("plumbing_intel")
            months = set()
            for f in files:
                name = f.name if hasattr(f, 'name') else str(f)
                # Directories look like "2026-02/" or files inside them
                parts = name.strip('/').split('/')
                if parts and len(parts[0]) == 7:  # YYYY-MM format
                    months.add(parts[0])
            return {
                "available_months": sorted(months, reverse=True),
                "total_scans": len(months)
            }
        except Exception as e:
            return {"available_months": [], "note": f"Could not list history: {str(e)}"}

    # ─────────────────────────────────────────────────────────────────────────
    # AI-powered source scanning
    # ─────────────────────────────────────────────────────────────────────────

    def _scan_source_with_ai(self, month: str, source: Dict) -> List[Dict]:
        """
        Use Azure OpenAI to research a single authoritative source and
        return structured SOURCE_LOG entries.
        """
        deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')

        system_prompt = f"""You are a regulatory research assistant specializing in commercial plumbing codes and standards.

Your task: identify documents published or updated by {source['name']} ({source['abbreviation']}) during or relevant to the month of {month}.

Scope of this source: {source['scope']}
Source website: {source['url']}

RULES:
1. Only report items you have HIGH confidence actually exist. Do not fabricate documents.
2. Prefer primary source documents over commentary.
3. If you cannot confirm a document exists, say so explicitly — do NOT guess.
4. Each entry must be neutral and factual — NO business implications, NO analysis.
5. Use the exact JSON schema provided.

For each item found, return a JSON array of objects with these fields:
- "governing_body": "{source['abbreviation']}"
- "document_title": exact title of the document
- "publication_date": date in YYYY-MM-DD format (or "unknown" if not available)
- "document_type": one of {json.dumps(DOCUMENT_TYPES)}
- "direct_link": URL to the document (or "not available")
- "description": 1-2 line neutral description of what the document is
- "primary_source_accessible": true/false — whether the primary document can be accessed
- "confidence": "high", "medium", or "low"

If no new or updated documents were found for this source during {month}, return an empty array [].

Return ONLY a valid JSON array. No markdown, no explanation."""

        user_prompt = f"""Search for new or updated documents from {source['name']} ({source['abbreviation']}) for the month of {month}.

Key search areas: {source['scope']}

Useful search terms: {json.dumps(source['search_terms'])}

Return a JSON array of SOURCE_LOG entries. If nothing found, return []."""

        try:
            response = self.openai_client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)

            # Handle both {"entries": [...]} and [...] formats
            if isinstance(parsed, list):
                entries = parsed
            elif isinstance(parsed, dict):
                entries = parsed.get("entries", parsed.get("items", parsed.get("source_log", [])))
                if isinstance(entries, dict):
                    entries = [entries]
            else:
                entries = []

            # Validate and normalize each entry
            validated = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                validated.append({
                    "governing_body": entry.get("governing_body", source["abbreviation"]),
                    "document_title": entry.get("document_title", "Untitled"),
                    "publication_date": entry.get("publication_date", "unknown"),
                    "document_type": entry.get("document_type", "informational"),
                    "direct_link": entry.get("direct_link", "not available"),
                    "description": entry.get("description", "No description provided."),
                    "primary_source_accessible": entry.get("primary_source_accessible", False),
                    "confidence": entry.get("confidence", "low"),
                    "source_category": source["category"]
                })

            logger.info(f"  {source['abbreviation']}: found {len(validated)} entries")
            return validated

        except Exception as e:
            logger.error(f"AI scan failed for {source['abbreviation']}: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # Build and persist SOURCE_LOG
    # ─────────────────────────────────────────────────────────────────────────

    def _build_source_log(self, month: str, entries: List[Dict], errors: List[str]) -> Dict[str, Any]:
        """Assemble the final SOURCE_LOG document."""
        # Count by governing body
        body_counts = {}
        for e in entries:
            body = e.get("governing_body", "Unknown")
            body_counts[body] = body_counts.get(body, 0) + 1

        # Count by type
        type_counts = {}
        for e in entries:
            doc_type = e.get("document_type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        return {
            "SOURCE_LOG": {
                "scan_month": month,
                "scan_date": datetime.now().isoformat(),
                "pipeline_position": "Agent 1 of 3 — Source Monitor",
                "downstream_consumer": "PlumbingCodeTechExtractor (Agent 2)",
                "output_tag": "SOURCE_LOG",
                "total_entries": len(entries),
                "entries_by_source": body_counts,
                "entries_by_type": type_counts,
                "scan_errors": errors,
                "sources_configured": len(AUTHORITATIVE_SOURCES),
                "entries": entries
            }
        }

    def _persist_source_log(self, month: str, source_log: Dict):
        """Save the SOURCE_LOG to Azure File Storage / local storage."""
        storage_path = f"plumbing_intel/{month}"
        try:
            self.storage_manager.ensure_directory_exists(storage_path)
            content = json.dumps(source_log, indent=2)
            self.storage_manager.write_file(storage_path, "source_log.json", content)
            logger.info(f"PlumbingCodeSourceMonitor: SOURCE_LOG persisted to {storage_path}/source_log.json")
        except Exception as e:
            logger.error(f"PlumbingCodeSourceMonitor: Failed to persist SOURCE_LOG: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Simulated data (used when no OpenAI client is available)
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_simulated_scan(self, month: str) -> Dict[str, Any]:
        """Generate a realistic simulated SOURCE_LOG for demo/testing purposes."""
        logger.info(f"PlumbingCodeSourceMonitor: Generating simulated scan for {month} (no AI client)")

        all_entries = []
        for source in AUTHORITATIVE_SOURCES:
            entries = self._get_simulated_entries_for_source(month, source)
            all_entries.extend(entries)

        source_log = self._build_source_log(month, all_entries, 
                                             errors=["Note: Simulated data — no live AI research performed"])
        source_log["SOURCE_LOG"]["mode"] = "simulated"

        self._persist_source_log(month, source_log)
        return source_log

    def _get_simulated_entries_for_source(self, month: str, source: Dict) -> List[Dict]:
        """Return simulated entries for a given source — realistic plumbing code content."""

        simulated_data = {
            "iapmo_upc": [
                {
                    "governing_body": "IAPMO/UPC",
                    "document_title": "2027 UPC Code Development — Cycle 1 Proposals Published",
                    "publication_date": f"{month}-05",
                    "document_type": "proposal",
                    "direct_link": "https://www.iapmo.org/upc-code-development",
                    "description": "IAPMO published the first set of code change proposals for the 2027 Uniform Plumbing Code cycle. Includes 47 proposals spanning backflow, water heaters, and drainage systems.",
                    "primary_source_accessible": True,
                    "confidence": "high",
                    "source_category": "model_code"
                },
                {
                    "governing_body": "IAPMO/UPC",
                    "document_title": "Technical Committee on Backflow Prevention — Meeting Minutes",
                    "publication_date": f"{month}-12",
                    "document_type": "minutes",
                    "direct_link": "https://www.iapmo.org/technical-committees",
                    "description": "Minutes from the quarterly meeting of the IAPMO Technical Committee on Backflow Prevention and Cross-Connection Control. Discussion included testability requirements for RPZ assemblies.",
                    "primary_source_accessible": True,
                    "confidence": "high",
                    "source_category": "model_code"
                }
            ],
            "icc_ipc": [
                {
                    "governing_body": "ICC/IPC",
                    "document_title": "IPC Public Comment Hearing Results — Group B (Plumbing)",
                    "publication_date": f"{month}-08",
                    "document_type": "public_comment",
                    "direct_link": "https://www.iccsafe.org/codes-development",
                    "description": "Results from the ICC public comment hearing on Group B International Plumbing Code proposals. Key actions on water efficiency provisions and trap seal protection.",
                    "primary_source_accessible": True,
                    "confidence": "high",
                    "source_category": "model_code"
                }
            ],
            "aspe": [
                {
                    "governing_body": "ASPE",
                    "document_title": "ASPE Research Foundation Report: Water Temperature Maintenance in Large Commercial Buildings",
                    "publication_date": f"{month}-15",
                    "document_type": "informational",
                    "direct_link": "https://www.aspe.org/research",
                    "description": "New research report examining hot water delivery performance and temperature maintenance strategies in buildings over 100,000 sq ft. Includes field data from 12 buildings.",
                    "primary_source_accessible": True,
                    "confidence": "high",
                    "source_category": "professional_body"
                }
            ],
            "ashrae": [
                {
                    "governing_body": "ASHRAE",
                    "document_title": "ASHRAE Standard 188-202x — Public Review Draft: Legionellosis Risk Management for Building Water Systems",
                    "publication_date": f"{month}-01",
                    "document_type": "proposal",
                    "direct_link": "https://www.ashrae.org/standards",
                    "description": "Public review draft for the next edition of ASHRAE Standard 188. Proposes expanded scope to include all building types and strengthened monitoring requirements.",
                    "primary_source_accessible": True,
                    "confidence": "high",
                    "source_category": "standard"
                },
                {
                    "governing_body": "ASHRAE",
                    "document_title": "ASHRAE Guideline 12-202x Update — Committee Activity Summary",
                    "publication_date": f"{month}-18",
                    "document_type": "committee_action",
                    "direct_link": "https://www.ashrae.org/technical-resources",
                    "description": "Summary of committee deliberations on updates to ASHRAE Guideline 12, Minimizing the Risk of Legionellosis Associated with Building Water Systems. Focus on monitoring technology provisions.",
                    "primary_source_accessible": True,
                    "confidence": "medium",
                    "source_category": "standard"
                }
            ],
            "epa": [
                {
                    "governing_body": "EPA",
                    "document_title": "Lead and Copper Rule Improvements (LCRI) — Implementation Guidance for Water Systems",
                    "publication_date": f"{month}-10",
                    "document_type": "guidance",
                    "direct_link": "https://www.epa.gov/ground-water-and-drinking-water/lead-and-copper-rule-improvements",
                    "description": "EPA published implementation guidance for the Lead and Copper Rule Improvements covering service line inventory requirements and lead-free product specifications relevant to plumbing systems.",
                    "primary_source_accessible": True,
                    "confidence": "high",
                    "source_category": "federal_agency"
                }
            ],
            "cdc": [
                {
                    "governing_body": "CDC",
                    "document_title": "Updated Toolkit: Developing a Water Management Program to Reduce Legionella Growth",
                    "publication_date": f"{month}-20",
                    "document_type": "guidance",
                    "direct_link": "https://www.cdc.gov/legionella/wmp/toolkit/index.html",
                    "description": "CDC updated its water management program toolkit with expanded guidance on temperature monitoring, flushing protocols, and point-of-use device management in healthcare and hospitality buildings.",
                    "primary_source_accessible": True,
                    "confidence": "high",
                    "source_category": "federal_agency"
                }
            ],
            "nsf": [
                {
                    "governing_body": "NSF",
                    "document_title": "NSF/ANSI 61 — Revision Ballot: Drinking Water System Components",
                    "publication_date": f"{month}-06",
                    "document_type": "ballot",
                    "direct_link": "https://www.nsf.org/standards",
                    "description": "NSF issued a revision ballot for NSF/ANSI 61 addressing extraction testing protocols for metallic plumbing components and updated weighted-average lead content calculations.",
                    "primary_source_accessible": True,
                    "confidence": "high",
                    "source_category": "standard"
                }
            ],
            "ahj_nyc": [
                {
                    "governing_body": "NYC",
                    "document_title": "NYC DOB Bulletin: Backflow Prevention Device Testing Frequency Update",
                    "publication_date": f"{month}-14",
                    "document_type": "adopted",
                    "direct_link": "https://www.nyc.gov/site/buildings/codes/plumbing-code.page",
                    "description": "NYC Department of Buildings issued a bulletin increasing backflow prevention device testing frequency for high-hazard occupancies from annual to semi-annual.",
                    "primary_source_accessible": True,
                    "confidence": "medium",
                    "source_category": "local_ahj"
                }
            ],
            "ahj_california": [
                {
                    "governing_body": "CA",
                    "document_title": "California BSC: 2025 Intervening Code Cycle — Plumbing Provisions Approved",
                    "publication_date": f"{month}-03",
                    "document_type": "adopted",
                    "direct_link": "https://www.dgs.ca.gov/BSC/Codes",
                    "description": "California Building Standards Commission approved plumbing provisions for the 2025 intervening code cycle including expanded water efficiency requirements and new greywater system provisions.",
                    "primary_source_accessible": True,
                    "confidence": "high",
                    "source_category": "local_ahj"
                }
            ],
            "ahj_texas": [],
            "ahj_massachusetts": [],
            "ahj_chicago": []
        }

        return simulated_data.get(source["id"], [])
