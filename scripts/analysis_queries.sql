-- WINNOW analysis queries against data/winnow.db
-- Run: sqlite3 data/winnow.db < scripts/analysis_queries.sql

-- ── 1. GCC market structure: 5-year average import value ─────────────────────
SELECT
    reporter,
    ROUND(AVG(total_value) / 1e6, 2)   AS avg_value_musd,
    ROUND(AVG(total_value) / 1e6 /
          (SELECT SUM(total_value)/1e6/COUNT(DISTINCT year)
           FROM annual_summary) * 100, 1) AS share_pct
FROM annual_summary
WHERE year BETWEEN 2019 AND 2023
GROUP BY reporter
ORDER BY avg_value_musd DESC;

-- ── 2. UAE demand trend 2016-2023 (total vs adjusted) ────────────────────────
SELECT
    year,
    ROUND(total_value / 1e6, 2)          AS total_musd,
    ROUND(uae_adjusted_value / 1e6, 2)   AS adjusted_musd,
    ROUND((total_value - COALESCE(uae_adjusted_value, total_value))
          / total_value * 100, 1)         AS reexport_pct
FROM annual_summary
WHERE reporter = 'UAE'
ORDER BY year;

-- ── 3. UAE vs Saudi Arabia divergence ────────────────────────────────────────
SELECT
    s_uae.year,
    ROUND(s_uae.total_value / 1e6, 2)  AS uae_musd,
    ROUND(s_sau.total_value / 1e6, 2)  AS sau_musd,
    ROUND((s_uae.total_value - s_sau.total_value) / 1e6, 2) AS uae_minus_sau
FROM annual_summary s_uae
JOIN annual_summary s_sau ON s_uae.year = s_sau.year
WHERE s_uae.reporter = 'UAE' AND s_sau.reporter = 'SAU'
ORDER BY s_uae.year;

-- ── 4. India APEDA exports to GCC: volume and unit price by destination ───────
SELECT
    country_iso3,
    fiscal_year,
    ROUND(value_usd)       AS value_usd,
    ROUND(qty_mt, 1)       AS qty_mt,
    ROUND(unit_price, 4)   AS usd_per_kg
FROM apeda_exports
WHERE country_iso3 IS NOT NULL
ORDER BY country_iso3, fiscal_year;

-- ── 5. FY2023-24 unit price ranking (Kuwait ceiling vs Oman floor) ────────────
SELECT
    country_iso3,
    ROUND(unit_price, 4)                     AS usd_per_kg,
    ROUND(qty_mt)                            AS qty_mt,
    ROUND(unit_price / 0.4406 * 100, 1)     AS pct_of_kuwait_ceiling
FROM apeda_exports
WHERE fiscal_year = '2023-24' AND country_iso3 IS NOT NULL
ORDER BY unit_price DESC;

-- ── 6. India share: APEDA FY2023-24 vs Comtrade 2023 ─────────────────────────
SELECT
    a.country_iso3,
    ROUND(a.value_usd)                            AS apeda_usd,
    ROUND(t.total_value)                          AS comtrade_usd,
    ROUND(a.value_usd / t.total_value * 100, 1)  AS india_share_pct
FROM apeda_exports a
JOIN annual_summary t
  ON a.country_iso3 = t.reporter AND t.year = 2023
WHERE a.fiscal_year = '2023-24' AND a.country_iso3 IS NOT NULL
ORDER BY apeda_usd DESC;

-- ── 7. India GCC export totals by fiscal year ─────────────────────────────────
SELECT
    fiscal_year,
    ROUND(SUM(qty_mt))    AS total_mt,
    ROUND(SUM(value_usd)) AS total_usd
FROM apeda_exports
WHERE country_iso3 IS NOT NULL
GROUP BY fiscal_year
ORDER BY fiscal_year;
