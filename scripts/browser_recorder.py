#!/usr/bin/env python3
"""
Demo Video Generator — Browser Recorder Module

Records browser sessions following demo script steps using Playwright.
Inserts timed pauses matching narration duration per scene for perfect
audio/video sync. Captures wall-clock timestamps for assembly.

Based on the existing capture_contract_demo.py pattern but generalized
for any demo JSON script.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SceneTimestamp:
    """Wall-clock timestamp for a recorded scene."""
    scene_id: str
    start_sec: float
    end_sec: float
    narration_pause_start_sec: float = 0.0
    narration_pause_duration_sec: float = 0.0


@dataclass
class RecordingResult:
    """Result of a browser recording session."""
    video_path: str
    timestamps: list  # list of SceneTimestamp dicts
    total_duration_sec: float
    viewport: dict = field(default_factory=lambda: {"width": 1920, "height": 1080})


class BrowserRecorder:
    """
    Records browser interactions following a video script.
    
    The recorder drives the browser through demo steps, inserting pauses
    where narration will be overlaid. Wall-clock timestamps are captured
    for each scene to enable precise audio alignment in post-production.
    """

    def __init__(self, base_url: str = "http://localhost:7071",
                 output_dir: str = "video_output/recordings",
                 viewport_width: int = 1920, viewport_height: int = 1080,
                 headed: bool = True, auth_state: str = None):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.viewport = {"width": viewport_width, "height": viewport_height}
        self.headed = headed
        self.auth_state = auth_state

    async def record(self, video_script: dict, narration_clips: dict = None) -> RecordingResult:
        """
        Record a complete demo session.
        
        Args:
            video_script: Parsed VideoScript dict with scenes
            narration_clips: {scene_id: NarrationClip} for pause timing
            
        Returns:
            RecordingResult with video path and timestamps
        """
        from playwright.async_api import async_playwright

        narration_clips = narration_clips or {}
        timestamps = []
        video_dir = self.output_dir / "raw"
        video_dir.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=not self.headed)

            context_opts = {
                "viewport": self.viewport,
                "record_video_dir": str(video_dir),
                "record_video_size": self.viewport,
            }

            if self.auth_state and Path(self.auth_state).exists():
                context_opts["storage_state"] = self.auth_state

            context = await browser.new_context(**context_opts)
            page = await context.new_page()

            # Navigate to the application
            target_url = video_script.get("base_url", self.base_url)
            chat_url = self._resolve_chat_url(target_url)
            logger.info(f"Navigating to: {chat_url}")

            try:
                await page.goto(chat_url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                logger.warning(f"Initial navigation timeout (may be expected): {e}")

            await page.wait_for_timeout(3000)  # Let the page settle

            # Record start time (wall clock)
            recording_start = time.monotonic()

            # Process each scene
            for scene in video_script.get("scenes", []):
                scene_type = scene.get("scene_type", "")
                scene_id = scene.get("id", "")

                if scene_type == "demo_step":
                    ts = await self._record_demo_step(
                        page, scene, recording_start, narration_clips.get(scene_id)
                    )
                    timestamps.append(ts)
                elif scene_type in ("intro", "section_header", "value_card", "outro"):
                    # These are title cards — pause the recording for their duration
                    # The title card images will be spliced in during assembly
                    narration_dur = 0.0
                    clip = narration_clips.get(scene_id)
                    if clip:
                        narration_dur = clip.get("duration_sec", 0) if isinstance(clip, dict) else clip.duration_sec

                    pause_duration = max(scene.get("duration_hint_sec", 5.0), narration_dur)
                    start = time.monotonic() - recording_start

                    # Brief visual pause in browser (shows current state)
                    await page.wait_for_timeout(int(pause_duration * 1000))

                    timestamps.append(SceneTimestamp(
                        scene_id=scene_id,
                        start_sec=start,
                        end_sec=time.monotonic() - recording_start,
                        narration_pause_start_sec=start,
                        narration_pause_duration_sec=pause_duration,
                    ))

            total_duration = time.monotonic() - recording_start

            # Close context to finalize video
            video_path_obj = page.video
            await context.close()
            await browser.close()

            # Get the final video path
            if video_path_obj:
                raw_video_path = await video_path_obj.path()
                final_video_path = str(self.output_dir / "recording.webm")
                # Move to a known location
                Path(raw_video_path).rename(final_video_path)
            else:
                final_video_path = ""
                logger.warning("No video was recorded (headless mode or recording failed)")

        result = RecordingResult(
            video_path=final_video_path,
            timestamps=[asdict(ts) if isinstance(ts, SceneTimestamp) else ts for ts in timestamps],
            total_duration_sec=total_duration,
            viewport=self.viewport,
        )

        # Save timestamps for assembler
        ts_path = self.output_dir / "timestamps.json"
        ts_path.write_text(json.dumps(result.timestamps, indent=2), encoding="utf-8")
        logger.info(f"Recording complete: {total_duration:.1f}s, {len(timestamps)} scenes")

        return result

    async def _record_demo_step(self, page, scene: dict, recording_start: float,
                                 narration_clip=None) -> SceneTimestamp:
        """Record a single demo step with browser interaction."""
        scene_id = scene.get("id", "")
        user_message = scene.get("user_message", "")
        wait_time = scene.get("wait_for_response_sec", 10.0)

        # Get narration duration for pause timing
        narration_dur = 0.0
        if narration_clip:
            narration_dur = (narration_clip.get("duration_sec", 0)
                           if isinstance(narration_clip, dict) else narration_clip.duration_sec)

        start = time.monotonic() - recording_start
        logger.info(f"Recording step: {scene_id} at {start:.1f}s")

        if user_message:
            # Find and interact with chat input
            input_sent = await self._send_message(page, user_message)
            if not input_sent:
                logger.warning(f"Could not send message for {scene_id}")

            # Wait for response to appear
            await page.wait_for_timeout(int(wait_time * 1000))

        # Insert narration pause — this is where TTS audio will be overlaid
        narration_pause_start = time.monotonic() - recording_start
        if narration_dur > 0:
            await page.wait_for_timeout(int(narration_dur * 1000))

        end = time.monotonic() - recording_start

        return SceneTimestamp(
            scene_id=scene_id,
            start_sec=start,
            end_sec=end,
            narration_pause_start_sec=narration_pause_start,
            narration_pause_duration_sec=narration_dur,
        )

    async def _send_message(self, page, message: str) -> bool:
        """Send a message in the chat interface. Tries multiple selector strategies."""
        selectors = [
            # M365 Copilot chat input
            'textarea[data-tid="chat-input"]',
            'div[role="textbox"][contenteditable="true"]',
            # Generic chat inputs
            'textarea[placeholder*="message"]',
            'textarea[placeholder*="Message"]',
            'input[placeholder*="message"]',
            '#chat-input',
            'textarea.chat-input',
            # Custom index.html input
            '#userInput',
            'textarea',
        ]

        for selector in selectors:
            try:
                el = page.locator(selector).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    await page.wait_for_timeout(300)
                    await el.fill(message)
                    await page.wait_for_timeout(300)

                    # Try pressing Enter or clicking send button
                    await page.keyboard.press("Enter")
                    logger.info(f"Sent message via: {selector}")
                    return True
            except Exception:
                continue

        logger.warning(f"Could not find chat input for message: {message[:50]}...")
        return False

    def _resolve_chat_url(self, base_url: str) -> str:
        """Resolve the target URL for recording."""
        if "m365.cloud.microsoft" in base_url or "copilot" in base_url.lower():
            return base_url
        # For local dev, point to the chat UI
        if "localhost" in base_url or "127.0.0.1" in base_url:
            # Use the index.html chat interface
            return base_url.rstrip("/")
        return base_url


if __name__ == "__main__":
    import sys

    async def test():
        recorder = BrowserRecorder(
            base_url="http://localhost:7071",
            output_dir="video_output/test_recording",
            headed=True,
        )
        test_script = {
            "base_url": "http://localhost:7071",
            "scenes": [
                {
                    "id": "step_1",
                    "scene_type": "demo_step",
                    "title": "Test Step",
                    "user_message": "Hello, what can you do?",
                    "wait_for_response_sec": 10.0,
                },
            ],
        }
        result = await recorder.record(test_script)
        print(f"Recording saved: {result.video_path}")
        print(f"Duration: {result.total_duration_sec:.1f}s")

    asyncio.run(test())
