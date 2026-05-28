# Local Business Lead Agent

A local Windows-friendly Streamlit application that finds local businesses with no website or broken websites for website development outreach.

The app uses deterministic browser automation and local Python code only. It does not use OpenAI, Claude, Gemini, or any paid AI API.

## Features

- Scrapes Google Maps, JustDial, IndiaMART, and Sulekha with Playwright.
- Extracts business name, category, address, phone, WhatsApp, email, website, social URLs, Google Maps link, rating, and review count.
- Detects mobile vs landline and prefers mobile numbers.
- Checks website reachability and keeps only `NO` or `BROKEN` website leads.
- Removes duplicate leads and known enterprise/franchise brands.
- Stores leads, duplicate checks, and scraping history in SQLite.
- Exports filtered leads to Excel with OpenPyXL formatting.

## Setup on Windows

```powershell
cd "Y:\Documents\Leads Google Map\project"
.\setup_windows.ps1
.\run_app.bat
```

Open the Streamlit URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Usage

1. Enter a location, such as `Mohali`, `Chandigarh`, or `Zirakpur`.
2. Choose a business category or select `Custom`.
3. Set the lead limit.
4. Click `Scrape Leads`.
5. Review the table and download the Excel file.

The exported filename format is:

```text
<location>_<category>_leads.xlsx
```

## Notes

Scraping public websites can be affected by layout changes, captchas, rate limits, and network speed. The code includes retries, random delays, human-like scrolling, duplicate removal, local website checks, and progress logs, but directories may still block automated traffic from time to time.

For best results, run smaller lead batches and avoid repeatedly scraping the same query in a short time.

## Deploy on Streamlit Community Cloud

1. Push this `project` folder to a GitHub repository.
2. In Streamlit Community Cloud, create a new app from that repository.
3. Set the main file path to:

```text
app.py
```

The repository includes `packages.txt` so Streamlit Cloud installs Chromium system packages for Playwright. On Windows local runs, use `run_app.bat`. On Linux/Streamlit Cloud, the app runs Playwright headlessly by default.
