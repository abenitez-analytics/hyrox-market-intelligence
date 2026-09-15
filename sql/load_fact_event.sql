-- ============================================================
-- 1. Small schema evolution: the original fact_event DDL didn't
--    anticipate registration status (only a sold_out boolean) or
--    raw venue text (since dim_venue isn't populated). Adding both
--    rather than losing real signal from the scraped data.
-- ============================================================

ALTER TABLE fact_event ADD registration_status VARCHAR(50) NULL;
ALTER TABLE fact_event ADD venue_name_raw VARCHAR(255) NULL;

-- ============================================================
-- 2. Populate fact_event from bronze_hyrox_events, joining to
--    dim_city, dim_brand, dim_date.
--
--    WITH CROSS-DATABASE REFERENCE:
-- ============================================================

INSERT INTO fact_event (
    event_id, date_id, brand_id, city_id, venue_id,
    participants_registered, venue_capacity, sold_out_flag,
    registration_status, venue_name_raw
)
SELECT
    ROW_NUMBER() OVER (ORDER BY b.city, b.start_date) AS event_id,
    CAST(FORMAT(b.start_date, 'yyyyMMdd') AS INT)      AS date_id,
    br.brand_id,
    c.city_id,
    NULL                                                 AS venue_id,       -- dim_venue not built yet
    NULL                                                 AS participants_registered,  -- not available from this source
    NULL                                                 AS venue_capacity,           -- not available from this source
    b.sold_out_flag,
    b.status                                              AS registration_status,
    b.venue                                               AS venue_name_raw
FROM hyrox_lakehouse.dbo.bronze_hyrox_events_v2 b
LEFT JOIN dim_brand br ON br.brand_name = b.brand_name
LEFT JOIN dim_city  c  ON c.city_name   = b.city
LEFT JOIN dim_date  d  ON d.date_id     = CAST(FORMAT(b.start_date, 'yyyyMMdd') AS INT);

-- ============================================================
-- 3. VALIDATION -- 
-- ============================================================
SELECT
    COUNT(*)                                              AS total_rows,
    SUM(CASE WHEN city_id IS NULL THEN 1 ELSE 0 END)       AS unmatched_city,
    SUM(CASE WHEN brand_id IS NULL THEN 1 ELSE 0 END)      AS unmatched_brand,
    SUM(CASE WHEN date_id NOT IN (SELECT date_id FROM dim_date) THEN 1 ELSE 0 END) AS unmatched_date
FROM fact_event;

-- If unmatched_city > 0, find exactly which cities failed to match:
SELECT DISTINCT b.city
FROM hyrox_lakehouse.dbo.bronze_hyrox_events_v2 b
LEFT JOIN dim_city c ON c.city_name = b.city
WHERE c.city_id IS NULL;
