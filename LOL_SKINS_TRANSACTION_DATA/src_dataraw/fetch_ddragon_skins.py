import requests
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "csv", "ddragon_skins.csv")

# Pobierz wersję
version = requests.get(
    "https://ddragon.leagueoflegends.com/api/versions.json"
).json()[0]

# Pobierz listę championów
champions = requests.get(
    f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
).json()["data"]

rows = []

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
df.to_csv(OUTPUT_PATH, index=False)

print(f"Zapisano: {OUTPUT_PATH}")
print(f"Liczba skinów: {len(df)}")
