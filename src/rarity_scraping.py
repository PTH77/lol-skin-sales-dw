import requests
import pandas as pd
import re

print("="*60)
print("POBIERANIE PRAWDZIWYCH DANYCH Z COMMUNITY DRAGON")
print("="*60)

CDRAGON_SKINS_URL = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/skins.json"

print("\nPobieranie danych...")
try:
    response = requests.get(CDRAGON_SKINS_URL, timeout=30)
    skins_data = response.json()
    print(f"Pobrano {len(skins_data)} skinów")
except Exception as e:
    print(f"BŁĄD: {e}")
    exit(1)

# Konwertuj słownik na listę
if isinstance(skins_data, dict):
    skins_list = list(skins_data.values())
else:
    skins_list = skins_data

print(f"Liczba skinów do przetworzenia: {len(skins_list)}")

# Funkcja do wyciągnięcia nazwy championa ze ścieżki
def extract_champion_from_path(path):
    """Wyciąga nazwę championa ze ścieżki do pliku"""
    if not path:
        return None
    
    # Przykład ścieżki: /lol-game-data/assets/ASSETS/Characters/Annie/Skins/Base/...
    # Szukamy wzorca: /Characters/NAZWA/
    match = re.search(r'/Characters/([^/]+)/', path)
    if match:
        return match.group(1)
    
    return None

# Mapowanie tierów
TIER_MAP = {
    "kNoRarity": "Default",
    "kBudget": "Legacy",
    "kStandard": "Legacy", 
    "kDeluxe": "Legacy",
    "kEpic": "Epic",
    "kLegendary": "Legendary",
    "kUltimate": "Ultimate",
    "kMythic": "Ultimate"
}

PRICE_MAP = {
    "Default": 0,
    "Legacy": 750,
    "Epic": 1350,
    "Legendary": 1820,
    "Ultimate": 3250
}

print("\n" + "="*60)
print("PRZETWARZANIE SKINÓW")
print("="*60)

results = []
skipped = 0
skipped_reasons = {"no_champion": 0, "no_name": 0, "other": 0}

for idx, skin in enumerate(skins_list):
    try:
        skin_id = skin.get("id")
        skin_name = skin.get("name", "").strip()
        
        # Wyciągnij nazwę championa ze ścieżki
        splash_path = skin.get("splashPath", "")
        champion_name = extract_champion_from_path(splash_path)
        
        # Jeśli nie ma splashPath, spróbuj innych ścieżek
        if not champion_name:
            tile_path = skin.get("tilePath", "")
            champion_name = extract_champion_from_path(tile_path)
        
        if not champion_name:
            load_path = skin.get("loadScreenPath", "")
            champion_name = extract_champion_from_path(load_path)
        
        # Debug dla pierwszych 5
        if idx < 5:
            print(f"\nSkin {idx + 1}:")
            print(f"  ID: {skin_id}")
            print(f"  Nazwa skina: {skin_name}")
            print(f"  Champion: {champion_name}")
            print(f"  Ścieżka: {splash_path[:80]}..." if splash_path else "  Brak ścieżki")
        
        # Pomiń jeśli brak nazwy lub championa
        if not skin_name:
            skipped += 1
            skipped_reasons["no_name"] += 1
            continue
        
        if not champion_name:
            skipped += 1
            skipped_reasons["no_champion"] += 1
            if idx < 10:
                print(f"    -> Pominięto: brak nazwy championa")
            continue
        
        # Sprawdź czy to default skin (base skin)
        is_base = skin.get("isBase", False)
        
        # Debug dla pierwszych 10
        if idx < 10:
            print(f"    isBase: {is_base}, skinType: {skin.get('skinType', 'brak')}")
        
        if is_base:
            rarity = "Default"
            price_rp = 0
        else:
            # Pobierz tier
            skin_type = skin.get("skinType", "")
            
            # Jeśli skin_type jest pusty lub None, to prawdopodobnie Epic
            if not skin_type or skin_type == "":
                rarity = "Epic"
            else:
                rarity = TIER_MAP.get(skin_type, "Epic")
            
            # Sprawdź rarityGemPath (dodatkowa weryfikacja)
            rarity_gem = skin.get("rarityGemPath", "").lower()
            if "epic" in rarity_gem:
                rarity = "Epic"
            elif "legendary" in rarity_gem:
                rarity = "Legendary"
            elif "ultimate" in rarity_gem:
                rarity = "Ultimate"
            
            price_rp = PRICE_MAP.get(rarity, 1350)
        
        is_legacy = skin.get("isLegacy", False)
        
        results.append({
            "skin_name": skin_name,
            "champion_name": champion_name,
            "rarity": rarity,
            "price_rp": price_rp,
            "is_legacy": is_legacy,
            "skin_id_cdragon": skin_id
        })
        
    except Exception as e:
        continue

print(f"\n\nPrzetworzone: {len(results)} skinów")
print(f"Pominięte: {skipped} skinów")
print(f"  - Brak nazwy: {skipped_reasons['no_name']}")
print(f"  - Brak championa: {skipped_reasons['no_champion']}")
print(f"  - Inne: {skipped_reasons['other']}")

# Konwersja do DataFrame
df_cdragon = pd.DataFrame(results)

if len(df_cdragon) == 0:
    print("\n" + "="*60)
    print("BŁĄD: Nie udało się przetworzyć żadnego skina!")
    print("="*60)
    exit(1)

# Usuń duplikaty
original_count = len(df_cdragon)
df_cdragon = df_cdragon.drop_duplicates(subset=['skin_name', 'champion_name'], keep='first')
print(f"Usunieto {original_count - len(df_cdragon)} duplikatów")

# Statystyki
print("\n" + "="*60)
print("STATYSTYKI")
print("="*60)
print(f"Całkowita liczba skinów: {len(df_cdragon)}")
print(f"Liczba championów: {df_cdragon['champion_name'].nunique()}")

print("\nRozkład rarity:")
rarity_counts = df_cdragon['rarity'].value_counts()
for rarity, count in rarity_counts.items():
    pct = (count / len(df_cdragon)) * 100
    print(f"  {rarity:12s}: {count:4d} ({pct:5.1f}%)")

print("\nRozkład cen:")
price_counts = df_cdragon.groupby('price_rp').size().sort_index()
for price, count in price_counts.items():
    print(f"  {price:4d} RP: {count:4d} skinów")

print("\nTop 10 championów z największą liczbą skinów:")
top_champs = df_cdragon.groupby('champion_name').size().sort_values(ascending=False).head(10)
for champ, count in top_champs.items():
    print(f"  {champ}: {count} skinów")

# Zapisz
output_file = "cdragon_skins_with_rarity.csv"
df_cdragon.to_csv(output_file, index=False)

print(f"\n{'='*60}")
print(f"Zapisano: {output_file}")
print(f"{'='*60}")

# Przykładowe dane
print("\nPrzykładowe skiny (bez Default):")
non_default = df_cdragon[df_cdragon['rarity'] != 'Default']
if len(non_default) > 0:
    sample = non_default.sample(min(15, len(non_default)))
    print(sample[['champion_name', 'skin_name', 'rarity', 'price_rp']].to_string(index=False))
else:
    print("UWAGA: Wszystkie skiny są oznaczone jako Default!")
    print("Przykładowe dane ze wszystkich skinów:")
    sample = df_cdragon.sample(min(15, len(df_cdragon)))
    print(sample[['champion_name', 'skin_name', 'rarity', 'price_rp']].to_string(index=False))

print("\n" + "="*60)
print("SUKCES!")
print("Następny krok: Połącz z dim_skins.csv")
print("Uruchom: python merge_cdragon_with_ddragon.py")
print("="*60)