# League of Legends Skin Sales – Data Warehouse Project

## Overview
This project presents a local data warehouse built using PostgreSQL and Python,
designed with Medallion Architecture (Bronze / Silver / Gold).

The dataset is based on League of Legends skins, players, and sales data,
prepared for analytical use cases.

## Tech Stack
- PostgreSQL
- Python (pandas, SQLAlchemy)
- SQL
- Medallion Architecture
- Git & GitHub
- DataGrip

## Architecture
- Bronze: raw CSV ingestion
- Silver: cleaned and standardized data
- Gold: star schema (fact & dimensions)

## Setup
1. Clone repository
2. Create virtual environment
3. Install requirements
4. Configure `.env`
5. Run ETL scripts

## Data Model
- fact_sales
- dim_skins
- dim_player

## Notes
This is a local, offline project intended for portfolio and educational purposes.
