import requests
import pandas as pd

# Pobierz najnowszą wersję Data Dragon
versions = requests.get(
    "https://ddragon.leagueoflegends.com/api/versions.json"
).json()
version = versions[0]

print("Używana wersja Data Dragon:", version)

# Pobierz listę championów
champions_resp = requests.get(
    f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
)

champions = champions_resp.json()["data"]

rows = []

# Iteruj po championach
for champ_id, champ in champions.items():
    champ_url = (
        f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion/{champ_id}.json"
    )

    resp = requests.get(champ_url)

    if resp.status_code != 200:
        print("Błąd pobierania:", champ_id)
        continue

    champ_data = resp.json()["data"][champ_id]

    for skin in champ_data["skins"]:
        rows.append({
            "champion": champ_data["name"],
            "champion_id": champ_id,
            "skin_id": skin["id"],
            "skin_num": skin["num"],
            "skin_name": skin["name"]
        })

# Zapis do CSV
df = pd.DataFrame(rows)
df.to_csv("dim_skins.csv", index=False)

print("Zapisano dim_skins.csv")
print("Liczba skinów:", len(df))