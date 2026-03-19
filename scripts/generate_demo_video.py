#!/usr/bin/env python3
"""
Demo Video Generator — Pipeline Orchestrator

Main entry point that orchestrates the full video generation pipeline:
    Demo JSON → Video Script → [TTS + Title Cards + Browser Recording] → Assembly → MP4

Usage:
    # Full pipeline (with browser recording)
    python generate_demo_video.py demos/carrier_case_triage_demo.json --headed

    # Narrative-only mode (title cards + TTS, no browser needed)
    python generate_demo_video.py demos/carrier_case_triage_demo.json --narrative-only

    # Custom settings
    python generate_demo_video.py demos/my_demo.json \\
        --voice en-US-AriaNeural \\
        --output-dir output/my_video \\
        --output-name my_demo_video \\
        --base-url http://localhost:7071

Pipeline Phases:
    Phase 1: Generate video script from demo JSON
    Phase 2: Generate TTS narration for each scene  
    Phase 3: Render title card images
    Phase 4: Record browser session (skip in narrative-only mode)
    Phase 5: Assemble final video with FFmpeg
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from script_generator import ScriptGenerator, VideoScript
from narrator import Narrator, SubtitleGenerator
from title_cards import TitleCardRenderer
from browser_recorder import BrowserRecorder
from video_assembler import VideoAssembler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("VideoGenerator")


class DemoVideoGenerator:
    """
    Orchestrates the complete demo video generation pipeline.
    
    Supports two modes:
    1. Full mode: Browser recording + title cards + narration → polished demo video
    2. Narrative mode: Title cards + narration only → storyline video (no app needed)
    """

    def __init__(self, output_dir: str = "video_output",
                 voice: str = None, voice_rate: str = "+0%",
                 viewport_width: int = 1920, viewport_height: int = 1080,
                 base_url: str = "http://localhost:7071",
                 headed: bool = True, auth_state: str = None,
                 tts_engine: str = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voice = voice
        self.voice_rate = voice_rate
        self.width = viewport_width
        self.height = viewport_height
        self.base_url = base_url
        self.headed = headed
        self.auth_state = auth_state
        self.tts_engine = tts_engine

    async def generate(self, demo_path: str, output_name: str = None,
                       narrative_only: bool = False, customer_name: str = None) -> dict:
        """
        Run the complete pipeline.
        
        Returns dict with output paths and metadata.
        """
        start_time = time.time()
        demo_path = Path(demo_path)

        if not demo_path.exists():
            raise FileNotFoundError(f"Demo JSON not found: {demo_path}")

        if not output_name:
            output_name = demo_path.stem

        logger.info(f"{'='*60}")
        logger.info(f"DEMO VIDEO GENERATOR")
        logger.info(f"{'='*60}")
        logger.info(f"Source: {demo_path}")
        logger.info(f"Mode:   {'Narrative Only' if narrative_only else 'Full (Browser + Cards)'}")
        logger.info(f"Voice:  {self.voice}")
        logger.info(f"Output: {self.output_dir / output_name}.mp4")
        logger.info(f"{'='*60}")

        # ─── PHASE 1: Generate Video Script ───────────────────────
        logger.info("\n📋 PHASE 1: Generating video script...")
        script = ScriptGenerator.from_demo_json(
            str(demo_path),
            base_url=self.base_url,
            voice=self.voice,
            voice_rate=self.voice_rate,
            customer_name=customer_name or "",
        )

        script_dict = script.to_dict()
        script_path = self.output_dir / f"{output_name}_script.json"
        script.to_json(str(script_path))

        logger.info(f"  ✓ {len(script.scenes)} scenes, "
                    f"~{script.total_estimated_duration():.0f}s estimated")
        for s in script.scenes:
            logger.info(f"    [{s.scene_type.value:16s}] {s.id}: {s.title[:50]}")

        # ─── PHASE 2: Generate TTS Narration ──────────────────────
        logger.info("\n🎤 PHASE 2: Generating TTS narration...")
        narrator = Narrator(
            voice=self.voice,
            rate=self.voice_rate,
            output_dir=str(self.output_dir / "audio"),
            engine=self.tts_engine,
        )
        narration_clips = await narrator.generate_all(script_dict["scenes"])

        total_narration = sum(
            c.duration_sec for c in narration_clips.values() if c.duration_sec > 0
        )
        logger.info(f"  ✓ {len(narration_clips)} clips, {total_narration:.1f}s total narration")

        # Convert to serializable format for assembler
        clips_dict = {}
        for scene_id, clip in narration_clips.items():
            clips_dict[scene_id] = {
                "audio_path": clip.audio_path,
                "duration_sec": clip.duration_sec,
                "text": clip.text,
            }

        # ─── PHASE 3: Render Title Cards ──────────────────────────
        logger.info("\n🎨 PHASE 3: Rendering title cards...")
        renderer = TitleCardRenderer(
            output_dir=str(self.output_dir / "cards"),
            width=self.width, height=self.height,
        )
        title_cards = await renderer.render_all_cards(script_dict["scenes"])
        logger.info(f"  ✓ {len(title_cards)} title cards rendered")

        # ─── PHASE 4: Browser Recording ──────────────────────────
        recording_path = ""
        timestamps = []

        if not narrative_only:
            logger.info("\n🌐 PHASE 4: Recording browser session...")
            recorder = BrowserRecorder(
                base_url=self.base_url,
                output_dir=str(self.output_dir / "recordings"),
                viewport_width=self.width,
                viewport_height=self.height,
                headed=self.headed,
                auth_state=self.auth_state,
            )
            recording = await recorder.record(script_dict, clips_dict)
            recording_path = recording.video_path
            timestamps = recording.timestamps
            logger.info(f"  ✓ Recording: {recording.total_duration_sec:.1f}s")
        else:
            logger.info("\n⏭️  PHASE 4: Skipped (narrative-only mode)")
            # Generate placeholder timestamps for title cards
            current_time = 0.0
            for scene in script_dict["scenes"]:
                scene_id = scene["id"]
                clip = clips_dict.get(scene_id, {})
                dur = max(scene.get("duration_hint_sec", 5.0),
                         clip.get("duration_sec", 0) + 1.0)
                timestamps.append({
                    "scene_id": scene_id,
                    "start_sec": current_time,
                    "end_sec": current_time + dur,
                })
                current_time += dur

        # ─── PHASE 5: Generate Subtitles ─────────────────────────
        logger.info("\n📝 PHASE 5: Generating subtitles...")
        srt_path = str(self.output_dir / f"{output_name}.srt")
        ts_dict = {ts["scene_id"]: ts for ts in timestamps}
        SubtitleGenerator.generate_srt(narration_clips, ts_dict, srt_path)
        logger.info(f"  ✓ Subtitles: {srt_path}")

        # ─── PHASE 6: Assemble Final Video ───────────────────────
        logger.info("\n🎬 PHASE 6: Assembling final video...")
        assembler = VideoAssembler(
            output_dir=str(self.output_dir),
            width=self.width, height=self.height,
        )

        result = assembler.assemble(
            video_script=script_dict,
            recording_path=recording_path,
            narration_clips=clips_dict,
            title_card_images=title_cards,
            timestamps=timestamps,
            srt_path=srt_path,
            output_name=output_name,
        )

        elapsed = time.time() - start_time
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ VIDEO COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"  Output:   {result.output_path}")
        logger.info(f"  Duration: {result.duration_sec:.1f}s")
        logger.info(f"  Size:     {result.file_size_mb:.1f} MB")
        logger.info(f"  Scenes:   {result.scene_count}")
        logger.info(f"  Pipeline: {elapsed:.1f}s")
        logger.info(f"{'='*60}")

        return {
            "video_path": result.output_path,
            "srt_path": result.srt_path,
            "script_path": str(script_path),
            "duration_sec": result.duration_sec,
            "file_size_mb": result.file_size_mb,
            "scene_count": result.scene_count,
            "pipeline_time_sec": round(elapsed, 1),
            "mode": "narrative_only" if narrative_only else "full",
        }

    def generate_sync(self, demo_path: str, **kwargs) -> dict:
        """Synchronous wrapper for generate()."""
        return asyncio.run(self.generate(demo_path, **kwargs))


def main():
    parser = argparse.ArgumentParser(
        description="Generate professional demo videos from RAPP demo JSON scripts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Narrative-only video (no browser needed)
  python generate_demo_video.py demos/carrier_case_triage_demo.json --narrative-only

  # Full pipeline with browser recording
  python generate_demo_video.py demos/my_demo.json --headed --base-url http://localhost:7071

  # Custom voice and output
  python generate_demo_video.py demos/my_demo.json \\
      --voice en-US-AriaNeural --output-name my_video --narrative-only
        """,
    )

    parser.add_argument("demo_json", help="Path to the RAPP demo JSON file")
    parser.add_argument("--output-dir", default="video_output",
                       help="Output directory (default: video_output)")
    parser.add_argument("--output-name", default=None,
                       help="Output filename without extension (default: demo JSON filename)")
    parser.add_argument("--narrative-only", action="store_true",
                       help="Generate title cards + narration only (no browser recording)")
    parser.add_argument("--voice", default=None,
                       help="TTS voice (default: best for engine)")
    parser.add_argument("--voice-rate", default="+0%",
                       help="TTS speech rate (default: +0%%)")
    parser.add_argument("--base-url", default="http://localhost:7071",
                       help="Application base URL for browser recording")
    parser.add_argument("--headed", action="store_true",
                       help="Run browser in headed mode (visible)")
    parser.add_argument("--auth-state", default=None,
                       help="Path to Playwright auth state JSON")
    parser.add_argument("--customer-name", default=None,
                       help="Customer name for branding")
    parser.add_argument("--tts-engine", default="azure", choices=["azure", "edge"],
                       help="TTS engine: azure (DragonHD) or edge (free)")
    parser.add_argument("--width", type=int, default=1920, help="Video width (default: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Video height (default: 1080)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    generator = DemoVideoGenerator(
        output_dir=args.output_dir,
        voice=args.voice,
        voice_rate=args.voice_rate,
        viewport_width=args.width,
        viewport_height=args.height,
        base_url=args.base_url,
        headed=args.headed,
        auth_state=args.auth_state,
        tts_engine=args.tts_engine,
    )

    result = generator.generate_sync(
        args.demo_json,
        output_name=args.output_name,
        narrative_only=args.narrative_only,
        customer_name=args.customer_name,
    )

    # Print result as JSON for programmatic use
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
