-- Drop existing tables if they exist
DROP TABLE IF EXISTS bronze.stg_sales CASCADE;
DROP TABLE IF EXISTS bronze.stg_players CASCADE;
DROP TABLE IF EXISTS bronze.stg_skins CASCADE;

-- ================================================================
-- 1. STAGING SKINS
-- ================================================================
CREATE TABLE bronze.stg_skins (
    skin_id INTEGER,
    champion_name VARCHAR(100),
    skin_name VARCHAR(200),
    rarity VARCHAR(50),
    price_rp INTEGER,
    release_date DATE,
    champion_id VARCHAR(100),
    skin_num INTEGER,
    skin_name_norm VARCHAR(200),
);

COMMENT ON TABLE bronze.stg_skins IS 'Raw skin data from dim_skins_final.csv';

-- ================================================================
-- 2. STAGING PLAYERS
-- ================================================================
CREATE TABLE bronze.stg_players (
    player_id INTEGER,
    region VARCHAR(10),
    account_created_date DATE,
    player_segment VARCHAR(20),
);

COMMENT ON TABLE bronze.stg_players IS 'Raw player data from dim_player.csv';

-- ================================================================
-- 3. STAGING SALES
-- ================================================================
CREATE TABLE bronze.stg_sales (
    transaction_id INTEGER,
    player_id INTEGER,
    skin_id INTEGER,
    purchase_date DATE,
    price_rp INTEGER,
    quantity INTEGER,
);

COMMENT ON TABLE bronze.stg_sales IS 'Raw sales transactions from fact_sales.csv';

SELECT 'stg_skins' as table_name, COUNT(*) as row_count FROM bronze.stg_skins
UNION ALL
SELECT 'stg_players', COUNT(*) FROM bronze.stg_players
UNION ALL
SELECT 'stg_sales', COUNT(*) FROM bronze.stg_sales;

-- Check sample data
SELECT * FROM bronze.stg_skins LIMIT 5;
SELECT * FROM bronze.stg_players LIMIT 5;
SELECT * FROM bronze.stg_sales LIMIT 5;

-- Check for NULLs
SELECT 
    COUNT(*) FILTER (WHERE skin_id IS NULL) as null_skin_id,
    COUNT(*) FILTER (WHERE champion_name IS NULL) as null_champion,
    COUNT(*) FILTER (WHERE price_rp IS NULL) as null_price
FROM bronze.stg_skins;

SELECT 
    COUNT(*) FILTER (WHERE player_id IS NULL) as null_player_id,
    COUNT(*) FILTER (WHERE region IS NULL) as null_region
FROM bronze.stg_players;

SELECT 
    COUNT(*) FILTER (WHERE transaction_id IS NULL) as null_transaction,
    COUNT(*) FILTER (WHERE player_id IS NULL) as null_player,
    COUNT(*) FILTER (WHERE skin_id IS NULL) as null_skin
FROM bronze.stg_sales;