"""
Agent: Commercial Plumbing Code – Technical Extractor
Purpose: Convert SOURCE_LOG entries into standardized Update Cards with topic tags
Pipeline Position: Agent 2 of 3 (Source Monitor → Technical Extractor → Monthly Synthesizer)
Input Tag: SOURCE_LOG
Output Tag: UPDATE_CARDS

This agent reads the SOURCE_LOG produced by Agent 1 (Source Monitor) and converts
each entry into a standardized technical summary called an Update Card. It extracts
technical substance in a neutral, factual way — no speculation, no impact ranking,
no business conclusions.

Topic Tags (1–3 per item):
- Water Safety / Legionella
- Water Efficiency
- Materials & Components
- Backflow / Cross-Connection
- Mixing / Temperature Control
- Drainage / Waste / Vent
- Digital / Monitoring / Controls
- Filtration / Treatment
- Installation / Testing / Commissioning
- Other (specify)
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
# Standardized topic tags
# ─────────────────────────────────────────────────────────────────────────────
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

# Valid status values for Update Cards
CARD_STATUSES = [
    "proposal",
    "public_comment",
    "committee_action",
    "ballot",
    "adopted",
    "guidance",
    "informational"
]


class PlumbingCodeTechExtractorAgent(BasicAgent):
    """
    Commercial Plumbing Code Technical Extractor — Agent 2 of the Code Intelligence Pipeline.

    Reads SOURCE_LOG from Agent 1 and converts each entry into a standardized
    Update Card with topic tags, status, and neutral technical extraction.

    Input:  plumbing_intel/{YYYY-MM}/source_log.json  (SOURCE_LOG)
    Output: plumbing_intel/{YYYY-MM}/update_cards.json (UPDATE_CARDS)
    Downstream consumer: PlumbingCodeMonthlySynthesizerAgent (Agent 3)
    """

    def __init__(self):
        self.name = 'PlumbingCodeTechExtractor'
        self.metadata = {
            "name": self.name,
            "description": (
                "Commercial Plumbing Code Technical Extractor. Reads the SOURCE_LOG "
                "produced by the Source Monitor agent and converts each entry into a "
                "standardized Update Card with topic tags, status tracking, and neutral "
                "technical extraction. No speculation, no impact rankings, no business "
                "conclusions. This is Agent 2 of the 3-agent Code Intelligence pipeline."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "extract_all",
                            "extract_single",
                            "get_update_cards",
                            "get_topic_summary",
                            "get_topic_tags"
                        ],
                        "description": (
                            "Action to perform: "
                            "'extract_all' = process the full SOURCE_LOG for a month into Update Cards; "
                            "'extract_single' = process one SOURCE_LOG entry by index; "
                            "'get_update_cards' = retrieve previously generated Update Cards; "
                            "'get_topic_summary' = get Update Cards filtered by topic tag; "
                            "'get_topic_tags' = list all available topic tags"
                        )
                    },
                    "month": {
                        "type": "string",
                        "description": "Target month in YYYY-MM format (e.g., '2026-02'). Defaults to current month."
                    },
                    "source_index": {
                        "type": "integer",
                        "description": "Index of a specific SOURCE_LOG entry to extract (for extract_single action). Zero-based."
                    },
                    "topic_filter": {
                        "type": "string",
                        "description": (
                            "Topic tag to filter by (for get_topic_summary action). One of: "
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
            logger.warning("Azure OpenAI SDK not available — AI-powered extraction disabled")
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
                logger.info("PlumbingCodeTechExtractor: OpenAI client initialized")
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
                    logger.info("PlumbingCodeTechExtractor: OpenAI client initialized (token auth)")
                except Exception:
                    logger.warning("PlumbingCodeTechExtractor: No OpenAI credentials available")
        except Exception as e:
            logger.error(f"PlumbingCodeTechExtractor: Failed to initialize OpenAI: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Action router
    # ─────────────────────────────────────────────────────────────────────────

    def perform(self, **kwargs) -> str:
        """Route to the requested action."""
        action = kwargs.get('action', 'get_topic_tags')
        month = kwargs.get('month') or datetime.now().strftime('%Y-%m')
        source_index = kwargs.get('source_index')
        topic_filter = kwargs.get('topic_filter')

        actions = {
            "extract_all": lambda: self._extract_all(month),
            "extract_single": lambda: self._extract_single(month, source_index),
            "get_update_cards": lambda: self._get_update_cards(month),
            "get_topic_summary": lambda: self._get_topic_summary(month, topic_filter),
            "get_topic_tags": lambda: self._get_topic_tags(),
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
            logger.error(f"PlumbingCodeTechExtractor error in {action}: {e}")
            return json.dumps({"error": str(e), "action": action}, indent=2)

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_topic_tags
    # ─────────────────────────────────────────────────────────────────────────

    def _get_topic_tags(self) -> Dict[str, Any]:
        """Return the list of available topic tags and card statuses."""
        return {
            "title": "Commercial Plumbing Code — Topic Tags & Status Values",
            "topic_tags": TOPIC_TAGS,
            "card_statuses": CARD_STATUSES,
            "usage": "Each Update Card receives 1-3 topic tags and exactly 1 status value"
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Action: extract_all
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_all(self, month: str) -> Dict[str, Any]:
        """
        Read the SOURCE_LOG for the given month and generate Update Cards
        for every entry. Persists the UPDATE_CARDS to storage.
        """
        logger.info(f"PlumbingCodeTechExtractor: Extracting all entries for {month}")

        # Read SOURCE_LOG
        source_log = self._read_source_log(month)
        if "error" in source_log:
            return source_log

        entries = source_log.get("SOURCE_LOG", {}).get("entries", [])
        if not entries:
            return {
                "error": f"SOURCE_LOG for {month} contains no entries",
                "hint": "Run PlumbingCodeSourceMonitor scan_sources first"
            }

        # Process entries
        if self.openai_client:
            update_cards = self._extract_with_ai(entries, month)
        else:
            update_cards = self._extract_simulated(entries, month)

        # Build the UPDATE_CARDS document
        cards_doc = self._build_update_cards_doc(month, update_cards, len(entries))

        # Persist
        self._persist_update_cards(month, cards_doc)

        return cards_doc

    # ─────────────────────────────────────────────────────────────────────────
    # Action: extract_single
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_single(self, month: str, source_index: Optional[int]) -> Dict[str, Any]:
        """Extract a single SOURCE_LOG entry by index into an Update Card."""
        if source_index is None:
            return {"error": "source_index is required for extract_single action"}

        source_log = self._read_source_log(month)
        if "error" in source_log:
            return source_log

        entries = source_log.get("SOURCE_LOG", {}).get("entries", [])
        if source_index < 0 or source_index >= len(entries):
            return {
                "error": f"source_index {source_index} out of range (0-{len(entries)-1})",
                "total_entries": len(entries)
            }

        entry = entries[source_index]

        if self.openai_client:
            card = self._extract_single_with_ai(entry, month)
        else:
            card = self._extract_single_simulated(entry, month)

        return {"update_card": card, "source_index": source_index}

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_update_cards
    # ─────────────────────────────────────────────────────────────────────────

    def _get_update_cards(self, month: str) -> Dict[str, Any]:
        """Retrieve previously generated UPDATE_CARDS from storage."""
        storage_path = f"plumbing_intel/{month}"
        try:
            content = self.storage_manager.read_file(storage_path, "update_cards.json")
            if content:
                return json.loads(content)
            else:
                return {
                    "message": f"No UPDATE_CARDS found for {month}",
                    "hint": "Run extract_all to generate Update Cards from the SOURCE_LOG"
                }
        except Exception as e:
            return {"error": f"Failed to read UPDATE_CARDS for {month}: {str(e)}"}

    # ─────────────────────────────────────────────────────────────────────────
    # Action: get_topic_summary
    # ─────────────────────────────────────────────────────────────────────────

    def _get_topic_summary(self, month: str, topic_filter: Optional[str]) -> Dict[str, Any]:
        """Get Update Cards filtered by a specific topic tag."""
        if not topic_filter:
            return {"error": "topic_filter is required for get_topic_summary action", "valid_tags": TOPIC_TAGS}

        cards_doc = self._get_update_cards(month)
        if "error" in cards_doc or "message" in cards_doc:
            return cards_doc

        all_cards = cards_doc.get("UPDATE_CARDS", {}).get("cards", [])
        filtered = [
            card for card in all_cards
            if topic_filter in card.get("topic_tags", [])
        ]

        return {
            "topic_filter": topic_filter,
            "month": month,
            "matching_cards": len(filtered),
            "total_cards": len(all_cards),
            "cards": filtered
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Read SOURCE_LOG from storage
    # ─────────────────────────────────────────────────────────────────────────

    def _read_source_log(self, month: str) -> Dict[str, Any]:
        """Read and parse the SOURCE_LOG for the given month."""
        storage_path = f"plumbing_intel/{month}"
        try:
            content = self.storage_manager.read_file(storage_path, "source_log.json")
            if not content:
                return {
                    "error": f"No SOURCE_LOG found for {month}",
                    "hint": "Run PlumbingCodeSourceMonitor with action='scan_sources' first"
                }
            return json.loads(content)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON in SOURCE_LOG for {month}: {str(e)}"}
        except Exception as e:
            return {"error": f"Failed to read SOURCE_LOG for {month}: {str(e)}"}

    # ─────────────────────────────────────────────────────────────────────────
    # AI-powered extraction
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_with_ai(self, entries: List[Dict], month: str) -> List[Dict]:
        """Use Azure OpenAI to convert all SOURCE_LOG entries into Update Cards."""
        deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')

        system_prompt = f"""You are a technical extractor for commercial plumbing codes and standards.

You are given a SOURCE_LOG — a list of document entries from authoritative plumbing code bodies.
Your job is to convert EACH entry into a standardized Update Card.

RULES:
1. Extract technical substance in a neutral, factual way.
2. Do NOT speculate, rank impact, or draw business conclusions.
3. Label uncertainty explicitly ("not specified," "unclear").
4. Each card gets 1-3 topic tags from this list: {json.dumps(TOPIC_TAGS)}
5. Each card gets exactly 1 status from: {json.dumps(CARD_STATUSES)}
6. "what_changed" should be 3-6 bullet points in plain language.

For each entry, produce an Update Card with these fields:
- "card_id": sequential integer starting at 1
- "source_governing_body": governing body name
- "document_title": title from the source entry
- "topic_tags": array of 1-3 tags from the approved list
- "status": one of {json.dumps(CARD_STATUSES)}
- "what_changed": array of 3-6 bullet strings describing what changed or is proposed
- "jurisdictional_relevance": "model code", "standard", or "local signal" with brief explanation
- "who_is_affected": array of affected parties if stated (specifier, contractor, owner, manufacturer, etc.) — use ["not specified"] if unclear
- "key_definitions_or_thresholds": array of definitions/thresholds ONLY if explicitly stated — use ["none stated"] if not present
- "primary_source_links": array of URLs from the source entry
- "publication_date": from the source entry
- "confidence": from the source entry

Return a JSON object: {{"cards": [...]}}"""

        user_prompt = f"""Convert the following SOURCE_LOG entries for {month} into Update Cards.

SOURCE_LOG entries:
{json.dumps(entries, indent=2)}

Return a JSON object with a "cards" array containing one Update Card per entry."""

        try:
            response = self.openai_client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=8000,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)

            cards = parsed.get("cards", [])
            if isinstance(parsed, list):
                cards = parsed

            # Validate and normalize
            validated = []
            for i, card in enumerate(cards):
                validated.append(self._normalize_card(card, i + 1))

            logger.info(f"PlumbingCodeTechExtractor: AI extracted {len(validated)} Update Cards")
            return validated

        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            # Fall back to simulated extraction
            return self._extract_simulated(entries, month)

    def _extract_single_with_ai(self, entry: Dict, month: str) -> Dict:
        """Use Azure OpenAI to convert a single SOURCE_LOG entry into an Update Card."""
        deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')

        system_prompt = f"""You are a technical extractor for commercial plumbing codes and standards.

Convert this single SOURCE_LOG entry into one Update Card.

RULES:
1. Extract technical substance in a neutral, factual way.
2. Do NOT speculate, rank impact, or draw business conclusions.
3. Label uncertainty explicitly ("not specified," "unclear").
4. Assign 1-3 topic tags from: {json.dumps(TOPIC_TAGS)}
5. Assign exactly 1 status from: {json.dumps(CARD_STATUSES)}
6. "what_changed" should be 3-6 bullet points in plain language.

Return a JSON object with these fields:
- "card_id": 1
- "source_governing_body": governing body name
- "document_title": title from the source entry
- "topic_tags": array of 1-3 tags
- "status": one status value
- "what_changed": array of 3-6 bullet strings
- "jurisdictional_relevance": brief explanation
- "who_is_affected": array of affected parties or ["not specified"]
- "key_definitions_or_thresholds": array or ["none stated"]
- "primary_source_links": array of URLs
- "publication_date": from source entry
- "confidence": from source entry"""

        user_prompt = f"""Convert this SOURCE_LOG entry into an Update Card:

{json.dumps(entry, indent=2)}"""

        try:
            response = self.openai_client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content.strip()
            parsed = json.loads(raw)
            return self._normalize_card(parsed, 1)

        except Exception as e:
            logger.error(f"AI single extraction failed: {e}")
            return self._build_simulated_card_from_entry(entry, 1)

    # ─────────────────────────────────────────────────────────────────────────
    # Card normalization
    # ─────────────────────────────────────────────────────────────────────────

    def _normalize_card(self, card: Dict, card_id: int) -> Dict:
        """Validate and normalize an Update Card to the expected schema."""
        # Normalize topic tags
        raw_tags = card.get("topic_tags", ["Other"])
        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]
        normalized_tags = []
        for tag in raw_tags[:3]:
            # Fuzzy match to canonical tags
            matched = self._match_topic_tag(tag)
            if matched and matched not in normalized_tags:
                normalized_tags.append(matched)
        if not normalized_tags:
            normalized_tags = ["Other"]

        # Normalize status
        raw_status = card.get("status", "informational")
        if raw_status not in CARD_STATUSES:
            raw_status = "informational"

        # Normalize what_changed
        what_changed = card.get("what_changed", [])
        if isinstance(what_changed, str):
            what_changed = [what_changed]
        if not what_changed:
            what_changed = ["Details not extracted"]

        # Normalize who_is_affected
        who = card.get("who_is_affected", ["not specified"])
        if isinstance(who, str):
            who = [who]

        # Normalize thresholds
        thresholds = card.get("key_definitions_or_thresholds", ["none stated"])
        if isinstance(thresholds, str):
            thresholds = [thresholds]

        # Normalize links
        links = card.get("primary_source_links", [])
        if isinstance(links, str):
            links = [links]

        return {
            "card_id": card_id,
            "source_governing_body": card.get("source_governing_body", card.get("governing_body", "Unknown")),
            "document_title": card.get("document_title", "Untitled"),
            "topic_tags": normalized_tags,
            "status": raw_status,
            "what_changed": what_changed,
            "jurisdictional_relevance": card.get("jurisdictional_relevance", "not specified"),
            "who_is_affected": who,
            "key_definitions_or_thresholds": thresholds,
            "primary_source_links": links,
            "publication_date": card.get("publication_date", "unknown"),
            "confidence": card.get("confidence", "low")
        }

    def _match_topic_tag(self, raw_tag: str) -> Optional[str]:
        """Fuzzy-match a raw tag string to the canonical topic tag list."""
        raw_lower = raw_tag.lower().strip()

        # Direct match
        for tag in TOPIC_TAGS:
            if tag.lower() == raw_lower:
                return tag

        # Keyword matching
        keyword_map = {
            "Water Safety / Legionella": ["legionella", "water safety", "waterborne", "water management"],
            "Water Efficiency": ["efficiency", "water conservation", "water use", "greywater", "graywater"],
            "Materials & Components": ["material", "component", "lead-free", "lead content", "nsf 61", "nsf/ansi 61", "extraction"],
            "Backflow / Cross-Connection": ["backflow", "cross-connection", "rpz", "reduced pressure", "double check", "dcva", "asse 1013", "asse 1015"],
            "Mixing / Temperature Control": ["mixing", "temperature", "tmv", "thermostatic", "tempering", "hot water"],
            "Drainage / Waste / Vent": ["drainage", "drain", "waste", "vent", "dwv", "trap seal", "sanitary"],
            "Digital / Monitoring / Controls": ["digital", "monitoring", "iot", "smart", "bluetooth", "connected", "sensor", "controls"],
            "Filtration / Treatment": ["filtration", "filter", "treatment", "purification", "pfas", "contaminant"],
            "Installation / Testing / Commissioning": ["installation", "testing", "commissioning", "inspection", "compliance", "test frequency"],
        }

        for tag, keywords in keyword_map.items():
            for kw in keywords:
                if kw in raw_lower:
                    return tag

        return "Other"

    # ─────────────────────────────────────────────────────────────────────────
    # Build and persist UPDATE_CARDS
    # ─────────────────────────────────────────────────────────────────────────

    def _build_update_cards_doc(self, month: str, cards: List[Dict], source_entry_count: int) -> Dict[str, Any]:
        """Assemble the final UPDATE_CARDS document."""
        # Count by topic tag
        tag_counts = {}
        for card in cards:
            for tag in card.get("topic_tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Count by status
        status_counts = {}
        for card in cards:
            s = card.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        # Count by governing body
        body_counts = {}
        for card in cards:
            body = card.get("source_governing_body", "Unknown")
            body_counts[body] = body_counts.get(body, 0) + 1

        return {
            "UPDATE_CARDS": {
                "extraction_month": month,
                "extraction_date": datetime.now().isoformat(),
                "pipeline_position": "Agent 2 of 3 — Technical Extractor",
                "input_source": f"plumbing_intel/{month}/source_log.json",
                "downstream_consumer": "PlumbingCodeMonthlySynthesizer (Agent 3)",
                "output_tag": "UPDATE_CARDS",
                "source_entries_processed": source_entry_count,
                "total_cards": len(cards),
                "cards_by_topic": tag_counts,
                "cards_by_status": status_counts,
                "cards_by_source": body_counts,
                "cards": cards
            }
        }

    def _persist_update_cards(self, month: str, cards_doc: Dict):
        """Save UPDATE_CARDS to storage."""
        storage_path = f"plumbing_intel/{month}"
        try:
            self.storage_manager.ensure_directory_exists(storage_path)
            content = json.dumps(cards_doc, indent=2)
            self.storage_manager.write_file(storage_path, "update_cards.json", content)
            logger.info(f"PlumbingCodeTechExtractor: UPDATE_CARDS persisted to {storage_path}/update_cards.json")
        except Exception as e:
            logger.error(f"PlumbingCodeTechExtractor: Failed to persist UPDATE_CARDS: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Simulated extraction (no OpenAI client)
    # ─────────────────────────────────────────────────────────────────────────

    def _extract_simulated(self, entries: List[Dict], month: str) -> List[Dict]:
        """Generate simulated Update Cards when no AI client is available."""
        logger.info(f"PlumbingCodeTechExtractor: Generating simulated cards (no AI client)")
        cards = []
        for i, entry in enumerate(entries):
            card = self._build_simulated_card_from_entry(entry, i + 1)
            cards.append(card)
        return cards

    def _build_simulated_card_from_entry(self, entry: Dict, card_id: int) -> Dict:
        """Build a realistic simulated Update Card from a SOURCE_LOG entry."""
        governing_body = entry.get("governing_body", "Unknown")
        doc_title = entry.get("document_title", "Untitled")
        doc_type = entry.get("document_type", "informational")
        description = entry.get("description", "")
        link = entry.get("direct_link", "not available")
        pub_date = entry.get("publication_date", "unknown")
        confidence = entry.get("confidence", "low")

        # Infer topic tags from the document description and title
        topic_tags = self._infer_topic_tags(doc_title, description)

        # Map document type to card status
        type_to_status = {
            "proposal": "proposal",
            "ballot": "ballot",
            "adopted": "adopted",
            "guidance": "guidance",
            "minutes": "committee_action",
            "informational": "informational",
            "revision": "proposal",
            "addendum": "adopted",
            "errata": "adopted",
            "rfi_rfc": "public_comment",
            "committee_action": "committee_action",
            "public_comment": "public_comment",
            "hearing": "public_comment"
        }
        status = type_to_status.get(doc_type, "informational")

        # Generate simulated what_changed bullets based on content
        what_changed = self._generate_simulated_bullets(governing_body, doc_title, description, doc_type)

        # Infer jurisdictional relevance
        category = entry.get("source_category", "")
        if category == "model_code":
            jurisdictional = "Model code — applicable in jurisdictions that adopt UPC or IPC"
        elif category == "standard":
            jurisdictional = "National standard — typically referenced by model codes or adopted independently"
        elif category == "federal_agency":
            jurisdictional = "Federal guidance — may inform state/local adoption or influence standards development"
        elif category == "local_ahj":
            jurisdictional = f"Local signal — applicable in {governing_body} jurisdiction only"
        else:
            jurisdictional = "not specified"

        # Infer who_is_affected
        who = self._infer_affected_parties(doc_title, description)

        # Infer thresholds
        thresholds = self._infer_thresholds(doc_title, description)

        return {
            "card_id": card_id,
            "source_governing_body": governing_body,
            "document_title": doc_title,
            "topic_tags": topic_tags,
            "status": status,
            "what_changed": what_changed,
            "jurisdictional_relevance": jurisdictional,
            "who_is_affected": who,
            "key_definitions_or_thresholds": thresholds,
            "primary_source_links": [link] if link != "not available" else [],
            "publication_date": pub_date,
            "confidence": confidence
        }

    def _infer_topic_tags(self, title: str, description: str) -> List[str]:
        """Infer topic tags from document title and description."""
        combined = (title + " " + description).lower()
        tags = []

        checks = [
            ("legionella" in combined or "water safety" in combined or "water management" in combined
             or "waterborne" in combined, "Water Safety / Legionella"),
            ("efficiency" in combined or "water conservation" in combined or "greywater" in combined
             or "graywater" in combined or "water use" in combined, "Water Efficiency"),
            ("material" in combined or "component" in combined or "lead-free" in combined
             or "lead content" in combined or "nsf" in combined or "extraction" in combined, "Materials & Components"),
            ("backflow" in combined or "cross-connection" in combined or "rpz" in combined
             or "reduced pressure zone" in combined or "double check" in combined, "Backflow / Cross-Connection"),
            ("mixing" in combined or "temperature" in combined or "tmv" in combined
             or "thermostatic" in combined or "hot water" in combined
             or "tempering" in combined, "Mixing / Temperature Control"),
            ("drainage" in combined or "drain" in combined or "waste" in combined
             or "vent" in combined or "trap seal" in combined or "dwv" in combined, "Drainage / Waste / Vent"),
            ("digital" in combined or "monitoring" in combined or "iot" in combined
             or "smart" in combined or "bluetooth" in combined
             or "connected" in combined or "sensor" in combined, "Digital / Monitoring / Controls"),
            ("filtration" in combined or "filter" in combined or "treatment" in combined
             or "pfas" in combined, "Filtration / Treatment"),
            ("installation" in combined or "testing" in combined or "commissioning" in combined
             or "inspection" in combined or "test frequency" in combined, "Installation / Testing / Commissioning"),
        ]

        for condition, tag in checks:
            if condition and tag not in tags:
                tags.append(tag)
            if len(tags) >= 3:
                break

        if not tags:
            tags = ["Other"]

        return tags

    def _infer_affected_parties(self, title: str, description: str) -> List[str]:
        """Infer who is affected from the document content."""
        combined = (title + " " + description).lower()
        parties = []

        party_keywords = {
            "specifier": ["specifier", "engineer", "design professional", "plumbing engineer"],
            "contractor": ["contractor", "installer", "plumber", "installation"],
            "building owner": ["owner", "facility manager", "building", "property"],
            "manufacturer": ["manufacturer", "product", "certification", "listing"],
            "water utility": ["utility", "water system", "water supplier", "public water"],
            "code official": ["code official", "inspector", "ahj", "authority having jurisdiction"],
            "testing agency": ["testing", "test", "inspection", "certification body"],
        }

        for party, keywords in party_keywords.items():
            for kw in keywords:
                if kw in combined:
                    if party not in parties:
                        parties.append(party)
                    break

        return parties if parties else ["not specified"]

    def _infer_thresholds(self, title: str, description: str) -> List[str]:
        """Extract any thresholds or definitions mentioned."""
        combined = (title + " " + description).lower()
        thresholds = []

        # Common plumbing thresholds
        threshold_patterns = {
            "100,000 sq ft": ["100,000 sq ft", "100000"],
            "semi-annual testing": ["semi-annual", "twice per year"],
            "lead-free": ["lead-free", "weighted average lead"],
            "temperature monitoring": ["temperature monitoring", "temperature maintenance"],
        }

        for threshold, patterns in threshold_patterns.items():
            for pattern in patterns:
                if pattern in combined:
                    thresholds.append(threshold)
                    break

        return thresholds if thresholds else ["none stated"]

    def _generate_simulated_bullets(self, body: str, title: str, description: str, doc_type: str) -> List[str]:
        """Generate realistic what_changed bullets based on the source entry."""

        # Source-specific simulated content
        simulated_bullets = {
            "IAPMO/UPC": {
                "proposal": [
                    f"{body} published code change proposals for the next UPC cycle",
                    "Proposals span multiple plumbing system categories",
                    "Public comment period is open for stakeholder input",
                    "Committee review scheduled for the following quarter"
                ],
                "minutes": [
                    f"{body} technical committee convened quarterly meeting",
                    "Committee reviewed pending proposals and public comments",
                    "Discussion included requirements for assembly testability",
                    "Action items assigned for follow-up research"
                ],
            },
            "ICC/IPC": {
                "public_comment": [
                    f"{body} completed public comment hearing on plumbing code proposals",
                    "Committee actions taken on water efficiency provisions",
                    "Trap seal protection requirements reviewed and debated",
                    "Results published for stakeholder review before final action"
                ],
            },
            "ASPE": {
                "informational": [
                    "New research report published by ASPE Research Foundation",
                    "Study examines field performance data from commercial buildings",
                    "Findings address hot water delivery and temperature maintenance",
                    "Data collected from buildings over 100,000 square feet"
                ],
            },
            "ASHRAE": {
                "proposal": [
                    "Public review draft released for next edition of the standard",
                    "Proposed scope expansion to include additional building types",
                    "Strengthened monitoring and documentation requirements proposed",
                    "Public comment period open for industry feedback"
                ],
                "committee_action": [
                    "Committee met to deliberate on pending standard updates",
                    "Discussion focused on monitoring technology provisions",
                    "Committee reviewed public comments from prior review draft",
                    "Next steps and timeline established for standard revision"
                ],
            },
            "EPA": {
                "guidance": [
                    "EPA published implementation guidance for drinking water rule",
                    "Guidance covers service line inventory requirements",
                    "Lead-free product specifications relevant to plumbing included",
                    "Compliance timeline and milestones detailed for water systems"
                ],
            },
            "CDC": {
                "guidance": [
                    "CDC updated water management program toolkit",
                    "Expanded guidance on temperature monitoring protocols",
                    "Flushing protocol recommendations updated",
                    "Point-of-use device management guidance added for healthcare and hospitality"
                ],
            },
            "NSF": {
                "ballot": [
                    "Revision ballot issued for drinking water system component standard",
                    "Updates to extraction testing protocols for metallic components",
                    "Weighted-average lead content calculation methodology revised",
                    "Ballot open for committee member voting"
                ],
            },
        }

        # Default bullets for AHJ and others
        default_bullets = {
            "adopted": [
                f"{body} adopted new or amended plumbing code provisions",
                "Changes affect local jurisdiction compliance requirements",
                "Implementation date and transition period established",
                "Stakeholders should review for local compliance impact"
            ],
            "proposal": [
                f"{body} proposed changes to plumbing code provisions",
                "Proposals under review by relevant committee or board",
                "Public input period may be open or scheduled"
            ],
            "informational": [
                f"Informational publication released by {body}",
                "Document provides technical data or guidance",
                "No immediate regulatory requirement indicated"
            ],
        }

        # Try source-specific bullets first
        body_bullets = simulated_bullets.get(body, {})
        if doc_type in body_bullets:
            return body_bullets[doc_type]

        # Fall back to default by document type
        if doc_type in default_bullets:
            return default_bullets[doc_type]

        # Generic fallback
        return [
            f"Document published by {body}",
            f"Document type: {doc_type}",
            description[:120] if description else "No additional detail available"
        ]
