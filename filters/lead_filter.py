from __future__ import annotations

import asyncio

from utils.logging import LogCallback, emit
from utils.models import Lead, NA
from utils.contact_enrichment import enrich_email_and_whatsapp
from utils.text import is_enterprise_or_franchise, lead_key
from utils.website import check_website


async def enrich_and_filter_leads(leads: list[Lead], log: LogCallback | None = None) -> list[Lead]:
    emit(log, f"Checking websites and duplicates for {len(leads)} candidates")
    deduped: dict[str, Lead] = {}
    for lead in leads:
        if is_enterprise_or_franchise(lead.business_name, lead.website_url):
            emit(log, f"Removed brand/franchise: {lead.business_name}")
            continue
        key = lead_key(lead.business_name, lead.contact_number, lead.address)
        if key not in deduped:
            deduped[key] = lead
        else:
            deduped[key] = _merge_leads(deduped[key], lead)

    checked = await asyncio.gather(*[_check_lead(lead) for lead in deduped.values()])
    filtered = [lead for lead in checked if lead.website_status in {"NO", "BROKEN"}]
    emit(log, f"Filtered to {len(filtered)} leads without working websites")
    return filtered


async def _check_lead(lead: Lead) -> Lead:
    if lead.email == NA or lead.whatsapp == NA:
        email, whatsapp = await enrich_email_and_whatsapp(lead.website_url, lead.instagram, lead.facebook)
        if lead.email == NA:
            lead.email = email
        if lead.whatsapp == NA:
            lead.whatsapp = whatsapp
    lead.website_status = await check_website(lead.website_url)
    return lead


def _merge_leads(primary: Lead, secondary: Lead) -> Lead:
    for field in primary.__dataclass_fields__:
        if getattr(primary, field) in (NA, "", None) and getattr(secondary, field) not in (NA, "", None):
            setattr(primary, field, getattr(secondary, field))
    return primary
