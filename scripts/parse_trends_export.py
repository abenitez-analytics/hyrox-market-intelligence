
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





