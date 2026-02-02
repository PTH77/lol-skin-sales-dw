-- GOLD VIEWS - Widoki analityczne

-- Revenue po segmentach i miesiącach
CREATE OR REPLACE VIEW gold.revenue_by_segment_month AS
SELECT 
    p.player_segment,
    d.year,
    d.month,
    d.month_name,
    COUNT(*) as transaction_count,
    SUM(f.total_rp) as total_revenue,
    AVG(f.total_rp) as avg_transaction,
    COUNT(DISTINCT f.player_key) as unique_players
FROM gold.fact_sales f
JOIN gold.dim_player p ON f.player_key = p.player_key
JOIN gold.dim_date d ON f.date_key = d.date_key
GROUP BY p.player_segment, d.year, d.month, d.month_name
ORDER BY d.year, d.month, p.player_segment;

COMMENT ON VIEW gold.revenue_by_segment_month IS 'Revenue miesięczny po segmentach';

-- Top skiny
CREATE OR REPLACE VIEW gold.top_selling_skins AS
SELECT 
    s.skin_id,
    s.champion_name,
    s.skin_name,
    s.rarity,
    s.price_rp,
    COUNT(*) as times_purchased,
    SUM(f.total_rp) as total_revenue,
    COUNT(DISTINCT f.player_key) as unique_buyers
FROM gold.fact_sales f
JOIN gold.dim_skin s ON f.skin_key = s.skin_key
GROUP BY s.skin_id, s.champion_name, s.skin_name, s.rarity, s.price_rp
ORDER BY total_revenue DESC;

COMMENT ON VIEW gold.top_selling_skins IS 'Najpopularniejsze skiny według revenue';

-- Weekend vs Weekday
CREATE OR REPLACE VIEW gold.weekend_vs_weekday_sales AS
SELECT 
    CASE 
        WHEN d.is_weekend = TRUE THEN 'Weekend'
        ELSE 'Weekday'
    END as day_type,
    COUNT(*) as transaction_count,
    SUM(f.total_rp) as total_revenue,
    AVG(f.total_rp) as avg_transaction
FROM gold.fact_sales f
JOIN gold.dim_date d ON f.date_key = d.date_key
GROUP BY d.is_weekend
ORDER BY day_type;

COMMENT ON VIEW gold.weekend_vs_weekday_sales IS 'Porównanie weekend vs dzień roboczy';

-- Lifetime Value graczy
CREATE OR REPLACE VIEW gold.player_lifetime_value AS
SELECT 
    p.player_key,
    p.player_id,
    p.player_segment,
    p.region,
    COUNT(*) as total_purchases,
    SUM(f.total_rp) as lifetime_value,
    AVG(f.total_rp) as avg_purchase_value,
    MIN(d.date) as first_purchase_date,
    MAX(d.date) as last_purchase_date,
    MAX(d.date) - MIN(d.date) as purchase_span_days
FROM gold.fact_sales f
JOIN gold.dim_player p ON f.player_key = p.player_key
JOIN gold.dim_date d ON f.date_key = d.date_key
GROUP BY p.player_key, p.player_id, p.player_segment, p.region
ORDER BY lifetime_value DESC;

COMMENT ON VIEW gold.player_lifetime_value IS 'LTV graczy - całkowite wydatki';

-- Trendy miesięczne
CREATE OR REPLACE VIEW gold.revenue_trends AS
SELECT 
    d.year,
    d.month,
    d.month_name,
    COUNT(*) as transactions,
    SUM(f.total_rp) as revenue,
    AVG(f.total_rp) as avg_transaction,
    COUNT(DISTINCT f.player_key) as active_players,
    ROUND(SUM(f.total_rp)::NUMERIC / COUNT(DISTINCT f.player_key), 2) as revenue_per_player
FROM gold.fact_sales f
JOIN gold.dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;

COMMENT ON VIEW gold.revenue_trends IS 'Trendy revenue miesięczne + KPI';