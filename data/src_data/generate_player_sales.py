import pandas as pd
import random
from datetime import datetime, timedelta
import os

# ================= USTAWIENIA =================
NUM_PLAYERS = 5000
NUM_TRANSACTIONS = 20000
ERROR_RATE = 0.10  # 10% błędnych danych w transakcjach

REGIONS = ["EUW", "EUNE", "NA", "KR"]
SEGMENTS = ["casual", "core", "whale"]

# ================= SCIEZKI =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, "..", "raw")
DATA_RAW_DIR = os.path.abspath(DATA_RAW_DIR)

skins_path = os.path.join(DATA_RAW_DIR, "dim_skins_final.csv")
dim_player_path = os.path.join(DATA_RAW_DIR, "dim_player.csv")
fact_sales_path = os.path.join(DATA_RAW_DIR, "fact_sales.csv")

print("="*60)
print("GENEROWANIE GRACZY I TRANSAKCJI")
print("="*60)

# ================= WCZYTAJ SKINY =================
print("\nWczytywanie skinów z dim_skins_final.csv...")

try:
    dim_skin_df = pd.read_csv(skins_path)
except FileNotFoundError:
    print(f"BŁĄD: Nie znaleziono pliku {skins_path}")
    print("Uruchom najpierw: python merge_final.py")
    exit(1)

print(f"Wczytano {len(dim_skin_df)} skinów")

# Usuń default skiny (nie są sprzedawane)
original_count = len(dim_skin_df)
dim_skin_df = dim_skin_df[dim_skin_df["rarity"] != "Default"].copy()
removed = original_count - len(dim_skin_df)
print(f"Usunięto {removed} default skinów (nie są sprzedawane)")

# Słownik skin_id -> price_rp
skin_price_map = dict(zip(
    dim_skin_df["skin_id"], 
    dim_skin_df["price_rp"]
))
skin_ids = list(skin_price_map.keys())

print(f"Dostępnych skinów do sprzedaży: {len(skin_ids)}")

# Statystyki cenowe
print("\nRozkład cen skinów:")
price_stats = dim_skin_df.groupby('price_rp').size().sort_index()
for price, count in price_stats.items():
    print(f"  {price:4d} RP: {count:4d} skinów")

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
print("\nRozkład segmentów:")
segment_counts = dim_player_df['player_segment'].value_counts()
for segment, count in segment_counts.items():
    pct = (count / len(dim_player_df)) * 100
    print(f"  {segment:8s}: {count:5d} ({pct:5.1f}%)")

print("\nRozkład regionów:")
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

# Segmentacja skinów po cenie dla różnych typów graczy
cheap_skins = [sid for sid, price in skin_price_map.items() if price <= 750]
mid_skins = [sid for sid, price in skin_price_map.items() if 751 <= price <= 1350]
expensive_skins = [sid for sid, price in skin_price_map.items() if price >= 1351]

print(f"\nSkiny tanie (<=750 RP): {len(cheap_skins)}")
print(f"Skiny średnie (751-1350 RP): {len(mid_skins)}")
print(f"Skiny drogie (>=1351 RP): {len(expensive_skins)}")

transactions = []

# Tracking błędów
error_log = {
    'null_player_id': 0,
    'null_skin_id': 0,
    'null_price': 0,
    'negative_price': 0,
    'zero_quantity': 0,
    'invalid_player_id': 0,
    'invalid_skin_id': 0,
    'future_date': 0,
    'past_date': 0
}

for t in range(1, NUM_TRANSACTIONS + 1):
    player = random.choice(players)
    segment = player["player_segment"]
    
    # Wybór skina na podstawie segmentu gracza
    if segment == "whale":
        # Whales preferują drogie skiny (70% drogie, 20% średnie, 10% tanie)
        if expensive_skins:
            skin_pool = (
                expensive_skins * 7 +
                (mid_skins * 2 if mid_skins else []) +
                (cheap_skins * 1 if cheap_skins else [])
            )
        else:
            skin_pool = skin_ids
    elif segment == "core":
        # Core preferują średnie i drogie (50% średnie, 30% drogie, 20% tanie)
        if mid_skins:
            skin_pool = (
                mid_skins * 5 +
                (expensive_skins * 3 if expensive_skins else []) +
                (cheap_skins * 2 if cheap_skins else [])
            )
        else:
            skin_pool = skin_ids
    else:  # casual
        # Casual preferują tanie i średnie (50% tanie, 40% średnie, 10% drogie)
        if cheap_skins:
            skin_pool = (
                cheap_skins * 5 +
                (mid_skins * 4 if mid_skins else []) +
                (expensive_skins * 1 if expensive_skins else [])
            )
        else:
            skin_pool = skin_ids
    
    # Jeśli pool jest pusty (edge case), użyj wszystkich skinów
    if not skin_pool:
        skin_pool = skin_ids
    
    skin_id = random.choice(skin_pool)
    price_rp = skin_price_map[skin_id]
    
    # Data zakupu (ostatni rok)
    purchase_days_ago = random.randint(1, 365)
    purchase_date = (datetime.now() - timedelta(days=purchase_days_ago)).date()
    
    quantity = 1
    player_id = player["player_id"]
    
    # ================= WSTRZYKNIJ BŁĘDY (10% transakcji) =================
    is_error = random.random() < ERROR_RATE
    
    if is_error:
        error_type = random.choice([
            'null_player_id',
            'null_skin_id', 
            'null_price',
            'negative_price',
            'zero_quantity',
            'invalid_player_id',
            'invalid_skin_id',
            'future_date',
            'past_date'
        ])
        
        if error_type == 'null_player_id':
            player_id = None
            error_log['null_player_id'] += 1
            
        elif error_type == 'null_skin_id':
            skin_id = None
            error_log['null_skin_id'] += 1
            
        elif error_type == 'null_price':
            price_rp = None
            error_log['null_price'] += 1
            
        elif error_type == 'negative_price':
            price_rp = random.randint(-1000, -1)
            error_log['negative_price'] += 1
            
        elif error_type == 'zero_quantity':
            quantity = 0
            error_log['zero_quantity'] += 1
            
        elif error_type == 'invalid_player_id':
            player_id = random.randint(10000, 99999)  # Nieistniejący
            error_log['invalid_player_id'] += 1
            
        elif error_type == 'invalid_skin_id':
            skin_id = random.randint(10000, 99999)  # Nieistniejący
            error_log['invalid_skin_id'] += 1
            
        elif error_type == 'future_date':
            purchase_date = (datetime.now() + timedelta(days=random.randint(1, 365))).date()
            error_log['future_date'] += 1
            
        elif error_type == 'past_date':
            purchase_date = (datetime.now() - timedelta(days=random.randint(3000, 5000))).date()
            error_log['past_date'] += 1
    
    transactions.append({
        "transaction_id": t,
        "player_id": player_id,
        "skin_id": skin_id,
        "purchase_date": purchase_date,
        "price_rp": price_rp,
        "quantity": quantity
    })

# Dodaj 1% duplikatów
num_duplicates = int(NUM_TRANSACTIONS * 0.01)
duplicates = random.sample(transactions, num_duplicates)
for dup in duplicates:
    new_dup = dup.copy()
    new_dup['transaction_id'] = len(transactions) + 1
    transactions.append(new_dup)

fact_sales_df = pd.DataFrame(transactions)

# Statystyki transakcji
print(f"\nWygenerowano {len(fact_sales_df)} transakcji")
print(f"  - Czyste: {NUM_TRANSACTIONS - sum(error_log.values())}")
print(f"  - Błędne: {sum(error_log.values())} ({sum(error_log.values())/len(fact_sales_df)*100:.1f}%)")

if sum(error_log.values()) > 0:
    print("\nRaport błędów:")
    for error_type, count in sorted(error_log.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {error_type:20s}: {count:4d}")

print("\nRozkład transakcji po segmentach:")
sales_by_segment = fact_sales_df.merge(
    dim_player_df[['player_id', 'player_segment']], 
    on='player_id'
)
segment_sales = sales_by_segment['player_segment'].value_counts()
for segment, count in segment_sales.items():
    pct = (count / len(fact_sales_df)) * 100
    print(f"  {segment:8s}: {count:5d} transakcji ({pct:5.1f}%)")

print("\nTop 10 najczęściej kupowanych cen:")
price_distribution = fact_sales_df['price_rp'].value_counts().sort_values(ascending=False).head(10)
for price, count in price_distribution.items():
    pct = (count / len(fact_sales_df)) * 100
    price_label = "NULL" if pd.isna(price) else int(price)
    print(f"  {price_label:>4} RP: {count:5d} transakcji ({pct:5.1f}%)")


# Całkowity przychód
total_revenue = fact_sales_df['price_rp'].sum()
print(f"\nCałkowity przychód: {total_revenue:,} RP")
print(f"Średnia wartość transakcji: {total_revenue / len(fact_sales_df):.2f} RP")

# Przychód po segmentach
print("\nPrzychód po segmentach graczy:")
revenue_by_segment = sales_by_segment.groupby('player_segment')['price_rp'].agg(['sum', 'mean', 'count'])
for segment in revenue_by_segment.index:
    row = revenue_by_segment.loc[segment]
    print(f"  {segment:8s}: {row['sum']:>10,.0f} RP ({row['count']:>5,.0f} transakcji, avg {row['mean']:>6.0f} RP)")

fact_sales_df.to_csv(fact_sales_path, index=False)
print(f"\nZapisano: {fact_sales_path}")

# ================= PODSUMOWANIE =================
print("\n" + "="*60)
print("PODSUMOWANIE")
print("="*60)
print(f"\nDIM_PLAYER: {len(dim_player_df)} graczy")
print(f"DIM_SKIN: {len(dim_skin_df)} skinów (bez Default)")
print(f"FACT_SALES: {len(fact_sales_df)} transakcji")
print(f"\nPliki zapisane w: {DATA_RAW_DIR}")