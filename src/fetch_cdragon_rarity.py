import requests
import pandas as pd
import re
import os

# ================= USTAWIENIA =================
CDRAGON_URL = (
    "https://raw.communitydragon.org/latest/"
    "plugins/rcp-be-lol-game-data/global/default/v1/skins.json"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "csv", "cdragon_skins.csv")

PRICE_MAP = {
    "Default": 0,
    "Epic": 1350,
    "Legendary": 1820,
    "Ultimate": 3250
}

# ================= FUNKCJE =================
def extract_champion_id(path: str):
    """
    Wyciąga champion_id z patha:
    /Characters/TwistedFate/Skins/...
    """
    if not path:
        return None
    match = re.search(r"/Characters/([^/]+)/", path)
    return match.group(1) if match else None


def normalize(text):
    if not isinstance(text, str):
        return None
    return (
        text.lower()
        .replace(" ", "")
        .replace("'", "")
        .replace("&", "and")
        .replace(".", "")
    )


def detect_rarity(skin: dict):
    """
    Jedyna poprawna logika rarity:
    - isBase -> Default
    - inaczej Epic / Legendary / Ultimate
    """
    if skin.get("isBase", False):
        return "Default"

    skin_type = (skin.get("skinType") or "").lower()
    gem_path = (skin.get("rarityGemPath") or "").lower()

    if "ultimate" in skin_type or "ultimate" in gem_path:
        return "Ultimate"
    if "legendary" in skin_type or "legendary" in gem_path:
        return "Legendary"

    return "Epic"


# ================= MAIN =================
print("=" * 60)
print("FETCH COMMUNITY DRAGON – RARITY")
print("=" * 60)

print("Pobieranie danych z CommunityDragon...")
resp = requests.get(CDRAGON_URL, timeout=30)
resp.raise_for_status()
skins_data = resp.json()

if isinstance(skins_data, dict):
    skins_data = list(skins_data.values())

print(f"Pobrano {len(skins_data)} rekordów")

rows = []
skipped = 0

for skin in skins_data:
    champion_id = extract_champion_id(skin.get("splashPath", ""))
    if not champion_id:
        skipped += 1
        continue

    skin_name = skin.get("name")
    if not skin_name:
        skipped += 1
        continue

    rarity = detect_rarity(skin)
    price_rp = PRICE_MAP[rarity]

    rows.append({
        "champion_id": champion_id,
        "skin_name": skin_name,
        "rarity": rarity,
        "price_rp": price_rp,
        "is_base": skin.get("isBase", False),
        "champion_id_norm": normalize(champion_id),
        "skin_name_norm": normalize(skin_name)
    })

df = pd.DataFrame(rows)

print(f"Przetworzone: {len(df)}")
print(f"Pominięte: {skipped}")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)

print(f"Zapisano: {OUTPUT_PATH}")
print("=" * 60)
