import re
import pandas as pd

print("="*60)
print("PARSOWANIE SKINDATA.LUA - POPRAWIONE")
print("="*60)

# Wczytaj plik
print("\nWczytywanie skindata_raw.lua...")
try:
    with open("skindata_raw.lua", "r", encoding="utf-8") as f:
        lua_content = f.read()
except FileNotFoundError:
    print("BŁĄD: Nie znaleziono pliku skindata_raw.lua")
    exit(1)

print(f"Wczytano {len(lua_content):,} znaków")

# POPRAWIONY PARSER
# Format Lua:
# ["Aatrox"] = {
#   ["id"] = 266,
#   ["skins"] = {
#     ["Original"] = { ["id"] = 0, ["cost"] = 880, ... },
#     ["Justicar"] = { ["id"] = 1, ["cost"] = 975, ... }
#   }
# }

skins = []
champions_found = []

# Wzorzec: znajdź każdego championa i jego blok skinów
# Musimy szukać: ["ChampionName"] = { ... ["skins"] = { ... } }
champion_blocks = re.finditer(
    r'\["([A-Z][^"]+)"\]\s*=\s*\{[^{]*\["id"\]\s*=\s*\d+[^{]*\["skins"\]\s*=\s*\{(.*?)\n\s{4}\}',
    lua_content,
    re.DOTALL
)

for champ_match in champion_blocks:
    champion_name = champ_match.group(1)
    skins_block = champ_match.group(2)
    
    champions_found.append(champion_name)
    
    # Debug dla pierwszych 3
    if len(champions_found) <= 3:
        print(f"\nPrzetwarzanie: {champion_name}")
    
    # W bloku skinów znajdź każdy skin
    # Format: ["Skin Name"] = { ["id"] = X, ["cost"] = Y, ... }
    skin_entries = re.finditer(
        r'\["([^"]+)"\]\s*=\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}(?=\s*,?\s*(?:\["|$))',
        skins_block
    )
    
    for skin_match in skin_entries:
        skin_name = skin_match.group(1)
        skin_props = skin_match.group(2)
        
        # Pomiń jeśli to nie jest skin (np. chromas, voiceactor)
        if not re.search(r'\["id"\]\s*=\s*\d+', skin_props):
            continue
        
        # Wyciągnij cost
        cost_match = re.search(r'\["cost"\]\s*=\s*(\d+)', skin_props)
        if cost_match:
            cost = int(cost_match.group(1))
        else:
            # Sprawdź Special
            if '"Special"' in skin_props or "'Special'" in skin_props:
                cost = 0  # Special (Prestige/Mythic)
            else:
                continue  # Pomiń jeśli brak ceny
        
        # Określ rarity
        if cost == 0:
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
        
        # Pełna nazwa
        if skin_name == "Original":
            full_name = champion_name
        else:
            full_name = f"{skin_name} {champion_name}"
        
        skins.append({
            'skin_name': full_name,
            'price_rp': cost,
            'rarity': rarity,
            'champion': champion_name
        })
    
    # Progress
    if len(champions_found) % 20 == 0:
        print(f"  Przetworzone: {len(champions_found)} championów, {len(skins)} skinów...")

print(f"\nZnaleziono {len(champions_found)} championów")
print(f"Wyciągnięto {len(skins)} skinów")

# Debug - pokaż pierwszych kilka championów
print("\nPierwszych 10 championów:")
for champ in champions_found[:10]:
    count = len([s for s in skins if s['champion'] == champ])
    print(f"  {champ}: {count} skinów")

# Jeśli za mało skinów, użyj prostszego parsera
if len(skins) < 500:
    print("\n⚠️ Za mało skinów! Używam prostszego parsera...")
    
    skins = []
    
    # Prostszy wzorzec - znajdź WSZYSTKIE bloki z cost
    all_cost_blocks = re.finditer(
        r'\["([^"]+)"\]\s*=\s*\{[^}]*\["cost"\]\s*=\s*(\d+)',
        lua_content
    )
    
    current_champion = None
    
    for match in all_cost_blocks:
        name = match.group(1)
        cost = int(match.group(2))
        
        # Jeśli nazwa zaczyna się wielką literą i nie ma spacji - to champion
        if name[0].isupper() and ' ' not in name and len(name) > 2:
            # Sprawdź czy to nie skin innego championa
            # Champions mają id w swoim bloku
            context_start = max(0, match.start() - 100)
            context = lua_content[context_start:match.start()]
            
            if '"id"]' in context and '"skins"]' not in context:
                current_champion = name
        
        # Określ rarity
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
        
        # Dodaj jako skin
        if name == "Original" and current_champion:
            full_name = current_champion
            champ = current_champion
        elif current_champion and name != current_champion:
            full_name = f"{name} {current_champion}"
            champ = current_champion
        else:
            # Spróbuj wyciągnąć championa z nazwy
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
            'champion': champ
        })
    
    print(f"Prostszy parser znalazł: {len(skins)} skinów")

# Usuń duplikaty
df = pd.DataFrame(skins)
original_len = len(df)
df = df.drop_duplicates(subset=['skin_name'], keep='first')
print(f"Usuniętch {original_len - len(df)} duplikatów")

# Filtruj Special
df_filtered = df[df['rarity'] != 'Special']
print(f"Usunięto {len(df) - len(df_filtered)} skinów Special")
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

# Zapisz
output = "wiki_skins_clean.csv"
df.to_csv(output, index=False)

print(f"\n{'='*60}")
print(f"Zapisano: {output}")
print(f"{'='*60}")

# Przykłady
print("\nPrzykładowe skiny:")
for rarity in ['Legacy', 'Epic', 'Legendary', 'Ultimate']:
    sample = df[df['rarity'] == rarity].head(2)
    if len(sample) > 0:
        print(f"\n{rarity}:")
        for _, row in sample.iterrows():
            print(f"  {row['skin_name']}: {row['price_rp']} RP")