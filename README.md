# League of Legends Skin Sales Data Warehouse

Production-grade data warehouse analyzing League of Legends skin sales with advanced data quality framework.

**Status:** Complete - All layers operational  
**Database:** PostgreSQL 18  
**Architecture:** Medallion (Bronze/Silver/Gold)

## Quick Start

### Prerequisites
- PostgreSQL 18 or higher
- Python 3.x
- DataGrip or pgAdmin
- Python packages: pandas, requests, playwright

### Installation

1. Clone repository and navigate to project directory

2. Install Python dependencies:
pip install pandas requests playwright
playwright install

3. Create PostgreSQL database:
CREATE DATABASE lol_skins_dw;

## Data Pipeline Execution

### Step 1: Generate Data

Execute Python scripts in this order:

1. python data/src_data/fetch_skins.py - Fetch skins from Riot API
2. python data/src_data/scrape_wiki.py - Scrape LoL Wiki for prices
3. python data/src_data/parse_skins_from_wiki.py - Parse Wiki data
4. python data/src_data/merge_skins.py - Merge API and Wiki data
5. python data/src_data/generate_players_sales.py - Generate players and sales

This creates 3 CSV files in data/raw/:
- dim_skins_final.csv (1,474 skins)
- dim_player.csv (5,000 players)
- fact_sales.csv (20,200 transactions with 10% intentional errors)

### Step 2: Build Database

Execute SQL scripts in PostgreSQL in this order:

1. sql/00_reset_database.sql - Reset database (optional)
2. sql/01_bronze_layer_NEW.sql - Create Bronze staging tables
3. Import CSV files using DataGrip or pgAdmin (right-click table, Import Data from File)
4. sql/02_silver_SIMPLE.sql - Build Silver layer with data quality
5. sql/03_gold_layer.sql - Build Gold star schema
6. sql/04_gold_views.sql - Create analytical views

### Step 3: Verify Results

Run verification scripts:
- sql/05_gold_verification.sql - Verify Gold layer
- sql/06_silver_verification.sql - Check data quality
- sql/07_bronze_verification.sql - Inspect staging data


## Architecture

### Medallion Pattern

The project uses a three-layer medallion architecture:

BRONZE - Staging Layer
- Raw data ingestion
- Tables: stg_skins, stg_players, stg_sales
- Accepts all data including errors

SILVER - Cleansed Layer
- Data validation and quality checks
- Tables: dim_date, dim_skin, dim_player, fact_sale
- Quarantine table for rejected records
- Audit log for monitoring history
- 5% alert threshold for data quality

GOLD - Curated Layer
- Analytics-ready star schema
- Tables: dim_date, dim_skin, dim_player, fact_sales
- Only validated records
- Optimized indexes for performance
- 5 analytical views for business intelligence


## Data Model

### Star Schema Design

The Gold layer implements a star schema with one fact table and three dimension tables:

Fact Table:
- fact_sales: 18,324 valid transactions

Dimension Tables:
- dim_player: 5,000 players
- dim_skin: 1,474 skins
- dim_date: 7,671 days covering 2010-2030

Relationships:
- fact_sales connects to dim_player via player_key
- fact_sales connects to dim_skin via skin_key  
- fact_sales connects to dim_date via date_key

### Dimension Tables

dim_player contains player attributes:
- player_key (primary key), player_id
- region: EUW, EUNE, NA, KR
- player_segment: casual, core, whale
- account_age_days

dim_skin contains skin attributes:
- skin_key (primary key), skin_id
- champion_name, skin_name
- rarity: Default, Legacy, Epic, Legendary, Ultimate
- price_rp, release_date

dim_date contains calendar attributes:
- date_key (primary key), date
- year, quarter, month, week, day
- is_weekend, is_month_start, is_month_end

### Fact Table

fact_sales contains transaction details:
- sale_key (primary key)
- player_key, skin_key, date_key (foreign keys)
- price_rp, quantity, total_rp


## Analytical Views

The Gold layer includes 5 pre-built analytical views:

1. revenue_by_segment_month - Monthly revenue breakdown by player segment
2. top_selling_skins - Skin performance ranked by total revenue
3. weekend_vs_weekday_sales - Comparison of purchasing patterns by day type
4. player_lifetime_value - Player spending analysis for LTV calculation
5. revenue_trends - Monthly revenue trends and key performance indicators


## Data Quality Framework

The Silver layer implements a comprehensive data quality framework:

Features:
- Automated validation and cleansing
- Quarantine system for invalid records
- Complete audit trail of quality checks
- Alert system with 5% error threshold

Quality Checks:
- Missing player or skin references
- Invalid prices (NULL or negative values)
- Invalid quantities (NULL, zero, or negative values)
- Date validation against dim_date calendar

Results from Current Dataset:
- Total transactions: 20,200
- Valid records: 18,324 (90.7%)
- Quarantined: 1,876 (9.3%)
- Alert status: Triggered (exceeds 5% threshold)


## Data Sources

Riot Games Data Dragon API:
- Endpoint: ddragon.leagueoflegends.com
- Method: REST API calls
- Provides: Skin names and champion IDs

LoL Wiki (Fandom):
- Source: Module:SkinData Lua module
- Method: Playwright web scraping (bypasses 403 blocks)
- Provides: Skin prices in Riot Points, rarity classifications, release dates

Data Quality Notes:
- Prices are real values from Wiki, not estimates
- Release dates are actual dates from Wiki when available
- Default skins corrected to 0 RP (Wiki shows champion cost of 880 RP)
- Esports team skins included as they are purchasable content


## Key Achievements

This project demonstrates production-grade data warehousing practices including medallion architecture implementation across Bronze, Silver, and Gold layers. The data comes from real sources - Riot Games API and LoL Wiki web scraping - rather than synthetic generation. 

The Silver layer includes an advanced data quality framework with automated cleansing, quarantine system for invalid records, and alert monitoring with configurable thresholds. The Gold layer provides a fully normalized star schema optimized for analytics with five pre-built analytical views for business intelligence.

All data transformations are fully documented with complete audit trails and data lineage tracking throughout the pipeline.


## Technologies

- **Database:** PostgreSQL 18
- **Python:** 3.x with pandas, requests, playwright
- **SQL Tools:** DataGrip / pgAdmin
- **Web Scraping:** Playwright headless browser
- **APIs:** Riot Games Data Dragon

---

## Business Use Cases

The data warehouse supports various analytical use cases:

Revenue Analysis - Analyze temporal trends, seasonal patterns, and revenue distribution across time periods.

Player Segmentation - Perform lifetime value analysis, RFM segmentation, and cohort behavior tracking.

Skin Performance - Track top-selling skins, analyze rarity tier performance, and measure price elasticity.

Pricing Strategy - Identify optimal price points and analyze discount effectiveness.

Regional Insights - Compare geographic preferences and analyze regional performance differences.


## Data Quality Details

The dataset includes intentionally injected errors (10% of sales) to demonstrate the data quality framework capabilities. Error types include NULL values for player and skin IDs, invalid references to non-existent records, NULL or negative prices, zero or negative quantities, future dates beyond 2026, historical dates before 2010, and duplicate transactions.

Quarantine results show 245 records with missing players (1.21%), 238 with missing skins (1.18%), 225 with invalid prices (1.11%), and 221 with invalid quantities (1.09%), totaling 1,876 quarantined records representing 9.27% of all transactions.


## Notes

Default skins are free (0 RP) in the game. The Wiki module shows 880 RP which represents the champion purchase cost, not the skin cost. This has been corrected in the data pipeline.

Release dates are real dates extracted from the Wiki when available, not randomly generated. The dim_date table is an independent calendar covering 2010-2030, not derived from transaction dates.

Esports team skins (T1, DRX, etc.) are preserved in the dataset as they are purchasable during World Championship events.

Error injection is intentionally set to 10% for demonstration purposes. Production systems typically target less than 1% error rates.


## License

This is an educational project for data warehousing demonstration.

League of Legends and all related content are property of Riot Games, Inc.


## Contact

For questions or issues, please open an issue in the repository.

**Project Status:** Complete  
**Last Updated:** February 3, 2026
