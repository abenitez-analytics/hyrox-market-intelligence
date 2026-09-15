-- Direct Lake on SQL doesn't support calculated columns in the semantic
-- model layer -- this logic has to live in the Warehouse table itself.

ALTER TABLE gold_search_forecast ADD series VARCHAR(60);

UPDATE gold_search_forecast
SET series = brand_name + ' (' + type + ')';

-- Confirm exactly 4 distinct values: HYROX (actual), HYROX (forecast),
-- CrossFit (actual), CrossFit (forecast)
SELECT DISTINCT series FROM gold_search_forecast;
