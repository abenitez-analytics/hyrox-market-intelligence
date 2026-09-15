-- ============================================================
-- 1. Add the 30 newly-discovered cities to dim_city
--    (continuing city_id numbering from 73)
-- ============================================================
INSERT INTO dim_city (city_id, city_name, country, region) VALUES
(73, 'St. Gallen', 'Switzerland', 'Europe'),
(74, 'Manchester', 'United Kingdom', 'Europe'),
(75, 'Amsterdam', 'Netherlands', 'Europe'),
(76, 'Auckland', 'New Zealand', 'APAC'),
(77, 'Phoenix', 'USA', 'North America'),
(78, 'Osaka', 'Japan', 'APAC'),
(79, 'Turin', 'Italy', 'Europe'),
(80, 'Vienna', 'Austria', 'Europe'),
(81, 'Guadalajara', 'Mexico', 'North America'),
(82, 'Bilbao', 'Spain', 'Europe'),
(83, 'Las Vegas', 'USA', 'North America'),
(84, 'Katowice', 'Poland', 'Europe'),
(85, 'Fortaleza', 'Brazil', 'South America'),
(86, 'Taipei', 'Taiwan', 'APAC'),
(87, 'Glasgow', 'United Kingdom', 'Europe'),
(88, 'Copenhagen', 'Denmark', 'Europe'),
(89, 'Cancún', 'Mexico', 'North America'),
(90, 'Toulouse', 'France', 'Europe'),
(91, 'Houston', 'USA', 'North America'),
(92, 'Mechelen', 'Belgium', 'Europe'),
(93, 'Singapore', 'Singapore', 'APAC'),
(94, 'Miami Beach', 'USA', 'North America'),
(95, 'Bologna', 'Italy', 'Europe'),
(96, 'Bengaluru', 'India', 'APAC'),
(97, 'Wuhan', 'China', 'APAC'),
(98, 'Perth', 'Australia', 'APAC'),
(99, 'Athens', 'Greece', 'Europe'),
(100, 'Cairo', 'Egypt', 'Africa'),
(101, 'Kuala Lumpur', 'Malaysia', 'APAC'),
(102, 'Melbourne', 'Australia', 'APAC');

-- ============================================================
-- 2. Wipe the old, incomplete fact_event and reload from the
--    corrected, full-year dataset (bronze_hyrox_events_v2).
--  
-- ============================================================

TRUNCATE TABLE fact_event;

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
    NULL,
    NULL,
    NULL,
    b.sold_out_flag,
    b.registration_status,
    NULL AS venue_name_raw   -- venue data isn't reliably available from this source
FROM hyrox_lakehouse.dbo.bronze_hyrox_events_v2 b
LEFT JOIN dim_brand br ON br.brand_name = b.brand_name
LEFT JOIN dim_city  c  ON c.city_name   = b.city;

-- ============================================================
-- 3. Validation -- 
-- ============================================================
SELECT
    COUNT(*)                                              AS total_rows,
    SUM(CASE WHEN city_id IS NULL THEN 1 ELSE 0 END)       AS unmatched_city,
    SUM(CASE WHEN brand_id IS NULL THEN 1 ELSE 0 END)      AS unmatched_brand
FROM fact_event;

SELECT DISTINCT b.city
FROM hyrox_lakehouse.dbo.bronze_hyrox_events_v2 b
LEFT JOIN dim_city c ON c.city_name = b.city
WHERE c.city_id IS NULL;

SELECT COUNT(*) AS total_events, COUNT(DISTINCT city_id) AS unique_cities FROM fact_event;
