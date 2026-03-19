# Automated Demo Video Generation Pipeline

Generate professional narrated demo videos from RAPP demo JSON scripts — no manual screen recording, voiceover, or video editing needed.

## What It Does

```
Demo JSON ──→ Video Script ──→ [Title Cards + Browser Recording + TTS Audio] ──→ FFmpeg ──→ MP4
```

**Pipeline produces:**
- Professional title cards (intro, sections, value cards, outro)
- Synchronized TTS narration (Microsoft Neural Voices)
- Browser screen recordings following the demo script
- Burned subtitles (SRT)
- Variable speed segments (compress wait times, normal for interactions)

## Quick Start

### 1. Install Dependencies

```bash
# From project root
pip install -r scripts/video_requirements.txt
playwright install chromium

# System dependency
winget install ffmpeg          # Windows
brew install ffmpeg            # Mac
sudo apt install ffmpeg        # Linux
```

### 2. Generate a Narrative Video (No Browser Needed)

```bash
python scripts/generate_demo_video.py demos/carrier_case_triage_demo.json --narrative-only
```

This creates title cards + TTS narration — perfect for storyline videos.

### 3. Generate Full Demo Video (With Browser Recording)

```bash
# Start the application first
python function_app.py  # or: func start

# Then generate
python scripts/generate_demo_video.py demos/carrier_case_triage_demo.json \
    --headed --base-url http://localhost:7071
```

### 4. Customize

```bash
python scripts/generate_demo_video.py demos/my_demo.json \
    --narrative-only \
    --voice en-US-AriaNeural \
    --customer-name "Contoso" \
    --output-name contoso_demo \
    --output-dir video_output/contoso
```

## Output Structure

```
video_output/
├── my_demo.mp4                    # Final video
├── my_demo.srt                    # Subtitles
├── my_demo_script.json            # Generated video script
├── audio/                         # TTS audio clips per scene
│   ├── intro.mp3
│   ├── step_1.mp3
│   └── ...
├── cards/                         # Title card PNGs
│   ├── intro.png
│   ├── value_comparison.png
│   └── outro.png
└── recordings/                    # Browser recording (full mode)
    ├── recording.webm
    └── timestamps.json
```

## Two Modes

| Mode | Command | Needs App Running | Use Case |
|------|---------|-------------------|----------|
| **Narrative Only** | `--narrative-only` | ❌ | Storyline videos, pitches, overviews |
| **Full Pipeline** | `--headed` | ✅ | Live software demo recordings |

## Architecture

| Module | Purpose |
|--------|---------|
| `script_generator.py` | Demo JSON → timed video script with scenes |
| `narrator.py` | edge-tts narration + SRT subtitles |
| `title_cards.py` | HTML/CSS → PNG cards via Playwright |
| `browser_recorder.py` | Playwright browser recording with sync |
| `video_assembler.py` | FFmpeg composition engine |
| `generate_demo_video.py` | Pipeline orchestrator (CLI entry point) |
| `agents/video_generator_agent.py` | Agent system integration |

## Agent Integration

The `VideoGeneratorAgent` can be invoked from the assistant:

```
"Generate a narrative video for the carrier case triage demo"
→ VideoGenerator.generate_narrative(demo_path="demos/carrier_case_triage_demo.json")
```

**Actions:**
- `generate_from_demo` — Full pipeline with browser recording
- `generate_narrative` — Title cards + TTS only
- `preview_script` — Show video script breakdown
- `list_voices` — Available TTS voices
- `list_demos` — Available demo JSONs

## Available Voices

| Voice | Style |
|-------|-------|
| `en-US-GuyNeural` | Male, US (default) |
| `en-US-DavisNeural` | Male, US (warm) |
| `en-US-AriaNeural` | Female, US (friendly) |
| `en-US-JennyNeural` | Female, US (professional) |
| `en-GB-RyanNeural` | Male, UK |
| `en-GB-SoniaNeural` | Female, UK |

## How Demo JSON Maps to Video

```
demo.json                           → Video Scene
─────────────────────────────────    ──────────────────
overview.customer + demo_name       → INTRO title card
overview.traditional_timeline       → VALUE_CARD (before/after)
conversation_flow[].description     → SECTION_HEADER (ACT markers)
conversation_flow[].user_message    → DEMO_STEP (browser interaction)
conversation_flow[].agent_response  → Wait + capture response
overview.key_differentiator         → OUTRO card
```
