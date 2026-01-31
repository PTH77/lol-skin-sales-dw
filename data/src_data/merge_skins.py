import pandas as pd
import re
from datetime import datetime, timedelta
import random
import os

print("="*60)
print("MERGE: Data Dragon + Wiki Prices")
print("="*60)

# Ścieżki
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw")

ddragon_path = os.path.join(RAW_DIR, "ddragon_skins.csv")
wiki_path = os.path.join(RAW_DIR, "wiki_skins_clean.csv")
output_path = os.path.join(RAW_DIR, "dim_skins_final.csv")

# Wczytaj pliki
print("\n1. Wczytywanie Data Dragon skins...")
try:
    df_ddragon = pd.read_csv(ddragon_path)
    print(f"   Wczytano {len(df_ddragon)} skinów z Data Dragon")
except FileNotFoundError:
    print(f"   BŁĄD: Nie znaleziono {ddragon_path}")
    exit(1)

# -----------------------------
# FILTRUJ skiny bez normalnych cen RP
# -----------------------------
print("\n1a. Filtrowanie skinów bez normalnych cen...")

exclude_keywords = [
    'prestige',
    'victorious',
    'championship',
    'immortalized legend',
    'risen legend',
    'after hours',
    'springs',
    'fright night',
    'drx', 't1', 'edg', 'damwon', 'fpx', 'ig', 'skt',
]

original_count = len(df_ddragon)
mask_exclude = df_ddragon['skin_name'].str.lower().str.contains(
    '|'.join(exclude_keywords), regex=True, na=False
)
df_ddragon = df_ddragon[~mask_exclude].copy()

print(f"   Usunięto {original_count - len(df_ddragon)} skinów bez normalnych cen RP")
print(f"   Pozostało {len(df_ddragon)} skinów")

# -----------------------------
# Wiki
# -----------------------------
print("\n2. Wczytywanie Wiki prices...")
try:
    df_wiki = pd.read_csv(wiki_path)
    print(f"   Wczytano {len(df_wiki)} skinów z Wiki")
except FileNotFoundError:
    print(f"   BŁĄD: Nie znaleziono {wiki_path}")
    exit(1)

# -----------------------------
# Normalizacja nazw
# -----------------------------
def normalize_name(name):
    if pd.isna(name):
        return ""
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

print("\n3. Przygotowanie danych...")

# Data Dragon
df_ddragon['skin_name_norm'] = df_ddragon['skin_name'].apply(normalize_name)

# >>> JEDYNA ISTOTNA POPRAWKA <<<
# używamy champion_name zamiast champion
mask_default = df_ddragon['skin_name'] == 'default'
df_ddragon.loc[mask_default, 'skin_name_norm'] = (
    df_ddragon.loc[mask_default, 'champion_name'].apply(normalize_name)
)

print(f"   Data Dragon: {len(df_ddragon)} skinów")
print(f"   Wiki: {len(df_wiki)} skinów")

# -----------------------------
# MERGE
# -----------------------------
print("\n4. Łączenie danych...")
df_merged = df_ddragon.merge(
    df_wiki[['skin_name_norm', 'price_rp', 'rarity']],
    on='skin_name_norm',
    how='left'
)

matched = df_merged['price_rp'].notna().sum()
unmatched = df_merged['price_rp'].isna().sum()

print("\n5. Wyniki matchowania:")
print(f"   Dopasowane: {matched} ({matched/len(df_merged)*100:.1f}%)")
print(f"   Niedopasowane: {unmatched} ({unmatched/len(df_merged)*100:.1f}%)")

# -----------------------------
# Obsługa defaultów
# -----------------------------
print("\n6. Obsługa niedopasowanych skinów...")

mask_default = (df_merged['skin_num'] == 0) | (df_merged['skin_name'] == 'default')
df_merged.loc[mask_default & df_merged['rarity'].isna(), 'rarity'] = 'Default'
df_merged.loc[mask_default & df_merged['price_rp'].isna(), 'price_rp'] = 0

# Usuń resztę bez ceny
mask_unmatched = df_merged['price_rp'].isna() & ~mask_default

if mask_unmatched.sum() > 0:
    print(f"   Usuwam {mask_unmatched.sum()} skinów bez dopasowanej ceny...")
    df_merged = df_merged[~mask_unmatched].copy()

# -----------------------------
# Finalne porządki
# -----------------------------
df_merged['price_rp'] = df_merged['price_rp'].astype(int)

if 'skin_id' in df_merged.columns:
    df_merged = df_merged.drop(columns=['skin_id'])

df_merged.insert(0, 'skin_id', range(1, len(df_merged) + 1))

df_merged['release_date'] = df_merged.apply(
    lambda _: (datetime.now() - timedelta(days=random.randint(1, 2190))).date(),
    axis=1
)

# Kolumny końcowe (bez zmiany struktury)
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

# -----------------------------
# Zapis
# -----------------------------
df_final.to_csv(output_path, index=False)

print("\n" + "="*60)
print("GOTOWE!")
print(f"Zapisano: {output_path}")
print(f"Liczba skinów: {len(df_final)}")
print("="*60)
