-- GOLD LAYER - Finalna gwiazda analityczna

-- Kasuj stare tabele
DROP TABLE IF EXISTS gold.fact_sales CASCADE;
DROP TABLE IF EXISTS gold.dim_player CASCADE;
DROP TABLE IF EXISTS gold.dim_skin CASCADE;
DROP TABLE IF EXISTS gold.dim_date CASCADE;

-- DIM_DATE - Kalendarz

CREATE TABLE gold.dim_date (
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

COMMENT ON TABLE gold.dim_date IS 'Kalendarz 2010-2030';

-- Kopiuj ze Silver
INSERT INTO gold.dim_date
SELECT * FROM silver.dim_date;

-- DIM_SKIN - Skiny (tylko valid)

CREATE TABLE gold.dim_skin (
    skin_key SERIAL PRIMARY KEY,
    skin_id INTEGER NOT NULL UNIQUE,
    champion_name VARCHAR(100) NOT NULL,
    skin_name VARCHAR(200) NOT NULL,
    rarity VARCHAR(50) NOT NULL,
    price_rp INTEGER NOT NULL,
    release_date DATE,
    champion_id VARCHAR(100),
    skin_num INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_price_positive CHECK (price_rp >= 0),
    CONSTRAINT chk_rarity_valid CHECK (rarity IN ('Default', 'Legacy', 'Epic', 'Legendary', 'Ultimate'))
);

COMMENT ON TABLE gold.dim_skin IS 'Wymiar skinów - tylko zwalidowane';

-- Załaduj tylko valid
INSERT INTO gold.dim_skin (
    skin_key, skin_id, champion_name, skin_name, rarity, 
    price_rp, release_date, champion_id, skin_num
)
SELECT 
    skin_key, skin_id, champion_name, skin_name, rarity,
    price_rp, release_date, champion_id, skin_num
FROM silver.dim_skin
WHERE is_valid = TRUE;

-- DIM_PLAYER - Gracze (tylko valid)

CREATE TABLE gold.dim_player (
    player_key SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL UNIQUE,
    region VARCHAR(10) NOT NULL,
    account_created_date DATE NOT NULL,
    player_segment VARCHAR(20) NOT NULL,
    account_age_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_region_valid CHECK (region IN ('EUW', 'EUNE', 'NA', 'KR')),
    CONSTRAINT chk_segment_valid CHECK (player_segment IN ('casual', 'core', 'whale'))
);

COMMENT ON TABLE gold.dim_player IS 'Wymiar graczy - tylko zwalidowani';

-- Załaduj tylko valid
INSERT INTO gold.dim_player (
    player_key, player_id, region, account_created_date, 
    player_segment, account_age_days
)
SELECT 
    player_key, player_id, region, account_created_date,
    player_segment, account_age_days
FROM silver.dim_player
WHERE is_valid = TRUE;

-- FACT_SALES - Transakcje (tylko valid)

CREATE TABLE gold.fact_sales (
    sale_key SERIAL PRIMARY KEY,
    transaction_id INTEGER,
    player_key INTEGER NOT NULL,
    skin_key INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    price_rp INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    total_rp INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_price_positive_fact CHECK (price_rp > 0),
    CONSTRAINT chk_total_calculation CHECK (total_rp = price_rp * quantity),
    
    -- Klucze obce
    CONSTRAINT fk_player FOREIGN KEY (player_key) REFERENCES gold.dim_player(player_key),
    CONSTRAINT fk_skin FOREIGN KEY (skin_key) REFERENCES gold.dim_skin(skin_key),
    CONSTRAINT fk_date FOREIGN KEY (date_key) REFERENCES gold.dim_date(date_key)
);

COMMENT ON TABLE gold.fact_sales IS 'Fakty sprzedaży - tylko zwalidowane';

-- Indeksy dla wydajności
CREATE INDEX idx_fact_sales_player ON gold.fact_sales(player_key);
CREATE INDEX idx_fact_sales_skin ON gold.fact_sales(skin_key);
CREATE INDEX idx_fact_sales_date ON gold.fact_sales(date_key);
CREATE INDEX idx_fact_sales_date_player ON gold.fact_sales(date_key, player_key);

-- Załaduj tylko valid
INSERT INTO gold.fact_sales (
    transaction_id, player_key, skin_key, date_key,
    price_rp, quantity, total_rp
)
SELECT 
    transaction_id::INTEGER,
    player_key,
    skin_key,
    date_key,
    price_rp::INTEGER,
    quantity::INTEGER,
    total_rp::INTEGER
FROM silver.fact_sale
WHERE is_valid = TRUE;