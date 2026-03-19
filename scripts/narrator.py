#!/usr/bin/env python3
"""
Demo Video Generator — TTS Narrator Module

Supports two TTS engines:
  1. Azure AI Speech (DragonHD voices) — enterprise-grade, Entra ID auth
  2. edge-tts (fallback) — free, no API key required

Set engine via constructor or NARRATOR_ENGINE env var ("azure" or "edge").
Azure Speech uses DefaultAzureCredential (az login) — no API keys needed.

Requires:
  Azure mode:  pip install azure-cognitiveservices-speech azure-identity
  Edge mode:   pip install edge-tts
"""

import asyncio
import json
import logging
import os
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class NarrationClip:
    """A generated narration audio clip with timing metadata."""
    scene_id: str
    audio_path: str
    duration_sec: float
    text: str
    voice: str


class Narrator:
    """Generates TTS narration clips using Azure Speech or edge-tts."""

    # Azure Speech DragonHD voices (requires Azure subscription)
    AZURE_VOICES = {
        "male_us_hd": "en-US-Adam:DragonHDLatestNeural",
        "female_us_hd": "en-US-Ava:DragonHDLatestNeural",
        "male_us_hd_alt": "en-US-Andrew:DragonHDLatestNeural",
        "female_us_hd_alt": "en-US-Emma:DragonHDLatestNeural",
        "male_uk_hd": "en-GB-Ethan:DragonHDLatestNeural",
        "female_uk_hd": "en-GB-Abbie:DragonHDLatestNeural",
    }

    # Edge-TTS voices (free, no API key required)
    EDGE_VOICES = {
        "male_us": "en-US-GuyNeural",
        "female_us": "en-US-AriaNeural",
        "male_us_professional": "en-US-DavisNeural",
        "female_us_professional": "en-US-JennyNeural",
        "male_uk": "en-GB-RyanNeural",
        "female_uk": "en-GB-SoniaNeural",
    }

    # Merged for backward compat
    VOICES = {**EDGE_VOICES, **AZURE_VOICES}

    def __init__(self, voice: str = None, rate: str = "+0%",
                 output_dir: str = "video_output/audio",
                 engine: str = None,
                 azure_region: str = None,
                 azure_resource_name: str = None):
        """
        Args:
            voice: Voice name. If None, picks best default for the engine.
            rate: Speech rate adjustment (e.g., "+10%", "-5%").
            output_dir: Where to save audio files.
            engine: "azure" or "edge". Defaults to NARRATOR_ENGINE env var, then "azure".
            azure_region: Azure region (e.g., "eastus"). Reads AZURE_SPEECH_REGION env var.
            azure_resource_name: Azure resource name for Entra ID auth.
                                 Reads AZURE_SPEECH_RESOURCE_NAME env var.
        """
        self.engine = (engine or os.environ.get("NARRATOR_ENGINE", "azure")).lower()
        self.rate = rate
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.azure_region = azure_region or os.environ.get("AZURE_SPEECH_REGION", "eastus")
        self.azure_resource_name = azure_resource_name or os.environ.get(
            "AZURE_SPEECH_RESOURCE_NAME", "ai-azureaihubbw560449660283"
        )

        if voice:
            self.voice = voice
        elif self.engine == "azure":
            self.voice = self.AZURE_VOICES["male_us_hd"]
        else:
            self.voice = self.EDGE_VOICES["male_us"]

        self._azure_synthesizer = None

        if self.engine == "azure":
            self._init_azure()

    def _init_azure(self):
        """Initialize Azure Speech with Entra ID (DefaultAzureCredential) via REST API."""
        try:
            import requests
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()
            self._azure_endpoint = f"https://{self.azure_resource_name}.cognitiveservices.azure.com"

            # Verify connectivity by fetching a token
            token = self._credential.get_token("https://cognitiveservices.azure.com/.default")
            logger.info(f"Azure Speech initialized: resource={self.azure_resource_name}, voice={self.voice}")
        except Exception as e:
            logger.warning(f"Azure Speech init failed ({e}), falling back to edge-tts")
            self.engine = "edge"
            if not self.voice or "Dragon" in self.voice:
                self.voice = self.EDGE_VOICES["male_us"]

    def _get_azure_token(self) -> str:
        """Get a fresh Entra ID token for Azure Speech."""
        return self._credential.get_token("https://cognitiveservices.azure.com/.default").token

    async def generate_clip(self, scene_id: str, text: str) -> NarrationClip:
        """Generate a single narration clip using the configured engine."""
        if not text or not text.strip():
            return NarrationClip(
                scene_id=scene_id, audio_path="", duration_sec=0.0,
                text="", voice=self.voice,
            )

        clean_text = self._clean_for_tts(text)

        if self.engine == "azure":
            return await self._generate_azure(scene_id, clean_text)
        else:
            return await self._generate_edge(scene_id, clean_text)

    async def _generate_azure(self, scene_id: str, text: str) -> NarrationClip:
        """Generate narration using Azure AI Speech REST API with Entra ID auth."""
        import requests

        output_path = self.output_dir / f"{scene_id}.mp3"
        ssml = self._build_ssml(text)
        token = self._get_azure_token()

        url = f"{self._azure_endpoint}/tts/cognitiveservices/v1"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3",
        }

        resp = await asyncio.to_thread(
            lambda: requests.post(url, headers=headers, data=ssml.encode("utf-8"), timeout=60)
        )

        if resp.status_code == 200:
            output_path.write_bytes(resp.content)
            duration = self._get_mp3_duration(str(output_path))
            logger.info(f"Azure TTS for {scene_id}: {duration:.1f}s ({self.voice})")
            return NarrationClip(
                scene_id=scene_id, audio_path=str(output_path),
                duration_sec=duration, text=text, voice=self.voice,
            )
        else:
            logger.error(f"Azure TTS failed for {scene_id}: HTTP {resp.status_code} - {resp.text[:200]}")
            logger.info("Falling back to edge-tts for this clip")
            return await self._generate_edge(scene_id, text)

    def _build_ssml(self, text: str) -> str:
        """Build SSML with voice and optional rate settings."""
        if self.rate and self.rate != "+0%":
            inner = f'<prosody rate="{self.rate}">{text}</prosody>'
        else:
            inner = text
        return (
            f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
            f'<voice name="{self.voice}">{inner}</voice></speak>'
        )

    async def _generate_edge(self, scene_id: str, text: str) -> NarrationClip:
        """Generate narration using edge-tts (free fallback)."""
        import edge_tts

        output_path = self.output_dir / f"{scene_id}.mp3"
        voice = self.voice if "Dragon" not in self.voice else self.EDGE_VOICES["male_us"]

        communicate = edge_tts.Communicate(text=text, voice=voice, rate=self.rate)
        await communicate.save(str(output_path))

        duration = self._get_mp3_duration(str(output_path))
        logger.info(f"Edge TTS for {scene_id}: {duration:.1f}s ({voice})")

        return NarrationClip(
            scene_id=scene_id, audio_path=str(output_path),
            duration_sec=duration, text=text, voice=voice,
        )

    async def generate_all(self, scenes: list) -> dict:
        """Generate narration for all scenes. Returns {scene_id: NarrationClip}."""
        clips = {}
        for scene in scenes:
            scene_id = scene.get("id", "")
            narration = scene.get("narration", "")
            clip = await self.generate_clip(scene_id, narration)
            clips[scene_id] = clip
        return clips

    def generate_all_sync(self, scenes: list) -> dict:
        """Synchronous wrapper for generate_all."""
        return asyncio.run(self.generate_all(scenes))

    @staticmethod
    def _clean_for_tts(text: str) -> str:
        """Clean text for natural TTS reading."""
        import re
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"#{1,6}\s*", "", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        text = re.sub(r"\|", " ", text)
        text = re.sub(r"-{3,}", "", text)
        text = re.sub(r"\n{2,}", ". ", text)
        text = re.sub(r"\n", " ", text)
        text = re.sub(r"\s{2,}", " ", text)
        # Escape XML special chars for SSML safety
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return text.strip()

    @staticmethod
    def _get_mp3_duration(path: str) -> float:
        """Estimate MP3 duration from file size and bitrate."""
        file_size = os.path.getsize(path)
        # Azure Speech outputs at ~192kbps, edge-tts at ~48kbps
        # Detect by file header or use conservative estimate
        estimated_bitrate = 192000 if file_size > 50000 else 48000
        duration = (file_size * 8) / estimated_bitrate
        return max(duration, 0.5)

    @classmethod
    async def list_voices(cls, language: str = "en", engine: str = None) -> list:
        """List available voices for a language."""
        engine = engine or os.environ.get("NARRATOR_ENGINE", "azure")
        voices = []

        if engine == "azure":
            try:
                import requests
                from azure.identity import DefaultAzureCredential

                resource = os.environ.get(
                    "AZURE_SPEECH_RESOURCE_NAME", "ai-azureaihubbw560449660283"
                )
                credential = DefaultAzureCredential()
                token = credential.get_token("https://cognitiveservices.azure.com/.default")
                url = f"https://{resource}.cognitiveservices.azure.com/tts/cognitiveservices/voices/list"
                resp = await asyncio.to_thread(
                    lambda: requests.get(url, headers={"Authorization": f"Bearer {token.token}"}, timeout=15)
                )
                if resp.status_code == 200:
                    for v in resp.json():
                        if v.get("Locale", "").startswith(language):
                            voices.append({
                                "name": v["ShortName"],
                                "gender": v.get("Gender", ""),
                                "locale": v.get("Locale", ""),
                                "style_list": v.get("StyleList", []),
                                "is_hd": "Dragon" in v.get("ShortName", ""),
                            })
            except Exception as e:
                logger.warning(f"Azure voice listing failed: {e}")

        # Always include edge-tts voices as fallback
        try:
            import edge_tts
            edge_voices = await edge_tts.list_voices()
            for v in edge_voices:
                if v["Locale"].startswith(language):
                    voices.append({
                        "name": v["ShortName"],
                        "gender": v["Gender"],
                        "locale": v["Locale"],
                        "style_list": [],
                        "is_hd": False,
                    })
        except Exception:
            pass

        return voices


class SubtitleGenerator:
    """Generate SRT subtitle files from narration clips."""

    @staticmethod
    def generate_srt(clips: dict, scene_timestamps: dict, output_path: str):
        """
        Generate an SRT subtitle file.
        
        Args:
            clips: {scene_id: NarrationClip}
            scene_timestamps: {scene_id: {"start_sec": float, "end_sec": float}}
            output_path: Where to save the .srt file
        """
        srt_lines = []
        index = 1

        for scene_id, clip in clips.items():
            if not clip.text or clip.duration_sec == 0:
                continue

            ts = scene_timestamps.get(scene_id, {})
            start = ts.get("start_sec", 0)
            end = start + clip.duration_sec

            start_tc = SubtitleGenerator._sec_to_timecode(start)
            end_tc = SubtitleGenerator._sec_to_timecode(end)

            # Split long narrations into chunks for readability
            chunks = SubtitleGenerator._split_text(clip.text, max_chars=80)
            for chunk in chunks:
                chunk_duration = clip.duration_sec / len(chunks)
                chunk_start_tc = SubtitleGenerator._sec_to_timecode(start)
                chunk_end_tc = SubtitleGenerator._sec_to_timecode(start + chunk_duration)

                srt_lines.append(str(index))
                srt_lines.append(f"{chunk_start_tc} --> {chunk_end_tc}")
                srt_lines.append(chunk)
                srt_lines.append("")

                start += chunk_duration
                index += 1

        Path(output_path).write_text("\n".join(srt_lines), encoding="utf-8")

    @staticmethod
    def _sec_to_timecode(seconds: float) -> str:
        """Convert seconds to SRT timecode format HH:MM:SS,mmm."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _split_text(text: str, max_chars: int = 80) -> list:
        """Split text into subtitle-friendly chunks."""
        words = text.split()
        chunks = []
        current = []
        current_len = 0
        for word in words:
            if current_len + len(word) + 1 > max_chars and current:
                chunks.append(" ".join(current))
                current = [word]
                current_len = len(word)
            else:
                current.append(word)
                current_len += len(word) + 1
        if current:
            chunks.append(" ".join(current))
        return chunks if chunks else [text]


if __name__ == "__main__":
    import sys

    async def main():
        engine = "azure" if "--azure" in sys.argv else ("edge" if "--edge" in sys.argv else None)

        if "--voices" in sys.argv:
            lang = sys.argv[sys.argv.index("--voices") + 1] if len(sys.argv) > sys.argv.index("--voices") + 1 else "en"
            voices = await Narrator.list_voices(lang, engine=engine)
            hd_voices = [v for v in voices if v.get("is_hd")]
            standard_voices = [v for v in voices if not v.get("is_hd")]
            if hd_voices:
                print(f"\n  === HD Voices ({len(hd_voices)}) ===")
                for v in hd_voices[:20]:
                    print(f"  {v['name']:45s} {v['gender']:8s} {v['locale']}")
            if standard_voices:
                print(f"\n  === Standard Voices ({len(standard_voices)}) ===")
                for v in standard_voices[:20]:
                    print(f"  {v['name']:45s} {v['gender']:8s} {v['locale']}")
            return

        narrator = Narrator(engine=engine)
        print(f"Engine: {narrator.engine} | Voice: {narrator.voice}")
        test_scenes = [
            {"id": "test_intro", "narration": "Welcome to the demo. Let's see how AI transforms enterprise workflows."},
            {"id": "test_step1", "narration": "First, we'll analyze the customer's current environment."},
        ]
        clips = await narrator.generate_all(test_scenes)
        for scene_id, clip in clips.items():
            print(f"  {scene_id}: {clip.duration_sec:.1f}s -> {clip.audio_path}")

    asyncio.run(main())
