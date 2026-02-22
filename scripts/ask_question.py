#!/usr/bin/env python3
"""
Simple Youmind question interface (stateless mode).
Each question opens a fresh browser context, asks once, then exits.
"""

import argparse
from collections import Counter
import sys
import time
from pathlib import Path
from typing import List, Optional

from patchright.sync_api import sync_playwright

# Add scripts directory to import path
sys.path.insert(0, str(Path(__file__).parent))

from auth_manager import AuthManager
from board_manager import BoardLibrary
from browser_utils import BrowserFactory, StealthUtils
from config import (
    QUERY_INPUT_SELECTORS,
    RESPONSE_SELECTORS,
    SEND_BUTTON_SELECTORS,
    THINKING_SELECTORS,
    YOUMIND_BOARD_URL_PREFIX,
)

FOLLOW_UP_REMINDER = (
    "\n\nEXTREMELY IMPORTANT: Is that ALL you need to know? "
    "Before replying to the user, compare this answer with the original request. "
    "If details are missing, ask another comprehensive follow-up question and include full context."
)


def _collect_responses(page) -> List[str]:
    """Collect response texts from the first matching selector in DOM order."""
    for selector in RESPONSE_SELECTORS:
        try:
            elements = page.query_selector_all(selector)
            selector_texts: List[str] = []
            for el in elements:
                text = el.inner_text().strip()
                if text:
                    selector_texts.append(text)
            if selector_texts:
                return selector_texts
        except Exception:
            continue

    return []


def _is_thinking(page) -> bool:
    """Best-effort detection for in-progress generation."""
    for selector in THINKING_SELECTORS:
        try:
            nodes = page.query_selector_all(selector)
            if any(node.is_visible() for node in nodes):
                return True
        except Exception:
            continue
    return False


def _find_input_selector(page) -> Optional[str]:
    """Return the first usable chat input selector."""
    for selector in QUERY_INPUT_SELECTORS:
        try:
            page.wait_for_selector(selector, timeout=5000, state="visible")
            return selector
        except Exception:
            continue
    return None


def ask_youmind(question: str, board_url: str, headless: bool = True) -> Optional[str]:
    """Send a question to a Youmind board chat and return the answer."""
    auth = AuthManager()
    if not auth.is_authenticated():
        print("⚠️ Not authenticated. Run: python scripts/run.py auth_manager.py setup")
        return None

    print(f"💬 Asking: {question}")
    print(f"🧠 Board: {board_url}")

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=headless)

        page = context.new_page()
        print("  🌐 Opening board...")
        page.goto(board_url, wait_until="domcontentloaded")

        # If redirected to sign-in, auth is invalid.
        if "youmind.com" not in page.url or "sign-in" in page.url:
            print("  ❌ Redirected to sign-in. Authentication may be expired.")
            return None

        # Snapshot previous latest response to ensure we only return new output.
        previous_responses = _collect_responses(page)
        previous_last_response = previous_responses[-1] if previous_responses else None
        previous_counts = Counter(previous_responses)

        input_selector = _find_input_selector(page)
        if not input_selector:
            print("  ❌ Could not find chat input")
            return None

        print(f"  ✓ Found chat input: {input_selector}")
        StealthUtils.realistic_click(page, input_selector)
        StealthUtils.human_type(page, input_selector, question)

        # Submit question via Enter first.
        print("  📤 Submitting question...")
        page.keyboard.press("Enter")

        # Some editors insert newline on Enter; click Send button as fallback.
        time.sleep(0.6)
        for send_selector in SEND_BUTTON_SELECTORS:
            try:
                if StealthUtils.realistic_click(page, send_selector):
                    break
            except Exception:
                continue

        print("  ⏳ Waiting for answer...")

        deadline = time.time() + 120
        stable_count = 0
        last_text = None

        while time.time() < deadline:
            responses = _collect_responses(page)
            candidate = None

            if responses:
                current_counts = Counter(responses)

                # Find text whose occurrence increased after submit.
                for text in reversed(responses):
                    if current_counts[text] > previous_counts.get(text, 0):
                        candidate = text
                        break

                # Fallback: updated-in-place latest response.
                if (
                    candidate is None
                    and previous_last_response
                    and responses[-1] != previous_last_response
                    and responses != previous_responses
                ):
                    candidate = responses[-1]

            if candidate:
                if candidate == last_text:
                    stable_count += 1
                    if stable_count >= 3:
                        print("  ✅ Got answer")
                        return candidate + FOLLOW_UP_REMINDER
                else:
                    last_text = candidate
                    stable_count = 1

            # Thinking state is informative but not blocking; keep polling text.
            if _is_thinking(page):
                time.sleep(0.8)
                continue

            time.sleep(0.8)

        print("  ❌ Timeout waiting for answer")
        return None

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass


def _resolve_board_url(board_url: Optional[str], board_id: Optional[str]) -> Optional[str]:
    if board_url:
        return board_url

    library = BoardLibrary()

    if board_id:
        board = library.get_board(board_id)
        if not board:
            print(f"❌ Board '{board_id}' not found")
            return None
        return board["url"]

    active = library.get_active_board()
    if active:
        print(f"🧠 Using active board: {active['name']}")
        return active["url"]

    boards = library.list_boards()
    if boards:
        print("\n🧠 Available boards:")
        for b in boards:
            mark = " [ACTIVE]" if b["id"] == library.active_board_id else ""
            print(f"  {b['id']}: {b['name']}{mark}")
        print("\nSpecify with --board-id or set active:")
        print("python scripts/run.py board_manager.py activate --id ID")
    else:
        print("❌ No boards in library. Add one first:")
        print("python scripts/run.py board_manager.py add --url URL --name NAME --description DESC --topics TOPICS")

    return None


def main():
    parser = argparse.ArgumentParser(description="Ask Youmind board chat a question")
    parser.add_argument("--question", required=True, help="Question to ask")
    parser.add_argument("--board-url", help="Youmind board URL")
    parser.add_argument("--board-id", help="Board ID from local library")
    parser.add_argument("--show-browser", action="store_true", help="Show browser for debugging")
    args = parser.parse_args()

    board_url = _resolve_board_url(args.board_url, args.board_id)
    if not board_url:
        return 1

    if not board_url.startswith(YOUMIND_BOARD_URL_PREFIX):
        print(f"⚠️ Board URL should start with: {YOUMIND_BOARD_URL_PREFIX}")

    answer = ask_youmind(
        question=args.question,
        board_url=board_url,
        headless=not args.show_browser,
    )

    if not answer:
        print("\n❌ Failed to get answer")
        return 1

    print("\n" + "=" * 60)
    print(f"Question: {args.question}")
    print("=" * 60)
    print()
    print(answer)
    print()
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
