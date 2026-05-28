from __future__ import annotations

import asyncio
import requests

from utils.models import NA
from utils.text import normalize_url


WORKING_CODES = set(range(200, 400)) | {401, 403}


def _check_url_sync(url: str, timeout: int = 8) -> str:
    url = normalize_url(url)
    if url == NA:
        return "NO"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LocalBusinessLeadAgent/1.0"
    }
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout, headers=headers)
        if response.status_code in WORKING_CODES:
            return "YES"
        response = requests.get(url, allow_redirects=True, timeout=timeout, headers=headers, stream=True)
        return "YES" if response.status_code in WORKING_CODES else "BROKEN"
    except requests.RequestException:
        return "BROKEN"


async def check_website(url: str) -> str:
    return await asyncio.to_thread(_check_url_sync, url)
