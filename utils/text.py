from __future__ import annotations

import re
from urllib.parse import urlparse

from utils.models import NA


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?91[\s-]?)?(?:0[\s-]?)?(?:[6-9]\d{9}|[1-9]\d{2,4}[\s-]?\d{6,8})")
SOCIAL_RE = {
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/[^\s\"'<>]+", re.I),
    "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[^\s\"'<>]+", re.I),
    "whatsapp": re.compile(r"https?://(?:wa\.me|api\.whatsapp\.com|web\.whatsapp\.com)/[^\s\"'<>]+", re.I),
}

ENTERPRISE_KEYWORDS = {
    "mcdonald", "kfc", "domino", "pizza hut", "starbucks", "subway", "burger king",
    "reliance", "tata", "airtel", "vodafone", "jio", "apollo", "fortis", "max hospital",
    "radisson", "marriott", "hilton", "holiday inn", "oyo", "cult.fit", "anytime fitness",
    "gold's gym", "looks salon", "naturals", "vlcc", "lakme", "ccd", "cafe coffee day",
}


def clean_text(value: str | None) -> str:
    if not value:
        return NA
    value = re.sub(r"\s+", " ", value).strip(" \t\r\n-|,")
    return value or NA


def normalize_phone(value: str | None) -> str:
    if not value:
        return NA
    digits = re.sub(r"\D", "", value)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) > 10:
        digits = digits[1:]
    return digits if len(digits) >= 7 else NA


def phone_type(phone: str) -> str:
    if not phone or phone == NA:
        return NA
    return "Mobile" if re.match(r"^[6-9]\d{9}$", phone) else "Landline"


def extract_best_phone(text: str) -> tuple[str, str]:
    phones = [normalize_phone(match.group(0)) for match in PHONE_RE.finditer(text or "")]
    phones = [phone for phone in phones if phone != NA]
    if not phones:
        return NA, NA
    mobiles = [phone for phone in phones if phone_type(phone) == "Mobile"]
    selected = mobiles[0] if mobiles else phones[0]
    return selected, phone_type(selected)


def extract_first_email(text: str) -> str:
    match = EMAIL_RE.search(text or "")
    return clean_text(match.group(0)) if match else NA


def extract_social(text: str, key: str) -> str:
    pattern = SOCIAL_RE[key]
    match = pattern.search(text or "")
    return clean_text(match.group(0).rstrip("/),.;")) if match else NA


def normalize_url(url: str | None) -> str:
    url = clean_text(url)
    if url == NA:
        return NA
    if url.lower().startswith(("mailto:", "tel:", "javascript:")):
        return NA
    if url.startswith("//"):
        url = "https:" + url
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url.rstrip("/")


def domain_key(url: str) -> str:
    if not url or url == NA:
        return NA
    parsed = urlparse(normalize_url(url))
    return parsed.netloc.lower().removeprefix("www.")


def lead_key(name: str, phone: str, address: str) -> str:
    bits = [clean_text(name).lower(), normalize_phone(phone), clean_text(address).lower()[:80]]
    return "|".join(bits)


def is_enterprise_or_franchise(name: str, website: str = NA) -> bool:
    haystack = f"{name} {domain_key(website)}".lower()
    return any(keyword in haystack for keyword in ENTERPRISE_KEYWORDS)


def safe_filename_part(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return re.sub(r"_+", "_", value).strip("_") or "leads"
