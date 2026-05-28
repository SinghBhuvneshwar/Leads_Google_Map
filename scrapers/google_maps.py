from __future__ import annotations

import re
from urllib.parse import quote_plus

from scrapers.base import BaseScraper
from utils.browser import human_scroll, random_delay, safe_attr, safe_text
from utils.logging import emit
from utils.models import Lead, NA
from utils.text import clean_text, extract_best_phone, extract_first_email, extract_social, normalize_url


class GoogleMapsScraper(BaseScraper):
    source_name = "Google Maps"

    async def scrape(self, context) -> list[Lead]:
        page = await context.new_page()
        leads: list[Lead] = []
        try:
            url = f"https://www.google.com/maps/search/{quote_plus(self.query)}"
            emit(self.log, f"Opening Google Maps: {self.query}")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await random_delay()
            await human_scroll(page, rounds=7)

            links = await page.locator('a[href*="/maps/place"]').evaluate_all(
                """els => [...new Set(els.map(a => a.href).filter(Boolean))]"""
            )
            links = links[: self.limit]
            emit(self.log, f"Google Maps found {len(links)} candidate listings")

            for index, link in enumerate(links, start=1):
                if len(leads) >= self.limit:
                    break
                try:
                    lead = await self._scrape_listing(context, link)
                    if lead.business_name != NA:
                        leads.append(lead)
                        emit(self.log, f"Google Maps parsed {index}/{len(links)}: {lead.business_name}")
                except Exception as exc:
                    emit(self.log, f"Google Maps skipped a listing: {exc}")
                await random_delay(0.5, 1.5)
        finally:
            await page.close()
        return leads

    async def _scrape_listing(self, context, link: str) -> Lead:
        page = await context.new_page()
        try:
            await page.goto(link, wait_until="domcontentloaded", timeout=45000)
            await random_delay(1, 2)
            text = await page.locator("body").inner_text(timeout=10000)
            html = await page.content()

            name = await safe_text(page.locator("h1"), NA)
            address = await self._button_text(page, "address")
            phone = await self._button_text(page, "phone")
            if phone == NA:
                phone, detected_type = extract_best_phone(text)
            else:
                phone, detected_type = extract_best_phone(phone)

            website = await self._website(page)
            rating, reviews = self._rating_reviews(text)

            return Lead(
                business_name=clean_text(name),
                category=self.category,
                address=clean_text(address),
                contact_number=phone,
                phone_type=detected_type,
                whatsapp=extract_social(html, "whatsapp"),
                email=extract_first_email(text),
                website_url=website,
                website_status="NO" if website == NA else "BROKEN",
                instagram=extract_social(html, "instagram"),
                facebook=extract_social(html, "facebook"),
                google_maps_link=link,
                rating=rating,
                review_count=reviews,
                source=self.source_name,
            )
        finally:
            await page.close()

    async def _button_text(self, page, item_id: str) -> str:
        selectors = [
            f'button[data-item-id*="{item_id}"]',
            f'a[data-item-id*="{item_id}"]',
            f'button[aria-label*="{item_id}" i]',
            f'a[aria-label*="{item_id}" i]',
        ]
        for selector in selectors:
            value = await safe_text(page.locator(selector), NA)
            if value != NA:
                return value.replace("Address:", "").replace("Phone:", "").strip()
        return NA

    async def _website(self, page) -> str:
        selectors = [
            'a[data-item-id="authority"]',
            'a[data-item-id*="authority"]',
            'a[aria-label*="Website" i]',
        ]
        for selector in selectors:
            href = await safe_attr(page.locator(selector), "href", NA)
            if href != NA and "google." not in href:
                return normalize_url(href)
        return NA

    def _rating_reviews(self, text: str) -> tuple[str, str]:
        rating = NA
        reviews = NA
        rating_match = re.search(r"(\d(?:\.\d)?)\s*(?:stars?|rating)", text, re.I)
        if rating_match:
            rating = rating_match.group(1)
        reviews_match = re.search(r"([\d,]+)\s+reviews?", text, re.I)
        if reviews_match:
            reviews = reviews_match.group(1).replace(",", "")
        return rating, reviews
