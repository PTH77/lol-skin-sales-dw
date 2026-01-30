import pandas as pd
import os

# ================= SCIEZKI DO PLIKOW =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dim_skins_path = os.path.join(BASE_DIR,"csv", "dim_skins.csv")
lookup_path = os.path.join(BASE_DIR,"csv", "skin_price_lookup.csv")
output_path = os.path.join(BASE_DIR, "dim_skins_merged.csv")

print("="*60)
print("MERGE: dim_skins.csv + skin_price_lookup.csv")
print("="*60)

# ================= WCZYTAJ PLIKI =================
print("\nWczytuje pliki...")

try:
    dim_skins = pd.read_csv(dim_skins_path)
    print(f"dim_skins.csv: {len(dim_skins)} wierszy")
except FileNotFoundError:
    print(f"BLAD: Nie znaleziono pliku {dim_skins_path}")
    exit(1)

try:
    lookup = pd.read_csv(lookup_path)
    print(f"skin_price_lookup.csv: {len(lookup)} wierszy")
except FileNotFoundError:
    print(f"BLAD: Nie znaleziono pliku {lookup_path}")
    exit(1)

# ================= ANALIZA KOLUMN =================
print("\n" + "="*60)
print("ANALIZA KOLUMN")
print("="*60)

print("\nKolumny w dim_skins.csv:")
for col in dim_skins.columns:
    print(f"  - {col}")

print("\nKolumny w skin_price_lookup.csv:")
for col in lookup.columns:
    print(f"  - {col}")

# Sprawdz ktore kolumny sa wspolne
common_cols = set(dim_skins.columns) & set(lookup.columns)
print(f"\nWspolne kolumny: {list(common_cols)}")

# Sprawdz ktore kolumny sa tylko w lookup
lookup_only = set(lookup.columns) - set(dim_skins.columns)
print(f"Tylko w lookup: {list(lookup_only)}")

# ================= MERGE =================
print("\n" + "="*60)
print("MERGOWANIE")
print("="*60)

# Jezeli dim_skins juz ma norm_skin, to nie merguj
if 'norm_skin' in dim_skins.columns:
    print("\nINFO: dim_skins.csv juz zawiera kolumne 'norm_skin'")
    print("Mergowanie nie jest potrzebne!")
    print("\nCzy chcesz nadpisac istniejaca kolumne? (t/n): ", end="")
    response = input().lower()
    
    if response != 't':
        print("\nMergowanie anulowane.")
        exit(0)
    else:
        # Usun stara kolumne norm_skin
        dim_skins = dim_skins.drop(columns=['norm_skin'])
        print("Usunieto stara kolumne 'norm_skin'")

# Merge na podstawie skin_name (LEFT JOIN - zachowaj wszystkie z dim_skins)
print("\nLacze pliki na podstawie kolumny 'skin_name'...")

merged = pd.merge(
    dim_skins,
    lookup[['skin_name', 'norm_skin']],  # Bierzemy tylko norm_skin z lookup
    on='skin_name',
    how='left'
)

print(f"Polaczono: {len(merged)} wierszy")

# ================= WALIDACJA =================
print("\n" + "="*60)
print("WALIDACJA")
print("="*60)

# Sprawdz czy sa braki w norm_skin
missing_norm = merged[merged['norm_skin'].isna()]
if len(missing_norm) > 0:
    print(f"\nUWAGA: {len(missing_norm)} skinow nie ma przypisanego norm_skin:")
    print(missing_norm[['skin_id', 'skin_name', 'champion_name']].head())
else:
    print("\n[OK] Wszystkie skiny maja przypisany norm_skin")

# Sprawdz czy liczba wierszy sie zgadza
if len(merged) == len(dim_skins):
    print("[OK] Liczba wierszy sie zgadza")
else:
    print(f"[UWAGA] Liczba wierszy sie nie zgadza! dim_skins: {len(dim_skins)}, merged: {len(merged)}")

# Sprawdz duplikaty
duplicates = merged[merged.duplicated(subset=['skin_id'], keep=False)]
if len(duplicates) > 0:
    print(f"[UWAGA] Znaleziono {len(duplicates)} duplikatow skin_id!")
else:
    print("[OK] Brak duplikatow")

# ================= ZAPIS =================
print("\n" + "="*60)
print("ZAPIS")
print("="*60)

merged.to_csv(output_path, index=False)
print(f"\nZapisano polaczony plik: {output_path}")
print(f"Liczba wierszy: {len(merged)}")
print(f"Liczba kolumn: {len(merged.columns)}")

print("\nKolumny w polaczonym pliku:")
for col in merged.columns:
    print(f"  - {col}")

# ================= PRZYKLADOWE DANE =================
print("\n" + "="*60)
print("PRZYKLADOWE DANE")
print("="*60)

print("\nPrzykladowe skiny z norm_skin:")
sample = merged[merged['rarity'] != 'Default'].sample(min(5, len(merged)))
print(sample[['skin_name', 'champion_name', 'rarity', 'price_rp', 'norm_skin']].to_string(index=False))

print("\n" + "="*60)
print("GOTOWE!")
print("="*60)
print(f"\nPlik zapisany jako: {output_path}")
print("Mozesz teraz uzyc tego pliku w swoim projekcie hurtowni.")