-- Statystyki tabel
SELECT
    'dim_date' as tabela,
    COUNT(*) as wiersze
FROM silver.dim_date
UNION ALL
SELECT 'dim_skin', COUNT(*) FROM silver.dim_skin
UNION ALL
SELECT 'dim_player', COUNT(*) FROM silver.dim_player
UNION ALL
SELECT 'fact_sale', COUNT(*) FROM silver.fact_sale
UNION ALL
SELECT 'fact_sale_quarantine', COUNT(*) FROM silver.fact_sale_quarantine
UNION ALL
SELECT 'data_quality_log', COUNT(*) FROM silver.data_quality_log;

-- Jakość danych - fact_sale
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE f.is_valid = TRUE) as valid,
    COUNT(*) FILTER (WHERE f.is_valid = FALSE) as invalid,
    ROUND(COUNT(*) FILTER (WHERE f.is_valid = FALSE)::NUMERIC / COUNT(*) * 100, 2) as invalid_pct
FROM silver.fact_sale f;

-- Logi DQ - podsumowanie
SELECT
    l.issue_type,
    l.issue_count,
    l.issue_pct,
    l.alert_triggered,
    l.run_timestamp
FROM silver.data_quality_log l
ORDER BY l.issue_pct DESC;

-- Alerty (przekroczone progi)
SELECT
    l.issue_type,
    l.issue_count,
    l.issue_pct,
    l.threshold_pct
FROM silver.data_quality_log l
WHERE l.alert_triggered = TRUE
ORDER BY l.issue_pct DESC;

-- Kwarantanna - rozkład błędów
SELECT
    q.rejection_reason,
    COUNT(*) as count,
    ROUND(COUNT(*)::NUMERIC * 100 / SUM(COUNT(*)) OVER (), 2) as pct
FROM silver.fact_sale_quarantine q
GROUP BY q.rejection_reason
ORDER BY count DESC
LIMIT 10;

-- Przykłady błędnych rekordów
SELECT
    q.transaction_id,
    q.player_id,
    q.skin_id,
    q.price_rp,
    q.quantity,
    q.rejection_reason
FROM silver.fact_sale_quarantine q
LIMIT 20;

-- Rozkład rarity w dim_skin
SELECT
    s.rarity,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE s.is_valid = TRUE) as valid,
    COUNT(*) FILTER (WHERE s.is_valid = FALSE) as invalid
FROM silver.dim_skin s
GROUP BY s.rarity
ORDER BY count DESC;

-- Rozkład segmentów graczy
SELECT
    p.player_segment,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE p.is_valid = TRUE) as valid
FROM silver.dim_player p
GROUP BY p.player_segment
ORDER BY count DESC;

-- Rozkład regionów
SELECT
    p.region,
    COUNT(*) as count
FROM silver.dim_player p
WHERE p.is_valid = TRUE
GROUP BY p.region
ORDER BY count DESC;