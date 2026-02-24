"""
Agent: Commercial Plumbing Code – Monthly Synthesizer
Purpose: Aggregate Update Cards into a monthly summary organized by topic tag
Pipeline Position: Agent 3 of 3 (Source Monitor → Technical Extractor → Monthly Synthesizer)
Input Tag: UPDATE_CARDS
Output Tag: MONTHLY_REPORT

This agent reads UPDATE_CARDS from Agent 2 (Technical Extractor) and produces a
structured monthly summary organized by topic tag. It aggregates across sources,
maintains neutrality, and labels uncertainty explicitly.

Report Structure:
- Header: month, generation date, data sources
- Topic sections (Water Safety / Legionella, Water Efficiency, etc.)
  - Each topic section lists the relevant Update Cards
  - Neutral summary of developments per topic
- Status dashboard: count of proposals, ballots, adopted, etc.
- Source coverage check: which sources were scanned, which had updates

Output: plumbing_intel/{YYYY-MM}/monthly_report.json
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

# Canonical topic tags (same as Agent 2)
TOPIC_TAGS = [
    "Water Safety / Legionella",
    "Water Efficiency",
    "Materials & Components",
    "Backflow / Cross-Connection",
    "Mixing / Temperature Control",
    "Drainage / Waste / Vent",
    "Digital / Monitoring / Controls",
    "Filtration / Treatment",
    "Installation / Testing / Commissioning",
    "Other"
]


class PlumbingCodeMonthlySynthesizerAgent(BasicAgent):
    """
    Commercial Plumbing Code Monthly Synthesizer — Agent 3 of the Code Intelligence Pipeline.

    Reads UPDATE_CARDS from Agent 2 and produces a structured monthly report
    organized by topic tag. Neutral, factual, no impact ranking.

    Input:  plumbing_intel/{YYYY-MM}/update_cards.json   (UPDATE_CARDS)
    Output: plumbing_intel/{YYYY-MM}/monthly_report.json (MONTHLY_REPORT)
    """

    def __init__(self):
        self.name = 'PlumbingCodeMonthlySynthesizer'
        self.metadata = {
            "name": self.name,
            "description": (
                "Commercial Plumbing Code Monthly Synthesizer. Reads UPDATE_CARDS "
                "produced by the Technical Extractor and generates a structured monthly "
                "report organized by topic tag. Includes topic-by-topic development summaries, "
                "a status dashboard, and source coverage analysis. This is Agent 3 of the "
                "3-agent Code Intelligence pipeline."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "generate_report",
                            "get_report",
                            "get_status_dashboard",
                            "get_source_coverage",
                            "get_topic_section"
                        ],
                        "description": (
                            "Action to perform: "
                            "'generate_report' = build the full monthly report from UPDATE_CARDS; "
                            "'get_report' = retrieve a previously generated monthly report; "
                            "'get_status_dashboard' = get the proposal/ballot/adopted status breakdown; "
                            "'get_source_coverage' = check which sources produced updates; "
                            "'get_topic_section' = get one topic section from the report"
                        )
                    },
                    "month": {
                        "type": "string",
                        "description": "Target month in YYYY-MM format (e.g., '2026-02'). Defaults to current month."
                    },
                    "topic": {
                        "type": "string",
                        "description": (
                            "Topic tag to retrieve (for get_topic_section action). One of: "
                            "Water Safety / Legionella, Water Efficiency, Materials & Components, "
                            "Backflow / Cross-Connection, Mixing / Temperature Control, "
                            "Drainage / Waste / Vent, Digital / Monitoring / Controls, "
                            "Filtration / Treatment, Installation / Testing / Commissioning, Other"
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
            logger.warning("Azure OpenAI SDK not available — AI synthesis disabled")
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
                logger.info("PlumbingCodeMonthlySynthesizer: OpenAI client initialized")
            else:
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
                    logger.info("PlumbingCodeMonthlySynthesizer: OpenAI client initialized (token auth)")
                except Exception:
                    logger.warning("PlumbingCodeMonthlySynthesizer: No OpenAI credentials available")
        except Exception as e:
            logger.error(f"PlumbingCodeMonthlySynthesizer: Failed to initialize OpenAI: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Action router
    # ─────────────────────────────────────────────────────────────────────────

    def perform(self, **kwargs) -> str:
        """Route to the requested action."""
        action = kwargs.get('action', 'get_report')
        month = kwargs.get('month') or datetime.now().strftime('%Y-%m')
        topic = kwargs.get('topic')

        actions = {
            "generate_report": lambda: self._generate_report(month),
            "get_report": lambda: self._get_report(month),
            "get_status_dashboard": lambda: self._get_status_dashboard(month),
            "get_source_coverage": lambda: self._get_source_coverage(month),
            "get_topic_section": lambda: self._get_topic_section(month, topic),
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
            logger.error(f"PlumbingCodeMonthlySynthesizer error in {action}: {e}")
            return json.dumps({"error": str(e), "action": action}, indent=2)

    # ─────────────────────────────────────────────────────────────────────────
    # Action: generate_report
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_report(self, month: str) -> Dict[str, Any]:
        """Build the full monthly report from UPDATE_CARDS."""
        logger.info(f"PlumbingCodeMonthlySynthesizer: Generating report for {month}")

        # Read UPDATE_CARDS
        cards_doc = self._read_update_cards(month)
        if "error" in cards_doc:
            return cards_doc

        cards = cards_doc.get("UPDATE_CARDS", {}).get("cards", [])
        if not cards:
            return {
                "error": f"UPDATE_CARDS for {month} contains no cards",
                "hint": "Run PlumbingCodeTechExtractor extract_all first"
            }

        # Read SOURCE_LOG for coverage analysis
        source_log = self._read_source_log(month)

        # Build report sections
        header = self._build_header(month, cards_doc, source_log)
        topic_sections = self._build_topic_sections(cards, month)
        status_dashboard = self._build_status_dashboard(cards)
        source_coverage = self._build_source_coverage(cards, source_log)

        # Assemble the MONTHLY_REPORT
        report = {
            "MONTHLY_REPORT": {
                "report_month": month,
                "generation_date": datetime.now().isoformat(),
                "pipeline": "Agent 3 of 3 — Monthly Synthesizer",
                "input_source": f"plumbing_intel/{month}/update_cards.json",
                "output_tag": "MONTHLY_REPORT",
                "header": header,
                "topic_sections": topic_sections,
                "status_dashboard": status_dashboard,
                "source_coverage": source_coverage
            }
        }

        # Persist
        self._persist_report(month, report)

        return report

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_report
    # ─────────────────────────────────────────────────────────────────────────

    def _get_report(self, month: str) -> Dict[str, Any]:
        """Retrieve a previously generated monthly report."""
        storage_path = f"plumbing_intel/{month}"
        try:
            content = self.storage_manager.read_file(storage_path, "monthly_report.json")
            if content:
                return json.loads(content)
            else:
                return {
                    "message": f"No MONTHLY_REPORT found for {month}",
                    "hint": "Run generate_report to build the monthly report from UPDATE_CARDS"
                }
        except Exception as e:
            return {"error": f"Failed to read MONTHLY_REPORT for {month}: {str(e)}"}

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_status_dashboard
    # ─────────────────────────────────────────────────────────────────────────

    def _get_status_dashboard(self, month: str) -> Dict[str, Any]:
        """Get the status breakdown from a persisted report, or compute from UPDATE_CARDS."""
        # Try to read from report first
        report = self._get_report(month)
        if "MONTHLY_REPORT" in report:
            return {
                "month": month,
                "status_dashboard": report["MONTHLY_REPORT"].get("status_dashboard", {})
            }

        # Fall back to computing from UPDATE_CARDS
        cards_doc = self._read_update_cards(month)
        if "error" in cards_doc:
            return cards_doc
        cards = cards_doc.get("UPDATE_CARDS", {}).get("cards", [])
        return {
            "month": month,
            "status_dashboard": self._build_status_dashboard(cards)
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_source_coverage
    # ─────────────────────────────────────────────────────────────────────────

    def _get_source_coverage(self, month: str) -> Dict[str, Any]:
        """Get source coverage analysis from a persisted report, or compute fresh."""
        report = self._get_report(month)
        if "MONTHLY_REPORT" in report:
            return {
                "month": month,
                "source_coverage": report["MONTHLY_REPORT"].get("source_coverage", {})
            }

        cards_doc = self._read_update_cards(month)
        if "error" in cards_doc:
            return cards_doc
        cards = cards_doc.get("UPDATE_CARDS", {}).get("cards", [])
        source_log = self._read_source_log(month)
        return {
            "month": month,
            "source_coverage": self._build_source_coverage(cards, source_log)
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_topic_section
    # ─────────────────────────────────────────────────────────────────────────

    def _get_topic_section(self, month: str, topic: Optional[str]) -> Dict[str, Any]:
        """Get one topic section from the monthly report."""
        if not topic:
            return {"error": "topic is required for get_topic_section action", "valid_topics": TOPIC_TAGS}

        report = self._get_report(month)
        if "MONTHLY_REPORT" in report:
            sections = report["MONTHLY_REPORT"].get("topic_sections", [])
            for section in sections:
                if section.get("topic_tag") == topic:
                    return {"month": month, "topic_section": section}
            return {"message": f"No section found for topic '{topic}' in {month} report"}

        # Fall back to computing from UPDATE_CARDS
        cards_doc = self._read_update_cards(month)
        if "error" in cards_doc:
            return cards_doc
        cards = cards_doc.get("UPDATE_CARDS", {}).get("cards", [])
        all_sections = self._build_topic_sections(cards, month)
        for section in all_sections:
            if section.get("topic_tag") == topic:
                return {"month": month, "topic_section": section}
        return {"message": f"No updates tagged '{topic}' found in {month} UPDATE_CARDS"}

    # ─────────────────────────────────────────────────────────────────────────
    # Read storage
    # ─────────────────────────────────────────────────────────────────────────

    def _read_update_cards(self, month: str) -> Dict[str, Any]:
        """Read and parse UPDATE_CARDS for the given month."""
        storage_path = f"plumbing_intel/{month}"
        try:
            content = self.storage_manager.read_file(storage_path, "update_cards.json")
            if not content:
                return {
                    "error": f"No UPDATE_CARDS found for {month}",
                    "hint": "Run PlumbingCodeTechExtractor with action='extract_all' first"
                }
            return json.loads(content)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON in UPDATE_CARDS for {month}: {str(e)}"}
        except Exception as e:
            return {"error": f"Failed to read UPDATE_CARDS for {month}: {str(e)}"}

    def _read_source_log(self, month: str) -> Dict[str, Any]:
        """Read SOURCE_LOG for coverage analysis. Returns empty structure on failure."""
        storage_path = f"plumbing_intel/{month}"
        try:
            content = self.storage_manager.read_file(storage_path, "source_log.json")
            if content:
                return json.loads(content)
        except Exception:
            pass
        return {}

    # ─────────────────────────────────────────────────────────────────────────
    # Report building blocks
    # ─────────────────────────────────────────────────────────────────────────

    def _build_header(self, month: str, cards_doc: Dict, source_log: Dict) -> Dict[str, Any]:
        """Build the report header with summary metadata."""
        uc = cards_doc.get("UPDATE_CARDS", {})
        sl = source_log.get("SOURCE_LOG", {})

        # Determine the scan date from source log
        scan_date = sl.get("scan_date", "unknown")

        # Count unique sources
        sources_scanned = sl.get("sources_scanned", 0)
        entries_found = sl.get("entries_found", 0)
        total_cards = uc.get("total_cards", 0)

        return {
            "title": f"Commercial Plumbing Code Intelligence — Monthly Report: {month}",
            "report_month": month,
            "generation_date": datetime.now().isoformat(),
            "pipeline_summary": (
                f"Source Monitor scanned {sources_scanned} authoritative sources "
                f"and found {entries_found} entries. Technical Extractor produced "
                f"{total_cards} Update Cards. This report organizes findings by topic."
            ),
            "data_sources": {
                "source_log": f"plumbing_intel/{month}/source_log.json",
                "update_cards": f"plumbing_intel/{month}/update_cards.json",
                "scan_date": scan_date,
                "sources_scanned": sources_scanned,
                "entries_found": entries_found,
                "total_cards": total_cards
            },
            "disclaimer": (
                "This report summarizes publicly available regulatory and standards "
                "activity for informational purposes only. It does not constitute legal "
                "advice or a compliance determination. Verify all details with original "
                "source documents before taking action."
            )
        }

    def _build_topic_sections(self, cards: List[Dict], month: str) -> List[Dict]:
        """Build topic sections — one per topic tag that has at least one card."""
        # Group cards by topic tag
        topic_cards: Dict[str, List[Dict]] = {}
        for card in cards:
            for tag in card.get("topic_tags", ["Other"]):
                if tag not in topic_cards:
                    topic_cards[tag] = []
                topic_cards[tag].append(card)

        # Build sections for each topic that has cards, in canonical order
        sections = []
        for tag in TOPIC_TAGS:
            if tag not in topic_cards:
                continue

            tagged_cards = topic_cards[tag]

            # Generate topic summary
            if self.openai_client:
                summary = self._generate_topic_summary_ai(tag, tagged_cards, month)
            else:
                summary = self._generate_topic_summary_simulated(tag, tagged_cards)

            # Build card summaries (concise view per card in this topic)
            card_summaries = []
            for card in tagged_cards:
                card_summaries.append({
                    "card_id": card.get("card_id"),
                    "source": card.get("source_governing_body"),
                    "title": card.get("document_title"),
                    "status": card.get("status"),
                    "what_changed": card.get("what_changed", []),
                    "jurisdictional_relevance": card.get("jurisdictional_relevance"),
                    "who_is_affected": card.get("who_is_affected", ["not specified"]),
                    "key_definitions_or_thresholds": card.get("key_definitions_or_thresholds", ["none stated"])
                })

            sections.append({
                "topic_tag": tag,
                "card_count": len(tagged_cards),
                "summary": summary,
                "cards": card_summaries
            })

        return sections

    def _build_status_dashboard(self, cards: List[Dict]) -> Dict[str, Any]:
        """Build the status dashboard — count by lifecycle stage."""
        status_counts = {}
        status_details = {}

        for card in cards:
            s = card.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1
            if s not in status_details:
                status_details[s] = []
            status_details[s].append({
                "card_id": card.get("card_id"),
                "source": card.get("source_governing_body"),
                "title": card.get("document_title")
            })

        # Lifecycle stage descriptions
        stage_labels = {
            "proposal": "Proposals — Changes proposed, not yet acted on",
            "public_comment": "Public Comment — Open for stakeholder input",
            "committee_action": "Committee Action — Committee has deliberated",
            "ballot": "Ballot — Voting underway on standard/code change",
            "adopted": "Adopted — Officially enacted or published",
            "guidance": "Guidance — Non-binding guidance or recommendation",
            "informational": "Informational — Reference material, no regulatory action"
        }

        dashboard = {
            "total_cards": len(cards),
            "status_breakdown": []
        }

        for status in ["proposal", "public_comment", "committee_action", "ballot",
                        "adopted", "guidance", "informational"]:
            count = status_counts.get(status, 0)
            if count > 0:
                dashboard["status_breakdown"].append({
                    "status": status,
                    "label": stage_labels.get(status, status),
                    "count": count,
                    "items": status_details.get(status, [])
                })

        return dashboard

    def _build_source_coverage(self, cards: List[Dict], source_log: Dict) -> Dict[str, Any]:
        """Analyze which sources were scanned and which produced updates."""
        # All known sources from the source monitor
        all_sources = [
            "IAPMO/UPC", "ICC/IPC", "ASPE", "ASHRAE", "EPA", "CDC", "NSF",
            "NYC", "CA", "TX", "MA", "Chicago"
        ]

        # Sources that produced entries in the SOURCE_LOG
        sl_entries = source_log.get("SOURCE_LOG", {}).get("entries", [])
        logged_sources = set()
        for entry in sl_entries:
            logged_sources.add(entry.get("governing_body", "Unknown"))

        # Sources that appear in UPDATE_CARDS
        carded_sources = set()
        for card in cards:
            carded_sources.add(card.get("source_governing_body", "Unknown"))

        # Determine sources with no updates
        sources_with_updates = []
        sources_without_updates = []

        for src in all_sources:
            card_count = sum(1 for c in cards if c.get("source_governing_body") == src)
            if card_count > 0:
                sources_with_updates.append({"source": src, "card_count": card_count})
            else:
                if src in logged_sources:
                    sources_without_updates.append({
                        "source": src,
                        "note": "Source was scanned but produced no entries this month"
                    })
                else:
                    sources_without_updates.append({
                        "source": src,
                        "note": "Source was not scanned or not reachable"
                    })

        return {
            "total_sources_monitored": len(all_sources),
            "sources_with_updates": len(sources_with_updates),
            "sources_without_updates": len(sources_without_updates),
            "details_with_updates": sources_with_updates,
            "details_without_updates": sources_without_updates
        }

    # ─────────────────────────────────────────────────────────────────────────
    # AI-powered topic summaries
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_topic_summary_ai(self, topic: str, cards: List[Dict], month: str) -> str:
        """Use Azure OpenAI to generate a neutral topic summary."""
        deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')

        system_prompt = """You are a technical writer for commercial plumbing code intelligence reports.

Write a neutral, factual 2-4 sentence summary of the developments listed below for the given topic.

RULES:
1. Summarize what happened — not what it means for anyone's business.
2. Do NOT rank impact, speculate, or offer opinions.
3. Name the sources (governing bodies) that published updates.
4. If something is uncertain or unconfirmed, say so.
5. Write in clear, professional English."""

        card_summaries = []
        for card in cards:
            card_summaries.append({
                "source": card.get("source_governing_body"),
                "title": card.get("document_title"),
                "status": card.get("status"),
                "what_changed": card.get("what_changed", [])
            })

        user_prompt = f"""Topic: {topic}
Month: {month}

Update Cards for this topic:
{json.dumps(card_summaries, indent=2)}

Write a 2-4 sentence neutral summary of the key developments for this topic."""

        try:
            response = self.openai_client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI topic summary failed for {topic}: {e}")
            return self._generate_topic_summary_simulated(topic, cards)

    def _generate_topic_summary_simulated(self, topic: str, cards: List[Dict]) -> str:
        """Generate a simulated topic summary without AI."""
        sources = list(set(card.get("source_governing_body", "Unknown") for card in cards))
        statuses = list(set(card.get("status", "unknown") for card in cards))

        source_str = ", ".join(sources)
        status_str = ", ".join(statuses)

        summary_templates = {
            "Water Safety / Legionella": (
                f"Water safety and Legionella-related activity this month from {source_str}. "
                f"Documents span the following lifecycle stages: {status_str}. "
                f"{len(cards)} update(s) address water management program requirements, "
                "temperature monitoring, or related building water system provisions."
            ),
            "Water Efficiency": (
                f"Water efficiency developments reported by {source_str}. "
                f"Document statuses include: {status_str}. "
                f"{len(cards)} update(s) relate to water conservation, fixture flow rates, "
                "or greywater/alternative water source provisions."
            ),
            "Materials & Components": (
                f"Materials and components updates from {source_str}. "
                f"Lifecycle stages: {status_str}. "
                f"{len(cards)} update(s) address product standards, material requirements, "
                "testing protocols, or certification criteria."
            ),
            "Backflow / Cross-Connection": (
                f"Backflow prevention and cross-connection control activity from {source_str}. "
                f"Document statuses: {status_str}. "
                f"{len(cards)} update(s) cover backflow prevention assembly requirements, "
                "testing procedures, or survey provisions."
            ),
            "Mixing / Temperature Control": (
                f"Mixing valve and temperature control activity from {source_str}. "
                f"Lifecycle stages: {status_str}. "
                f"{len(cards)} update(s) address thermostatic mixing valve requirements, "
                "hot water delivery standards, or temperature maintenance provisions."
            ),
            "Drainage / Waste / Vent": (
                f"Drainage, waste, and vent system activity from {source_str}. "
                f"Document statuses: {status_str}. "
                f"{len(cards)} update(s) relate to DWV system design, trap seal protection, "
                "or sanitary drainage provisions."
            ),
            "Digital / Monitoring / Controls": (
                f"Digital monitoring and controls activity from {source_str}. "
                f"Lifecycle stages: {status_str}. "
                f"{len(cards)} update(s) address connected device integration, sensor requirements, "
                "or digital monitoring provisions for plumbing systems."
            ),
            "Filtration / Treatment": (
                f"Filtration and treatment activity from {source_str}. "
                f"Document statuses: {status_str}. "
                f"{len(cards)} update(s) cover point-of-use/point-of-entry treatment, "
                "contaminant reduction, or filtration system requirements."
            ),
            "Installation / Testing / Commissioning": (
                f"Installation, testing, and commissioning activity from {source_str}. "
                f"Lifecycle stages: {status_str}. "
                f"{len(cards)} update(s) address inspection requirements, test procedures, "
                "commissioning protocols, or compliance verification."
            ),
            "Other": (
                f"Additional plumbing code and standards activity from {source_str}. "
                f"Document statuses: {status_str}. "
                f"{len(cards)} update(s) cover topics not classified under the primary categories."
            ),
        }

        return summary_templates.get(topic, (
            f"{len(cards)} update(s) from {source_str} for topic: {topic}. "
            f"Statuses: {status_str}."
        ))

    # ─────────────────────────────────────────────────────────────────────────
    # Persist
    # ─────────────────────────────────────────────────────────────────────────

    def _persist_report(self, month: str, report: Dict):
        """Save MONTHLY_REPORT to storage."""
        storage_path = f"plumbing_intel/{month}"
        try:
            self.storage_manager.ensure_directory_exists(storage_path)
            content = json.dumps(report, indent=2)
            self.storage_manager.write_file(storage_path, "monthly_report.json", content)
            logger.info(f"PlumbingCodeMonthlySynthesizer: MONTHLY_REPORT persisted to {storage_path}/monthly_report.json")
        except Exception as e:
            logger.error(f"PlumbingCodeMonthlySynthesizer: Failed to persist report: {e}")
