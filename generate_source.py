import pandas as pd
import random
from datetime import datetime, timedelta
import os

# ================= USTAWIENIA =================
NUM_PLAYERS = 5000
NUM_TRANSACTIONS = 20000

REGIONS = ["EUW", "EUNE", "NA", "KR"]
SEGMENTS = ["casual", "core", "whale"]

# Mapowanie rarity -> ceny RP (zgodne z nowym systemem)
# Legacy ma 3 mozliwe ceny, wiec bedziemy brali z pliku
RARITY_BASE_PRICE = {
    "default": 0,
    "legacy": 750,      # Srednia cena Legacy (520, 750, 975)
    "epic": 1350,
    "legendary": 1820,
    "ultimate": 3250
}

# ================= SCIEZKI =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
skins_path = os.path.join(BASE_DIR,"csv", "dim_skins.csv")
dim_player_path = os.path.join(BASE_DIR,"csv", "dim_player.csv")
fact_sales_path = os.path.join(BASE_DIR, "fact_sales.csv")

print("="*60)
print("GENEROWANIE DANYCH ZRODLOWYCH")
print("="*60)

# ================= WCZYTAJ SKINY =================
print("\nWczytuje plik skinow z:", skins_path)

try:
    dim_skin_df = pd.read_csv(skins_path)
except FileNotFoundError:
    print(f"BLAD: Nie znaleziono pliku {skins_path}")
    print("Uruchom najpierw: python generate_skin_data_clean.py")
    exit(1)

print(f"Wczytano {len(dim_skin_df)} skinow")

# Usun default skiny (nie sa sprzedawane)
if "rarity" in dim_skin_df.columns:
    original_count = len(dim_skin_df)
    dim_skin_df = dim_skin_df[dim_skin_df["rarity"].str.lower() != "default"]
    removed = original_count - len(dim_skin_df)
    print(f"Usunieto {removed} default skinow (nie sa sprzedawane)")
else:
    raise ValueError("BLAD: Plik dim_skins.csv musi miec kolumne 'rarity'!")

# Sprawdz czy jest kolumna price_rp
if "price_rp" not in dim_skin_df.columns:
    raise ValueError("BLAD: Plik dim_skins.csv musi miec kolumne 'price_rp'!")

# Utworz slownik skin_id -> price_rp (bedziemy brali ceny bezposrednio z pliku)
skin_price_map = dict(zip(dim_skin_df["skin_id"], dim_skin_df["price_rp"]))
skin_ids = list(skin_price_map.keys())

print(f"Dostepnych skinow do sprzedazy: {len(skin_ids)}")

# Statystyki cenowe
print("\nRozklad cen skinow:")
price_stats = dim_skin_df.groupby('price_rp').size().sort_index()
for price, count in price_stats.items():
    print(f"  {price:4d} RP: {count:4d} skinow")

# ================= GENERUJ DIM_PLAYER =================
print("\n" + "="*60)
print("GENEROWANIE GRACZY")
print("="*60)

players = []
for i in range(1, NUM_PLAYERS + 1):
    segment = random.choices(SEGMENTS, weights=[0.6, 0.3, 0.1])[0]
    
    # Data utworzenia konta (ostatnie 5 lat)
    account_age_days = random.randint(30, 1825)
    
    players.append({
        "player_id": i,
        "region": random.choice(REGIONS),
        "account_created_date": (
            datetime.now() - timedelta(days=account_age_days)
        ).date(),
        "player_segment": segment
    })

dim_player_df = pd.DataFrame(players)

# Statystyki graczy
print(f"\nWygenerowano {len(dim_player_df)} graczy")
print("\nRozklad segmentow:")
segment_counts = dim_player_df['player_segment'].value_counts()
for segment, count in segment_counts.items():
    pct = (count / len(dim_player_df)) * 100
    print(f"  {segment:8s}: {count:5d} ({pct:5.1f}%)")

print("\nRozklad regionow:")
region_counts = dim_player_df['region'].value_counts()
for region, count in region_counts.items():
    pct = (count / len(dim_player_df)) * 100
    print(f"  {region:4s}: {count:5d} ({pct:5.1f}%)")

dim_player_df.to_csv(dim_player_path, index=False)
print(f"\nZapisano: {dim_player_path}")

# ================= GENERUJ FACT_SALES =================
print("\n" + "="*60)
print("GENEROWANIE TRANSAKCJI")
print("="*60)

# Segmentacja skinow po cenie dla roznych typow graczy
cheap_skins = [sid for sid, price in skin_price_map.items() if price <= 750]
mid_skins = [sid for sid, price in skin_price_map.items() if 751 <= price <= 1350]
expensive_skins = [sid for sid, price in skin_price_map.items() if price >= 1351]

print(f"\nSkiny tanie (<=750 RP): {len(cheap_skins)}")
print(f"Skiny srednie (751-1350 RP): {len(mid_skins)}")
print(f"Skiny drogie (>=1351 RP): {len(expensive_skins)}")

transactions = []
for t in range(1, NUM_TRANSACTIONS + 1):
    player = random.choice(players)
    segment = player["player_segment"]
    
    # Wybor skina na podstawie segmentu gracza
    if segment == "whale":
        # Whales preferuja drogie skiny (70% drogie, 20% srednie, 10% tanie)
        skin_pool = (
            expensive_skins * 7 +
            mid_skins * 2 +
            cheap_skins * 1
        )
    elif segment == "core":
        # Core preferuja srednie i drogie (50% srednie, 30% drogie, 20% tanie)
        skin_pool = (
            mid_skins * 5 +
            expensive_skins * 3 +
            cheap_skins * 2
        )
    else:  # casual
        # Casual preferuja tanie i srednie (50% tanie, 40% srednie, 10% drogie)
        skin_pool = (
            cheap_skins * 5 +
            mid_skins * 4 +
            expensive_skins * 1
        )
    
    # Jesli pool jest pusty (edge case), uzyj wszystkich skinow
    if not skin_pool:
        skin_pool = skin_ids
    
    skin_id = random.choice(skin_pool)
    price_rp = skin_price_map[skin_id]
    
    # Data zakupu (ostatni rok)
    purchase_days_ago = random.randint(1, 365)
    purchase_date = (datetime.now() - timedelta(days=purchase_days_ago)).date()
    
    transactions.append({
        "transaction_id": t,
        "player_id": player["player_id"],
        "skin_id": skin_id,
        "purchase_date": purchase_date,
        "price_rp": price_rp,
        "quantity": 1
    })

fact_sales_df = pd.DataFrame(transactions)

# Statystyki transakcji
print(f"\nWygenerowano {len(fact_sales_df)} transakcji")

print("\nRozklad transakcji po segmentach:")
sales_by_segment = fact_sales_df.merge(
    dim_player_df[['player_id', 'player_segment']], 
    on='player_id'
)
segment_sales = sales_by_segment['player_segment'].value_counts()
for segment, count in segment_sales.items():
    pct = (count / len(fact_sales_df)) * 100
    print(f"  {segment:8s}: {count:5d} transakcji ({pct:5.1f}%)")

print("\nRozklad wartosci transakcji:")
price_distribution = fact_sales_df['price_rp'].value_counts().sort_index()
for price, count in price_distribution.items():
    pct = (count / len(fact_sales_df)) * 100
    print(f"  {price:4d} RP: {count:5d} transakcji ({pct:5.1f}%)")

# Calkowity przychod
total_revenue = fact_sales_df['price_rp'].sum()
print(f"\nCalkowity przychod: {total_revenue:,} RP")
print(f"Srednia wartosc transakcji: {total_revenue / len(fact_sales_df):.2f} RP")

fact_sales_df.to_csv(fact_sales_path, index=False)
print(f"\nZapisano: {fact_sales_path}")

# ================= PODSUMOWANIE =================
print("\n" + "="*60)
print("PODSUMOWANIE")
print("="*60)
print(f"\nDIM_PLAYER: {len(dim_player_df)} graczy")
print(f"DIM_SKIN: {len(dim_skin_df)} skinow (bez Default)")
print(f"FACT_SALES: {len(fact_sales_df)} transakcji")
print(f"\nPliki zapisane w: {BASE_DIR}")
print("  - dim_player.csv")
print("  - fact_sales.csv")
print("\nPlik dim_skins.csv juz istnial (wygenerowany przez generate_skin_data_clean.py)")
print("\n" + "="*60)
print("GOTOWE! Dane sa gotowe do zaladowania do hurtowni.")
print("="*60)