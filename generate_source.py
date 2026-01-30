import pandas as pd
import random
from datetime import datetime, timedelta
import os

# ================= USTAWIENIA =================
NUM_PLAYERS = 5000
NUM_TRANSACTIONS = 20000

REGIONS = ["EUW", "EUNE", "NA", "KR"]
SEGMENTS = ["casual", "core", "whale"]

# Rarity -> cena RP
RARITY_PRICE = {
    "legacy": 520,
    "epic": 1350,
    "legendary": 1820,
    "mythic": 3250
}

# ================= ŚCIEŻKI =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
skins_path = os.path.join(BASE_DIR, "csv", "dim_skins.csv")  # plik w podfolderze csv
dim_player_path = os.path.join(BASE_DIR, "dim_player.csv")
fact_sales_path = os.path.join(BASE_DIR, "fact_sales.csv")

print("Ładuję plik skinów z:", skins_path)
print("Zawartość folderu BASE_DIR:", os.listdir(BASE_DIR))
print("Zawartość folderu csv:", os.listdir(os.path.join(BASE_DIR, "csv")))

# ================= WCZYTAJ SKINY =================
dim_skin_df = pd.read_csv(skins_path)

# Usuń default skiny
if "skin_name" in dim_skin_df.columns:
    dim_skin_df = dim_skin_df[dim_skin_df["skin_name"] != "default"]

# Sprawdź kolumnę rarity
if "rarity" not in dim_skin_df.columns:
    raise ValueError("Plik dim_skins.csv musi mieć kolumnę 'rarity'!")

# Słownik skin_id -> price_rp
skin_price_map = {row.skin_id: RARITY_PRICE.get(row.rarity.lower(), 520)
                  for _, row in dim_skin_df.iterrows()}

skin_ids = list(skin_price_map.keys())

# ================= GENERUJ DIM_PLAYER =================
players = []
for i in range(1, NUM_PLAYERS + 1):
    players.append({
        "player_id": i,
        "region": random.choice(REGIONS),
        "account_created_date": (
            datetime.now() - timedelta(days=random.randint(30, 2000))
        ).date(),
        "player_segment": random.choices(
            SEGMENTS, weights=[0.6, 0.3, 0.1]
        )[0]
    })

dim_player_df = pd.DataFrame(players)
dim_player_df.to_csv(dim_player_path, index=False)
print("DIM_PLAYER zapisany do:", dim_player_path)

# ================= GENERUJ FACT_SALES =================
transactions = []
for t in range(1, NUM_TRANSACTIONS + 1):
    player = random.choice(players)
    skin_id = random.choice(skin_ids)
    base_price = skin_price_map[skin_id]

    # whales mogą kupować droższe skiny
    if player["player_segment"] == "whale" and base_price < 1350:
        base_price = random.choice([1350, 1820, 3250])

    transactions.append({
        "transaction_id": t,
        "player_id": player["player_id"],
        "skin_id": skin_id,
        "purchase_date": (
            datetime.now() - timedelta(days=random.randint(1, 365))
        ).date(),
        "price_rp": base_price,
        "quantity": 1
    })

fact_sales_df = pd.DataFrame(transactions)
fact_sales_df.to_csv(fact_sales_path, index=False)
print("FACT_SALES zapisany do:", fact_sales_path)

# ================= PODSUMOWANIE =================
print("===================================")
print("DIM_PLAYER:", len(dim_player_df))
print("DIM_SKIN:", len(dim_skin_df))
print("FACT_SALES:", len(fact_sales_df))
print("Gotowe! Wszystkie pliki zapisane w folderze LOLDW")
