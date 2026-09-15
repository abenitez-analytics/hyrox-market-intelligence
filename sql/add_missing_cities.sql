-- Three cities I missed adding to dim_city when compiling the "new cities" list --
-- they were correctly parsed from the event data, just never inserted here.

INSERT INTO dim_city (city_id, city_name, country, region) VALUES
(103, 'İzmir', 'Turkey', 'Europe'),
(104, 'Bangkok', 'Thailand', 'APAC'),
(105, 'Sanya', 'China', 'APAC');

-- Confirm no more gaps before retrying the fact_event load
SELECT DISTINCT b.city
FROM bronze_hyrox_events_v2 b
LEFT JOIN dim_city c ON c.city_name = b.city
WHERE c.city_id IS NULL;
