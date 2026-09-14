"""
parse_trends_export.py
-----------------------
Phase 2 -- Data collection layer for the HYROX BI project.

REPLACES collect_trends.py's live pytrends call, which is hitting persistent
429s (Google has hardened the Trends backend; pytrends is an unofficial,
frequently-broken wrapper around it). Search-interest data doesn't change
intraday, so a manual export is a reasonable, defensible design choice --
not automated, but this is a low-frequency dimension, not a live feed.

How to get the input file:
    1. Go to https://trends.google.com/trends/explore
    2. Compare terms: HYROX, XENOM fitness, ATHX Games, CrossFit
    3. Time range: Past 5 years | Location: Worldwide
    4. Click the download icon on the "Interest over time" chart
    5. Save the file as trends_export.csv in this same folder


"""

import logging
from datetime import datetime, timezone

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

INPUT_PATH = "trends_export.csv"
OUTPUT_PATH = "trends_raw.csv"


def parse_export(path: str) -> pd.DataFrame:
    # Google's export has 1-2 metadata lines before the real header
    # (e.g. "Category: All categories" then a blank line), so we scan
    # for the first line that actually looks like a header row.
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_row_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Week,") or line.startswith("Day,") or line.startswith("Month,"):
            header_row_idx = i
            break
    if header_row_idx is None:
        raise ValueError(
            "Couldn't find a header row starting with 'Week,'/'Day,'/'Month,'. "
            "Open trends_export.csv and check it matches Google's export format."
        )

    df = pd.read_csv(path, skiprows=header_row_idx)
    date_col = df.columns[0]  # "Week", "Day", or "Month" depending on the timeframe chosen
    df = df.rename(columns={date_col: "full_date"})
    df["full_date"] = pd.to_datetime(df["full_date"])

    # Strip Google's "<term>: (Worldwide)" suffix down to the clean brand name
    rename_map = {}
    for col in df.columns:
        if col == "full_date":
            continue
        clean_name = col.split(":")[0].strip()
        rename_map[col] = clean_name
    df = df.rename(columns=rename_map)

    long_df = df.melt(id_vars="full_date", var_name="brand_name", value_name="search_index")

    # Google sometimes marks suppressed low-volume weeks with "<1" -- treat as 0
    long_df["search_index"] = (
        long_df["search_index"].astype(str).str.replace("<1", "0", regex=False)
    )
    long_df["search_index"] = pd.to_numeric(long_df["search_index"], errors="coerce")

    long_df["date_id"] = long_df["full_date"].dt.strftime("%Y%m%d").astype(int)
    long_df["collected_at"] = datetime.now(timezone.utc).isoformat()

    return long_df[["date_id", "full_date", "brand_name", "search_index", "collected_at"]]


def main():
    trends_df = parse_export(INPUT_PATH)
    trends_df.to_csv(OUTPUT_PATH, index=False)
    log.info("Saved %d rows to %s", len(trends_df), OUTPUT_PATH)
    log.info("Brands found: %s", trends_df["brand_name"].unique().tolist())
    log.info("Date range: %s to %s", trends_df["full_date"].min(), trends_df["full_date"].max())
    log.info("Preview:\n%s", trends_df.head(8).to_string(index=False))


if __name__ == "__main__":
    main()




# ---------------------------------------------------------------------
# Run this snippet separately, INSIDE a Fabric notebook attached to your
# Lakehouse, after uploading trends_raw.csv to Files/bronze/trends/
# ---------------------------------------------------------------------
LOAD_TO_LAKEHOUSE_SNIPPET = """
df = spark.read.option("header", True).option("inferSchema", True) \\
    .csv("Files/bronze/trends/trends_raw.csv")

df.write.format("delta").mode("overwrite") \\
    .saveAsTable("bronze_trends")

display(spark.sql('''
    SELECT brand_name, COUNT(*) AS rows, MAX(full_date) AS latest
    FROM bronze_trends
    GROUP BY brand_name
'''))
"""
