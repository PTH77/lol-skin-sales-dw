-- SILVER LAYER - Cleaned and validated data
-- Database: lol_skins_dw
-- Purpose: Transform Bronze → Silver with data quality rules

-- ================================================================
-- 1. DIM_DATE - Generate date dimension
-- ================================================================

DROP TABLE IF EXISTS silver.dim_date CASCADE;

CREATE TABLE silver.dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    
    -- Date parts
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    week INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    
    -- Flags
    is_weekend BOOLEAN NOT NULL,
    is_month_start BOOLEAN NOT NULL,
    is_month_end BOOLEAN NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE silver.dim_date IS 'Date dimension for time-based analysis';

-- Populate date dimension (2020-2030)
INSERT INTO silver.dim_date (
    date_key, date, year, quarter, month, month_name,
    week, day_of_month, day_of_week, day_name,
    is_weekend, is_month_start, is_month_end
)
SELECT 
    TO_CHAR(d, 'YYYYMMDD')::INTEGER as date_key,
    d::DATE as date,
    EXTRACT(YEAR FROM d)::INTEGER as year,
    EXTRACT(QUARTER FROM d)::INTEGER as quarter,
    EXTRACT(MONTH FROM d)::INTEGER as month,
    TO_CHAR(d, 'Month') as month_name,
    EXTRACT(WEEK FROM d)::INTEGER as week,
    EXTRACT(DAY FROM d)::INTEGER as day_of_month,
    EXTRACT(DOW FROM d)::INTEGER as day_of_week,
    TO_CHAR(d, 'Day') as day_name,
    CASE WHEN EXTRACT(DOW FROM d) IN (0, 6) THEN TRUE ELSE FALSE END as is_weekend,
    CASE WHEN EXTRACT(DAY FROM d) = 1 THEN TRUE ELSE FALSE END as is_month_start,
    CASE WHEN d = (DATE_TRUNC('month', d) + INTERVAL '1 month' - INTERVAL '1 day')::DATE 
         THEN TRUE ELSE FALSE END as is_month_end
FROM generate_series(
    '2020-01-01'::DATE,
    '2030-12-31'::DATE,
    '1 day'::INTERVAL
) d;

-- Verify
SELECT 
    MIN(date) as min_date,
    MAX(date) as max_date,
    COUNT(*) as total_days
FROM silver.dim_date;

-- ================================================================
-- 2. DIM_SKIN - Cleaned skin dimension
-- ================================================================

DROP TABLE IF EXISTS silver.dim_skin CASCADE;

CREATE TABLE silver.dim_skin (
    skin_key SERIAL PRIMARY KEY,
    
    -- Business key
    skin_id INTEGER NOT NULL UNIQUE,
    
    -- Attributes
    champion_name VARCHAR(100) NOT NULL,
    skin_name VARCHAR(200) NOT NULL,
    rarity VARCHAR(50) NOT NULL,
    price_rp INTEGER NOT NULL,
    release_date DATE,
    
    -- Additional info
    champion_id VARCHAR(100),
    skin_num INTEGER,
    
    -- Data quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_price_positive CHECK (price_rp >= 0),
    CONSTRAINT chk_rarity_valid CHECK (rarity IN ('Legacy', 'Epic', 'Legendary', 'Ultimate'))
);

COMMENT ON TABLE silver.dim_skin IS 'Validated skin dimension';

-- Load from Bronze
INSERT INTO silver.dim_skin (
    skin_id, champion_name, skin_name, rarity, price_rp,
    release_date, champion_id, skin_num, is_valid
)
SELECT 
    skin_id,
    TRIM(champion_name) as champion_name,
    TRIM(skin_name) as skin_name,
    rarity,
    price_rp,
    release_date,
    champion_id,
    skin_num,
    -- Data quality check
    CASE 
        WHEN champion_name IS NULL OR TRIM(champion_name) = '' THEN FALSE
        WHEN skin_name IS NULL OR TRIM(skin_name) = '' THEN FALSE
        WHEN price_rp < 0 THEN FALSE
        WHEN rarity NOT IN ('Legacy', 'Epic', 'Legendary', 'Ultimate') THEN FALSE
        ELSE TRUE
    END as is_valid
FROM bronze.stg_skins
WHERE skin_id IS NOT NULL;

-- Verify
SELECT 
    COUNT(*) as total_skins,
    COUNT(*) FILTER (WHERE is_valid = TRUE) as valid_skins,
    COUNT(*) FILTER (WHERE is_valid = FALSE) as invalid_skins
FROM silver.dim_skin;

SELECT rarity, COUNT(*) as count
FROM silver.dim_skin
WHERE is_valid = TRUE
GROUP BY rarity
ORDER BY count DESC;

-- ================================================================
-- 3. DIM_PLAYER - Cleaned player dimension
-- ================================================================

DROP TABLE IF EXISTS silver.dim_player CASCADE;

CREATE TABLE silver.dim_player (
    player_key SERIAL PRIMARY KEY,
    
    -- Business key
    player_id INTEGER NOT NULL UNIQUE,
    
    -- Attributes
    region VARCHAR(10) NOT NULL,
    account_created_date DATE NOT NULL,
    player_segment VARCHAR(20) NOT NULL,
    
    -- Derived attributes
    account_age_days INTEGER,
    
    -- Data quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_region_valid CHECK (region IN ('EUW', 'EUNE', 'NA', 'KR')),
    CONSTRAINT chk_segment_valid CHECK (player_segment IN ('casual', 'core', 'whale'))
);

COMMENT ON TABLE silver.dim_player IS 'Validated player dimension';

-- Load from Bronze
INSERT INTO silver.dim_player (
    player_id, region, account_created_date, player_segment,
    account_age_days, is_valid
)
SELECT 
    player_id,
    UPPER(TRIM(region)) as region,
    account_created_date,
    LOWER(TRIM(player_segment)) as player_segment,
    CURRENT_DATE - account_created_date as account_age_days,
    -- Data quality check
    CASE 
        WHEN player_id IS NULL THEN FALSE
        WHEN region NOT IN ('EUW', 'EUNE', 'NA', 'KR') THEN FALSE
        WHEN player_segment NOT IN ('casual', 'core', 'whale') THEN FALSE
        WHEN account_created_date > CURRENT_DATE THEN FALSE
        ELSE TRUE
    END as is_valid
FROM bronze.stg_players
WHERE player_id IS NOT NULL;

-- Verify
SELECT 
    COUNT(*) as total_players,
    COUNT(*) FILTER (WHERE is_valid = TRUE) as valid_players,
    COUNT(*) FILTER (WHERE is_valid = FALSE) as invalid_players
FROM silver.dim_player;

SELECT region, COUNT(*) as count
FROM silver.dim_player
WHERE is_valid = TRUE
GROUP BY region
ORDER BY count DESC;

SELECT player_segment, COUNT(*) as count
FROM silver.dim_player
WHERE is_valid = TRUE
GROUP BY player_segment
ORDER BY count DESC;

-- ================================================================
-- 4. FACT_SALE - Cleaned sales fact table
-- ================================================================

DROP TABLE IF EXISTS silver.fact_sale CASCADE;

CREATE TABLE silver.fact_sale (
    sale_key SERIAL PRIMARY KEY,
    
    -- Foreign keys
    player_key INTEGER NOT NULL,
    skin_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    
    -- Measures
    price_rp INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    total_rp INTEGER NOT NULL,
    
    -- Data quality flags
    is_valid BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_price_positive_sale CHECK (price_rp > 0),
    CONSTRAINT chk_total_calc CHECK (total_rp = price_rp * quantity)
);

COMMENT ON TABLE silver.fact_sale IS 'Validated sales transactions';

-- Load from Bronze with FK lookups
INSERT INTO silver.fact_sale (
    player_key, skin_key, date_key,
    price_rp, quantity, total_rp, is_valid
)
SELECT 
    p.player_key,
    s.skin_key,
    TO_CHAR(sale.purchase_date, 'YYYYMMDD')::INTEGER as date_key,
    sale.price_rp,
    sale.quantity,
    sale.price_rp * sale.quantity as total_rp,
    -- Data quality check
    CASE 
        WHEN p.player_key IS NULL THEN FALSE
        WHEN s.skin_key IS NULL THEN FALSE
        WHEN sale.price_rp <= 0 THEN FALSE
        WHEN sale.quantity <= 0 THEN FALSE
        ELSE TRUE
    END as is_valid
FROM bronze.stg_sales sale
LEFT JOIN silver.dim_player p ON sale.player_id = p.player_id
LEFT JOIN silver.dim_skin s ON sale.skin_id = s.skin_id
WHERE sale.transaction_id IS NOT NULL;

-- Verify
SELECT 
    COUNT(*) as total_sales,
    COUNT(*) FILTER (WHERE is_valid = TRUE) as valid_sales,
    COUNT(*) FILTER (WHERE is_valid = FALSE) as invalid_sales,
    SUM(total_rp) FILTER (WHERE is_valid = TRUE) as total_revenue
FROM silver.fact_sale;

-- Check referential integrity
SELECT 
    COUNT(*) FILTER (WHERE player_key IS NULL) as missing_players,
    COUNT(*) FILTER (WHERE skin_key IS NULL) as missing_skins,
    COUNT(*) FILTER (WHERE date_key NOT IN (SELECT date_key FROM silver.dim_date)) as missing_dates
FROM silver.fact_sale;

-- ================================================================
-- DATA QUALITY SUMMARY
-- ================================================================

SELECT 'Silver Layer - Data Quality Summary' as report;

SELECT 
    'dim_date' as table_name,
    COUNT(*) as row_count,
    COUNT(*) as valid_rows,
    0 as invalid_rows
FROM silver.dim_date
UNION ALL
SELECT 
    'dim_skin',
    COUNT(*),
    COUNT(*) FILTER (WHERE is_valid = TRUE),
    COUNT(*) FILTER (WHERE is_valid = FALSE)
FROM silver.dim_skin
UNION ALL
SELECT 
    'dim_player',
    COUNT(*),
    COUNT(*) FILTER (WHERE is_valid = TRUE),
    COUNT(*) FILTER (WHERE is_valid = FALSE)
FROM silver.dim_player
UNION ALL
SELECT 
    'fact_sale',
    COUNT(*),
    COUNT(*) FILTER (WHERE is_valid = TRUE),
    COUNT(*) FILTER (WHERE is_valid = FALSE)
FROM silver.fact_sale;