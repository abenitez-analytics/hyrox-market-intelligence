"""
cluster_cities.py
--------------------
Phase 4 -- ML layer, part 2: cluster HYROX's 72 scheduled events by
"market maturity / saturation" to support the capacity-and-crowding
narrative -- distinguishing established, high-density markets from
early-stage expansion markets.

Honest note on features: we don't have participant counts or venue
capacity (not available from the scraped source), so this can't be a
literal "sold-out speed" model. Instead it clusters on what we DO have:
registration status (a real proxy for demand urgency) and how many
other HYROX events share the same country (a real proxy for market
saturation). That's a legitimate, defensible clustering -- just be
clear in your write-up about what it is and isn't measuring.

Input: fact_events.csv (as exported from the Fabric Warehouse)
Output: city_clusters.csv -- cluster assignment + label per event.
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

INPUT_PATH = "fact_events.csv"
OUTPUT_PATH = "city_clusters.csv"

STATUS_RANK = {
    "Sold Out": 5, "Past": 4, "On Sale": 3, "Coming Soon": 2,
    "Not Yet Announced": 1, "Scheduled": 1,  # "Scheduled" = confirmed but no finer detail known; treat like "Not Yet Announced"
}

df = pd.read_csv(INPUT_PATH, na_values=["NULL"])
df["full_date"] = pd.to_datetime(df["date_id"], format="%Y%m%d")
df["status_rank"] = df["registration_status"].map(STATUS_RANK)
if df["status_rank"].isna().any():
    unmapped = df.loc[df["status_rank"].isna(), "registration_status"].unique()
    print(f"WARNING: unmapped registration_status values found: {list(unmapped)} -- defaulting to rank 1")
    df["status_rank"] = df["status_rank"].fillna(1)
df["month"] = df["full_date"].dt.month

# Market saturation proxy: how many other HYROX events are in the same country
country_counts = df.groupby("country")["event_id"].transform("count")
df["events_in_country"] = country_counts

features = df[["status_rank", "events_in_country", "month"]].copy()
scaled = StandardScaler().fit_transform(features)

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(scaled)

# Label clusters by their ACTUAL two-factor profile, not just density sorted --
# a naive density-only sort mislabels the China expansion cluster (high density,
# but LOW status_rank since they're simultaneous future launches, not
# long-established markets) as "saturated," which would be misleading.
cluster_profile = df.groupby("cluster")[["status_rank", "events_in_country"]].mean()

def label_cluster(row):
    if row["status_rank"] >= 3.0:
        return "Active / Near-Term Markets"          # already on sale, sold out, or already happened
    elif row["events_in_country"] >= 6:
        return "Multi-City Expansion Push (early stage)"  # many simultaneous cities, mostly unannounced yet
    else:
        return "Standalone Early-Stage Markets"       # single/few cities in-country, not yet urgent

cluster_label_map = {cid: label_cluster(row) for cid, row in cluster_profile.iterrows()}
df["cluster_label"] = df["cluster"].map(cluster_label_map)
labels_in_order = list(cluster_profile.index.map(cluster_label_map))

output = df[[
    "event_id", "city_name", "country", "region", "registration_status",
    "events_in_country", "full_date", "cluster", "cluster_label",
]].sort_values(["cluster", "country", "city_name"])

output.to_csv(OUTPUT_PATH, index=False)

print(f"Saved {len(output)} rows to {OUTPUT_PATH}\n")
print("Cluster sizes and profile:")
print(df.groupby("cluster_label")[["status_rank", "events_in_country"]].agg(["mean", "count"]))
print("\nSample cities per cluster:")
for label in labels_in_order:
    sample = df[df["cluster_label"] == label]["city_name"].head(6).tolist()
    print(f"  {label}: {sample}")