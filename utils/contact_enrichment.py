from __future__ import annotations

import asyncio
from urllib.parse import urljoin

import requests

from utils.models import NA
from utils.text import extract_first_email, extract_social, normalize_url


def _fetch_text(url: str, timeout: int = 8) -> str:
    url = normalize_url(url)
    if url == NA:
        return ""
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 LocalBusinessLeadAgent/1.0"},
        )
        if response.status_code >= 400:
            return ""
        return response.text[:500_000]
    except requests.RequestException:
        return ""


async def enrich_email_and_whatsapp(website: str, instagram: str, facebook: str) -> tuple[str, str]:
    pages = []
    if website != NA:
        base = normalize_url(website)
        pages.extend([base, urljoin(base + "/", "contact"), urljoin(base + "/", "contact-us")])
    pages.extend([url for url in [instagram, facebook] if url != NA])

    for page in pages[:5]:
        html = await asyncio.to_thread(_fetch_text, page)
        email = extract_first_email(html)
        whatsapp = extract_social(html, "whatsapp")
        if email != NA or whatsapp != NA:
            return email, whatsapp
    return NA, NA
