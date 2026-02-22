"""
Browser utilities for Youmind skill.
Handles browser launch configuration, cookie injection, and human-like actions.
"""

import json
import random
import time
from typing import Optional

from patchright.sync_api import BrowserContext, Page, Playwright

from config import BROWSER_ARGS, BROWSER_PROFILE_DIR, STATE_FILE, USER_AGENT


class BrowserFactory:
    """Factory for creating configured browser contexts."""

    @staticmethod
    def launch_persistent_context(
        playwright: Playwright,
        headless: bool = True,
        user_data_dir: str = str(BROWSER_PROFILE_DIR),
    ) -> BrowserContext:
        """
        Launch a persistent Chrome context with anti-detection defaults.

        We still inject cookies from state.json because session cookies may
        not always persist reliably across launches.
        """
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=headless,
            no_viewport=True,
            ignore_default_args=["--enable-automation"],
            user_agent=USER_AGENT,
            args=BROWSER_ARGS,
        )

        BrowserFactory._inject_cookies(context)
        return context

    @staticmethod
    def _inject_cookies(context: BrowserContext):
        """Inject cookies from state.json when available."""
        if not STATE_FILE.exists():
            return

        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            cookies = state.get("cookies", [])
            if cookies:
                context.add_cookies(cookies)
        except Exception as e:
            print(f"  ⚠️  Could not load state.json: {e}")


class StealthUtils:
    """Small helpers for human-like browser interaction."""

    @staticmethod
    def random_delay(min_ms: int = 100, max_ms: int = 500):
        time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

    @staticmethod
    def random_mouse_movement(page: Page):
        """Move mouse in short random steps to look less robotic."""
        try:
            start_x = random.randint(100, 500)
            start_y = random.randint(100, 500)
            page.mouse.move(start_x, start_y, steps=6)
            for _ in range(2):
                x = random.randint(80, 1200)
                y = random.randint(80, 700)
                page.mouse.move(x, y, steps=random.randint(4, 10))
                StealthUtils.random_delay(50, 180)
        except Exception:
            # Mouse movement is best-effort only.
            pass

    @staticmethod
    def _resolve_visible_element(page: Page, selector: str) -> Optional[object]:
        element = page.query_selector(selector)
        if element:
            try:
                if element.is_visible():
                    return element
            except Exception:
                return element

        try:
            return page.wait_for_selector(selector, timeout=2000, state="visible")
        except Exception:
            return None

    @staticmethod
    def human_type(page: Page, selector: str, text: str, wpm_min: int = 220, wpm_max: int = 320):
        """Type text with variable per-character delay."""
        element = StealthUtils._resolve_visible_element(page, selector)
        if not element:
            print(f"⚠️ Element not found for typing: {selector}")
            return

        try:
            element.click()
        except Exception:
            pass

        # Convert rough WPM range to per-character delay in ms.
        # Assuming ~5 chars per word.
        min_delay = int((60_000 / (wpm_max * 5)))
        max_delay = int((60_000 / (wpm_min * 5)))

        for char in text:
            element.type(char, delay=random.uniform(min_delay, max_delay))
            if random.random() < 0.04:
                time.sleep(random.uniform(0.08, 0.25))

    @staticmethod
    def realistic_click(page: Page, selector: str) -> bool:
        """Try clicking an element after moving mouse near it."""
        element = StealthUtils._resolve_visible_element(page, selector)
        if not element:
            return False

        try:
            box = element.bounding_box()
            if box:
                x = box["x"] + box["width"] / 2
                y = box["y"] + box["height"] / 2
                page.mouse.move(x, y, steps=5)
        except Exception:
            pass

        StealthUtils.random_delay(80, 220)
        try:
            element.click()
            StealthUtils.random_delay(80, 220)
            return True
        except Exception:
            return False
