-- ============================================================
-- Populate fact_financials -- HYROX only, since it's the only brand
-- with published revenue/valuation estimates. XENOM, ATHX Games, and
-- CrossFit are private and haven't disclosed comparable figures.
--
-- Every number here is a press ESTIMATE, not audited disclosure --
-- that's why source_note exists on every row. 
-- ============================================================

INSERT INTO fact_financials (
    fiscal_year, brand_id, revenue_eur_million, ebitda_eur_million,
    total_participants, cities_active, valuation_eur_million, source_note
)
SELECT v.fiscal_year, br.brand_id, v.revenue_eur_million, v.ebitda_eur_million,
       v.total_participants, v.cities_active, v.valuation_eur_million, v.source_note
FROM dim_brand br
CROSS JOIN (VALUES
    (2023, 40.0,  NULL, NULL,    NULL, NULL,
     'Press estimate: revenue ~€40M, cited as the base year for 2025''s ~87% growth figure'),
    (2025, 135.0, 30.0, NULL,    NULL, NULL,
     'Press estimate: revenue €130-140M (midpoint used), EBITDA ~€30M (~20% margin)'),
    (2026, 235.0, NULL, 1300000, 34,   850.0,
     'Press estimate: 2026 revenue projection €200-270M (midpoint used); 1.3M+ participants across 34 cities; L Catterton/LVMH stake-talk valuation range €700M-1B (midpoint used)')
) AS v(fiscal_year, revenue_eur_million, ebitda_eur_million, total_participants, cities_active, valuation_eur_million, source_note)
WHERE br.brand_name = 'HYROX';

-- Sanity check
SELECT * FROM fact_financials ORDER BY fiscal_year;
