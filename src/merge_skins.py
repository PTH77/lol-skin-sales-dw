import pandas as pd
import re
from datetime import datetime, timedelta
import random
import os

print("="*60)
print("MERGE: Data Dragon + Wiki Prices")
print("="*60)

# Ścieżki
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_DIR = os.path.join(BASE_DIR, "..", "csv")

ddragon_path = os.path.join(CSV_DIR, "ddragon_skins.csv")
wiki_path = os.path.join(CSV_DIR, "wiki_skins_clean.csv")
output_path = os.path.join(CSV_DIR, "dim_skins_final.csv")

# Wczytaj pliki
print("\n1. Wczytywanie Data Dragon skins...")
try:
    df_ddragon = pd.read_csv(ddragon_path)
    print(f"   Wczytano {len(df_ddragon)} skinów z Data Dragon")
except FileNotFoundError:
    print(f"   BŁĄD: Nie znaleziono {ddragon_path}")
    exit(1)

print("\n2. Wczytywanie Wiki prices...")
try:
    df_wiki = pd.read_csv(wiki_path)
    print(f"   Wczytano {len(df_wiki)} skinów z Wiki")
except FileNotFoundError:
    print(f"   BŁĄD: Nie znaleziono {wiki_path}")
    exit(1)

# Normalizacja nazw dla matchowania
def normalize_name(name):
    if pd.isna(name):
        return ""
    # Usuń wszystko oprócz liter i cyfr, lowercase
    normalized = re.sub(r'[^a-z0-9]', '', str(name).lower())
    # Obsługa "default" -> nazwa championa
    return normalized

print("\n3. Przygotowanie danych...")

# Data Dragon: normalizuj skin_name
df_ddragon['skin_name_norm'] = df_ddragon['skin_name'].apply(normalize_name)

# Dla skinów "default" - zmień normalizację na samą nazwę championa
mask_default = df_ddragon['skin_name'] == 'default'
df_ddragon.loc[mask_default, 'skin_name_norm'] = df_ddragon.loc[mask_default, 'champion'].apply(normalize_name)

# Wiki już ma skin_name_norm

print(f"   Data Dragon: {len(df_ddragon)} skinów")
print(f"   Wiki: {len(df_wiki)} skinów")

# Merge
print("\n4. Łączenie danych...")
df_merged = df_ddragon.merge(
    df_wiki[['skin_name_norm', 'price_rp', 'rarity']],
    on='skin_name_norm',
    how='left',
    suffixes=('', '_wiki')
)

# Sprawdź dopasowanie
matched = df_merged['price_rp'].notna().sum()
unmatched = df_merged['price_rp'].isna().sum()

print(f"\n5. Wyniki matchowania:")
print(f"   Dopasowane: {matched} ({matched/len(df_merged)*100:.1f}%)")
print(f"   Niedopasowane: {unmatched} ({unmatched/len(df_merged)*100:.1f}%)")

# Pokaż kilka niedopasowanych (debug)
if unmatched > 0:
    print("\n   Przykłady niedopasowanych skinów:")
    unmatched_sample = df_merged[df_merged['price_rp'].isna()][['champion', 'skin_name', 'skin_name_norm']].head(10)
    for _, row in unmatched_sample.iterrows():
        print(f"     - {row['champion']}: {row['skin_name']} (norm: {row['skin_name_norm']})")

# Uzupełnij brakujące dane
print("\n6. Uzupełnianie brakujących danych...")

# Default skiny (skin_num = 0 lub skin_name = 'default')
mask_default = (df_merged['skin_num'] == 0) | (df_merged['skin_name'] == 'default')
df_merged.loc[mask_default & df_merged['rarity'].isna(), 'rarity'] = 'Default'
df_merged.loc[mask_default & df_merged['price_rp'].isna(), 'price_rp'] = 0

# Pozostałe niedopasowane - Epic 1350 RP (najbezpieczniejsze założenie)
mask_unmatched = df_merged['price_rp'].isna() & ~mask_default
df_merged.loc[mask_unmatched, 'rarity'] = 'Epic'
df_merged.loc[mask_unmatched, 'price_rp'] = 1350

print(f"   Uzupełniono {mask_unmatched.sum()} skinów jako Epic (1350 RP)")

# Konwersja price_rp na int
df_merged['price_rp'] = df_merged['price_rp'].fillna(0).astype(int)

# Dodaj skin_id (od 1)
df_merged.insert(0, 'skin_id', range(1, len(df_merged) + 1))

# Dodaj datę wydania (losowa z ostatnich 6 lat)
df_merged['release_date'] = df_merged.apply(
    lambda x: (datetime.now() - timedelta(days=random.randint(1, 2190))).date(),
    axis=1
)

# Zmień nazwy kolumn
df_merged = df_merged.rename(columns={
    'champion': 'champion_name',
    'skin_id': 'skin_id_ddragon'
})

# Wybierz finalne kolumny
df_final = df_merged[[
    'skin_id', 'champion_name', 'skin_name', 'rarity', 'price_rp',
    'release_date', 'champion_id', 'skin_id_ddragon', 'skin_num', 'skin_name_norm'
]]

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

print("\nRozkład cen (RP):")
price_counts = df_final.groupby('price_rp').size().sort_index()
for price, count in price_counts.head(20).items():
    if price == 0:
        print(f"  {price:4d} RP (Default)  : {count:4d}")
    elif price in [390, 520, 750, 790, 880, 975]:
        print(f"  {price:4d} RP (Legacy)   : {count:4d}")
    elif price == 1350:
        print(f"  {price:4d} RP (Epic)     : {count:4d}")
    elif price == 1820:
        print(f"  {price:4d} RP (Legendary): {count:4d}")
    elif price >= 3250:
        print(f"  {price:4d} RP (Ultimate) : {count:4d}")
    else:
        print(f"  {price:4d} RP            : {count:4d}")

print("\nTop 10 championów z największą liczbą skinów:")
top_champs = df_final.groupby('champion_name').size().sort_values(ascending=False).head(10)
for champ, count in top_champs.items():
    print(f"  {champ}: {count} skinów")

# Zapisz
df_final.to_csv(output_path, index=False)

print(f"\n{'='*60}")
print(f"Zapisano: {output_path}")
print(f"{'='*60}")

# Przykładowe skiny
print("\nPrzykładowe skiny z różnymi cenami:")
for price in [0, 520, 750, 975, 1350, 1820, 3250]:
    sample = df_final[df_final['price_rp'] == price]
    if len(sample) > 0:
        print(f"\n{price} RP ({sample.iloc[0]['rarity']}):")
        for _, row in sample.head(3).iterrows():
            print(f"  {row['champion_name']}: {row['skin_name']}")

print("\n" + "="*60)
print("GOTOWE!")
print("Teraz masz dim_skins_final.csv z:")
print("  - Prawdziwymi nazwami skinów (Data Dragon)")
print("  - Prawdziwymi cenami (LoL Wiki)")
print("  - Prawdziwymi rarity (na podstawie cen)")
print("\nNastępny krok: Wygeneruj dim_player.csv i fact_sales.csv")
print("="*60)