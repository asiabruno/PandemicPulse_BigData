"""
═══════════════════════════════════════════════════════════════════
FAKECOVID FACT-CHECK DATASET — Download, Process & Merge
═══════════════════════════════════════════════════════════════════
Dataset: 7,623 notizie fact-checked da 92 siti di fact-checking,
classificate in 11 categorie, da 105 paesi in 40 lingue.
Fonte: Shahi & Nandini (2020), ICWSM Workshop.

Uso:
    cd ~/Desktop/PROJECT
    python 6_fakecovid_factcheck.py
    python 2_parquet_to_mongo.py

═══════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
import os
import sys
import requests

MAIN_CSV     = "master_merged_complete.csv"
OUTPUT_CSV   = "master_merged_complete.csv"
PARQUET      = "data_lake/gold/master_covid_gold.parquet"
RAW_DIR      = "data_lake/raw"
FAKECOVID_LOCAL = os.path.join(RAW_DIR, "FakeCovid_July2020.csv")

# URL possibili per il download (GitHub raw)
FAKECOVID_URLS = [
    "https://raw.githubusercontent.com/Gautamshahi/FakeCovid/master/FakeCovid_July2020.csv",
    "https://raw.githubusercontent.com/Gautamshahi/FakeCovid/main/FakeCovid_July2020.csv",
]

# Mappa country name → ISO3 (i paesi più presenti in FakeCovid)
COUNTRY_TO_ISO = {
    "India": "IND", "United States": "USA", "US": "USA", "USA": "USA",
    "Spain": "ESP", "Brazil": "BRA", "France": "FRA", "Colombia": "COL",
    "United Kingdom": "GBR", "UK": "GBR", "Nigeria": "NGA",
    "Philippines": "PHL", "Indonesia": "IDN", "Argentina": "ARG",
    "Turkey": "TUR", "Mexico": "MEX", "Italy": "ITA", "Germany": "DEU",
    "Australia": "AUS", "Canada": "CAN", "Pakistan": "PAK",
    "Sri Lanka": "LKA", "South Africa": "ZAF", "Kenya": "KEN",
    "Thailand": "THA", "Peru": "PER", "Ecuador": "ECU", "Chile": "CHL",
    "Bangladesh": "BGD", "Myanmar": "MMR", "Nepal": "NPL",
    "Egypt": "EGY", "Iran": "IRN", "Iraq": "IRQ", "Poland": "POL",
    "Romania": "ROU", "Russia": "RUS", "Ukraine": "UKR",
    "Taiwan": "TWN", "Japan": "JPN", "South Korea": "KOR",
    "Malaysia": "MYS", "Singapore": "SGP", "Vietnam": "VNM",
    "Netherlands": "NLD", "Belgium": "BEL", "Sweden": "SWE",
    "Switzerland": "CHE", "Austria": "AUT", "Portugal": "PRT",
    "Greece": "GRC", "Czech Republic": "CZE", "Czechia": "CZE",
    "Denmark": "DNK", "Norway": "NOR", "Finland": "FIN",
    "Ireland": "IRL", "New Zealand": "NZL", "China": "CHN",
    "Bolivia": "BOL", "Venezuela": "VEN", "Paraguay": "PRY",
    "Uruguay": "URY", "Guatemala": "GTM", "Honduras": "HND",
    "Costa Rica": "CRI", "Panama": "PAN", "Dominican Republic": "DOM",
    "Ghana": "GHA", "Tanzania": "TZA", "Uganda": "UGA",
    "Ethiopia": "ETH", "Senegal": "SEN", "Cameroon": "CMR",
    "Global": None, "International": None,
}


def download_fakecovid():
    """Scarica FakeCovid da GitHub."""
    os.makedirs(RAW_DIR, exist_ok=True)

    
    if os.path.exists(FAKECOVID_LOCAL):
        print(f"   Trovato in locale: {FAKECOVID_LOCAL}")
        return pd.read_csv(FAKECOVID_LOCAL, low_memory=False)

    
    for url in FAKECOVID_URLS:
        print(f"   Tentativo download: {url}")
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                with open(FAKECOVID_LOCAL, 'wb') as f:
                    f.write(resp.content)
                print(f"   Scaricato ({len(resp.content)/1024:.0f} KB)")
                return pd.read_csv(FAKECOVID_LOCAL, low_memory=False)
        except Exception as e:
            print(f"    Fallito: {e}")

  
    sys.exit(1)


def main():
    print("=" * 60)
    print("FAKECOVID FACT-CHECK DATASET")
    print("=" * 60)

    # ── 1. SCARICA/CARICA ──
    print("\n Step 1: Download dataset...")
    df_fc = download_fakecovid()
    print(f"   {df_fc.shape[0]:,} righe × {df_fc.shape[1]} colonne")
    print(f"   Colonne: {list(df_fc.columns)}")

    # ── 2. PULIZIA E PROCESSING ──
    print("\n Step 2: Processing...")

    
    date_col = None
    for c in df_fc.columns:
        if 'date' in c.lower():
            date_col = c
            break
    if date_col is None:
        
        for c in df_fc.columns:
            try:
                sample = pd.to_datetime(df_fc[c].head(10), errors='coerce')
                if sample.notna().sum() > 5:
                    date_col = c
                    break
            except:
                pass

    if date_col:
        df_fc['date'] = pd.to_datetime(df_fc[date_col], errors='coerce')
        print(f"   Colonna data: '{date_col}'")
        print(f"   Range: {df_fc['date'].min()} → {df_fc['date'].max()}")
    else:
        print("    Nessuna colonna data trovata, uso le altre colonne")

    
    country_col = None
    for c in df_fc.columns:
        if 'country' in c.lower():
            country_col = c
            break

    
    class_col = None
    for c in ['class', 'category']:
        if c in df_fc.columns:
            n_unique = df_fc[c].nunique()
            print(f"  📋 Colonna '{c}': {n_unique} valori unici")
            if n_unique <= 20:
                class_col = c
                break
    
   
    rating_col = 'category' if 'category' in df_fc.columns else None

    print(f"   Colonna paese: '{country_col}'")
    print(f"   Colonna categoria: '{class_col}'")
    print(f"   Colonna rating: '{rating_col}'")

    # ── 3. AGGREGA PER PAESE E SETTIMANA ──
    print("\n Step 3: Aggregazione per paese/settimana...")

    
    if country_col:
        
        country_cols = [c for c in df_fc.columns if 'country' in c.lower()]
        print(f"   Colonne paese trovate: {country_cols}")

        
        rows = []
        for _, row in df_fc.iterrows():
            for cc in country_cols:
                val = row.get(cc)
                if pd.notna(val) and str(val).strip():
                    country_name = str(val).strip()
                    iso = COUNTRY_TO_ISO.get(country_name)
                    if iso:
                        rows.append({
                            'ISO_Code': iso,
                            'date': row.get('date'),
                            'category': row.get(class_col, 'unknown') if class_col else 'unknown',
                            'rating': row.get(rating_col, 'unknown') if rating_col else 'unknown',
                        })

        df_expanded = pd.DataFrame(rows)
        print(f"   Record espansi (1 per paese): {len(df_expanded):,}")
    else:
        print("    Nessuna colonna paese, impossibile aggregare per paese")
        df_expanded = pd.DataFrame()

    if df_expanded.empty or 'date' not in df_expanded.columns:
        print("   Dati insufficienti per il merge")
        sys.exit(1)

    df_expanded['date'] = pd.to_datetime(df_expanded['date'], errors='coerce')
    df_expanded = df_expanded.dropna(subset=['date'])

    
    df_expanded['_week'] = df_expanded['date'].dt.to_period('W').dt.start_time

    weekly = df_expanded.groupby(['ISO_Code', '_week']).agg(
        factcheck_count=('date', 'count'),  
    ).reset_index()

    
    if 'category' in df_expanded.columns:
        
        df_expanded['category'] = df_expanded['category'].astype(str).str.strip().str.lower()
        
        top_cats = df_expanded['category'].value_counts().head(15).index.tolist()
        df_expanded.loc[~df_expanded['category'].isin(top_cats), 'category'] = 'other'
        
        cat_counts = df_expanded.groupby(['ISO_Code', '_week', 'category']).size().reset_index(name='count')
        cat_pivot = cat_counts.pivot_table(index=['ISO_Code', '_week'], columns='category', values='count', fill_value=0).reset_index()
        cat_pivot.columns.name = None
        
        
        new_cols = ['ISO_Code', '_week']
        for c in cat_pivot.columns[2:]:
            clean_name = 'fc_' + str(c).strip().replace(' ', '_').replace('/', '_').replace("'", "").replace('"', '').replace('.', '').replace('(', '').replace(')', '')[:25]
            
            while clean_name in new_cols:
                clean_name += '_2'
            new_cols.append(clean_name)
        cat_pivot.columns = new_cols
        
        weekly = weekly.merge(cat_pivot, on=['ISO_Code', '_week'], how='left')

    
    weekly = weekly.sort_values(['ISO_Code', '_week'])
    weekly['factcheck_cumulative'] = weekly.groupby('ISO_Code')['factcheck_count'].cumsum()

    print(f"   Dati settimanali: {len(weekly):,} righe × {weekly.shape[1]} colonne")
    print(f"   Paesi: {weekly['ISO_Code'].nunique()}")

    
    fc_output = os.path.join(RAW_DIR, "fakecovid_weekly.csv")
    weekly.to_csv(fc_output, index=False)
    print(f"  💾 Salvato: {fc_output}")

    # ── 4. MERGE CON DATASET PRINCIPALE ──
    print("\n Step 4: Merge con dataset principale...")

    if not os.path.exists(MAIN_CSV):
        print(f"  ❌ {MAIN_CSV} non trovato")
        sys.exit(1)

    df = pd.read_csv(MAIN_CSV, low_memory=False)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['_week'] = df['Date'].dt.to_period('W').dt.start_time
    print(f"   Dataset principale: {df.shape[0]:,} × {df.shape[1]}")

    
    fc_cols = [c for c in df.columns if c.startswith('factcheck_') or c.startswith('fc_')]
    if fc_cols:
        df.drop(columns=fc_cols, inplace=True)

    
    merge_cols = [c for c in weekly.columns if c not in ['_week', 'ISO_Code']]
    weekly_merge = weekly[['ISO_Code', '_week'] + merge_cols].drop_duplicates(subset=['ISO_Code', '_week'])

    df = df.merge(weekly_merge, on=['ISO_Code', '_week'], how='left')
    df.drop(columns=['_week'], inplace=True)

    matched = df['factcheck_count'].notna().sum()
    print(f"   Merge: {matched:,} righe con dati fact-check ({matched/len(df)*100:.1f}%)")

    # ── 5. SALVA ──
    print("\n Step 5: Salvataggio...")

    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"  CSV: {OUTPUT_CSV} ({os.path.getsize(OUTPUT_CSV)/1024/1024:.1f} MB)")

    # ── RIEPILOGO ──
    print(f"""
{'='*60}
ESEGUITO
{'='*60}

  Nuove colonne:
    • factcheck_count        — N. fake news verificate quella settimana
    • factcheck_cumulative   — Totale cumulativo fact-check
    • fc_*                   — Conteggio per categoria di fake news

  Paesi con dati fact-check: {weekly['ISO_Code'].nunique()}
  Totale fact-check: {weekly['factcheck_count'].sum():,}
  Colonne totali dataset: {df.shape[1]}

     Esegui:
     python 2_parquet_to_mongo.py
     streamlit run 5_dashboard_wow.py
""")

    
    print("  TOP 10 PAESI PER FACT-CHECK:")
    top = weekly.groupby('ISO_Code')['factcheck_count'].sum().nlargest(10)
    for iso, count in top.items():
        print(f"     {iso}: {int(count)} fact-check")


if __name__ == "__main__":
    main()
