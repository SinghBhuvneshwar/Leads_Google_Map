from __future__ import annotations

import asyncio
from pathlib import Path

import streamlit as st

from database.db import finish_history, init_db, recent_history, save_leads, start_history
from exports.excel_exporter import build_excel, export_filename, leads_to_dataframe
from scrapers.manager import scrape_all_sources
from utils.models import Lead, NA


st.set_page_config(page_title="Local Business Lead Agent", page_icon="LB", layout="wide")

CATEGORIES = [
    "Gyms", "Salons", "Cafes", "Restaurants", "Clinics", "Dentists",
    "Repair Shops", "Boutiques", "Hotels", "Real Estate", "Coaching Centers", "Custom",
]


def init_state() -> None:
    st.session_state.setdefault("logs", [])
    st.session_state.setdefault("leads", [])
    st.session_state.setdefault("progress", 0.0)


def stats(leads: list[Lead]) -> dict[str, int]:
    return {
        "Total Leads": len(leads),
        "No Website": sum(1 for lead in leads if lead.website_status == "NO"),
        "Broken Website": sum(1 for lead in leads if lead.website_status == "BROKEN"),
        "WhatsApp": sum(1 for lead in leads if lead.whatsapp != NA),
        "Email": sum(1 for lead in leads if lead.email != NA),
    }


def main() -> None:
    init_db()
    init_state()

    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.6rem; }
        div[data-testid="stMetric"] {
            background: #f7f9fc;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
            padding: 14px 16px;
        }
        .logbox {
            height: 220px;
            overflow-y: auto;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
            padding: 12px;
            background: #0f172a;
            color: #e2e8f0;
            font-family: Consolas, monospace;
            font-size: 13px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.title("Local Business Lead Agent")
        location = st.text_input("Location", value="Mohali", placeholder="Mohali, Chandigarh, Zirakpur")
        selected_category = st.selectbox("Business category", CATEGORIES)
        custom_category = ""
        if selected_category == "Custom":
            custom_category = st.text_input("Custom category", placeholder="Pet clinics, bakeries, spas")
        category = custom_category.strip() if selected_category == "Custom" else selected_category
        lead_limit = st.slider("Lead limit", min_value=5, max_value=100, value=25, step=5)
        scrape_clicked = st.button("Scrape Leads", type="primary", use_container_width=True)

        st.divider()
        st.caption("Recent scraping history")
        for row in recent_history(5):
            st.caption(f"{row['started_at']} - {row['category']} in {row['location']}: {row['exported_leads']}")

    st.title("Local Business Lead Agent")
    st.caption("Finds local businesses with no website or broken websites using local browser automation.")

    progress_bar = st.progress(st.session_state.progress)
    log_area = st.empty()

    def render_logs() -> None:
        log_html = "<br>".join(st.session_state.logs[-200:]) or "Logs will appear here after scraping starts."
        log_area.markdown(f"<div class='logbox'>{log_html}</div>", unsafe_allow_html=True)

    def ui_log(message: str) -> None:
        st.session_state.logs.append(message)
        render_logs()

    def ui_progress(value: str) -> None:
        try:
            st.session_state.progress = max(0.0, min(1.0, float(value)))
            progress_bar.progress(st.session_state.progress)
        except ValueError:
            pass

    if scrape_clicked:
        if not location.strip() or not category.strip():
            st.error("Enter both location and category.")
            return
        st.session_state.logs = []
        st.session_state.leads = []
        st.session_state.progress = 0.0
        history_id = start_history(location.strip(), category.strip(), lead_limit)
        ui_log(f"Search query: {category.strip()} in {location.strip()}")
        with st.spinner("Scraping live listings. A browser window may open while Playwright works."):
            leads = asyncio.run(
                scrape_all_sources(
                    category.strip(),
                    location.strip(),
                    lead_limit,
                    log=ui_log,
                    progress=ui_progress,
                )
            )
        save_leads(leads)
        finish_history(history_id, total_candidates=len(leads), exported_leads=len(leads))
        st.session_state.leads = leads
        st.session_state.progress = 1.0
        ui_progress("1.0")
        ui_log("Scraping complete")

    progress_bar.progress(st.session_state.progress)
    render_logs()

    leads = st.session_state.leads
    stat_values = stats(leads)
    cols = st.columns(5)
    for col, (label, value) in zip(cols, stat_values.items()):
        col.metric(label, value)

    st.subheader("Lead Preview")
    if leads:
        df = leads_to_dataframe(leads)
        st.dataframe(df, use_container_width=True, hide_index=True)
        excel_bytes = build_excel(leads)
        st.download_button(
            "Download Excel",
            data=excel_bytes,
            file_name=export_filename(location, category),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        st.success(
            f"Completed: total leads {stat_values['Total Leads']}, "
            f"leads without websites {stat_values['No Website']}, "
            f"leads with WhatsApp {stat_values['WhatsApp']}, "
            f"leads with email {stat_values['Email']}."
        )
    else:
        st.info("No leads loaded yet. Configure the sidebar and start scraping.")


if __name__ == "__main__":
    main()
