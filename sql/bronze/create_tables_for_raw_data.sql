-- BRONZE LAYER - Raw staging tables (UPDATED)

-- 1. STAGING SKINS
DROP TABLE IF EXISTS bronze.stg_skins CASCADE;

CREATE TABLE bronze.stg_skins (
    skin_id INTEGER,
    champion_name VARCHAR(100),
    skin_name VARCHAR(200),
    rarity VARCHAR(50),
    price_rp INTEGER,
    release_date DATE,         -- DATE (z CSV już w formacie YYYY-MM-DD)
    champion_id VARCHAR(100),
    skin_num INTEGER,
    skin_name_norm VARCHAR(200),
    
    -- Metadata
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bronze.stg_skins IS 'Raw skin data from dim_skins_final.csv (CORRECTED)';

-- 2. STAGING PLAYERS

DROP TABLE IF EXISTS bronze.stg_players CASCADE;

CREATE TABLE bronze.stg_players (
    player_id INTEGER,
    region VARCHAR(10),
    account_created_date DATE,
    player_segment VARCHAR(20),
    
    -- Metadata
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bronze.stg_players IS 'Raw player data from dim_player.csv';

-- 3. STAGING SALES (with error support)
DROP TABLE IF EXISTS bronze.stg_sales CASCADE;

CREATE TABLE bronze.stg_sales (
    transaction_id NUMERIC,      -- NUMERIC - może być NULL
    player_id NUMERIC,            -- NUMERIC - może być NULL lub invalid
    skin_id NUMERIC,              -- NUMERIC - może być NULL lub invalid
    purchase_date TEXT,           -- TEXT - może być invalid format
    price_rp NUMERIC,             -- NUMERIC - może być NULL lub negative
    quantity NUMERIC,             -- NUMERIC - może być NULL lub 0
    
    -- Metadata
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE bronze.stg_sales IS 'Raw sales with intentional errors (10%) for DQ testing';

-- ================================================================
-- VERIFICATION
-- ================================================================

-- Check row counts
SELECT 'stg_skins' as table_name, COUNT(*) as row_count FROM bronze.stg_skins
UNION ALL
SELECT 'stg_players', COUNT(*) FROM bronze.stg_players
UNION ALL
SELECT 'stg_sales', COUNT(*) FROM bronze.stg_sales;

-- Expected:
-- stg_skins   : ~1600-1700 (with Default skins, esports skins)
-- stg_players : 5000
-- stg_sales   : ~20200 (20000 + ~200 duplicates)

-- Check Default skins (should be 0 RP!)
SELECT champion_name, skin_name, rarity, price_rp
FROM bronze.stg_skins
WHERE rarity = 'Default'
LIMIT 10;

-- Check release dates
SELECT 
    COUNT(*) as total,
    COUNT(release_date) as with_date,
    COUNT(*) - COUNT(release_date) as null_dates
FROM bronze.stg_skins;

-- Check for errors in sales
SELECT 
    COUNT(*) as total_sales,
    COUNT(*) FILTER (WHERE player_id IS NULL) as null_player,
    COUNT(*) FILTER (WHERE skin_id IS NULL) as null_skin,
    COUNT(*) FILTER (WHERE price_rp IS NULL) as null_price,
    COUNT(*) FILTER (WHERE price_rp < 0) as negative_price,
    COUNT(*) FILTER (WHERE quantity <= 0) as invalid_quantity
FROM bronze.stg_sales;

-- Should show ~10% errors