from __future__ import annotations

import asyncio
import random


async def random_delay(min_seconds: float = 0.8, max_seconds: float = 2.2) -> None:
    await asyncio.sleep(random.uniform(min_seconds, max_seconds))


async def human_scroll(page, rounds: int = 5) -> None:
    for _ in range(rounds):
        await page.mouse.wheel(0, random.randint(600, 1300))
        await random_delay(0.4, 1.1)


async def safe_text(locator, default: str = "N/A") -> str:
    try:
        text = await locator.first.text_content(timeout=2500)
        return " ".join((text or "").split()) or default
    except Exception:
        return default


async def safe_attr(locator, attr: str, default: str = "N/A") -> str:
    try:
        value = await locator.first.get_attribute(attr, timeout=2500)
        return value or default
    except Exception:
        return default
