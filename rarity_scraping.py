import requests
import pandas as pd
from datetime import datetime, timedelta
import random

# ================= KONFIGURACJA =================
# TYLKO 4 PODSTAWOWE RARITY Z NORMALNYMI CENAMI
RARITY_PRICES = {
    "Legacy": [520, 750, 975],  # Legacy maja 3 mozliwe ceny
    "Epic": 1350,                # Standardowe skiny
    "Legendary": 1820,           # Skiny z nowymi animacjami
    "Ultimate": 3250             # Najdrozsze skiny (Elementalist Lux, DJ Sona)
}

# Lista championów
CHAMPIONS = [
    "Ahri", "Yasuo", "Lux", "Jinx", "Zed", "Ezreal", "Thresh", "Lee Sin",
    "Vayne", "Katarina", "Akali", "Darius", "Jhin", "Kai'Sa", "Sylas",
    "Yone", "Seraphine", "Viego", "Gwen", "Aphelios", "Sett", "Samira",
    "Miss Fortune", "Ashe", "Caitlyn", "Draven", "Pyke", "Ekko", "Aatrox"
]

# Tematy skinów
SKIN_THEMES = [
    "PROJECT", "Star Guardian", "Blood Moon", "Pool Party", "Arcade",
    "Elderwood", "Spirit Blossom", "Battle Academia", "K/DA", "True Damage",
    "High Noon", "Cosmic", "Dark Star", "Snow Day", "Lunar Beast",
    "Crime City", "Pulsefire", "Mecha", "Coven", "Divine Sword"
]

# ================= GENERUJ SKINY =================
print("Generuje dane skinow...")

skins = []
skin_id = 1

for champion in CHAMPIONS:
    # Default skin (zawsze darmowy, nie sprzedawany)
    skins.append({
        "skin_id": skin_id,
        "champion_name": champion,
        "skin_name": f"Default {champion}",
        "rarity": "Default",
        "price_rp": 0,
        "release_date": (datetime.now() - timedelta(days=random.randint(1500, 3000))).date()
    })
    skin_id += 1
    
    # Losuj 3-7 skinów premium dla każdego championa
    num_premium_skins = random.randint(3, 7)
    
    # Rozklad rarity (realistyczny):
    # Epic - 60%, Legacy - 25%, Legendary - 13%, Ultimate - 2%
    rarity_pool = (
        ["Epic"] * 60 +
        ["Legacy"] * 25 +
        ["Legendary"] * 13 +
        ["Ultimate"] * 2
    )
    
    used_themes = []
    
    for _ in range(num_premium_skins):
        # Wybierz temat który jeszcze nie był użyty dla tego championa
        available_themes = [t for t in SKIN_THEMES if t not in used_themes]
        if not available_themes:
            available_themes = SKIN_THEMES  # Reset jeśli wszystkie użyte
        
        theme = random.choice(available_themes)
        used_themes.append(theme)
        
        # Wybierz rarity
        rarity = random.choice(rarity_pool)
        
        # Ustaw cenę na podstawie rarity
        if rarity == "Legacy":
            # Legacy moze miec 3 rozne ceny - losuj jedna
            price_rp = random.choice(RARITY_PRICES[rarity])
        else:
            price_rp = RARITY_PRICES[rarity]
        
        # Losowa data wydania (ostatnie 5 lat)
        release_date = (datetime.now() - timedelta(days=random.randint(1, 1825))).date()
        
        skins.append({
            "skin_id": skin_id,
            "champion_name": champion,
            "skin_name": f"{theme} {champion}",
            "rarity": rarity,
            "price_rp": price_rp,
            "release_date": release_date
        })
        
        skin_id += 1

# ================= KONWERSJA DO DATAFRAME =================
df = pd.DataFrame(skins)

# ================= STATYSTYKI =================
print("\n" + "="*60)
print("PODSUMOWANIE WYGENEROWANYCH DANYCH")
print("="*60)

print(f"\nCalkowita liczba skinow: {len(df)}")
print(f"Liczba championow: {df['champion_name'].nunique()}")
print(f"Liczba skinow premium (bez Default): {len(df[df['rarity'] != 'Default'])}")

print("\nRozklad rarity:")
rarity_counts = df['rarity'].value_counts()
for rarity, count in rarity_counts.items():
    pct = (count / len(df)) * 100
    print(f"  {rarity:12s}: {count:4d} ({pct:5.1f}%)")

print("\nRozklad cen (RP):")
price_counts = df.groupby('price_rp').size().sort_index()
for price, count in price_counts.items():
    if price == 0:
        print(f"  {price:4d} RP (Default)  : {count:4d}")
    elif price in [520, 750, 975]:
        print(f"  {price:4d} RP (Legacy)   : {count:4d}")
    elif price == 1350:
        print(f"  {price:4d} RP (Epic)     : {count:4d}")
    elif price == 1820:
        print(f"  {price:4d} RP (Legendary): {count:4d}")
    elif price == 3250:
        print(f"  {price:4d} RP (Ultimate) : {count:4d}")

# Pokaz rozklad cen Legacy
legacy_skins = df[df['rarity'] == 'Legacy']
if len(legacy_skins) > 0:
    print("\n  Rozklad cen Legacy:")
    legacy_price_counts = legacy_skins['price_rp'].value_counts().sort_index()
    for price, count in legacy_price_counts.items():
        pct = (count / len(legacy_skins)) * 100
        print(f"    {price} RP: {count:3d} ({pct:5.1f}%)")

# ================= WALIDACJA =================
print("\n" + "="*60)
print("WALIDACJA DANYCH")
print("="*60)

# Sprawdz czy wszystkie ceny sa prawidlowe
valid_prices = [0, 520, 750, 975, 1350, 1820, 3250]
invalid_prices = df[~df['price_rp'].isin(valid_prices)]
if len(invalid_prices) > 0:
    print(f"\n[BLAD] Znaleziono {len(invalid_prices)} skinow z nieprawidlowa cena!")
else:
    print("\n[OK] Wszystkie ceny sa prawidlowe")

# Sprawdz czy wszystkie rarity są prawidłowe
valid_rarities = ["Default", "Legacy", "Epic", "Legendary", "Ultimate"]
invalid_rarity = df[~df['rarity'].isin(valid_rarities)]
if len(invalid_rarity) > 0:
    print(f"[BLAD] Znaleziono {len(invalid_rarity)} skinow z nieprawidlowa rarity!")
else:
    print("[OK] Wszystkie rarity sa prawidlowe")

# Sprawdz czy Default skiny maja cene 0
default_skins = df[df['rarity'] == 'Default']
if (default_skins['price_rp'] != 0).any():
    print("[BLAD] Niektore Default skiny maja cene wieksza niz 0!")
else:
    print("[OK] Wszystkie Default skiny maja cene 0 RP")

# Sprawdz duplikaty
duplicates = df[df.duplicated(subset=['champion_name', 'skin_name'], keep=False)]
if len(duplicates) > 0:
    print(f"[UWAGA] Znaleziono {len(duplicates)} duplikatow!")
else:
    print("[OK] Brak duplikatow")

# ================= ZAPIS DO CSV =================
output_file = "dim_skins.csv"
df.to_csv(output_file, index=False)
print("\n" + "="*60)
print(f"Zapisano plik: {output_file}")

# Utworz lookup table (pomocnicza tabela do szybkiego wyszukiwania)
lookup = df[["skin_name", "champion_name", "rarity", "price_rp"]].copy()
lookup["norm_skin"] = lookup["skin_name"].str.lower().str.replace(r'[^a-z0-9]', '', regex=True)
lookup_file = "skin_price_lookup.csv"
lookup.to_csv(lookup_file, index=False)
print(f"Zapisano plik: {lookup_file}")
print("="*60)

# Podglad danych
print("\nPrzykladowe skiny:")
print(df[df['rarity'] != 'Default'].sample(min(10, len(df))).to_string(index=False))

print("\n" + "="*60)
print("GOTOWE! Mozesz teraz uruchomic generate_source.py")
print("="*60)