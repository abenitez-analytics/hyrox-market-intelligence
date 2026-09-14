# HYROX: Reading the Growth, the Money, and the Risk

## A Competitive & Financial Intelligence Study of the Hybrid Fitness Market

`Python` `SQL` `Microsoft Fabric` `Power BI` `Machine Learning`

---

## 📌 Executive Summary

This project investigates a fast-moving business question: how did a fitness competition founded in 2017 grow into a company reportedly valued at ~€850M, in active acquisition talks with LVMH's L Catterton — and how does it stack up against both legacy competitors (CrossFit) and newly-funded challengers (XENOM, ATHX Games)?

Rather than relying on press-release narrative, this builds an end-to-end pipeline — real (not simulated) data collection, a Microsoft Fabric Lakehouse/Warehouse architecture, two machine learning models, and a Power BI report — to answer why HYROX is growing, how it monetizes, and what its 2026 expansion strategy actually reveals about market saturation and capacity.

---

## ⚙️ Core Architecture & Data Pipeline

The pipeline runs as a four-stage loop:

1. **Data Collection Engine (Python)**: collects real search-interest trends (Google Trends), news-mention volume (GDELT 2.0 Doc API), and the full 2026 event calendar (web scraping), each with rate-limit handling and source-quality validation built in — not simulated data.
2. **Lakehouse Landing Layer (Microsoft Fabric)**: raw collected data lands as Bronze-tier Delta tables, kept separate from curated data until validated.
3. **Warehouse Star Schema (T-SQL)**: a dimensional model (`dim_date`, `dim_brand`, `dim_city` + `fact_event`, `fact_trends`, `fact_financials`) built with referential-integrity checks, non-recursive date-spine generation (Fabric Warehouse doesn't support recursive CTEs), and a reusable data-quality diagnostic script.
4. **ML & Semantic Layer**: a Holt-Winters exponential smoothing model forecasts brand search-trend trajectory; a K-means clustering model segments the 121-event 2026 calendar by market maturity. Both outputs land as Gold-tier tables, consumed by a Power BI report via a Direct Lake on SQL semantic model.

---

## 📊 Key Findings & Core Measures

- **Search interest has already flipped**: HYROX now leads CrossFit in search volume, forecast **+10.4%** over 6 months vs. CrossFit's **-5.7%**
- **Media coverage lags the trend reversal**: CrossFit still leads on raw news mentions (408 vs. HYROX's 235)
- **Not all competitors are equally real**: XENOM shows zero measurable search volume and minimal news coverage — a funded idea, not yet a market presence, in clear contrast to Adidas-backed ATHX Games
- **Expansion is three distinct strategies at once**: K-means clustering of the 121-event calendar reveals 60 active/near-term events, 40 standalone single-city tests, and 21 events in aggressive multi-city pushes (notably China)

## Core DAX Measures Implemented:

```dax
Revenue (EUR M) =
CALCULATE(
    SUM(fact_financials[revenue_eur_million]),
    fact_financials[fiscal_year] = MAX(fact_financials[fiscal_year])
)

Growth vs Prior Data Point % =
VAR CurrentYear = SELECTEDVALUE(fact_financials[fiscal_year])
VAR CurrentRev = SUM(fact_financials[revenue_eur_million])
VAR PriorYear =
    CALCULATE(MAX(fact_financials[fiscal_year]), ALLSELECTED(fact_financials),
        fact_financials[fiscal_year] < CurrentYear)
VAR PriorRev =
    CALCULATE(SUM(fact_financials[revenue_eur_million]), ALLSELECTED(fact_financials),
        fact_financials[fiscal_year] = PriorYear)
RETURN DIVIDE(CurrentRev - PriorRev, PriorRev)

Sold Out Rate % =
DIVIDE([Sold Out Events], [Total Events])

Events per Cluster =
COUNTROWS(gold_city_clusters)
```

---

## Data sources — and their honest limitations

| Source | Provides | Limitation |
|---|---|---|
| Google Trends (manual export) | 5-year weekly search interest | `pytrends` API proved unreliable (persistent 429s); switched to manual export — a deliberate call, not a workaround |
| GDELT 2.0 Doc API | Daily news-mention volume | Free/keyless but strictly rate-limited; XENOM mention backfill still pending |
| roxupdates.com → gowod.app | 2026 event calendar | First source was missing all of Q1 2026; rebuilt from a more complete source (121 events vs. original 72) after catching the gap |
| Press estimates | Revenue, EBITDA, valuation | No company discloses these directly — every figure is source-tagged, not presented as fact |

## What I'd add next

- XENOM news-mention backfill (rate-limit-throttled, pending an isolated run)
- Real per-city ticket pricing (source identified, not yet integrated)
- City coordinates for a true geographic map visual
