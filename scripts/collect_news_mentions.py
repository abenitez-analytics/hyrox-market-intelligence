
import logging
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

BRAND_KEYWORDS = {
    "HYROX": "HYROX",
    "XENOM": "XENOM",
    "ATHX Games": "ATHX",
    "CrossFit": "CrossFit",
}

WINDOW_DAYS = 90
MIN_SECONDS_BETWEEN_REQUESTS = 10  # widened from 6s after hitting an escalated cool-down during testing
MAX_RETRIES = 4
OUTPUT_PATH = "news_mentions_raw.csv"
DT_FMT = "%Y%m%d%H%M%S"


def fetch_one_brand(brand_name: str, keyword: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    params = {
        "query": keyword,
        "mode": "timelinevolraw",
        "format": "json",
        "startdatetime": start_dt.strftime(DT_FMT),
        "enddatetime": end_dt.strftime(DT_FMT),
    }

    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.get(BASE_URL, params=params, timeout=30)

        if resp.status_code == 429:
            wait = MIN_SECONDS_BETWEEN_REQUESTS * (2 ** (attempt - 1))
            log.warning("%s: rate-limited (429), waiting %ds before retry %d/%d",
                        brand_name, wait, attempt, MAX_RETRIES)
            time.sleep(wait)
            continue

        if resp.status_code != 200:
            log.warning("%s: unexpected status %d, body: %s", brand_name, resp.status_code, resp.text[:300])
            return pd.DataFrame()

        payload = resp.json()
        rows = []
        for series in payload.get("timeline", []):
            for point in series.get("data", []):
                rows.append({"full_date": point["date"], "news_mentions": point["value"]})

        if not rows:
            log.info("%s: request succeeded but returned zero data points (likely genuinely low/no coverage)", brand_name)
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["brand_name"] = brand_name
        return df

    log.error("%s: exhausted retries, giving up", brand_name)
    return pd.DataFrame()


def fetch_mentions() -> pd.DataFrame:
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=WINDOW_DAYS)

    log.info("Waiting 60s before first request -- GDELT's rate limit is tracked "
             "per IP globally, not per script run, and repeated 429s can trigger "
             "a longer cool-down (we hit this during testing), so giving it "
             "extra room here.")
    time.sleep(60)

    all_dfs = []
    for i, (brand_name, keyword) in enumerate(BRAND_KEYWORDS.items()):
        if i > 0:
            time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)  # respect the 1-request-per-5s limit
        log.info("Fetching GDELT timeline for %s ('%s')", brand_name, keyword)
        brand_df = fetch_one_brand(brand_name, keyword, start_dt, end_dt)
        if not brand_df.empty:
            all_dfs.append(brand_df)

    if not all_dfs:
        raise RuntimeError("No timeline data retrieved for any brand -- check the printed status codes above.")

    combined = pd.concat(all_dfs, ignore_index=True)
    combined["full_date"] = pd.to_datetime(combined["full_date"], format="%Y%m%dT%H%M%SZ").dt.date
    combined["date_id"] = pd.to_datetime(combined["full_date"]).dt.strftime("%Y%m%d").astype(int)
    combined["collected_at"] = datetime.now(timezone.utc).isoformat()

    return combined[["date_id", "full_date", "brand_name", "news_mentions", "collected_at"]]


def main():
    df = fetch_mentions()
    df.to_csv(OUTPUT_PATH, index=False)
    log.info("Saved %d rows to %s", len(df), OUTPUT_PATH)
    log.info("Brands found: %s", df["brand_name"].unique().tolist())
    log.info("Preview:\n%s", df.head(8).to_string(index=False))


if __name__ == "__main__":
    main()



