import re
import pandas as pd

print("="*60)
print("PARSOWANIE SKINDATA.LUA - TYLKO NAZWA, CENA, RARITY")
print("="*60)

# Wczytaj plik Lua
print("\nWczytywanie skindata_raw.lua...")
try:
    with open("skindata_raw.lua", "r", encoding="utf-8") as f:
        lua_content = f.read()
except FileNotFoundError:
    print("BŁĄD: Nie znaleziono pliku skindata_raw.lua")
    print("Uruchom najpierw: python scrape_wiki_better.py")
    exit(1)

print(f"Wczytano {len(lua_content)} znaków")

# Parsowanie - wyciągnij championa i jego skiny
# Wzorzec: ["Champion"] = { ["id"] = X, ["skins"] = { ... } }
champion_pattern = r'\["([^"]+)"\]\s*=\s*\{[^}]*\["skins"\]\s*=\s*\{(.*?)\n\s*\}\s*\}'

skins = []
processed_champions = 0

for champ_match in re.finditer(champion_pattern, lua_content, re.DOTALL):
    champion_name = champ_match.group(1)
    skins_block = champ_match.group(2)
    
    # Dla każdego championa, wyciągnij jego skiny
    # Wzorzec: ["Skin Name"] = { ... ["cost"] = 1350, ... }
    skin_pattern = r'\["([^"]+)"\]\s*=\s*\{([^}]+)\}'
    
    for skin_match in re.finditer(skin_pattern, skins_block):
        skin_name = skin_match.group(1)
        skin_properties = skin_match.group(2)
        
        # Wyciągnij cost
        cost_match = re.search(r'\["cost"\]\s*=\s*(\d+)', skin_properties)
        if cost_match:
            cost = int(cost_match.group(1))
        else:
            # Sprawdź czy to "Special" (Prestige/Mythic)
            special_match = re.search(r'\["cost"\]\s*=\s*"Special"', skin_properties)
            if special_match:
                cost = 0  # Prestige/Mythic - oznacz jako 0
            else:
                continue  # Pomiń jeśli brak ceny
        
        # Określ rarity na podstawie ceny
        if cost == 0:
            rarity = "Special"  # Prestige/Mythic/Event
        elif cost <= 520:
            rarity = "Legacy"
        elif cost <= 750:
            rarity = "Legacy"
        elif cost <= 975:
            rarity = "Legacy"
        elif cost <= 1350:
            rarity = "Epic"
        elif cost <= 1820:
            rarity = "Legendary"
        elif cost >= 3250:
            rarity = "Ultimate"
        else:
            rarity = "Epic"
        
        # Pełna nazwa skina = Skin Name + Champion
        if skin_name == "Original":
            full_skin_name = champion_name  # Original = nazwa championa
        else:
            full_skin_name = f"{skin_name} {champion_name}"
        
        skins.append({
            'skin_name': full_skin_name,
            'price_rp': cost,
            'rarity': rarity,
            'champion': champion_name
        })
    
    processed_champions += 1
    if processed_champions % 10 == 0:
        print(f"  Przetworzone: {processed_champions} championów...")

print(f"\nCałkowita liczba skinów: {len(skins)}")

# DataFrame
df = pd.DataFrame(skins)

# Filtruj Special (Prestige/Mythic) jeśli chcesz tylko normalne ceny
print("\nCzy chcesz usunąć skiny Special (Prestige/Mythic)? (t/n): ", end="")
# Automatycznie usuń Special
df_filtered = df[df['rarity'] != 'Special'].copy()
print(f"Usunięto {len(df) - len(df_filtered)} skinów Special")
df = df_filtered

# Normalizacja nazw
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

print("\nRozkład cen (RP):")
price_counts = df['price_rp'].value_counts().sort_index()
for price, count in price_counts.head(15).items():
    print(f"  {price:4d} RP: {count:4d} skinów")

if len(price_counts) > 15:
    print(f"  ... i {len(price_counts) - 15} innych cen")

# Zapisz
output_file = "wiki_skins_clean.csv"
df.to_csv(output_file, index=False)

print(f"\n{'='*60}")
print(f"Zapisano: {output_file}")
print(f"{'='*60}")

# Przykłady
print("\nPrzykładowe skiny z każdej rarity:")
for rarity in ['Legacy', 'Epic', 'Legendary', 'Ultimate']:
    sample = df[df['rarity'] == rarity].head(3)
    if len(sample) > 0:
        print(f"\n{rarity}:")
        for _, row in sample.iterrows():
            print(f"  {row['skin_name']}: {row['price_rp']} RP")

print("\n" + "="*60)
print("GOTOWE!")
print("Plik wiki_skins_clean.csv zawiera:")
print("  - skin_name (np. 'K/DA Ahri')")
print("  - price_rp (np. 1350)")
print("  - rarity (Legacy/Epic/Legendary/Ultimate)")
print("  - champion (np. 'Ahri')")
print("  - skin_name_norm (znormalizowana nazwa)")
print("\nNastępny krok: Połącz z dim_skins.csv")
print("="*60)