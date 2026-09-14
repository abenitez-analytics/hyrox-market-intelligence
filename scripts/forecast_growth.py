"""
ML layer, part 1: forecast HYROX and CrossFit search-interest
trajectory 26 weeks (~6 months) forward using Holt-Winters exponential
smoothing (trend + yearly seasonality).

Only run on HYROX and CrossFit -- they're the only brands with a real
multi-year weekly time series. XENOM/ATHX Games don't have search volume
to forecast (that's itself the finding for them).

Input: fact_trends.csv (as exported from the Fabric Warehouse)
Output: forecast_output.csv -- actual + forecasted search_index per brand,
         ready to load into Power BI.
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings
warnings.filterwarnings("ignore")

INPUT_PATH = "fact_trends.csv"
OUTPUT_PATH = "forecast_output.csv"

BRAND_NAMES = {1: "HYROX", 4: "CrossFit"}
FORECAST_WEEKS = 26

df = pd.read_csv(INPUT_PATH, na_values=["NULL"])
df["full_date"] = pd.to_datetime(df["date_id"], format="%Y%m%d")

all_rows = []
summary = []

for brand_id, brand_name in BRAND_NAMES.items():
    series = (
        df[(df["brand_id"] == brand_id) & df["search_index"].notna()]
        .sort_values("full_date")
        .set_index("full_date")["search_index"]
        .asfreq("W", method="pad")  # ensure a clean weekly frequency, forward-fill tiny gaps
    )

    model = ExponentialSmoothing(
        series, trend="add", seasonal="add", seasonal_periods=52, damped_trend=True
    ).fit()

    forecast = model.forecast(FORECAST_WEEKS)

    actual_df = pd.DataFrame({
        "full_date": series.index, "brand_name": brand_name,
        "search_index": series.values, "type": "actual",
    })
    forecast_df = pd.DataFrame({
        "full_date": forecast.index, "brand_name": brand_name,
        "search_index": forecast.values.clip(min=0), "type": "forecast",
    })
    all_rows.append(pd.concat([actual_df, forecast_df]))

    current_level = series.iloc[-8:].mean()   # recent 8-week average, smooths noise
    forecast_level = forecast.iloc[-8:].mean()  # last 8 weeks of the forecast horizon
    pct_change = (forecast_level - current_level) / current_level * 100
    summary.append((brand_name, round(current_level, 1), round(forecast_level, 1), round(pct_change, 1)))

combined = pd.concat(all_rows, ignore_index=True)
combined["date_id"] = combined["full_date"].dt.strftime("%Y%m%d").astype(int)
combined = combined[["date_id", "full_date", "brand_name", "search_index", "type"]]
combined.to_csv(OUTPUT_PATH, index=False)

print(f"Saved {len(combined)} rows to {OUTPUT_PATH}\n")
print(f"{'Brand':<10}{'Recent avg':<14}{'Forecast avg (6mo)':<22}{'% change':<10}")
for brand_name, cur, fc, pct in summary:
    print(f"{brand_name:<10}{cur:<14}{fc:<22}{pct:+.1f}%")
