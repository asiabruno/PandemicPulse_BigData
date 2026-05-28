"""
═══════════════════════════════════════════════════════════════════
RIMOZIONE DUPLICATI — 85 col → ~60 col pulite
═══════════════════════════════════════════════════════════════════
Uso:
    cd ~/Desktop/PROJECT
    python 3_remove_duplicates.py
    python 2_parquet_to_mongo.py
═══════════════════════════════════════════════════════════════════
"""

import pandas as pd
import os, sys

INPUT  = "master_merged_complete.csv"
OUTPUT = "master_merged_complete.csv"       
PARQUET = "data_lake/gold/master_covid_gold.parquet"

if not os.path.exists(INPUT):
    print(f"❌ Non trovo {INPUT} — sei in ~/Desktop/PROJECT?"); sys.exit(1)

print("Caricamento...")
df = pd.read_csv(INPUT, low_memory=False)
print(f"   PRIMA: {df.shape[0]:,} righe × {df.shape[1]} colonne")

before = df.shape[1]

# ════════════════════════════════════════════════════════════════
# 1. COLONNE DUPLICATE : manteniamo la versione OWID
# ════════════════════════════════════════════════════════════════
DUPLICATES_TO_DROP = [
    # Master original          →  Kept OWID version
    "income_support",           # = e1_income_support
    "restriction_gatherings",   # = c4m_restrictions_on_gatherings
    "contact_tracing",          # = h3_contact_tracing
    "facial_coverings",         # = h6m_facial_coverings
    "school_closures",          # = c1m_school_closing
    "workplace_closures",       # = c2m_workplace_closing
    "stay_home_requirements",   # = c6m_stay_at_home_requirements
    "international_travel_controls",  # = c8ev_international_travel_controls
    "restrictions_internal_movements", # = c7m_restrictions_on_internal_movement
    "stringency_index",         # = stringency_index_weighted_average
    "Daily hospital occupancy", # = daily_occupancy_hosp
    "short_term_positivity_rate", # = positive_rate
    "new_tests_per_thousand_7day_smoothed", # = new_tests_7day_smoothed
    "total_tests_per_thousand", # ≈ tests_per_case (diversa metrica ma ridondante)
]

# ════════════════════════════════════════════════════════════════
# 2. COLONNE RIDONDANTI / INUTILI
# ════════════════════════════════════════════════════════════════
USELESS_TO_DROP = [
    "145610-annotations",       
    "142605-annotations",       
    "142753-annotations",       
    "Total confirmed cases of COVID-19",   
    "Total confirmed deaths due to COVID-19", 
    "Daily new confirmed cases of COVID-19 per million people (rolling 7-day average, right-aligned)",  
    "Year",                     
    "Recovered",                
]

all_drop = DUPLICATES_TO_DROP + USELESS_TO_DROP

# Filtra solo colonne che esistono
to_drop = [c for c in all_drop if c in df.columns]
not_found = [c for c in all_drop if c not in df.columns]

print(f"\n  Colonne da rimuovere: {len(to_drop)}")
for c in to_drop:
    print(f"   ✗ {c}")

if not_found:
    print(f"\n     {len(not_found)} già assenti (ignorate):")
    for c in not_found:
        print(f"      - {c}")

df.drop(columns=to_drop, inplace=True)

# ════════════════════════════════════════════════════════════════
# 3. RINOMINA PER CHIAREZZA
# ════════════════════════════════════════════════════════════════
RENAMES = {
    "stringency_index_weighted_average": "stringency_index",  
}
for old, new in RENAMES.items():
    if old in df.columns and new not in df.columns:
        df.rename(columns={old: new}, inplace=True)
        print(f"\n    Rinominata: {old} → {new}")

# ════════════════════════════════════════════════════════════════
# 4. SALVA
# ════════════════════════════════════════════════════════════════
print(f"\n   DOPO: {df.shape[0]:,} righe × {df.shape[1]} colonne")
print(f"   🗑️  Rimosse: {before - df.shape[1]} colonne")

# CSV
df.to_csv(OUTPUT, index=False)
print(f"\nCSV: {OUTPUT} ({os.path.getsize(OUTPUT)/1024/1024:.1f} MB)")

print(f"""
{'='*60}
PROCESSO COMPLETATO
{'='*60}

  PRIMA: {before} colonne
  DOPO:  {df.shape[1]} colonne (-{before - df.shape[1]})

     Esegui:
     python 2_parquet_to_mongo.py

📋 COLONNE FINALI ({df.shape[1]}):
{'-'*60}""")
for i, c in enumerate(df.columns, 1):
    fill = (1 - df[c].isna().mean()) * 100
    print(f"   {i:2d}. {c:<50s} ({fill:.0f}%)")
