import requests
import pandas as pd
import os

print("FETCH DDRAGON SKINS")

# ŚCIEŻKI – POPRAWIONE

# Jesteśmy w: LOLDW/data/src_data/fetch_ddragon_skins.py
SRC_DIR = os.path.dirname(os.path.abspath(__file__))   # data/src_data
DATA_DIR = os.path.dirname(SRC_DIR)                     # data
RAW_DIR = os.path.join(DATA_DIR, "raw")                 # data/raw

OUTPUT_PATH = os.path.join(RAW_DIR, "ddragon_skins.csv")

# Upewnij się że katalog istnieje
os.makedirs(RAW_DIR, exist_ok=True)

print("OUTPUT:", OUTPUT_PATH)

# DATA DRAGON

print("\nPobieranie wersji Data Dragon...")
version = requests.get(
    "https://ddragon.leagueoflegends.com/api/versions.json"
).json()[0]

print("Wersja:", version)

print("\nPobieranie listy championów...")
champions = requests.get(
    f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
).json()["data"]

rows = []

print("\nPobieranie skinów...")

for champ_id, champ in champions.items():
    champ_data = requests.get(
        f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion/{champ_id}.json"
    ).json()["data"][champ_id]

    for skin in champ_data["skins"]:
        rows.append({
            "champion_id": champ_id,
            "champion_name": champ_data["name"],
            "skin_num": skin["num"],
            "skin_name": skin["name"]
        })

df = pd.DataFrame(rows)

# ZAPIS

df.to_csv(OUTPUT_PATH, index=False)

print("ZAPIS ZAKOŃCZONY")
print(f"Plik: {OUTPUT_PATH}")
print(f"Liczba skinów: {len(df)}")
