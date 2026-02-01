import pandas as pd
import re
from datetime import datetime
import os

print("="*60)
print("MERGE: Data Dragon + Wiki Prices (FIXED PATHS)")
print("="*60)

# ŚCIEŻKI - POPRAWIONE!
# Skrypt jest tutaj: LOLDW/data/src_data/merge_skins.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # LOLDW/data/src_data/
DATA_DIR = os.path.dirname(SCRIPT_DIR)                   # LOLDW/data/
RAW_DIR = os.path.join(DATA_DIR, "raw")                  # LOLDW/data/raw/

ddragon_path = os.path.join(RAW_DIR, "ddragon_skins.csv")
wiki_path = os.path.join(RAW_DIR, "wiki_skins_clean.csv")
output_path = os.path.join(RAW_DIR, "dim_skins_final.csv")

print(f"\nŚcieżki:")
print(f"  Data Dragon: {ddragon_path}")
print(f"  Wiki: {wiki_path}")
print(f"  Output: {output_path}")

# Wczytaj pliki
print("\n1. Wczytywanie Data Dragon skins...")
try:
    df_ddragon = pd.read_csv(ddragon_path)
    print(f"   ✓ Wczytano {len(df_ddragon)} skinów z Data Dragon")
except FileNotFoundError:
    print(f"   BŁĄD: Nie znaleziono {ddragon_path}")
    exit(1)

# FILTRUJ tylko event-exclusive (NIE esportowe!)
print("\n1a. Filtrowanie skinów event-exclusive...")

exclude_keywords = [
    'prestige',
    'victorious',
    'immortalized legend',
    'risen legend',
    'after hours',
    'springs',
    'fright night',
]

original_count = len(df_ddragon)
mask_exclude = df_ddragon['skin_name'].str.lower().str.contains(
    '|'.join(exclude_keywords), regex=True, na=False
)
df_ddragon = df_ddragon[~mask_exclude].copy()

print(f"   Usunięto {original_count - len(df_ddragon)} skinów event-exclusive")
print(f"   Pozostało {len(df_ddragon)} skinów (zachowano esportowe)")

# Wiki
print("\n2. Wczytywanie Wiki prices...")
try:
    df_wiki = pd.read_csv(wiki_path)
    print(f"   ✓ Wczytano {len(df_wiki)} skinów z Wiki")
except FileNotFoundError:
    print(f"   BŁĄD: Nie znaleziono {wiki_path}")
    exit(1)

# Normalizacja nazw
def normalize_name(name):
    if pd.isna(name):
        return ""
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

print("\n3. Przygotowanie danych...")

df_ddragon['skin_name_norm'] = df_ddragon['skin_name'].apply(normalize_name)

mask_default = df_ddragon['skin_name'] == 'default'
df_ddragon.loc[mask_default, 'skin_name_norm'] = (
    df_ddragon.loc[mask_default, 'champion_name'].apply(normalize_name)
)

print(f"   Data Dragon: {len(df_ddragon)} skinów")
print(f"   Wiki: {len(df_wiki)} skinów")

# MERGE (z release_date!)
print("\n4. Łączenie danych...")
df_merged = df_ddragon.merge(
    df_wiki[['skin_name_norm', 'price_rp', 'rarity', 'release_date']],
    on='skin_name_norm',
    how='left'
)

matched = df_merged['price_rp'].notna().sum()
unmatched = df_merged['price_rp'].isna().sum()

print("\n5. Wyniki matchowania:")
print(f"   Dopasowane: {matched} ({matched/len(df_merged)*100:.1f}%)")
print(f"   Niedopasowane: {unmatched} ({unmatched/len(df_merged)*100:.1f}%)")

# Obsługa defaultów
print("\n6. Obsługa niedopasowanych skinów...")

# FIX: Default = 0 RP ZAWSZE
mask_default = (df_merged['skin_num'] == 0) | (df_merged['skin_name'] == 'default')
df_merged.loc[mask_default, 'rarity'] = 'Default'
df_merged.loc[mask_default, 'price_rp'] = 0

# Usuń resztę bez ceny
mask_unmatched = df_merged['price_rp'].isna() & ~mask_default

if mask_unmatched.sum() > 0:
    print(f"   Usuwam {mask_unmatched.sum()} skinów bez dopasowanej ceny...")
    examples = df_merged[mask_unmatched][['champion_name', 'skin_name']].head(5)
    for _, row in examples.iterrows():
        print(f"     - {row['champion_name']}: {row['skin_name']}")
    df_merged = df_merged[~mask_unmatched].copy()

print(f"   Pozostało {len(df_merged)} skinów")

# Finalne porządki
df_merged['price_rp'] = df_merged['price_rp'].astype(int)

if 'skin_id' in df_merged.columns:
    df_merged = df_merged.drop(columns=['skin_id'])

df_merged.insert(0, 'skin_id', range(1, len(df_merged) + 1))

# Użyj prawdziwej daty z Wiki
df_merged['release_date'] = pd.to_datetime(
    df_merged['release_date'], 
    errors='coerce'
).dt.date

# Kolumny końcowe
final_columns = [
    'skin_id',
    'champion_name',
    'skin_name',
    'rarity',
    'price_rp',
    'release_date',
    'champion_id',
    'skin_num',
    'skin_name_norm'
]

df_final = df_merged[[c for c in final_columns if c in df_merged.columns]]

# Statystyki
print("\n" + "="*60)
print("STATYSTYKI KOŃCOWE")
print("="*60)
print(f"Całkowita liczba skinów: {len(df_final)}")
print(f"Liczba championów: {df_final['champion_name'].nunique()}")

print("\nRozkład rarity:")
for rarity, count in df_final['rarity'].value_counts().items():
    pct = (count / len(df_final)) * 100
    print(f"  {rarity:12s}: {count:4d} ({pct:5.1f}%)")

print("\nRozkład cen:")
for price in [0, 520, 750, 880, 975, 1350, 1820, 3250]:
    count = (df_final['price_rp'] == price).sum()
    if count > 0:
        print(f"  {price:4d} RP: {count:4d}")

# Daty
has_date = df_final['release_date'].notna().sum()
no_date = df_final['release_date'].isna().sum()
print(f"\nRelease dates:")
print(f"  Z datą: {has_date} ({has_date/len(df_final)*100:.1f}%)")
print(f"  Bez daty: {no_date}")

# Zapis
df_final.to_csv(output_path, index=False)

print(f"\n{'='*60}")
print(f"✓ Zapisano: {output_path}")
print(f"{'='*60}")

print("\nPoprawki:")
print("  ✓ Default skiny = 0 RP")
print("  ✓ Release_date z Wiki")
print("  ✓ Zachowano esportowe (T1, DRX)")
print("  ✓ Usunięto event-exclusive")
print("\nGOTOWE!")