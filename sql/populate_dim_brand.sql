-- ============================================================
-- Populate dim_brand -- static reference data based on project research
-- ============================================================

INSERT INTO dim_brand (brand_id, brand_name, founded_year, parent_owner, format_type, primary_sponsor)
VALUES
    (1, 'HYROX',      2017, 'Infront Sports & Media (Wanda Group); L Catterton/LVMH stake talks ongoing 2026', 'mass-participation', 'Amazfit (wearables, exclusive)'),
    (2, 'XENOM',       2025, 'Independent, $15M funding round',                                                 'elite-competitive',  NULL),
    (3, 'ATHX Games',  2025, 'Adidas-backed',                                                                    'hybrid',             'Adidas'),
    (4, 'CrossFit',    2000, 'Independent',                                                                      'elite-competitive',  NULL);

-- Sanity check
SELECT * FROM dim_brand ORDER BY brand_id;
