-- ============================================================
-- Gold layer: ML model outputs, ready for direct Power BI use
-- ============================================================

CREATE TABLE gold_search_forecast (
    date_id       INTEGER,
    full_date     DATE,
    brand_name    VARCHAR(50),
    search_index  DECIMAL(6,2),
    type          VARCHAR(20)   -- 'actual' or 'forecast'
);

CREATE TABLE gold_city_clusters (
    event_id             BIGINT,
    city_name             VARCHAR(100),
    country               VARCHAR(100),
    region                VARCHAR(50),
    registration_status   VARCHAR(50),
    events_in_country     INTEGER,
    full_date             DATE,
    cluster               INTEGER,
    cluster_label         VARCHAR(100)
);

-- After uploading forecast_output.csv and city_clusters.csv to
-- Files/gold/ in the Lakehouse and loading them there as Delta
-- tables named staging_forecast / staging_city_clusters we
-- pull them into the Warehouse:

INSERT INTO gold_search_forecast
SELECT date_id, full_date, brand_name, search_index, type
FROM staging_forecast;   -- adjust to LakehouseName.dbo.staging_forecast if needed

INSERT INTO gold_city_clusters
SELECT event_id, city_name, country, region, registration_status,
       events_in_country, full_date, cluster, cluster_label
FROM staging_city_clusters;  -- adjust cross-database reference if needed

-- Sanity checks
SELECT type, COUNT(*) FROM gold_search_forecast GROUP BY type;
SELECT cluster_label, COUNT(*) FROM gold_city_clusters GROUP BY cluster_label;
