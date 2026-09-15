-- ============================================================
-- Populate dim_date: a standard date spine, 2020-01-01 to 2027-12-31
-- Covers Trends history (5y back) through the full 2026 event calendar
-- Run this in your Fabric Warehouse (T-SQL)
--
-- NOTE: Fabric Warehouse does NOT support recursive CTEs (confirmed
-- platform limitation, not just a preview gap). This uses the standard
-- non-recursive workaround: build a "numbers" set via cross-joined
-- small VALUES lists, then DATEADD off a base date.
-- ============================================================

WITH E1(n) AS (
    SELECT n FROM (VALUES (1),(1),(1),(1),(1),(1),(1),(1),(1),(1)) AS t(n)  -- 10 rows
),
E2(n) AS (SELECT 1 FROM E1 a CROSS JOIN E1 b),        -- 100 rows
E4(n) AS (SELECT 1 FROM E2 a CROSS JOIN E2 b),        -- 10,000 rows
Numbers AS (
    SELECT ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
    FROM E4
),
date_spine AS (
    SELECT DATEADD(DAY, n, CAST('2020-01-01' AS DATE)) AS full_date
    FROM Numbers
    WHERE n <= DATEDIFF(DAY, '2020-01-01', '2027-12-31')
)
INSERT INTO dim_date (date_id, full_date, year, quarter, month, month_name, week_of_year, day_of_week, is_weekend)
SELECT
    CAST(FORMAT(full_date, 'yyyyMMdd') AS INT)                AS date_id,
    full_date,
    YEAR(full_date)                                            AS year,
    DATEPART(QUARTER, full_date)                               AS quarter,
    MONTH(full_date)                                           AS month,
    DATENAME(MONTH, full_date)                                 AS month_name,
    DATEPART(WEEK, full_date)                                  AS week_of_year,
    DATENAME(WEEKDAY, full_date)                                AS day_of_week,
    CASE WHEN DATENAME(WEEKDAY, full_date) IN ('Saturday','Sunday') THEN 1 ELSE 0 END AS is_weekend
FROM date_spine;

-- Sanity check
SELECT COUNT(*) AS total_dates, MIN(full_date) AS earliest, MAX(full_date) AS latest
FROM dim_date;

