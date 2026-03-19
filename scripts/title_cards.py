#!/usr/bin/env python3
"""
Demo Video Generator — Title Card Renderer

Creates professional title cards, section headers, value cards, and outros
using HTML/CSS templates rendered to images via Playwright.

Each card type is a self-contained HTML template with embedded CSS.
Playwright renders them to PNG at exact viewport dimensions, then
FFmpeg converts to short video clips with fade transitions.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TitleCardTemplates:
    """HTML/CSS templates for professional video title cards."""

    INTRO = """<!DOCTYPE html>
<html><head><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    width: {width}px; height: {height}px;
    background: linear-gradient(135deg, #0a0a23 0%, #1a1a4e 40%, #0033A0 100%);
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    color: white; overflow: hidden;
}
.accent-bar {
    position: absolute; top: 0; left: 0; right: 0; height: 6px;
    background: linear-gradient(90deg, #00BCF2, #7FBA00, #F25022, #FFB900);
}
.logo-area {
    position: absolute; top: 40px; left: 60px;
    font-size: 16px; font-weight: 300; letter-spacing: 2px; opacity: 0.7;
    text-transform: uppercase;
}
.main-title {
    font-size: 64px; font-weight: 700; text-align: center;
    max-width: 80%; line-height: 1.2; margin-bottom: 20px;
    text-shadow: 0 2px 40px rgba(0,188,242,0.3);
}
.subtitle {
    font-size: 28px; font-weight: 300; opacity: 0.85; text-align: center;
    max-width: 70%; line-height: 1.4;
}
.challenge-box {
    margin-top: 40px; padding: 20px 40px; border-left: 4px solid #00BCF2;
    background: rgba(0,188,242,0.1); border-radius: 0 8px 8px 0;
    max-width: 70%; font-size: 22px; font-style: italic; opacity: 0.9;
}
.bottom-bar {
    position: absolute; bottom: 40px; display: flex; gap: 40px;
    font-size: 14px; opacity: 0.5; letter-spacing: 1px;
}
</style></head><body>
<div class="accent-bar"></div>
<div class="logo-area">{branding}</div>
<div class="main-title">{title}</div>
<div class="subtitle">{subtitle}</div>
{challenge_html}
<div class="bottom-bar">
    <span>AI-POWERED DEMONSTRATION</span>
    <span>•</span>
    <span>CONFIDENTIAL</span>
</div>
</body></html>"""

    SECTION_HEADER = """<!DOCTYPE html>
<html><head><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    width: {width}px; height: {height}px;
    background: linear-gradient(135deg, #0a0a23 0%, #1b1b3a 100%);
    font-family: 'Segoe UI', system-ui, sans-serif;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    color: white; overflow: hidden;
}
.section-number {
    font-size: 120px; font-weight: 800; opacity: 0.08;
    position: absolute; right: 80px; top: 50%; transform: translateY(-50%);
}
.content { text-align: left; padding-left: 120px; max-width: 70%; }
.eyebrow {
    font-size: 14px; text-transform: uppercase; letter-spacing: 4px;
    color: #00BCF2; margin-bottom: 16px;
}
.title { font-size: 52px; font-weight: 600; line-height: 1.2; }
.divider {
    width: 80px; height: 4px; background: #00BCF2;
    margin-top: 24px; border-radius: 2px;
}
</style></head><body>
<div class="section-number">{section_num}</div>
<div class="content">
    <div class="eyebrow">{eyebrow}</div>
    <div class="title">{title}</div>
    <div class="divider"></div>
</div>
</body></html>"""

    VALUE_CARD = """<!DOCTYPE html>
<html><head><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    width: {width}px; height: {height}px;
    background: linear-gradient(135deg, #0a1628 0%, #0d2137 100%);
    font-family: 'Segoe UI', system-ui, sans-serif;
    display: flex; justify-content: center; align-items: center;
    color: white; overflow: hidden;
}
.comparison {
    display: flex; gap: 80px; align-items: center;
}
.before, .after {
    text-align: center; padding: 40px;
}
.before .metric {
    font-size: 72px; font-weight: 700; color: #ff4444;
    text-decoration: line-through; opacity: 0.6;
}
.after .metric {
    font-size: 72px; font-weight: 700; color: #7FBA00;
}
.label {
    font-size: 20px; margin-top: 12px; opacity: 0.7; text-transform: uppercase;
    letter-spacing: 2px;
}
.arrow {
    font-size: 64px; color: #00BCF2; animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
.title {
    position: absolute; top: 60px; left: 0; right: 0;
    text-align: center; font-size: 32px; font-weight: 300; opacity: 0.8;
}
.insight {
    position: absolute; bottom: 60px; left: 0; right: 0;
    text-align: center; font-size: 22px; font-style: italic; opacity: 0.6;
    max-width: 60%; margin: 0 auto;
}
</style></head><body>
<div class="title">{title}</div>
<div class="comparison">
    <div class="before">
        <div class="metric">{before_value}</div>
        <div class="label">{before_label}</div>
    </div>
    <div class="arrow">→</div>
    <div class="after">
        <div class="metric">{after_value}</div>
        <div class="label">{after_label}</div>
    </div>
</div>
<div class="insight">{insight}</div>
</body></html>"""

    OUTRO = """<!DOCTYPE html>
<html><head><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    width: {width}px; height: {height}px;
    background: linear-gradient(135deg, #0033A0 0%, #001a52 100%);
    font-family: 'Segoe UI', system-ui, sans-serif;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    color: white; overflow: hidden;
}
.accent-bar {
    position: absolute; bottom: 0; left: 0; right: 0; height: 6px;
    background: linear-gradient(90deg, #00BCF2, #7FBA00, #F25022, #FFB900);
}
.thank-you {
    font-size: 56px; font-weight: 700; margin-bottom: 24px;
}
.message {
    font-size: 26px; font-weight: 300; opacity: 0.85; text-align: center;
    max-width: 60%; line-height: 1.5; margin-bottom: 48px;
}
.cta {
    padding: 16px 48px; border: 2px solid #00BCF2; border-radius: 30px;
    font-size: 20px; letter-spacing: 2px; text-transform: uppercase;
    color: #00BCF2;
}
.contact {
    position: absolute; bottom: 40px;
    font-size: 16px; opacity: 0.5; letter-spacing: 1px;
}
</style></head><body>
<div class="thank-you">{title}</div>
<div class="message">{subtitle}</div>
<div class="cta">{cta_text}</div>
<div class="contact">{contact}</div>
<div class="accent-bar"></div>
</body></html>"""

    LOWER_THIRD = """<!DOCTYPE html>
<html><head><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    width: {width}px; height: 120px;
    background: transparent; font-family: 'Segoe UI', system-ui, sans-serif;
}
.lower-third {
    position: absolute; bottom: 0; left: 40px;
    background: linear-gradient(90deg, rgba(0,51,160,0.95), rgba(0,51,160,0.7));
    padding: 12px 32px; border-radius: 8px 8px 0 0;
    display: flex; align-items: center; gap: 16px;
    backdrop-filter: blur(10px);
}
.step-badge {
    background: #00BCF2; color: white; width: 36px; height: 36px;
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 16px;
}
.step-text {
    color: white; font-size: 18px; font-weight: 500;
}
.agent-ref {
    color: #00BCF2; font-size: 14px; font-weight: 300;
    margin-left: 12px;
}
</style></head><body>
<div class="lower-third">
    <div class="step-badge">{step_num}</div>
    <div class="step-text">{title}</div>
    <div class="agent-ref">{agent_ref}</div>
</div>
</body></html>"""


class TitleCardRenderer:
    """Renders HTML title card templates to PNG images using Playwright."""

    def __init__(self, output_dir: str = "video_output/cards",
                 width: int = 1920, height: int = 1080):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.width = width
        self.height = height
        self.templates = TitleCardTemplates()

    async def render_scene_card(self, scene: dict) -> str:
        """Render a title card for a scene. Returns path to PNG."""
        scene_type = scene.get("scene_type", "")
        scene_id = scene.get("id", "unknown")

        if scene_type == "intro":
            return await self._render_intro(scene)
        elif scene_type == "section_header":
            return await self._render_section_header(scene)
        elif scene_type == "value_card":
            return await self._render_value_card(scene)
        elif scene_type == "outro":
            return await self._render_outro(scene)
        else:
            return ""

    async def render_lower_third(self, step_num: int, title: str,
                                  agent_ref: str = "") -> str:
        """Render a lower-third overlay for a demo step."""
        html = self._fill_template(TitleCardTemplates.LOWER_THIRD,
            width=self.width, step_num=step_num,
            title=title, agent_ref=agent_ref,
        )
        output_path = self.output_dir / f"lower_third_{step_num}.png"
        await self._render_html_to_png(html, str(output_path),
                                        width=self.width, height=120)
        return str(output_path)

    async def render_all_cards(self, scenes: list) -> dict:
        """Render title cards for all applicable scenes."""
        cards = {}
        for scene in scenes:
            scene_type = scene.get("scene_type", "")
            if scene_type in ("intro", "section_header", "value_card", "outro"):
                path = await self.render_scene_card(scene)
                if path:
                    cards[scene["id"]] = path
        return cards

    async def _render_intro(self, scene: dict) -> str:
        challenge = scene.get("challenge", "")
        challenge_html = ""
        if challenge:
            challenge_html = f'<div class="challenge-box">{challenge}</div>'

        html = self._fill_template(TitleCardTemplates.INTRO,
            width=self.width, height=self.height,
            branding="COPILOT ENTRA AGENT",
            title=scene.get("title", "Demo"),
            subtitle=scene.get("subtitle", ""),
            challenge_html=challenge_html,
        )
        output_path = self.output_dir / f"{scene['id']}.png"
        await self._render_html_to_png(html, str(output_path))
        return str(output_path)

    async def _render_section_header(self, scene: dict) -> str:
        section_num = "".join(c for c in scene.get("id", "") if c.isdigit()) or ""
        html = self._fill_template(TitleCardTemplates.SECTION_HEADER,
            width=self.width, height=self.height,
            section_num=section_num,
            eyebrow=f"SECTION {section_num}" if section_num else "NEXT",
            title=scene.get("title", ""),
        )
        output_path = self.output_dir / f"{scene['id']}.png"
        await self._render_html_to_png(html, str(output_path))
        return str(output_path)

    async def _render_value_card(self, scene: dict) -> str:
        metrics = scene.get("metrics", {})
        html = self._fill_template(TitleCardTemplates.VALUE_CARD,
            width=self.width, height=self.height,
            title=scene.get("title", "Impact"),
            before_value=metrics.get("traditional", "Months"),
            before_label="Traditional Approach",
            after_value=metrics.get("agent_approach", "Days"),
            after_label="AI Agent Approach",
            insight=scene.get("subtitle", ""),
        )
        output_path = self.output_dir / f"{scene['id']}.png"
        await self._render_html_to_png(html, str(output_path))
        return str(output_path)

    async def _render_outro(self, scene: dict) -> str:
        html = self._fill_template(TitleCardTemplates.OUTRO,
            width=self.width, height=self.height,
            title=scene.get("title", "Thank You"),
            subtitle=scene.get("subtitle", ""),
            cta_text="LET'S BUILD THIS TOGETHER",
            contact="Powered by Copilot Entra Agent",
        )
        output_path = self.output_dir / f"{scene['id']}.png"
        await self._render_html_to_png(html, str(output_path))
        return str(output_path)

    @staticmethod
    def _fill_template(template: str, **kwargs) -> str:
        """Fill template placeholders without conflicting with CSS braces."""
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    async def _render_html_to_png(self, html: str, output_path: str,
                                   width: int = None, height: int = None):
        """Render HTML string to PNG using Playwright."""
        from playwright.async_api import async_playwright

        w = width or self.width
        h = height or self.height

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": w, "height": h})
            await page.set_content(html)
            await page.wait_for_timeout(500)  # Let CSS render
            await page.screenshot(path=output_path, type="png")
            await browser.close()

        logger.info(f"Rendered card: {output_path}")


if __name__ == "__main__":
    import asyncio

    async def demo():
        renderer = TitleCardRenderer(output_dir="video_output/test_cards")
        # Test intro card
        await renderer.render_scene_card({
            "id": "test_intro",
            "scene_type": "intro",
            "title": "Contract Analysis Agent",
            "subtitle": "Sony Music Entertainment",
            "challenge": "Manual contract review takes 2-3 hours per agreement",
        })
        # Test value card
        await renderer.render_scene_card({
            "id": "test_value",
            "scene_type": "value_card",
            "title": "Time to Value",
            "metrics": {"traditional": "18-24 months", "agent_approach": "1 week"},
        })
        print("Test cards rendered in video_output/test_cards/")

    asyncio.run(demo())
