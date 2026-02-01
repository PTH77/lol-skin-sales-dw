import re
import pandas as pd
import os

print("="*60)
print("PARSOWANIE SKINDATA.LUA - POPRAWIONE")
print("="*60)

# ŚCIEŻKI - POPRAWIONE!
# Skrypt jest tutaj: LOLDW/data/src_data/parse_skins_from_wiki.py
# __file__ = /path/to/LOLDW/data/src_data/parse_skins_from_wiki.py
# dirname(__file__) = /path/to/LOLDW/data/src_data/
# dirname(dirname(__file__)) = /path/to/LOLDW/data/
# Więc: BASE_DIR/raw = /path/to/LOLDW/data/raw/

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # LOLDW/data/src_data/
DATA_DIR = os.path.dirname(SCRIPT_DIR)                   # LOLDW/data/
RAW_DIR = os.path.join(DATA_DIR, "raw")                  # LOLDW/data/raw/

INPUT_LUA = os.path.join(RAW_DIR, "skindata_raw.lua")
OUTPUT_CSV = os.path.join(RAW_DIR, "wiki_skins_clean.csv")

print(f"Szukam pliku: {INPUT_LUA}")

# WCZYTAJ PLIK
print("\nWczytywanie skindata_raw.lua...")
try:
    with open(INPUT_LUA, "r", encoding="utf-8") as f:
        lua_content = f.read()
except FileNotFoundError:
    print(f"BŁĄD: Nie znaleziono pliku!")
    print(f"Sprawdź czy plik istnieje: {INPUT_LUA}")
    print(f"\nAktualny katalog: {os.getcwd()}")
    print(f"Katalog skryptu: {SCRIPT_DIR}")
    print(f"Katalog raw: {RAW_DIR}")
    exit(1)

print(f"Wczytano {len(lua_content):,} znaków")

# PARSER
skins = []
champions_found = []

champion_blocks = re.finditer(
    r'\["([A-Z][^"]+)"\]\s*=\s*\{[^{]*\["id"\]\s*=\s*\d+[^{]*\["skins"\]\s*=\s*\{(.*?)\n\s{4}\}',
    lua_content,
    re.DOTALL
)

for champ_match in champion_blocks:
    champion_name = champ_match.group(1)
    skins_block = champ_match.group(2)
    
    champions_found.append(champion_name)
    
    if len(champions_found) <= 3:
        print(f"\nPrzetwarzanie: {champion_name}")
    
    skin_entries = re.finditer(
        r'\["([^"]+)"\]\s*=\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}(?=\s*,?\s*(?:\["|$))',
        skins_block
    )
    
    for skin_match in skin_entries:
        skin_name = skin_match.group(1)
        skin_props = skin_match.group(2)
        
        if not re.search(r'\["id"\]\s*=\s*\d+', skin_props):
            continue
        
        # Cost
        cost_match = re.search(r'\["cost"\]\s*=\s*(\d+)', skin_props)
        if cost_match:
            cost = int(cost_match.group(1))
        else:
            if '"Special"' in skin_props or "'Special'" in skin_props:
                cost = 0
            else:
                continue
        
        # FIX: Default/Original = 0 RP
        if skin_name == "Original":
            cost = 0
        
        # Release date
        release_match = re.search(r'\["release"\]\s*=\s*"([^"]+)"', skin_props)
        release_date = release_match.group(1) if release_match else None
        
        # Rarity
        if cost == 0:
            if skin_name == "Original":
                rarity = "Default"
            else:
                rarity = "Special"
        elif cost in [390, 520, 750, 790, 880, 975]:
            rarity = "Legacy"
        elif cost == 1350:
            rarity = "Epic"
        elif cost == 1820:
            rarity = "Legendary"
        elif cost >= 3250:
            rarity = "Ultimate"
        else:
            rarity = "Epic"
        
        # Full name
        if skin_name == "Original":
            full_name = champion_name
        else:
            full_name = f"{skin_name} {champion_name}"
        
        skins.append({
            'skin_name': full_name,
            'price_rp': cost,
            'rarity': rarity,
            'champion': champion_name,
            'release_date': release_date
        })
    
    if len(champions_found) % 20 == 0:
        print(f"  Przetworzone: {len(champions_found)} championów, {len(skins)} skinów...")

print(f"\nZnaleziono {len(champions_found)} championów")
print(f"Wyciągnięto {len(skins)} skinów")

# Fallback parser jeśli za mało
if len(skins) < 500:
    print("\n⚠ Za mało skinów! Używam prostszego parsera...")
    
    skins = []
    all_cost_blocks = re.finditer(
        r'\["([^"]+)"\]\s*=\s*\{[^}]*\["cost"\]\s*=\s*(\d+)',
        lua_content
    )
    
    current_champion = None
    
    for match in all_cost_blocks:
        name = match.group(1)
        cost = int(match.group(2))
        
        if name[0].isupper() and ' ' not in name and len(name) > 2:
            context_start = max(0, match.start() - 100)
            context = lua_content[context_start:match.start()]
            
            if '"id"]' in context and '"skins"]' not in context:
                current_champion = name
        
        # Rarity
        if cost in [390, 520, 750, 790, 880, 975]:
            rarity = "Legacy"
        elif cost == 1350:
            rarity = "Epic"
        elif cost == 1820:
            rarity = "Legendary"
        elif cost >= 3250:
            rarity = "Ultimate"
        else:
            rarity = "Epic"
        
        if name == "Original" and current_champion:
            full_name = current_champion
            champ = current_champion
            cost = 0  # FIX
            rarity = "Default"
        elif current_champion and name != current_champion:
            full_name = f"{name} {current_champion}"
            champ = current_champion
        else:
            parts = name.split()
            if len(parts) > 1:
                champ = parts[-1]
                full_name = name
            else:
                continue
        
        skins.append({
            'skin_name': full_name,
            'price_rp': cost,
            'rarity': rarity,
            'champion': champ,
            'release_date': None
        })
    
    print(f"Prostszy parser znalazł: {len(skins)} skinów")

# DataFrame
df = pd.DataFrame(skins)
original_len = len(df)
df = df.drop_duplicates(subset=['skin_name'], keep='first')
print(f"Usuniętch {original_len - len(df)} duplikatów")

# Filtruj tylko Special (zachowaj Default!)
df_filtered = df[df['rarity'] != 'Special']
print(f"Usunięto {len(df) - len(df_filtered)} skinów Special (Prestige/Mythic)")
print(f"Zachowano {len(df_filtered[df_filtered['rarity'] == 'Default'])} skinów Default")
df = df_filtered

# Normalizacja
def normalize_name(name):
    if pd.isna(name):
        return ""
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

df['skin_name_norm'] = df['skin_name'].apply(normalize_name)

# Statystyki
print("\n" + "="*60)
print("STATYSTYKI")
print("="*60)
print(f"Całkowita liczba skinów: {len(df)}")
print(f"Liczba championów: {df['champion'].nunique()}")

print("\nRozkład rarity:")
for rarity, count in df['rarity'].value_counts().items():
    pct = (count / len(df)) * 100
    print(f"  {rarity:12s}: {count:4d} ({pct:5.1f}%)")

print("\nRozkład cen (top 15):")
for price, count in df['price_rp'].value_counts().sort_index().head(15).items():
    print(f"  {price:4d} RP: {count:4d}")

# Release dates
has_date = df['release_date'].notna().sum()
no_date = df['release_date'].isna().sum()
print(f"\nDaty wydania:")
print(f"  Z datą: {has_date} ({has_date/len(df)*100:.1f}%)")
print(f"  Bez daty: {no_date} ({no_date/len(df)*100:.1f}%)")

# Zapisz
df.to_csv(OUTPUT_CSV, index=False)

print(f"\n{'='*60}")
print(f"Zapisano: {OUTPUT_CSV}")
print(f"{'='*60}")

# Przykłady
print("\nPrzykładowe skiny:")
for rarity in ['Default', 'Legacy', 'Epic', 'Legendary', 'Ultimate']:
    sample = df[df['rarity'] == rarity].head(2)
    if len(sample) > 0:
        print(f"\n{rarity}:")
        for _, row in sample.iterrows():
            date_str = f" ({row['release_date']})" if pd.notna(row['release_date']) else ""
            print(f"  {row['skin_name']}: {row['price_rp']} RP{date_str}")

print("\n" + "="*60)
print("GOTOWE!")
print("  ✓ Default skiny mają 0 RP")
print("  ✓ Wyciągnięto release_date z Wiki")
print("  ✓ Zachowano Default, usunięto Special")
print("="*60)