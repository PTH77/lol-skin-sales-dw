-- Liczba wierszy w tabelach staging
SELECT
    'stg_skins' as tabela,
    COUNT(*) as wiersze
FROM bronze.stg_skins
UNION ALL
SELECT 'stg_players', COUNT(*) FROM bronze.stg_players
UNION ALL
SELECT 'stg_sales', COUNT(*) FROM bronze.stg_sales;

-- Pierwsze 10 skinów
SELECT
    skin_id,
    champion_name,
    skin_name,
    rarity,
    price_rp,
    release_date
FROM bronze.stg_skins
LIMIT 10;

-- Default skiny (sprawdzenie czy cena = 0)
SELECT
    skin_id,
    champion_name,
    skin_name,
    rarity,
    price_rp
FROM bronze.stg_skins
WHERE rarity = 'Default'
LIMIT 10;

-- Rozkład rarity
SELECT
    s.rarity,
    COUNT(*) as count
FROM bronze.stg_skins s
GROUP BY s.rarity
ORDER BY count DESC;

-- Rozkład cen (top 10)
SELECT
    s.price_rp,
    COUNT(*) as count
FROM bronze.stg_skins s
GROUP BY s.price_rp
ORDER BY count DESC
LIMIT 10;

-- Skiny bez daty wydania
SELECT
    COUNT(*) as total,
    COUNT(s.release_date) as with_date,
    COUNT(*) - COUNT(s.release_date) as without_date,
    ROUND((COUNT(*) - COUNT(s.release_date))::NUMERIC / COUNT(*) * 100, 2) as pct_without_date
FROM bronze.stg_skins s;

-- Gracze - rozkład segmentów
SELECT
    p.player_segment,
    COUNT(*) as count
FROM bronze.stg_players p
GROUP BY p.player_segment
ORDER BY count DESC;

-- Gracze - rozkład regionów
SELECT
    p.region,
    COUNT(*) as count
FROM bronze.stg_players p
GROUP BY p.region
ORDER BY count DESC;

-- Sales - wykryj błędy
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE s.player_id IS NULL) as null_player,
    COUNT(*) FILTER (WHERE s.skin_id IS NULL) as null_skin,
    COUNT(*) FILTER (WHERE s.price_rp IS NULL) as null_price,
    COUNT(*) FILTER (WHERE s.price_rp < 0) as negative_price,
    COUNT(*) FILTER (WHERE s.quantity IS NULL) as null_quantity,
    COUNT(*) FILTER (WHERE s.quantity <= 0) as invalid_quantity
FROM bronze.stg_sales s;

-- Przykłady błędnych transakcji
SELECT
    s.transaction_id,
    s.player_id,
    s.skin_id,
    s.purchase_date,
    s.price_rp,
    s.quantity
FROM bronze.stg_sales s
WHERE s.player_id IS NULL
   OR s.skin_id IS NULL
   OR s.price_rp IS NULL
   OR s.price_rp < 0
   OR s.quantity IS NULL
   OR s.quantity <= 0
LIMIT 20;

-- Zakres dat transakcji
SELECT
    MIN(s.purchase_date::DATE) as min_date,
    MAX(s.purchase_date::DATE) as max_date,
    COUNT(DISTINCT s.purchase_date::DATE) as unique_dates
FROM bronze.stg_sales s
WHERE s.purchase_date ~ '^\d{4}-\d{2}-\d{2}$';