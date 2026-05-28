from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from utils.models import Lead
from utils.text import lead_key


DB_PATH = Path(__file__).resolve().parent / "leads.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT,
                category TEXT,
                address TEXT,
                contact_number TEXT,
                phone_type TEXT,
                whatsapp TEXT,
                email TEXT,
                website_url TEXT,
                website_status TEXT,
                instagram TEXT,
                facebook TEXT,
                google_maps_link TEXT,
                rating TEXT,
                review_count TEXT,
                source TEXT,
                duplicate_key TEXT UNIQUE,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS duplicate_checks (
                duplicate_key TEXT PRIMARY KEY,
                first_seen TEXT,
                last_seen TEXT,
                seen_count INTEGER DEFAULT 1
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scraping_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT,
                category TEXT,
                lead_limit INTEGER,
                total_candidates INTEGER,
                exported_leads INTEGER,
                started_at TEXT,
                finished_at TEXT
            )
            """
        )


def start_history(location: str, category: str, lead_limit: int) -> int:
    started_at = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO scraping_history
            (location, category, lead_limit, total_candidates, exported_leads, started_at)
            VALUES (?, ?, ?, 0, 0, ?)
            """,
            (location, category, lead_limit, started_at),
        )
        return int(cur.lastrowid)


def finish_history(history_id: int, total_candidates: int, exported_leads: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE scraping_history
            SET total_candidates = ?, exported_leads = ?, finished_at = ?
            WHERE id = ?
            """,
            (total_candidates, exported_leads, datetime.now().isoformat(timespec="seconds"), history_id),
        )


def save_leads(leads: list[Lead]) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        for lead in leads:
            key = lead_key(lead.business_name, lead.contact_number, lead.address)
            conn.execute(
                """
                INSERT INTO duplicate_checks (duplicate_key, first_seen, last_seen, seen_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(duplicate_key) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    seen_count = seen_count + 1
                """,
                (key, now, now),
            )
            conn.execute(
                """
                INSERT INTO leads (
                    business_name, category, address, contact_number, phone_type,
                    whatsapp, email, website_url, website_status, instagram, facebook,
                    google_maps_link, rating, review_count, source, duplicate_key, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(duplicate_key) DO UPDATE SET
                    category = excluded.category,
                    address = excluded.address,
                    contact_number = excluded.contact_number,
                    phone_type = excluded.phone_type,
                    whatsapp = excluded.whatsapp,
                    email = excluded.email,
                    website_url = excluded.website_url,
                    website_status = excluded.website_status,
                    instagram = excluded.instagram,
                    facebook = excluded.facebook,
                    google_maps_link = excluded.google_maps_link,
                    rating = excluded.rating,
                    review_count = excluded.review_count,
                    source = excluded.source
                """,
                (
                    lead.business_name,
                    lead.category,
                    lead.address,
                    lead.contact_number,
                    lead.phone_type,
                    lead.whatsapp,
                    lead.email,
                    lead.website_url,
                    lead.website_status,
                    lead.instagram,
                    lead.facebook,
                    lead.google_maps_link,
                    lead.rating,
                    lead.review_count,
                    lead.source,
                    key,
                    now,
                ),
            )


def recent_history(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT location, category, lead_limit, exported_leads, started_at, finished_at
            FROM scraping_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
