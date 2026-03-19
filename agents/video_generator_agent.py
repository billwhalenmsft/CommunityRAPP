#!/usr/bin/env python3
"""
VideoGeneratorAgent — Agent wrapper for the demo video pipeline.

Integrates the video generation pipeline into the RAPP agent system.
Can be invoked from the assistant to generate demo videos on demand.

Actions:
    generate_from_demo  — Run full pipeline on a demo JSON
    generate_narrative   — Generate narrative-only video (no browser)
    preview_script       — Show the video script without generating video
    list_voices          — List available TTS voices
"""

import json
import logging
import os
import sys
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    # Fallback if running standalone
    class BasicAgent:
        def __init__(self, name, metadata):
            self.name = name
            self.metadata = metadata

logger = logging.getLogger(__name__)


class VideoGeneratorAgent(BasicAgent):
    """
    Agent for generating professional demo videos from RAPP demo JSON scripts.
    
    Supports full pipeline (browser recording + title cards + TTS) and
    narrative-only mode (title cards + TTS, no running application needed).
    """

    def __init__(self):
        self.name = "VideoGenerator"
        self.metadata = {
            "name": self.name,
            "description": (
                "Generate professional demo videos from RAPP demo JSON scripts. "
                "Creates narrated videos with title cards, browser recordings, "
                "TTS voiceover, and subtitles. Supports full pipeline mode "
                "(with live browser recording) and narrative-only mode "
                "(title cards + narration, no app required)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "generate_from_demo",
                            "generate_narrative",
                            "preview_script",
                            "list_voices",
                            "list_demos",
                        ],
                        "description": (
                            "Action to perform: "
                            "generate_from_demo (full pipeline with browser), "
                            "generate_narrative (title cards + TTS only), "
                            "preview_script (show video script), "
                            "list_voices (available TTS voices), "
                            "list_demos (available demo JSONs)"
                        ),
                    },
                    "demo_path": {
                        "type": "string",
                        "description": "Path to demo JSON file (e.g., 'demos/carrier_case_triage_demo.json')",
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name for branding in the video",
                    },
                    "voice": {
                        "type": "string",
                        "description": "TTS voice name (default: en-US-GuyNeural). Use list_voices to see options.",
                    },
                    "output_name": {
                        "type": "string",
                        "description": "Output filename without extension",
                    },
                    "base_url": {
                        "type": "string",
                        "description": "Application URL for browser recording (default: http://localhost:7071)",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "")
        demo_path = kwargs.get("demo_path", "")
        customer_name = kwargs.get("customer_name", "")
        voice = kwargs.get("voice", "en-US-GuyNeural")
        output_name = kwargs.get("output_name", "")
        base_url = kwargs.get("base_url", "http://localhost:7071")

        try:
            if action == "list_demos":
                return self._list_demos()

            elif action == "list_voices":
                return self._list_voices()

            elif action == "preview_script":
                if not demo_path:
                    return "Error: demo_path is required for preview_script"
                return self._preview_script(demo_path, customer_name, voice)

            elif action == "generate_narrative":
                if not demo_path:
                    return "Error: demo_path is required for generate_narrative"
                return self._generate(demo_path, narrative_only=True,
                                     customer_name=customer_name, voice=voice,
                                     output_name=output_name, base_url=base_url)

            elif action == "generate_from_demo":
                if not demo_path:
                    return "Error: demo_path is required for generate_from_demo"
                return self._generate(demo_path, narrative_only=False,
                                     customer_name=customer_name, voice=voice,
                                     output_name=output_name, base_url=base_url)

            else:
                return (
                    f"Unknown action: {action}. "
                    f"Available: generate_from_demo, generate_narrative, "
                    f"preview_script, list_voices, list_demos"
                )

        except Exception as e:
            logger.error(f"VideoGenerator error: {e}", exc_info=True)
            return f"Error: {str(e)}"

    def _list_demos(self) -> str:
        """List available demo JSON files."""
        demos_dir = PROJECT_ROOT / "demos"
        demos = []
        if demos_dir.exists():
            for f in sorted(demos_dir.glob("*.json")):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    name = data.get("demo_name", data.get("agent", {}).get("name", f.stem))
                    steps = len(data.get("conversation_flow", data.get("demoConversation", [])))
                    demos.append(f"  • {f.name}: {name} ({steps} steps)")
                except Exception:
                    demos.append(f"  • {f.name}: (could not parse)")

        if not demos:
            return "No demo JSON files found in demos/ directory."

        return f"**Available Demo Scripts ({len(demos)}):**\n" + "\n".join(demos)

    def _list_voices(self) -> str:
        """List popular TTS voices."""
        voices = [
            ("en-US-GuyNeural", "Male, US (Professional)"),
            ("en-US-DavisNeural", "Male, US (Warm)"),
            ("en-US-AriaNeural", "Female, US (Friendly)"),
            ("en-US-JennyNeural", "Female, US (Professional)"),
            ("en-GB-RyanNeural", "Male, UK"),
            ("en-GB-SoniaNeural", "Female, UK"),
            ("en-AU-WilliamNeural", "Male, Australian"),
            ("en-IN-PrabhatNeural", "Male, Indian English"),
        ]
        lines = ["**Available TTS Voices:**"]
        for name, desc in voices:
            lines.append(f"  • `{name}` — {desc}")
        lines.append("\nUse `edge-tts --list-voices` for the complete list.")
        return "\n".join(lines)

    def _preview_script(self, demo_path: str, customer_name: str, voice: str) -> str:
        """Preview the video script without generating video."""
        from script_generator import ScriptGenerator

        full_path = self._resolve_demo_path(demo_path)
        script = ScriptGenerator.from_demo_json(
            str(full_path), customer_name=customer_name, voice=voice,
        )
        script_dict = script.to_dict()

        lines = [
            f"**Video Script Preview: {script_dict['title']}**",
            f"Customer: {script_dict['customer_name'] or 'N/A'}",
            f"Scenes: {script_dict['scene_count']}",
            f"Estimated Duration: {script_dict['total_estimated_duration_sec']:.0f}s",
            f"Voice: {script_dict['voice']}",
            "",
            "**Scene Breakdown:**",
        ]
        for s in script_dict["scenes"]:
            icon = {"intro": "🎬", "section_header": "📌", "demo_step": "🖥️",
                    "value_card": "💡", "transition": "➡️", "outro": "🎤"}.get(s["scene_type"], "▶️")
            lines.append(
                f"  {icon} [{s['scene_type']:16s}] {s['id']}: {s['title'][:60]} "
                f"(~{s['duration_hint_sec']:.0f}s)"
            )
            if s.get("narration"):
                lines.append(f"    🔊 \"{s['narration'][:100]}...\"" if len(s.get("narration", "")) > 100
                           else f"    🔊 \"{s['narration']}\"")

        return "\n".join(lines)

    def _generate(self, demo_path: str, narrative_only: bool,
                  customer_name: str, voice: str,
                  output_name: str, base_url: str) -> str:
        """Run the video generation pipeline."""
        from generate_demo_video import DemoVideoGenerator

        full_path = self._resolve_demo_path(demo_path)
        output_dir = str(PROJECT_ROOT / "video_output")

        generator = DemoVideoGenerator(
            output_dir=output_dir,
            voice=voice,
            base_url=base_url,
            headed=True,
        )

        result = generator.generate_sync(
            str(full_path),
            output_name=output_name or full_path.stem,
            narrative_only=narrative_only,
            customer_name=customer_name,
        )

        return (
            f"**✅ Video Generated Successfully**\n\n"
            f"**Output:** `{result['video_path']}`\n"
            f"**Duration:** {result['duration_sec']:.1f}s\n"
            f"**Size:** {result['file_size_mb']:.1f} MB\n"
            f"**Scenes:** {result['scene_count']}\n"
            f"**Pipeline Time:** {result['pipeline_time_sec']:.1f}s\n"
            f"**Mode:** {result['mode']}\n\n"
            f"Subtitles: `{result['srt_path']}`\n"
            f"Script: `{result['script_path']}`"
        )

    def _resolve_demo_path(self, demo_path: str) -> Path:
        """Resolve a demo path (absolute or relative to project root)."""
        p = Path(demo_path)
        if p.is_absolute() and p.exists():
            return p
        # Try relative to project root
        full = PROJECT_ROOT / demo_path
        if full.exists():
            return full
        # Try in demos/ directory
        demo_dir = PROJECT_ROOT / "demos" / demo_path
        if demo_dir.exists():
            return demo_dir
        # Try adding .json
        if not demo_path.endswith(".json"):
            for candidate in [PROJECT_ROOT / f"{demo_path}.json",
                            PROJECT_ROOT / "demos" / f"{demo_path}.json"]:
                if candidate.exists():
                    return candidate
        raise FileNotFoundError(f"Demo not found: {demo_path}")
