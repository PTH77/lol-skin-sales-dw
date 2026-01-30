import pandas as pd
import os

# ================= ŚCIEŻKI =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DDRAGON_PATH = os.path.join(BASE_DIR, "csv", "ddragon_skins.csv")
CDRAGON_PATH = os.path.join(BASE_DIR, "csv", "cdragon_skins.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "csv", "dim_skins_merged.csv")

# ================= FUNKCJE =================
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


# ================= MAIN =================
print("=" * 60)
print("MERGE DDRAGON + CDRAGON")
print("=" * 60)

dd = pd.read_csv(DDRAGON_PATH)
cd = pd.read_csv(CDRAGON_PATH)

print(f"DDRAGON: {len(dd)} skinów")
print(f"CDRAGON: {len(cd)} skinów")

# Normalizacja (defensywnie)
dd["champion_id_norm"] = dd["champion_id"].apply(normalize)
dd["skin_name_norm"] = dd["skin_name"].apply(normalize)

# Merge logiczny (SEDNO)
merged = dd.merge(
    cd[
        [
            "champion_id_norm",
            "skin_name_norm",
            "rarity",
            "price_rp",
            "is_base"
        ]
    ],
    on=["champion_id_norm", "skin_name_norm"],
    how="left"
)

# Fallback biznesowy
merged["rarity"] = merged["rarity"].fillna("Epic")
merged["price_rp"] = merged["price_rp"].fillna(1350)
merged["is_base"] = merged["is_base"].fillna(False)

# Usuwamy base skiny (nie są sprzedawane)
before = len(merged)
merged = merged[merged["price_rp"] > 0]
after = len(merged)

print(f"Usunięto base skiny: {before - after}")

# Klucz hurtowni
merged = merged.reset_index(drop=True)
merged["skin_id_hurtownia"] = merged.index + 1

# Finalny zestaw kolumn
final = merged[
    [
        "skin_id_hurtownia",
        "champion_id",
        "champion_name",
        "skin_num",
        "skin_name",
        "rarity",
        "price_rp"
    ]
]

final.to_csv(OUTPUT_PATH, index=False)

print(f"Zapisano: {OUTPUT_PATH}")
print(f"Liczba skinów sprzedażowych: {len(final)}")
print("=" * 60)
