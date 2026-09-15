-- ============================================================
-- Populate fact_trends by FULL OUTER JOINing the two Bronze sources
-- on (date_id, brand_name) -- a date/brand may have search data,
-- news data, both, or (for XENOM, pending its backfill) neither yet.
--
-- ADJUST CROSS-DATABASE REFERENCES if needed, same as fact_event.
-- ============================================================

INSERT INTO fact_trends (date_id, brand_id, search_index, social_mentions, news_mentions, sentiment_score)
SELECT
    COALESCE(t.date_id, n.date_id)         AS date_id,
    br.brand_id,
    t.search_index,
    NULL                                    AS social_mentions,  -- not collected yet
    n.news_mentions,
    NULL                                    AS sentiment_score   -- Phase 4 (ML layer)
FROM bronze_trends t
FULL OUTER JOIN bronze_news_mentions n
    ON t.date_id = n.date_id AND t.brand_name = n.brand_name
INNER JOIN dim_brand br
    ON br.brand_name = COALESCE(t.brand_name, n.brand_name);

-- Validation: row counts per brand, and confirm every date_id resolves in dim_date
SELECT
    br.brand_name,
    COUNT(*) AS rows,
    SUM(CASE WHEN ft.search_index IS NOT NULL THEN 1 ELSE 0 END) AS rows_with_search,
    SUM(CASE WHEN ft.news_mentions IS NOT NULL THEN 1 ELSE 0 END) AS rows_with_news
FROM fact_trends ft
JOIN dim_brand br ON br.brand_id = ft.brand_id
GROUP BY br.brand_name
ORDER BY br.brand_name;
