"""
═══════════════════════════════════════════════════════════════════
MERGE GOOGLE TRENDS (DISINFO + PROSCIENCE) → DATASET + TRUST RATIO
═══════════════════════════════════════════════════════════════════
Uso:
    cd ~/Desktop/PROJECT
    python 5_merge_trends.py
    python 2_parquet_to_mongo.py
═══════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
import os, sys

MAIN_CSV      = "master_merged_complete.csv"
DISINFO_CSV   = "data_lake/raw/google_trends_disinfo_weekly.csv"
PROSCIENCE_CSV = "data_lake/raw/google_trends_proscience_weekly.csv"
OUTPUT_CSV    = "master_merged_complete.csv"
PARQUET       = "data_lake/gold/master_covid_gold.parquet"

print("=" * 60)
print("MERGE TRENDS (DISINFO + PROSCIENCE) + TRUST RATIO")
print("=" * 60)

if not os.path.exists(MAIN_CSV):
    print(f" {MAIN_CSV} non trovato"); sys.exit(1)

# ── Carica dataset principale ──
df = pd.read_csv(MAIN_CSV, low_memory=False)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['_week'] = df['Date'].dt.to_period('W').dt.start_time
print(f"\n Dataset principale: {df.shape[0]:,} × {df.shape[1]}")

# ── Colonne da aggiungere / sovrascrivere ──
all_trend_cols = [
    # Disinfo
    'disinfo_index', 'disinfo_max', 'disinfo_terms_active',
    'antivax_index', 'denialism_index', 'conspiracy_index', 'altmed_index',
    # ProScience
    'proscience_index', 'proscience_max',
    'provax_action_index', 'provax_trust_index', 'info_seeking_index',
    # Derived
    'trust_ratio', 'trust_ratio_smooth', 'sentiment_balance',
]
for c in all_trend_cols:
    if c in df.columns:
        df.drop(columns=[c], inplace=True)

# ── Merge DISINFO ──
if os.path.exists(DISINFO_CSV):
    dfd = pd.read_csv(DISINFO_CSV)
    dfd['Date'] = pd.to_datetime(dfd['Date'], errors='coerce')
    dfd['_week'] = dfd['Date'].dt.to_period('W').dt.start_time
    disinfo_cols = [c for c in dfd.columns if c not in ['Date', 'ISO_Code', 'country', '_week']]
    dfd_merge = dfd[['ISO_Code', '_week'] + disinfo_cols].drop_duplicates(subset=['ISO_Code', '_week'])
    df = df.merge(dfd_merge, on=['ISO_Code', '_week'], how='left')
    matched = df['disinfo_index'].notna().sum()
    print(f" Disinfo: +{len(disinfo_cols)} colonne | {matched:,} righe matchate")
else:
    print("  Disinfo CSV non trovato, salto")

# ── Merge PROSCIENCE ──
if os.path.exists(PROSCIENCE_CSV):
    dfp = pd.read_csv(PROSCIENCE_CSV)
    dfp['Date'] = pd.to_datetime(dfp['Date'], errors='coerce')
    dfp['_week'] = dfp['Date'].dt.to_period('W').dt.start_time
    pro_cols = [c for c in dfp.columns if c not in ['Date', 'ISO_Code', 'country', '_week']]
    dfp_merge = dfp[['ISO_Code', '_week'] + pro_cols].drop_duplicates(subset=['ISO_Code', '_week'])
    df = df.merge(dfp_merge, on=['ISO_Code', '_week'], how='left')
    matched = df['proscience_index'].notna().sum()
    print(f" ProScience: +{len(pro_cols)} colonne | {matched:,} righe matchate")
else:
    print("  ProScience CSV non trovato, salto")

# ── Calcola TRUST RATIO ──
if 'disinfo_index' in df.columns and 'proscience_index' in df.columns:
    # Trust ratio = proscience / (disinfo + 1) → evita divisione per zero
    # Valore > 1 = la gente cerca più info pro-scienza che disinformazione
    # Valore < 1 = prevale la disinformazione
    df['trust_ratio'] = df['proscience_index'] / (df['disinfo_index'] + 1)

    # Smoothed version (media mobile 4 settimane)
    df['trust_ratio_smooth'] = df.groupby('ISO_Code')['trust_ratio'].transform(
        lambda x: x.rolling(4, min_periods=1).mean()
    )

    # Sentiment balance = proscience - disinfo (positivo = pro-scienza prevale)
    df['sentiment_balance'] = df['proscience_index'] - df['disinfo_index']

    print(f"  Trust Ratio calcolato")
    print(f"   Media trust ratio: {df['trust_ratio'].mean():.2f}")
    print(f"   Media sentiment balance: {df['sentiment_balance'].mean():.1f}")

# ── Pulizia ──
df.drop(columns=['_week'], inplace=True)

# ── Salva ──
df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
df.to_csv(OUTPUT_CSV, index=False)
print(f"\nCSV: {OUTPUT_CSV} ({os.path.getsize(OUTPUT_CSV)/1024/1024:.1f} MB)")

print(f"""
{'='*60}
🎉 FATTO! Dataset arricchito con {df.shape[1]} colonne
{'='*60}

  Nuove colonne Google Trends:
  ─── DISINFORMAZIONE ───
    • disinfo_index            — indice complessivo (0-100)
    • antivax_index            — sotto-indice anti-vaccino
    • denialism_index          — negazionismo / hoax
    • conspiracy_index         — cospirazioni (5G, Gates, Great Reset)
    • altmed_index             — cure alternative (ivermectina, clorochina)

  ─── PRO-SCIENZA ───
    • proscience_index         — indice complessivo positivo (0-100)
    • provax_action_index      — "prenotare vaccino", "dove vaccinarsi"
    • provax_trust_index       — "vaccino funziona", "efficacia"
    • info_seeking_index       — ricerca informativa neutra

  ─── DERIVATI ───
    • trust_ratio              — proscience / (disinfo + 1)
    • trust_ratio_smooth       — media mobile 4 settimane
    • sentiment_balance        — proscience - disinfo

     Esegui:
     python 2_parquet_to_mongo.py
     streamlit run 5_dashboard_wow.py
""")
