from __future__ import annotations

from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from utils.browser import human_scroll, random_delay
from utils.logging import emit
from utils.models import Lead, NA
from utils.text import clean_text, extract_best_phone, extract_first_email, extract_social, normalize_url


class DirectoryScraper(BaseScraper):
    source_name = "Directory"
    start_url = ""

    async def scrape(self, context) -> list[Lead]:
        page = await context.new_page()
        leads: list[Lead] = []
        try:
            url = self.start_url.format(
                query=quote_plus(self.query),
                category=quote_plus(self.category),
                location=quote_plus(self.location),
            )
            emit(self.log, f"Opening {self.source_name}: {self.query}")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await random_delay()
            await human_scroll(page, rounds=5)
            html = await page.content()
            leads = self._parse_html(html, page.url)
            emit(self.log, f"{self.source_name} parsed {len(leads)} candidate listings")
        except Exception as exc:
            emit(self.log, f"{self.source_name} failed: {exc}")
        finally:
            await page.close()
        return leads[: self.limit]

    def _parse_html(self, html: str, current_url: str) -> list[Lead]:
        soup = BeautifulSoup(html, "html.parser")
        candidates = []
        card_selectors = [
            "article", "[class*=card]", "[class*=listing]", "[class*=result]",
            "[class*=store]", "[class*=vendor]", "[class*=company]", "li",
        ]
        for selector in card_selectors:
            candidates.extend(soup.select(selector))
        if not candidates:
            candidates = [soup.body or soup]

        leads: list[Lead] = []
        seen = set()
        for card in candidates:
            text = clean_text(card.get_text(" ", strip=True))
            if text == NA or len(text) < 12:
                continue

            links = [a.get("href", "") for a in card.select("a[href]")]
            links_text = " ".join(links)
            website = self._pick_website(links)
            name = self._name_from_card(card)
            phone, detected_type = extract_best_phone(text)
            if name == NA and phone == NA:
                continue

            key = f"{name}|{phone}|{text[:60]}"
            if key in seen:
                continue
            seen.add(key)

            leads.append(
                Lead(
                    business_name=name,
                    category=self.category,
                    address=self._address_from_text(text),
                    contact_number=phone,
                    phone_type=detected_type,
                    whatsapp=extract_social(html + " " + links_text, "whatsapp"),
                    email=extract_first_email(text + " " + html),
                    website_url=website,
                    website_status="NO" if website == NA else "BROKEN",
                    instagram=extract_social(html + " " + links_text, "instagram"),
                    facebook=extract_social(html + " " + links_text, "facebook"),
                    google_maps_link=NA,
                    rating=self._rating(text),
                    review_count=self._reviews(text),
                    source=self.source_name,
                )
            )
            if len(leads) >= self.limit:
                break
        return leads

    def _name_from_card(self, card) -> str:
        for selector in ["h1", "h2", "h3", "h4", "a[title]", "a"]:
            element = card.select_one(selector)
            if not element:
                continue
            title = element.get("title") or element.get_text(" ", strip=True)
            title = clean_text(title)
            if title != NA and len(title) > 2:
                return title[:140]
        return NA

    def _pick_website(self, links: list[str]) -> str:
        blocked = ("justdial", "indiamart", "sulekha", "google", "facebook", "instagram", "whatsapp", "wa.me")
        for href in links:
            href = normalize_url(href)
            if href == NA:
                continue
            if href.startswith("mailto:") or href.startswith("tel:"):
                continue
            if not any(domain in href.lower() for domain in blocked):
                return href
        return NA

    def _address_from_text(self, text: str) -> str:
        if text == NA:
            return NA
        fragments = [part.strip() for part in text.split("|") if part.strip()]
        if len(fragments) > 1:
            return fragments[-1][:240]
        return text[:240]

    def _rating(self, text: str) -> str:
        import re

        match = re.search(r"\b([1-5](?:\.\d)?)\b\s*(?:/5|rating|ratings|star)", text, re.I)
        return match.group(1) if match else NA

    def _reviews(self, text: str) -> str:
        import re

        match = re.search(r"([\d,]+)\s*(?:reviews?|ratings?)", text, re.I)
        return match.group(1).replace(",", "") if match else NA


class JustDialScraper(DirectoryScraper):
    source_name = "JustDial"
    start_url = "https://www.justdial.com/{location}/{category}"


class IndiaMartScraper(DirectoryScraper):
    source_name = "IndiaMART"
    start_url = "https://dir.indiamart.com/search.mp?ss={query}"


class SulekhaScraper(DirectoryScraper):
    source_name = "Sulekha"
    start_url = "https://www.sulekha.com/search?keyword={query}"
