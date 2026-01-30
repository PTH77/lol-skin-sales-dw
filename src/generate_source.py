import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random

# ============================================================
# GENERATE SOURCE – SYNTHETIC SALES DATA
# ============================================================

print("=" * 60)
print("GENERATE SOURCE – SYNTHETIC SALES DATA")
print("=" * 60)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKINS_PATH = os.path.join(BASE_DIR, "csv", "dim_skins_merged.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "csv", "fact_skin_sales.csv")

# ------------------------------------------------------------
# PARAMETRY GENEROWANIA
# ------------------------------------------------------------
NUM_PLAYERS = 5000
NUM_TRANSACTIONS = 100_000
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2024, 12, 31)

REGIONS = ["EUW", "EUNE", "NA", "KR", "BR", "JP"]

# Wagi popularności rarity (im droższy, tym rzadziej kupowany)
RARITY_WEIGHTS = {
    "Common": 1.0,
    "Uncommon": 0.9,
    "Rare": 0.8,
    "Epic": 0.6,
    "Legendary": 0.35,
    "Mythic": 0.15,
    "Ultimate": 0.1
}

# ------------------------------------------------------------
# WCZYTANIE DANYCH
# ------------------------------------------------------------
skins = pd.read_csv(SKINS_PATH)

print(f"Załadowano skinów: {len(skins)}")

# Usuwamy base skiny (dla pewności)
skins = skins[~skins["skin_name"].str.lower().isin(["default", "base"])].copy()

# Wagi losowania
skins["weight"] = skins["rarity"].map(RARITY_WEIGHTS).fillna(0.5)

# ------------------------------------------------------------
# GENEROWANIE GRACZY
# ------------------------------------------------------------
players = pd.DataFrame({
    "player_id": range(1, NUM_PLAYERS + 1),
    "region": np.random.choice(REGIONS, NUM_PLAYERS),
    "account_created": [
        START_DATE + timedelta(days=random.randint(0, 900))
        for _ in range(NUM_PLAYERS)
    ]
})

# ------------------------------------------------------------
# GENEROWANIE TRANSAKCJI
# ------------------------------------------------------------
transactions = []

skin_choices = skins.index.to_list()
skin_weights = skins["weight"].to_list()

for tx_id in range(1, NUM_TRANSACTIONS + 1):
    skin_idx = random.choices(skin_choices, weights=skin_weights, k=1)[0]
    skin = skins.loc[skin_idx]

    player = players.sample(1).iloc[0]

    sale_date = START_DATE + timedelta(
        days=random.randint(0, (END_DATE - START_DATE).days)
    )

    transactions.append({
        "transaction_id": tx_id,
        "sale_date": sale_date.date(),
        "player_id": player["player_id"],
        "region": player["region"],
        "champion_id": skin["champion_id"],
        "skin_name": skin["skin_name"],
        "rarity": skin["rarity"],
        "price_rp": skin["price_rp"]
    })

fact_sales = pd.DataFrame(transactions)

# ------------------------------------------------------------
# ZAPIS
# ------------------------------------------------------------
fact_sales.to_csv(OUTPUT_PATH, index=False)

print(f"Zapisano: {OUTPUT_PATH}")
print(f"Liczba transakcji: {len(fact_sales)}")
print("=" * 60)
