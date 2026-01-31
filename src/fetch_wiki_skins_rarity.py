from playwright.sync_api import sync_playwright
import pandas as pd
import re
import time

print("="*60)
print("SCRAPING PRAWDZIWYCH CEN Z LOL WIKI (PLAYWRIGHT)")
print("="*60)

# URL bezpośrednio do edycji - pokazuje pełny kod
MODULE_URL = "https://leagueoflegends.fandom.com/wiki/Module:SkinData/data?action=edit"

print("\nUruchamianie przeglądarki...")

with sync_playwright() as p:
    # Uruchom przeglądarkę (headless=False żeby widzieć)
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    print(f"Ładowanie strony: {MODULE_URL}")
    page.goto(MODULE_URL, wait_until="domcontentloaded", timeout=60000)
    
    # Poczekaj aż strona się załaduje
    print("Czekam na załadowanie edytora...")
    time.sleep(5)  # Dłużej bo ładuje edytor
    
    print("Pobieranie kodu Lua...")
    lua_content = None
    
    # Próba 1: textarea (tryb edycji)
    if page.locator("textarea#wpTextbox1").count() > 0:
        lua_content = page.text_content("textarea#wpTextbox1")
        print(f"Znaleziono kod w textarea: {len(lua_content)} znaków")
    
    # Próba 2: .mw-code lub .mw-parser-output pre
    if not lua_content or len(lua_content) < 10000:
        if page.locator(".mw-code").count() > 0:
            lua_content = page.text_content(".mw-code")
            print(f"Znaleziono kod w .mw-code: {len(lua_content)} znaków")
    
    # Próba 3: Wszystkie elementy <pre>
    if not lua_content or len(lua_content) < 10000:
        if page.locator("pre").count() > 0:
            # Może być kilka <pre>, weź najdłuższy
            all_pres = page.locator("pre").all()
            for pre_elem in all_pres:
                content = pre_elem.text_content()
                if len(content) > (len(lua_content) if lua_content else 0):
                    lua_content = content
            print(f"Znaleziono kod w <pre>: {len(lua_content) if lua_content else 0} znaków")
    
    browser.close()

# Sprawdź co udało się pobrać
if not lua_content:
    print("\nBŁĄD: Nie udało się pobrać żadnego kodu!")
    exit(1)

print(f"\nPobrano {len(lua_content)} znaków")

# Zapisz surowy backup
with open("skindata_raw.lua", "w", encoding="utf-8") as f:
    f.write(lua_content)
print("Zapisano backup: skindata_raw.lua")

# Debug
print("\nFragment kodu (pierwsze 300 znaków):")
print(lua_content[:300])

# Jeśli to HTML, wyciągnij kod
if "<html" in lua_content.lower() or "<!doctype" in lua_content.lower():
    print("\nWykryto HTML, wyciągam czysty kod Lua...")
    
    # Dekoduj HTML entities
    import html
    lua_content = html.unescape(lua_content)
    
    # Spróbuj wyciągnąć return {...}
    match = re.search(r'(return\s*\{.*\})', lua_content, re.DOTALL)
    if match:
        lua_content = match.group(1)
        print(f"Wyciągnięto kod Lua: {len(lua_content)} znaków")

# Sprawdź rozmiar
if len(lua_content) < 50000:
    print(f"\n⚠️ UWAGA: Pobrano tylko {len(lua_content)} znaków")
    print("Pełny moduł SkinData ma zwykle >200,000 znaków")
    print("\nMOŻLIWE ROZWIĄZANIE:")
    print("Pobierz ręcznie:")
    print("1. Wejdź: https://leagueoflegends.fandom.com/wiki/Module:SkinData/data")
    print("2. Kliknij 'Edit'")
    print("3. Zaznacz cały kod (Ctrl+A)")
    print("4. Skopiuj (Ctrl+C)")
    print("5. Zapisz jako 'skindata_manual.lua' w tym folderze")
    print("\nKontynuuję z tym co mam...")

# Parsowanie
print("\nParsowanie skinów...")

pattern = r'\["([^"]+)"\]\s*=\s*\{([^}]+)\}'
matches = list(re.finditer(pattern, lua_content))

print(f"Znaleziono {len(matches)} dopasowań wzorca")

skins = []

for match in matches:
    skin_name = match.group(1)
    properties = match.group(2)
    
    # Wyciągnij cost
    cost_match = re.search(r'cost\s*=\s*(\d+)', properties)
    if not cost_match:
        continue
    
    cost = int(cost_match.group(1))
    
    # Określ rarity
    if cost == 0:
        rarity = "Default"
    elif cost in [390, 520, 750, 975]:
        rarity = "Legacy"
    elif cost == 1350:
        rarity = "Epic"
    elif cost == 1820:
        rarity = "Legendary"
    elif cost >= 3250:
        rarity = "Ultimate"
    else:
        rarity = "Epic"
    
    skins.append({
        'skin_name': skin_name,
        'price_rp': cost,
        'rarity': rarity
    })

print(f"Przetworzone: {len(skins)} skinów")

if len(skins) == 0:
    print("\n❌ BŁĄD: Nie znaleziono żadnych skinów!")
    print("\nSprawdź plik skindata_raw.lua i zobacz co zostało pobrane")
    print("\nLUB pobierz ręcznie kod i zapisz jako 'skindata_manual.lua',")
    print("a potem uruchom: python parse_manual_lua.py")
    exit(1)

# DataFrame
df = pd.DataFrame(skins)

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

print("\nRozkład rarity:")
for rarity, count in df['rarity'].value_counts().items():
    pct = (count / len(df)) * 100
    print(f"  {rarity:12s}: {count:4d} ({pct:5.1f}%)")

print("\nRozkład cen:")
for price, count in df.groupby('price_rp').size().sort_index().items():
    print(f"  {price:4d} RP: {count:4d}")

# Zapisz
output = "wiki_skin_prices_real.csv"
df.to_csv(output, index=False)

print(f"\n{'='*60}")
print(f"✓ Zapisano: {output}")
print(f"{'='*60}")

# Przykłady
print("\nPrzykładowe skiny:")
for rarity in ['Legacy', 'Epic', 'Legendary', 'Ultimate']:
    sample = df[df['rarity'] == rarity].head(2)
    if len(sample) > 0:
        print(f"\n{rarity}:")
        for _, row in sample.iterrows():
            print(f"  {row['skin_name']}: {row['price_rp']} RP")

print("\n" + "="*60)
print("NASTĘPNY KROK: Połącz z dim_skins.csv")
print("="*60)