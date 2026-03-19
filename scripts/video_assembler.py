#!/usr/bin/env python3
"""
Demo Video Generator — FFmpeg Video Assembler

Merges title card images, browser recordings, TTS audio, and subtitles
into a final polished MP4 video.

Key sync strategy (from demo-recorder best practices):
- Use wall-clock timestamps from browser recording
- Pad audio with apad=whole_dur to prevent progressive drift
- Never use -shortest flag in concatenation
- Variable speed segments via setpts filter

Requires: FFmpeg installed on system PATH
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AssemblyResult:
    """Result of the video assembly process."""
    output_path: str
    srt_path: str
    duration_sec: float
    scene_count: int
    file_size_mb: float


class VideoAssembler:
    """
    FFmpeg-based video composition engine.
    
    Assembles title card clips, browser recordings, and narration audio
    into a final MP4 with subtitles.
    """

    def __init__(self, output_dir: str = "video_output",
                 width: int = 1920, height: int = 1080, fps: int = 30):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.width = width
        self.height = height
        self.fps = fps
        self._verify_ffmpeg()

    def _verify_ffmpeg(self):
        """Check that FFmpeg is available."""
        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "FFmpeg not found. Install it:\n"
                "  Windows: winget install ffmpeg\n"
                "  Mac:     brew install ffmpeg\n"
                "  Linux:   sudo apt install ffmpeg"
            )

    def assemble(self, video_script: dict, recording_path: str,
                 narration_clips: dict, title_card_images: dict,
                 timestamps: list, srt_path: str = None,
                 output_name: str = "demo_video") -> AssemblyResult:
        """
        Assemble the final video from all components.
        
        Strategy:
        1. Create short video clips from title card PNGs
        2. Split browser recording at scene boundaries
        3. Overlay narration audio on each clip
        4. Concatenate all clips in order
        5. Burn subtitles if provided
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="video_assembly_"))
        clips_dir = temp_dir / "clips"
        clips_dir.mkdir()

        try:
            clip_paths = []
            scenes = video_script.get("scenes", [])

            for i, scene in enumerate(scenes):
                scene_id = scene.get("id", f"scene_{i}")
                scene_type = scene.get("scene_type", "")
                clip = narration_clips.get(scene_id, {})
                narration_path = ""
                narration_dur = 0.0

                if isinstance(clip, dict):
                    narration_path = clip.get("audio_path", "")
                    narration_dur = clip.get("duration_sec", 0)
                elif hasattr(clip, "audio_path"):
                    narration_path = clip.audio_path
                    narration_dur = clip.duration_sec

                if scene_type in ("intro", "section_header", "value_card", "outro"):
                    # Create video clip from title card image
                    card_path = title_card_images.get(scene_id, "")
                    if card_path and os.path.exists(card_path):
                        duration = max(scene.get("duration_hint_sec", 5.0), narration_dur + 1.0)
                        clip_path = self._image_to_clip(
                            card_path, clips_dir / f"{i:03d}_{scene_id}.mp4",
                            duration, narration_path,
                        )
                        if clip_path:
                            clip_paths.append(clip_path)

                elif scene_type == "demo_step" and recording_path and os.path.exists(recording_path):
                    # Extract segment from browser recording
                    ts = self._find_timestamp(timestamps, scene_id)
                    if ts:
                        clip_path = self._extract_segment(
                            recording_path, clips_dir / f"{i:03d}_{scene_id}.mp4",
                            ts["start_sec"], ts["end_sec"],
                            narration_path, narration_dur,
                            scene.get("speed_segments", []),
                        )
                        if clip_path:
                            clip_paths.append(clip_path)

            if not clip_paths:
                raise RuntimeError("No clips were generated. Check input files.")

            # Concatenate all clips
            concat_path = temp_dir / "concat.mp4"
            self._concatenate_clips(clip_paths, str(concat_path))

            # Burn subtitles if available
            final_path = self.output_dir / f"{output_name}.mp4"
            if srt_path and os.path.exists(srt_path):
                self._burn_subtitles(str(concat_path), srt_path, str(final_path))
            else:
                shutil.copy2(str(concat_path), str(final_path))

            duration = self._get_duration(str(final_path))
            file_size = os.path.getsize(str(final_path)) / (1024 * 1024)

            return AssemblyResult(
                output_path=str(final_path),
                srt_path=srt_path or "",
                duration_sec=duration,
                scene_count=len(clip_paths),
                file_size_mb=round(file_size, 1),
            )

        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _image_to_clip(self, image_path: str, output_path: str,
                        duration: float, audio_path: str = "") -> Optional[str]:
        """Convert a static image to a video clip, optionally with audio."""
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", str(duration),
            "-vf", f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                   f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black,"
                   f"fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest",
            "-r", str(self.fps),
            str(output_path),
        ]

        if audio_path and os.path.exists(audio_path):
            # Replace silent audio with narration, padded to match video duration
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", image_path,
                "-i", audio_path,
                "-t", str(duration),
                "-filter_complex",
                f"[0:v]scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black,"
                f"fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5[v];"
                f"[1:a]adelay=500|500,apad=whole_dur={duration}[a]",
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-r", str(self.fps),
                str(output_path),
            ]

        return self._run_ffmpeg(cmd, str(output_path))

    def _extract_segment(self, video_path: str, output_path: str,
                          start: float, end: float,
                          audio_path: str = "", audio_dur: float = 0,
                          speed_segments: list = None) -> Optional[str]:
        """Extract a segment from the browser recording with optional audio overlay."""
        duration = end - start
        if duration <= 0:
            return None

        # Base extraction
        if audio_path and os.path.exists(audio_path):
            # Overlay narration audio, padded to match segment duration
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start), "-t", str(duration), "-i", video_path,
                "-i", audio_path,
                "-filter_complex",
                f"[0:v]scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black[v];"
                f"[1:a]adelay=500|500,apad=whole_dur={duration}[a]",
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-r", str(self.fps),
                str(output_path),
            ]
        else:
            # Video only with silent audio track
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start), "-t", str(duration), "-i", video_path,
                "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t", str(duration),
                "-filter_complex",
                f"[0:v]scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black[v]",
                "-map", "[v]", "-map", "1:a",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-r", str(self.fps),
                str(output_path),
            ]

        return self._run_ffmpeg(cmd, str(output_path))

    def _concatenate_clips(self, clip_paths: list, output_path: str):
        """Concatenate video clips using FFmpeg concat demuxer."""
        # Write concat file list
        concat_list = Path(output_path).parent / "concat_list.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            for clip in clip_paths:
                # FFmpeg requires forward slashes in concat lists
                safe_path = str(clip).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-movflags", "+faststart",
            str(output_path),
        ]
        self._run_ffmpeg(cmd, output_path)

    def _burn_subtitles(self, video_path: str, srt_path: str, output_path: str):
        """Burn SRT subtitles into the video."""
        # Escape path for FFmpeg subtitles filter (needs forward slashes + escaping)
        safe_srt = srt_path.replace("\\", "/").replace(":", "\\:")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles='{safe_srt}':force_style='FontSize=22,FontName=Segoe UI,"
                   f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,"
                   f"MarginV=40'",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(output_path),
        ]
        self._run_ffmpeg(cmd, output_path)

    def _get_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json",
            video_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception:
            return 0.0

    @staticmethod
    def _find_timestamp(timestamps: list, scene_id: str) -> Optional[dict]:
        """Find timestamp entry for a scene."""
        for ts in timestamps:
            if ts.get("scene_id") == scene_id:
                return ts
        return None

    @staticmethod
    def _run_ffmpeg(cmd: list, output_path: str) -> Optional[str]:
        """Run an FFmpeg command and return output path on success."""
        logger.debug(f"FFmpeg: {' '.join(cmd[:6])}...")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
            )
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr[-500:]}")
                return None
            if os.path.exists(output_path):
                return output_path
            return None
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg command timed out")
            return None
        except Exception as e:
            logger.error(f"FFmpeg execution error: {e}")
            return None


class QuickAssembler:
    """
    Simplified assembler for title-card-only videos (no browser recording).
    
    Useful for quickly generating narrative videos from demo scripts
    without needing a running application instance.
    """

    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30):
        self.assembler = VideoAssembler(width=width, height=height, fps=fps)

    def assemble_cards_only(self, title_card_images: dict,
                            narration_clips: dict, scenes: list,
                            output_name: str = "demo_narrative") -> AssemblyResult:
        """
        Create a video from title cards + narration only.
        No browser recording needed.
        """
        return self.assembler.assemble(
            video_script={"scenes": scenes},
            recording_path="",
            narration_clips=narration_clips,
            title_card_images=title_card_images,
            timestamps=[],
            output_name=output_name,
        )
