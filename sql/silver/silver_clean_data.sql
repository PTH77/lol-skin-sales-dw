-- SILVER LAYER - SIMPLIFIED
-- Drop existing
DROP TABLE IF EXISTS silver.fact_sale CASCADE;
DROP TABLE IF EXISTS silver.dim_player CASCADE;
DROP TABLE IF EXISTS silver.dim_skin CASCADE;
DROP TABLE IF EXISTS silver.dim_date CASCADE;
DROP TABLE IF EXISTS silver.fact_sale_quarantine CASCADE;
DROP TABLE IF EXISTS silver.data_quality_log CASCADE;

-- QUARANTINE & AUDIT

CREATE TABLE silver.data_quality_log (
    log_id SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    table_name VARCHAR(100),
    issue_type VARCHAR(100),
    issue_count INTEGER,
    issue_pct NUMERIC(5,2),
    threshold_pct NUMERIC(5,2),
    alert_triggered BOOLEAN DEFAULT FALSE
);

CREATE TABLE silver.fact_sale_quarantine (
    quarantine_id SERIAL PRIMARY KEY,
    transaction_id INTEGER,
    player_id INTEGER,
    skin_id INTEGER,
    purchase_date DATE,
    price_rp INTEGER,
    quantity INTEGER,
    rejection_reason VARCHAR(200),
    rejection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DIM_DATE

CREATE TABLE silver.dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    week INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_month_start BOOLEAN NOT NULL,
    is_month_end BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO silver.dim_date (
    date_key, date, year, quarter, month, month_name,
    week, day_of_month, day_of_week, day_name,
    is_weekend, is_month_start, is_month_end
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER,
    d::DATE,
    EXTRACT(YEAR FROM d)::INTEGER,
    EXTRACT(QUARTER FROM d)::INTEGER,
    EXTRACT(MONTH FROM d)::INTEGER,
    TRIM(TO_CHAR(d, 'Month')),
    EXTRACT(WEEK FROM d)::INTEGER,
    EXTRACT(DAY FROM d)::INTEGER,
    EXTRACT(DOW FROM d)::INTEGER,
    TRIM(TO_CHAR(d, 'Day')),
    EXTRACT(DOW FROM d) IN (0, 6),
    EXTRACT(DAY FROM d) = 1,
    d = (DATE_TRUNC('month', d) + INTERVAL '1 month' - INTERVAL '1 day')::DATE
FROM generate_series('2010-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) d;

SELECT 'dim_date created' as status, COUNT(*) as days FROM silver.dim_date;

-- DIM_SKIN

CREATE TABLE silver.dim_skin (
    skin_key SERIAL PRIMARY KEY,
    skin_id INTEGER NOT NULL UNIQUE,
    champion_name VARCHAR(100) NOT NULL,
    skin_name VARCHAR(200) NOT NULL,
    rarity VARCHAR(50) NOT NULL,
    price_rp INTEGER NOT NULL,
    release_date DATE,
    champion_id VARCHAR(100),
    skin_num INTEGER,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_price_positive CHECK (price_rp >= 0),
    CONSTRAINT chk_rarity_valid CHECK (rarity IN ('Default', 'Legacy', 'Epic', 'Legendary', 'Ultimate'))
);

INSERT INTO silver.dim_skin (
    skin_id, champion_name, skin_name, rarity, price_rp,
    release_date, champion_id, skin_num, is_valid
)
SELECT
    skin_id, TRIM(champion_name), TRIM(skin_name), rarity, price_rp,
    release_date, champion_id, skin_num,
    CASE
        WHEN champion_name IS NULL OR TRIM(champion_name) = '' THEN FALSE
        WHEN skin_name IS NULL OR TRIM(skin_name) = '' THEN FALSE
        WHEN price_rp < 0 THEN FALSE
        WHEN rarity NOT IN ('Default', 'Legacy', 'Epic', 'Legendary', 'Ultimate') THEN FALSE
        ELSE TRUE
    END
FROM bronze.stg_skins
WHERE skin_id IS NOT NULL;

SELECT 'dim_skin created' as status, COUNT(*) as skins FROM silver.dim_skin;

-- DIM_PLAYER

CREATE TABLE silver.dim_player (
    player_key SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL UNIQUE,
    region VARCHAR(10) NOT NULL,
    account_created_date DATE NOT NULL,
    player_segment VARCHAR(20) NOT NULL,
    account_age_days INTEGER,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_region_valid CHECK (region IN ('EUW', 'EUNE', 'NA', 'KR')),
    CONSTRAINT chk_segment_valid CHECK (player_segment IN ('casual', 'core', 'whale'))
);

INSERT INTO silver.dim_player (
    player_id, region, account_created_date, player_segment, account_age_days, is_valid
)
SELECT
    player_id, UPPER(TRIM(region)), account_created_date, LOWER(TRIM(player_segment)),
    CURRENT_DATE - account_created_date,
    CASE
        WHEN player_id IS NULL THEN FALSE
        WHEN region NOT IN ('EUW', 'EUNE', 'NA', 'KR') THEN FALSE
        WHEN player_segment NOT IN ('casual', 'core', 'whale') THEN FALSE
        WHEN account_created_date > CURRENT_DATE THEN FALSE
        ELSE TRUE
    END
FROM bronze.stg_players
WHERE player_id IS NOT NULL;

SELECT 'dim_player created' as status, COUNT(*) as players FROM silver.dim_player;

-- FACT_SALE

CREATE TABLE silver.fact_sale (
    sale_key SERIAL PRIMARY KEY,
    transaction_id NUMERIC,
    player_key INTEGER,
    skin_key INTEGER,
    date_key INTEGER,
    price_rp NUMERIC,
    quantity NUMERIC,
    total_rp NUMERIC,
    is_valid BOOLEAN DEFAULT FALSE,
    dq_issues TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO silver.fact_sale (
    transaction_id, player_key, skin_key, date_key,
    price_rp, quantity, total_rp, is_valid, dq_issues
)
SELECT
    sale.transaction_id,
    p.player_key,
    s.skin_key,
    CASE
        WHEN sale.purchase_date ~ '^\d{4}-\d{2}-\d{2}$'
        THEN TO_CHAR(sale.purchase_date::DATE, 'YYYYMMDD')::INTEGER
        ELSE NULL
    END,
    sale.price_rp,
    sale.quantity,
    CASE
        WHEN sale.price_rp IS NOT NULL AND sale.quantity IS NOT NULL
        THEN sale.price_rp * sale.quantity
        ELSE NULL
    END,
    FALSE,
    NULL
FROM bronze.stg_sales sale
LEFT JOIN silver.dim_player p ON sale.player_id::INTEGER = p.player_id
LEFT JOIN silver.dim_skin s ON sale.skin_id::INTEGER = s.skin_id
WHERE sale.transaction_id IS NOT NULL;

SELECT 'fact_sale loaded' as status, COUNT(*) as sales FROM silver.fact_sale;

-- CLEANSING (bez procedures - bezpośrednio)

-- Step 1: Fix missing price
UPDATE silver.fact_sale f
SET
    price_rp = s.price_rp,
    total_rp = s.price_rp * f.quantity,
    dq_issues = COALESCE(f.dq_issues || ',', '') || 'price_fixed'
FROM silver.dim_skin s
WHERE f.skin_key = s.skin_key
  AND f.price_rp IS NULL
  AND f.quantity > 0
  AND s.price_rp > 0;

-- Step 2: Recalculate total
UPDATE silver.fact_sale
SET
    total_rp = price_rp * quantity,
    dq_issues = COALESCE(dq_issues || ',', '') || 'total_recalculated'
WHERE price_rp > 0
  AND quantity > 0
  AND (total_rp IS NULL OR total_rp != price_rp * quantity);

-- Step 3: Mark issues
UPDATE silver.fact_sale
SET dq_issues = TRIM(BOTH ',' FROM
    CASE WHEN player_key IS NULL THEN 'missing_player,' ELSE '' END ||
    CASE WHEN skin_key IS NULL THEN 'missing_skin,' ELSE '' END ||
    CASE WHEN price_rp IS NULL THEN 'missing_price,' ELSE '' END ||
    CASE WHEN price_rp < 0 THEN 'negative_price,' ELSE '' END ||
    CASE WHEN quantity IS NULL THEN 'missing_quantity,' ELSE '' END ||
    CASE WHEN quantity <= 0 THEN 'invalid_quantity,' ELSE '' END ||
    CASE WHEN date_key NOT IN (SELECT date_key FROM silver.dim_date) THEN 'invalid_date,' ELSE '' END ||
    COALESCE(dq_issues, '')
)
WHERE dq_issues IS NULL OR dq_issues = '';

-- Step 4: Mark valid
UPDATE silver.fact_sale
SET is_valid = TRUE
WHERE player_key IS NOT NULL
  AND skin_key IS NOT NULL
  AND price_rp > 0
  AND quantity > 0
  AND total_rp = price_rp * quantity
  AND date_key IN (SELECT date_key FROM silver.dim_date);

-- Step 5: Quarantine
INSERT INTO silver.fact_sale_quarantine (
    transaction_id, player_id, skin_id, purchase_date,
    price_rp, quantity, rejection_reason
)
SELECT
    f.transaction_id::INTEGER,
    s.player_id::INTEGER,
    s.skin_id::INTEGER,
    CASE
        WHEN s.purchase_date ~ '^\d{4}-\d{2}-\d{2}$'
        THEN s.purchase_date::DATE
        ELSE NULL
    END,
    s.price_rp::INTEGER,
    s.quantity::INTEGER,
    f.dq_issues
FROM silver.fact_sale f
JOIN bronze.stg_sales s ON f.transaction_id = s.transaction_id
WHERE f.is_valid = FALSE;

-- MONITORING (bezpośrednio, bez procedure)

DO $$
DECLARE
    v_total INTEGER;
    v_count INTEGER;
    v_pct NUMERIC;
    v_threshold NUMERIC := 5.0;
BEGIN
    SELECT COUNT(*) INTO v_total FROM silver.fact_sale;

    -- Missing players
    SELECT COUNT(*) INTO v_count FROM silver.fact_sale WHERE player_key IS NULL;
    v_pct := ROUND((v_count::NUMERIC / NULLIF(v_total, 0) * 100), 2);
    INSERT INTO silver.data_quality_log (table_name, issue_type, issue_count, issue_pct, threshold_pct, alert_triggered)
    VALUES ('fact_sale', 'missing_player', v_count, v_pct, v_threshold, v_pct > v_threshold);

    -- Missing skins
    SELECT COUNT(*) INTO v_count FROM silver.fact_sale WHERE skin_key IS NULL;
    v_pct := ROUND((v_count::NUMERIC / NULLIF(v_total, 0) * 100), 2);
    INSERT INTO silver.data_quality_log (table_name, issue_type, issue_count, issue_pct, threshold_pct, alert_triggered)
    VALUES ('fact_sale', 'missing_skin', v_count, v_pct, v_threshold, v_pct > v_threshold);

    -- Invalid prices
    SELECT COUNT(*) INTO v_count FROM silver.fact_sale WHERE price_rp <= 0 OR price_rp IS NULL;
    v_pct := ROUND((v_count::NUMERIC / NULLIF(v_total, 0) * 100), 2);
    INSERT INTO silver.data_quality_log (table_name, issue_type, issue_count, issue_pct, threshold_pct, alert_triggered)
    VALUES ('fact_sale', 'invalid_price', v_count, v_pct, v_threshold, v_pct > v_threshold);

    -- Invalid quantity
    SELECT COUNT(*) INTO v_count FROM silver.fact_sale WHERE quantity <= 0 OR quantity IS NULL;
    v_pct := ROUND((v_count::NUMERIC / NULLIF(v_total, 0) * 100), 2);
    INSERT INTO silver.data_quality_log (table_name, issue_type, issue_count, issue_pct, threshold_pct, alert_triggered)
    VALUES ('fact_sale', 'invalid_quantity', v_count, v_pct, v_threshold, v_pct > v_threshold);

    -- Total invalid
    SELECT COUNT(*) INTO v_count FROM silver.fact_sale WHERE is_valid = FALSE;
    v_pct := ROUND((v_count::NUMERIC / NULLIF(v_total, 0) * 100), 2);
    INSERT INTO silver.data_quality_log (table_name, issue_type, issue_count, issue_pct, threshold_pct, alert_triggered)
    VALUES ('fact_sale', 'total_invalid', v_count, v_pct, v_threshold, v_pct > v_threshold);
END $$;

-- REPORTS

SELECT
    issue_type as "Check",
    issue_count as "Count",
    issue_pct as "% Error",
    CASE WHEN alert_triggered THEN 'ALERT!' ELSE '✓ OK' END as "Status"
FROM silver.data_quality_log
ORDER BY issue_pct DESC;


SELECT
    COUNT(*) as total_sales,
    COUNT(*) FILTER (WHERE is_valid = TRUE) as valid_sales,
    COUNT(*) FILTER (WHERE is_valid = FALSE) as invalid_sales,
    ROUND(COUNT(*) FILTER (WHERE is_valid = FALSE)::NUMERIC / COUNT(*) * 100, 2) as error_pct,
    SUM(total_rp) FILTER (WHERE is_valid = TRUE) as total_revenue
FROM silver.fact_sale;

SELECT
    rejection_reason,
    COUNT(*) as count
FROM silver.fact_sale_quarantine
GROUP BY rejection_reason
ORDER BY count DESC
LIMIT 10;

SELECT
    issue_type,
    issue_pct,
    'THRESHOLD EXCEEDED!' as message
FROM silver.data_quality_log
WHERE alert_triggered = TRUE
ORDER BY issue_pct DESC;