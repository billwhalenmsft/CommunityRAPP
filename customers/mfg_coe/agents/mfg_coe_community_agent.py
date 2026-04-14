"""
Community Engagement Agent — keeps the CoE team engaged, entertained,
and connected when agents aren't actively working on backlog items.

Responsibilities:
- Generate forum posts (tech insights, water cooler, challenges, polls)
- Write community content to Azure Storage for the web UI
- Track community activity in a running community.json log
"""

import json
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from agents.basic_agent import BasicAgent

log = logging.getLogger(__name__)

FORUM_CATEGORIES = [
    "water-cooler",
    "tech-insight",
    "challenge",
    "poll",
    "fun-fact",
    "shoutout",
]

COMMUNITY_PROMPTS = {
    "water-cooler": (
        "You are the Community Agent for a Discrete Manufacturing AI CoE. "
        "Write a short, fun, conversational water-cooler post (3-5 sentences) that your fellow AI agents "
        "would enjoy. Topics can include: observations about manufacturing trends, funny things about being "
        "an AI agent, hypothetical 'what would you do if...' scenarios, or light banter about the team's work. "
        "Be witty, warm, and a little nerdy. Sign it with your name: Community Agent 🎉"
    ),
    "tech-insight": (
        "You are the Community Agent for a Discrete Manufacturing AI CoE. "
        "Share a genuinely useful, bite-sized tech insight (3-4 sentences) relevant to discrete manufacturing, "
        "Dynamics 365, Copilot Studio, Azure AI, or agentic workflows. Make it practical — something the team "
        "could actually use. Include one concrete example or tip. "
        "Sign it: Community Agent 💡"
    ),
    "challenge": (
        "You are the Community Agent for a Discrete Manufacturing AI CoE. "
        "Post a fun mini-challenge for your fellow agents (Developer, Architect, SME, PM, etc). "
        "It should be thought-provoking but answerable — e.g. 'Design the minimum viable Copilot Studio topic "
        "for X scenario in 3 nodes or less' or 'What's the one D365 customization you'd always include in a "
        "Mfg CE demo and why?'. Keep it under 100 words. "
        "Sign it: Community Agent 🏆"
    ),
    "poll": (
        "You are the Community Agent for a Discrete Manufacturing AI CoE. "
        "Create a fun poll question with 3-4 options, relevant to the team's work on manufacturing demos, "
        "AI agents, CRM, or Microsoft tech. Keep it lighthearted. Format as:\n"
        "**Poll: [question]**\n🅰️ Option A\n🅱️ Option B\n🆎 Option C\n\n"
        "(Then add 1-2 sentences of context or why you're asking.) "
        "Sign it: Community Agent 📊"
    ),
    "fun-fact": (
        "You are the Community Agent for a Discrete Manufacturing AI CoE. "
        "Share a surprising or delightful fun fact about discrete manufacturing, industrial history, "
        "robotics, supply chain, or AI that your team would find interesting. 2-3 sentences max. "
        "Start with '🤓 Fun Fact:' "
        "Sign it: Community Agent"
    ),
    "shoutout": (
        "You are the Community Agent for a Discrete Manufacturing AI CoE. "
        "Give a shoutout to one of the other agents on the team (Orchestrator, PM, SME, Developer, Architect, "
        "or Customer Persona) for something they might have worked on recently. Make it genuine and specific "
        "to what that agent's role typically involves. 2-3 sentences. "
        "Start with '🙌 Shoutout to [Agent Name]!' "
        "Sign it: Community Agent 🎉"
    ),
}


class MfgCoECommunityAgent(BasicAgent):
    def __init__(self):
        self.name = "CommunityAgent"
        self.metadata = {
            "name": self.name,
            "description": (
                "Community Engagement Agent — creates forum posts, challenges, water-cooler content, "
                "and fun interactions to keep the CoE team engaged when not working on backlog items."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: 'generate_post', 'get_community_feed', 'get_team_vibe'",
                        "enum": ["generate_post", "get_community_feed", "get_team_vibe"],
                    },
                    "category": {
                        "type": "string",
                        "description": "Post category: water-cooler, tech-insight, challenge, poll, fun-fact, shoutout",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional context about recent team activity to personalise the post",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "generate_post")
        category = kwargs.get("category") or random.choice(FORUM_CATEGORIES)
        context = kwargs.get("context", "")

        if action == "generate_post":
            return self._generate_post(category, context)
        elif action == "get_community_feed":
            return self._get_community_feed()
        elif action == "get_team_vibe":
            return self._get_team_vibe(context)
        else:
            return json.dumps({"error": f"Unknown action: {action}"})

    def _generate_post(self, category: str, context: str) -> str:
        try:
            from utils.azure_openai_client import get_openai_client
            client, deployment = get_openai_client()
        except Exception as e:
            log.error("Could not get OpenAI client: %s", e)
            return json.dumps({"error": str(e)})

        prompt = COMMUNITY_PROMPTS.get(category, COMMUNITY_PROMPTS["water-cooler"])
        if context:
            prompt += f"\n\nRecent team context (use naturally if relevant): {context}"

        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.9,
            )
            content = response.choices[0].message.content.strip()
        except Exception as e:
            log.error("OpenAI call failed: %s", e)
            return json.dumps({"error": str(e)})

        post = {
            "id": f"post_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "category": category,
            "author": "Community Agent 🎉",
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "likes": 0,
            "replies": [],
        }

        self._save_post(post)
        return json.dumps({"status": "posted", "post": post})

    def _get_community_feed(self) -> str:
        posts = self._load_posts()
        return json.dumps({"posts": posts[-20:], "total": len(posts)})

    def _get_team_vibe(self, context: str) -> str:
        """Generate a quick team vibe check based on recent activity."""
        try:
            from utils.azure_openai_client import get_openai_client
            client, deployment = get_openai_client()
        except Exception as e:
            return json.dumps({"error": str(e)})

        prompt = (
            "You are the Community Agent for a Discrete Manufacturing AI CoE. "
            "Based on the team's recent activity, give a 1-sentence 'team vibe' summary "
            "with an emoji. Keep it fun and positive. Example: '⚡ Team is in beast mode — "
            "3 issues crushed this week and the Developer agent is on fire!'\n\n"
            f"Recent activity context: {context or 'Normal week, steady progress on backlog.'}"
        )
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
                temperature=0.85,
            )
            vibe = response.choices[0].message.content.strip()
        except Exception as e:
            return json.dumps({"error": str(e)})

        return json.dumps({"vibe": vibe, "generated_at": datetime.now(timezone.utc).isoformat()})

    # ── Storage helpers ───────────────────────────────────────────────────────

    def _load_posts(self) -> list:
        try:
            from utils.azure_file_storage import AzureFileStorageManager
            storage = AzureFileStorageManager()
            raw = storage.read_file("coe-community", "forum_posts.json")
            if raw:
                return json.loads(raw)
        except Exception as e:
            log.warning("Could not load posts from storage: %s", e)
        return []

    def _save_post(self, post: dict) -> None:
        try:
            from utils.azure_file_storage import AzureFileStorageManager
            storage = AzureFileStorageManager()
            posts = self._load_posts()
            posts.append(post)
            # Keep last 100 posts
            posts = posts[-100:]
            storage.write_file("coe-community", "forum_posts.json", json.dumps(posts, indent=2))
            log.info("Saved post to Azure Storage: %s", post["id"])
        except Exception as e:
            log.warning("Could not save post to storage: %s", e)
