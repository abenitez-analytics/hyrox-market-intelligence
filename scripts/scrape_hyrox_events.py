
import logging
import re
import time
from datetime import datetime, date, timezone

import pandas as pd
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

SOURCE_URL = "https://www.roxupdates.com/cities/"
OUTPUT_PATH = "hyrox_events_raw.csv"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
)}
MONTH_RE = "|".join(MONTHS.keys())

STATUS_RE = r"(?P<status>Past|On Sale|Sold Out|Coming Soon|Not Yet Announced)"
DATE_RE = (
    rf"(?P<mon1>{MONTH_RE})\.?\s+(?P<day1>\d{{1,2}})"
    rf"(?:-(?P<day2same>\d{{1,2}}))?"
    rf"(?:\s*-\s*(?P<mon2>{MONTH_RE})\.?\s+(?P<day2>\d{{1,2}}))?"
    rf",\s*(?P<year>\d{{4}})"
)
FULL_RE = re.compile(rf"^{STATUS_RE}(?P<city>.+?){DATE_RE}(?P<venue>.+)$")


def parse_event_text(text: str):
    m = FULL_RE.match(text.strip())
    if not m:
        return None
    d = m.groupdict()
    mon1, year = MONTHS[d["mon1"]], int(d["year"])
    if d["mon2"]:
        start = date(year, mon1, int(d["day1"]))
        end = date(year, MONTHS[d["mon2"]], int(d["day2"]))
    elif d["day2same"]:
        start = date(year, mon1, int(d["day1"]))
        end = date(year, mon1, int(d["day2same"]))
    else:
        start = date(year, mon1, int(d["day1"]))
        end = start
    return {
        "status": d["status"],
        "city": d["city"].strip(),
        "start_date": start,
        "end_date": end,
        "venue": d["venue"].strip(),
    }


def fetch_and_parse() -> pd.DataFrame:
    log.info("Fetching %s", SOURCE_URL)

    resp = None
    for attempt in range(1, 4):
        resp = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
        if resp.status_code != 429:
            break
        wait = 20 * attempt
        log.warning("429 from source site, waiting %ds before retry %d/3", wait, attempt)
        time.sleep(wait)

    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    rows = []
    skipped = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/cities/" not in href or href.rstrip("/").endswith("/cities"):
            continue
        text = a.get_text(strip=True)
        parsed = parse_event_text(text)
        if parsed is None:
            continue  # nav links, footer links etc. won't match the event pattern
        slug = href.rstrip("/").split("/")[-1]
        parsed["city_slug"] = slug
        parsed["source_url"] = href if href.startswith("http") else f"https://www.roxupdates.com{href}"
        rows.append(parsed)

    if not rows:
        raise RuntimeError(
            "No events parsed -- the page structure may have changed. "
            "Inspect the raw HTML and update FULL_RE / the <a> tag selection logic."
        )

    df = pd.DataFrame(rows).drop_duplicates(subset=["city_slug"])
    df["brand_name"] = "HYROX"
    df["sold_out_flag"] = df["status"].eq("Sold Out")
    df["scraped_at"] = datetime.now(timezone.utc).isoformat()

    return df[[
        "brand_name", "city", "city_slug", "start_date", "end_date",
        "venue", "status", "sold_out_flag", "source_url", "scraped_at",
    ]]


def main():
    df = fetch_and_parse()
    df.to_csv(OUTPUT_PATH, index=False)
    log.info("Saved %d events to %s", len(df), OUTPUT_PATH)
    log.info("Status breakdown:\n%s", df["status"].value_counts().to_string())
    log.info("Preview:\n%s", df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

