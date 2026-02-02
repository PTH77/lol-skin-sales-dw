-- Liczność tabel
SELECT
    'dim_date' as tabela,
    COUNT(*) as liczba_wierszy,
    MIN(d.date) as min_data,
    MAX(d.date) as max_data
FROM gold.dim_date d
UNION ALL
SELECT
    'dim_skin',
    COUNT(*),
    NULL,
    NULL
FROM gold.dim_skin
UNION ALL
SELECT
    'dim_player',
    COUNT(*),
    NULL,
    NULL
FROM gold.dim_player
UNION ALL
SELECT
    'fact_sales',
    COUNT(*),
    NULL,
    NULL
FROM gold.fact_sales;

-- Revenue po segmentach
SELECT
    p.player_segment,
    COUNT(*) as transakcje,
    SUM(f.total_rp) as total_revenue,
    ROUND(AVG(f.total_rp), 2) as avg_transaction,
    ROUND(100.0 * SUM(f.total_rp) / SUM(SUM(f.total_rp)) OVER (), 2) as revenue_pct
FROM gold.fact_sales f
JOIN gold.dim_player p ON f.player_key = p.player_key
GROUP BY p.player_segment
ORDER BY total_revenue DESC;

-- Top 10 skinów
SELECT
    v.champion_name,
    v.skin_name,
    v.rarity,
    v.times_purchased,
    v.total_revenue
FROM gold.top_selling_skins v
LIMIT 10;

-- Trend miesięczny (ostatnie 6 miesięcy)
SELECT
    v.year,
    v.month_name,
    v.transactions,
    v.revenue,
    v.active_players,
    v.revenue_per_player
FROM gold.revenue_trends v
ORDER BY v.year DESC, v.month DESC
LIMIT 6;

-- Porównanie weekend vs weekday
SELECT
    v.day_type,
    v.transaction_count,
    v.total_revenue,
    v.avg_transaction
FROM gold.weekend_vs_weekday_sales v;

-- Top 10 graczy (biggest spenders)
SELECT
    v.player_id,
    v.player_segment,
    v.region,
    v.total_purchases,
    v.lifetime_value,
    v.avg_purchase_value
FROM gold.player_lifetime_value v
LIMIT 10;

-- Rozkład rarity w sprzedaży
SELECT 
    s.rarity,
    COUNT(*) as sprzedane,
    SUM(f.total_rp) as revenue,
    ROUND(AVG(f.total_rp), 2) as avg_price
FROM gold.fact_sales f
JOIN gold.dim_skin s ON f.skin_key = s.skin_key
GROUP BY s.rarity
ORDER BY revenue DESC;

-- Sprzedaż po regionach
SELECT 
    p.region,
    COUNT(*) as transakcje,
    SUM(f.total_rp) as revenue,
    COUNT(DISTINCT f.player_key) as gracze
FROM gold.fact_sales f
JOIN gold.dim_player p ON f.player_key = p.player_key
GROUP BY p.region
ORDER BY revenue DESC;