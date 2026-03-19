#!/usr/bin/env python3
"""
Demo Video Generator — Script Generator Module

Converts RAPP demo JSON conversation_flow into a timed video script
with typed scenes (intro, demo_step, transition, value_card, outro).

Usage:
    from generate_demo_video import ScriptGenerator
    script = ScriptGenerator.from_demo_json("demos/my_demo.json")
    print(script.to_dict())
"""

import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class SceneType(str, Enum):
    INTRO = "intro"
    SECTION_HEADER = "section_header"
    DEMO_STEP = "demo_step"
    VALUE_CARD = "value_card"
    TRANSITION = "transition"
    OUTRO = "outro"


@dataclass
class SpeedSegment:
    """Variable speed within a scene (proportion 0.0-1.0 of scene duration)."""
    start_pct: float
    end_pct: float
    speed: float = 1.0


@dataclass
class Scene:
    id: str
    scene_type: SceneType
    title: str
    narration: str = ""
    duration_hint_sec: float = 5.0
    # For demo_step scenes
    user_message: str = ""
    wait_for_response_sec: float = 10.0
    agent_reference: str = ""
    # For title cards
    subtitle: str = ""
    challenge: str = ""
    metrics: dict = field(default_factory=dict)
    # Speed control
    speed_segments: list = field(default_factory=list)
    # Styling
    background_color: str = "#0033A0"
    accent_color: str = "#00BCF2"

    def to_dict(self):
        d = asdict(self)
        d["scene_type"] = self.scene_type.value
        return d


@dataclass
class VideoScript:
    title: str
    description: str = ""
    customer_name: str = ""
    base_url: str = "http://localhost:7071"
    viewport_width: int = 1920
    viewport_height: int = 1080
    voice: str = "en-US-GuyNeural"
    voice_rate: str = "+0%"
    scenes: list = field(default_factory=list)

    def total_estimated_duration(self) -> float:
        return sum(s.duration_hint_sec for s in self.scenes)

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "customer_name": self.customer_name,
            "base_url": self.base_url,
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
            "voice": self.voice,
            "voice_rate": self.voice_rate,
            "total_estimated_duration_sec": self.total_estimated_duration(),
            "scene_count": len(self.scenes),
            "scenes": [s.to_dict() for s in self.scenes],
        }

    def to_json(self, path: str):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


class ScriptGenerator:
    """Converts a RAPP demo JSON into a VideoScript."""

    # Patterns that indicate ACT/section markers in step descriptions
    ACT_PATTERN = re.compile(r"ACT\s+\d+[:\s]|^Day\s+\d+|^Phase\s+\d+", re.IGNORECASE)

    @classmethod
    def from_demo_json(cls, demo_path: str, **overrides) -> VideoScript:
        """Load a demo JSON and generate a video script."""
        with open(demo_path, "r", encoding="utf-8") as f:
            demo = json.load(f)
        return cls.generate(demo, **overrides)

    @classmethod
    def generate(cls, demo: dict, **overrides) -> VideoScript:
        """Generate a VideoScript from a parsed demo dict."""
        # Extract metadata
        agent_info = demo.get("agent", {})
        overview = demo.get("overview", {})
        demo_name = demo.get("demo_name", agent_info.get("name", "Demo"))
        description = demo.get("description", agent_info.get("description", ""))
        customer = overview.get("customer", overrides.get("customer_name", ""))
        challenge = overview.get("challenge", "")
        differentiator = overview.get("key_differentiator", "")
        traditional = overview.get("traditional_timeline", "")
        agent_timeline = overview.get("agent_swarm_timeline", "")

        script = VideoScript(
            title=demo_name,
            description=description,
            customer_name=customer,
            base_url=overrides.get("base_url", "http://localhost:7071"),
            voice=overrides.get("voice", "en-US-GuyNeural"),
            voice_rate=overrides.get("voice_rate", "+0%"),
        )

        # --- INTRO SCENE ---
        intro_narration = f"Welcome. Today we're looking at {demo_name}."
        if customer:
            intro_narration = f"Welcome. Today we're demonstrating {demo_name} for {customer}."
        if challenge:
            intro_narration += f" The challenge: {challenge}"

        script.scenes.append(Scene(
            id="intro",
            scene_type=SceneType.INTRO,
            title=demo_name,
            subtitle=customer or description,
            challenge=challenge,
            narration=intro_narration,
            duration_hint_sec=7.0,
        ))

        # --- VALUE CARD (if timeline comparison exists) ---
        if traditional and agent_timeline:
            value_narration = (
                f"Traditional approaches take {traditional}. "
                f"With our AI agent approach, we deliver in {agent_timeline}."
            )
            script.scenes.append(Scene(
                id="value_comparison",
                scene_type=SceneType.VALUE_CARD,
                title="Time to Value",
                narration=value_narration,
                duration_hint_sec=6.0,
                metrics={
                    "traditional": traditional,
                    "agent_approach": agent_timeline,
                },
            ))

        # --- DEMO STEPS ---
        conversation_flow = demo.get("conversation_flow", [])
        # Also check demoConversation format (alternate JSON schema)
        if not conversation_flow:
            conversation_flow = cls._convert_demo_conversation(
                demo.get("demoConversation", [])
            )

        last_act = None
        for step in conversation_flow:
            step_num = step.get("step_number", 0)
            desc = step.get("description", "")
            user_msg = step.get("user_message", step.get("content", ""))
            agent_resp = step.get("agent_response", "")
            agent_ref = step.get("agent_reference", "")

            # Check for ACT/section header
            act_match = cls.ACT_PATTERN.search(desc)
            if act_match and desc != last_act:
                last_act = desc
                section_title = desc.split(":", 1)[-1].strip() if ":" in desc else desc
                script.scenes.append(Scene(
                    id=f"section_{step_num}",
                    scene_type=SceneType.SECTION_HEADER,
                    title=section_title,
                    narration=section_title,
                    duration_hint_sec=3.0,
                ))

            # Estimate response wait time based on response length
            resp_text = agent_resp if isinstance(agent_resp, str) else json.dumps(agent_resp)
            resp_len = len(resp_text)
            wait_time = min(max(resp_len / 200, 5.0), 90.0)  # 5-90 sec range

            # Build narration from user message context
            step_narration = cls._build_step_narration(step_num, user_msg, desc, agent_ref)

            # Speed segments: real speed for interaction, fast for waiting
            speed_segs = []
            if wait_time > 15:
                speed_segs = [
                    SpeedSegment(0.0, 0.15, 1.0),   # Send message at normal speed
                    SpeedSegment(0.15, 0.7, 8.0),    # Speed up waiting
                    SpeedSegment(0.7, 1.0, 1.0),     # Normal for reading response
                ]

            scene_duration = wait_time + 5.0  # wait + narration buffer

            script.scenes.append(Scene(
                id=f"step_{step_num}",
                scene_type=SceneType.DEMO_STEP,
                title=desc or f"Step {step_num}",
                narration=step_narration,
                user_message=user_msg,
                wait_for_response_sec=wait_time,
                agent_reference=agent_ref,
                duration_hint_sec=scene_duration,
                speed_segments=[asdict(s) for s in speed_segs],
            ))

        # --- OUTRO SCENE ---
        outro_narration = f"That concludes our {demo_name} demonstration."
        if differentiator:
            outro_narration += f" Key takeaway: {differentiator}"
        outro_narration += " Thank you for watching."

        script.scenes.append(Scene(
            id="outro",
            scene_type=SceneType.OUTRO,
            title="Thank You",
            subtitle=differentiator or f"{demo_name} — Powered by AI Agent Swarms",
            narration=outro_narration,
            duration_hint_sec=7.0,
        ))

        return script

    @classmethod
    def _build_step_narration(cls, step_num: int, user_msg: str, desc: str, agent_ref: str) -> str:
        """Create natural narration for a demo step."""
        parts = []
        if desc and not cls.ACT_PATTERN.search(desc):
            parts.append(desc.rstrip(".") + ".")
        if user_msg:
            # Shorten very long user messages for narration
            msg = user_msg if len(user_msg) < 120 else user_msg[:117] + "..."
            parts.append(f'We ask: "{msg}"')
        if agent_ref:
            agent_name = agent_ref.split(".")[0] if "." in agent_ref else agent_ref
            parts.append(f"The {agent_name} agent processes this request.")
        return " ".join(parts) if parts else f"Step {step_num}."

    @classmethod
    def _convert_demo_conversation(cls, demo_conv: list) -> list:
        """Convert demoConversation format to conversation_flow format."""
        steps = []
        step_num = 0
        for i, entry in enumerate(demo_conv):
            if entry.get("role") == "user":
                step_num += 1
                agent_resp = ""
                if i + 1 < len(demo_conv) and demo_conv[i + 1].get("role") == "agent":
                    agent_resp = demo_conv[i + 1].get("content", "")
                steps.append({
                    "step_number": step_num,
                    "description": f"Step {step_num}",
                    "user_message": entry.get("content", ""),
                    "agent_response": agent_resp,
                })
        return steps


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script_generator.py <demo.json> [output.json]")
        sys.exit(1)
    demo_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    script = ScriptGenerator.from_demo_json(demo_path)
    if output_path:
        script.to_json(output_path)
        print(f"Video script saved to {output_path}")
    else:
        print(json.dumps(script.to_dict(), indent=2))
