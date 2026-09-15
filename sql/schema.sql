-- ============================================================
-- — Star Schema
-- Microsoft Fabric Warehouse
-- ============================================================

-- ---------- DIMENSION TABLES ----------

CREATE TABLE dim_date (
    date_id         INTEGER PRIMARY KEY,   -- format YYYYMMDD
    full_date       DATE NOT NULL,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      VARCHAR(20) NOT NULL,
    week_of_year    INTEGER NOT NULL,
    day_of_week     VARCHAR(10) NOT NULL,
    is_weekend      BOOLEAN NOT NULL
);

CREATE TABLE dim_brand (
    brand_id        INTEGER PRIMARY KEY,
    brand_name      VARCHAR(50) NOT NULL,      -- HYROX, XENOM, ATHX Games, CrossFit, Deka Fit, METRIX
    founded_year    INTEGER,
    parent_owner    VARCHAR(100),              -- e.g. Infront Sports & Media, Adidas-backed, independent
    format_type     VARCHAR(50),               -- mass-participation / elite-competitive / hybrid
    primary_sponsor VARCHAR(100)
);

CREATE TABLE dim_city (
    city_id         INTEGER PRIMARY KEY,
    city_name       VARCHAR(100) NOT NULL,
    country         VARCHAR(100) NOT NULL,
    region          VARCHAR(50),               -- Europe, North America, APAC, etc.
    population      BIGINT,
    latitude        DECIMAL(9,6),
    longitude       DECIMAL(9,6)
);

CREATE TABLE dim_venue (
    venue_id        INTEGER PRIMARY KEY,
    city_id         INTEGER NOT NULL REFERENCES dim_city(city_id),
    venue_name      VARCHAR(150),
    max_capacity    INTEGER,                   -- hard cap per wave/day, drives crowding analysis
    venue_type      VARCHAR(50)                -- exhibition hall, arena, outdoor
);

-- ---------- FACT TABLES ----------

-- One row per event (a brand's competition in a city on a date)
CREATE TABLE fact_event (
    event_id                BIGINT PRIMARY KEY,
    date_id                 INTEGER NOT NULL REFERENCES dim_date(date_id),
    brand_id                INTEGER NOT NULL REFERENCES dim_brand(brand_id),
    city_id                 INTEGER NOT NULL REFERENCES dim_city(city_id),
    venue_id                INTEGER REFERENCES dim_venue(venue_id),
    division                VARCHAR(50),        -- Open, Pro, Doubles, Relay, etc.
    participants_registered INTEGER,
    venue_capacity           INTEGER,
    sold_out_flag            BOOLEAN,
    hours_to_sell_out        DECIMAL(6,2),      -- key crowding/demand metric
    avg_ticket_price_eur     DECIMAL(8,2),
    spectator_tickets_sold   INTEGER
);

-- One row per brand per date: search & social interest (proxy for "free" marketing/virality)
CREATE TABLE fact_trends (
    date_id             INTEGER NOT NULL REFERENCES dim_date(date_id),
    brand_id            INTEGER NOT NULL REFERENCES dim_brand(brand_id),
    search_index        DECIMAL(6,2),   -- normalized Google Trends value 0-100
    social_mentions     INTEGER,
    news_mentions       INTEGER,
    sentiment_score     DECIMAL(4,3),   -- -1 (negative) to 1 (positive)
    PRIMARY KEY (date_id, brand_id)
);

-- One row per brand per fiscal year: published/estimated company financials
CREATE TABLE fact_financials (
    fiscal_year         INTEGER NOT NULL,
    brand_id            INTEGER NOT NULL REFERENCES dim_brand(brand_id),
    revenue_eur_million  DECIMAL(10,2),
    ebitda_eur_million   DECIMAL(10,2),
    total_participants   INTEGER,
    cities_active        INTEGER,
    valuation_eur_million DECIMAL(10,2),
    source_note          VARCHAR(255),   -- cite the article/estimate source
    PRIMARY KEY (fiscal_year, brand_id)
);

