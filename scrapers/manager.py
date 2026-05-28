from __future__ import annotations

import asyncio
import os
import platform
import shutil

from playwright.async_api import async_playwright

from filters.lead_filter import enrich_and_filter_leads
from scrapers.directory_scraper import IndiaMartScraper, JustDialScraper, SulekhaScraper
from scrapers.google_maps import GoogleMapsScraper
from utils.logging import LogCallback, emit
from utils.models import Lead


async def _run_with_retry(scraper, context, attempts: int = 2) -> list[Lead]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await scraper.scrape(context)
        except Exception as exc:
            last_error = exc
            emit(scraper.log, f"{scraper.source_name} attempt {attempt} failed: {exc}")
            await asyncio.sleep(2 * attempt)
    if last_error:
        raise last_error
    return []


async def scrape_all_sources(
    category: str,
    location: str,
    lead_limit: int,
    log: LogCallback | None = None,
    progress: LogCallback | None = None,
) -> list[Lead]:
    per_source_limit = max(5, lead_limit)
    raw_leads: list[Lead] = []

    async with async_playwright() as p:
        default_headless = "true" if platform.system() != "Windows" else "false"
        headless = os.getenv("LBLA_HEADLESS", default_headless).lower() in {"1", "true", "yes"}
        launch_kwargs = {"headless": headless, "slow_mo": 40}
        system_chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
        if system_chromium:
            launch_kwargs["executable_path"] = system_chromium
        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            viewport={"width": 1366, "height": 850},
            locale="en-IN",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
        )

        scrapers = [
            GoogleMapsScraper(category, location, per_source_limit, log),
            JustDialScraper(category, location, per_source_limit, log),
            IndiaMartScraper(category, location, per_source_limit, log),
            SulekhaScraper(category, location, per_source_limit, log),
        ]

        for index, scraper in enumerate(scrapers, start=1):
            emit(log, f"Starting {scraper.source_name}")
            if progress:
                progress(str((index - 1) / len(scrapers) * 0.65))
            try:
                raw_leads.extend(await _run_with_retry(scraper, context))
            except Exception as exc:
                emit(log, f"{scraper.source_name} error: {exc}")

        await context.close()
        await browser.close()

    if progress:
        progress("0.75")
    filtered = await enrich_and_filter_leads(raw_leads, log)
    if progress:
        progress("1.0")
    return filtered[:lead_limit]
