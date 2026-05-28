import pandas as pd
import time
import os
import sys
import json
from datetime import datetime

try:
    from pytrends.request import TrendReq
except ImportError:
    print("❌ pytrends non installato. Esegui:")
    print("   pip install pytrends")
    sys.exit(1)


OUTPUT_CSV      = "data_lake/raw/google_trends_disinfo.csv"
OUTPUT_MERGED   = "data_lake/raw/google_trends_disinfo_weekly.csv"
PROGRESS_FILE   = "data_lake/raw/_gt_progress.json"
TIMEFRAME       = "2020-01-01 2023-12-31"
SLEEP_BETWEEN   = 12  # secondi tra richieste (Google rate limit)

# 12 Paesi — codice Google Trends (ISO-2) + codice ISO-3 per merge
COUNTRIES = {
    "IT": {"iso3": "ITA", "name": "Italy",    "lang": "it"},
    "US": {"iso3": "USA", "name": "USA",      "lang": "en"},
    "BR": {"iso3": "BRA", "name": "Brazil",   "lang": "pt"},
    "GB": {"iso3": "GBR", "name": "UK",       "lang": "en"},
    "FR": {"iso3": "FRA", "name": "France",   "lang": "fr"},
    "DE": {"iso3": "DEU", "name": "Germany",  "lang": "de"},
    "TR": {"iso3": "TUR", "name": "Turkey",   "lang": "tr"},
    "IN": {"iso3": "IND", "name": "India",    "lang": "en"},
    "RU": {"iso3": "RUS", "name": "Russia",   "lang": "ru"},
    "PL": {"iso3": "POL", "name": "Poland",   "lang": "pl"},
    "RO": {"iso3": "ROU", "name": "Romania",  "lang": "ro"},
    "MX": {"iso3": "MEX", "name": "Mexico",   "lang": "es"},
}

# Termini di ricerca organizzati per categoria e lingua
SEARCH_TERMS = {
    # ── ANTI-VACCINO ──
    "antivax": {
        "default": "vaccine dangerous",
        "it": "vaccino pericoloso",
        "pt": "vacina perigosa",
        "fr": "vaccin dangereux",
        "de": "Impfung gefährlich",
        "es": "vacuna peligrosa",
        "tr": "aşı tehlikeli",
        "ru": "вакцина опасна",
        "pl": "szczepionka niebezpieczna",
        "ro": "vaccin periculos",
    },
    "vaccine_death": {
        "default": "vaccine side effects death",
        "it": "vaccino effetti collaterali morte",
        "pt": "vacina efeitos colaterais morte",
        "fr": "vaccin effets secondaires mort",
        "de": "Impfung Nebenwirkungen Tod",
        "es": "vacuna efectos secundarios muerte",
    },
    "microchip": {
        "default": "vaccine microchip",  
    },
    # ── NEGAZIONISMO ──
    "covid_hoax": {
        "default": "covid hoax",
        "it": "covid falso",
        "pt": "covid farsa",
        "fr": "covid canular",
        "de": "Corona Lüge",
        "es": "covid mentira",
    },
    "plandemic": {
        "default": "plandemic",  
    },
    "fake_pandemic": {
        "default": "fake pandemic",
        "it": "pandemia falsa",
        "it2": "dittatura sanitaria",
        "de": "Plandemie",
    },
    # ── COSPIRAZIONI ──
    "5g_covid": {
        "default": "5G covid",  
    },
    "bill_gates": {
        "default": "bill gates vaccine",  
    },
    "great_reset": {
        "default": "great reset",  
    },
    # ── CURE ALTERNATIVE ──
    "ivermectin": {
        "default": "ivermectin covid",
    },
    "hydroxychloroquine": {
        "default": "hydroxychloroquine",
        "it": "idrossiclorochina",
        "pt": "cloroquina covid",
        "fr": "hydroxychloroquine",
        "de": "Hydroxychloroquin",
        "es": "hidroxicloroquina",
    },
}


def get_term_for_country(term_dict, lang):
    """Restituisce il termine di ricerca nella lingua giusta per il paese."""
    if lang in term_dict:
        return term_dict[lang]
    return term_dict["default"]


def load_progress():
    """Carica progresso per riprendere download interrotti."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": []}


def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)


def fetch_trend(pytrends, keyword, geo, timeframe, max_retries=3):
    """Scarica un singolo trend con retry."""
    for attempt in range(max_retries):
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
            df = pytrends.interest_over_time()
            if df.empty:
                return None
            df = df.drop(columns=['isPartial'], errors='ignore')
            df = df.rename(columns={keyword: 'search_interest'})
            df['keyword'] = keyword
            df.index.name = 'date'
            return df.reset_index()
        except Exception as e:
            wait = SLEEP_BETWEEN * (attempt + 1)
            print(f"         Retry {attempt+1}/{max_retries}: {e}")
            print(f"         Attendo {wait}s...")
            time.sleep(wait)
    return None


def main():
    print("=" * 65)
    print("  GOOGLE TRENDS — COVID DISINFORMATION INDEX")
    print("=" * 65)
    print(f"  Paesi: {len(COUNTRIES)}")
    print(f"  Termini: {len(SEARCH_TERMS)}")
    print(f"  Periodo: {TIMEFRAME}")
    print(f"  Pausa tra richieste: {SLEEP_BETWEEN}s")
    
    total_queries = len(COUNTRIES) * len(SEARCH_TERMS)
    est_minutes = (total_queries * SLEEP_BETWEEN) / 60
    print(f"  Query totali: {total_queries}")
    print(f"  Tempo stimato: ~{est_minutes:.0f} minuti")
    print()
    
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    
    pytrends = TrendReq(hl='en-US', tz=0, timeout=(10, 30))
    progress = load_progress()
    
    all_results = []
    query_count = 0
    
    for geo_code, country_info in COUNTRIES.items():
        iso3 = country_info["iso3"]
        name = country_info["name"]
        lang = country_info["lang"]
        
        print(f"\n  🌍 {name} ({geo_code} → {iso3})")
        print(f"  {'─' * 50}")
        
        for term_id, term_dict in SEARCH_TERMS.items():
            query_key = f"{geo_code}_{term_id}"
            query_count += 1
            
            # Skip se già completato (per ripresa dopo interruzione)
            if query_key in progress["completed"]:
                print(f"     ✓ {term_id:<25s} (già scaricato)")
                continue
            
            keyword = get_term_for_country(term_dict, lang)
            pct = query_count / total_queries * 100
            print(f"     [{pct:5.1f}%] {term_id:<25s} → \"{keyword}\"", end="", flush=True)
            
            df = fetch_trend(pytrends, keyword, geo_code, TIMEFRAME)
            
            if df is not None and not df.empty:
                df['geo'] = geo_code
                df['ISO_Code'] = iso3
                df['country'] = name
                df['term_category'] = term_id
                all_results.append(df)
                print(f"   {len(df)} punti")
            else:
                print(f"  ⬚ no data")
            
            # Salva progresso
            progress["completed"].append(query_key)
            save_progress(progress)
            
            # Rate limiting
            time.sleep(SLEEP_BETWEEN)
    
    if not all_results:
        print("\n❌ Nessun dato scaricato. Controlla la connessione internet.")
        sys.exit(1)
    

    print("\n" + "=" * 65)
    print("   AGGREGAZIONE RISULTATI")
    print("=" * 65)
    
    df_all = pd.concat(all_results, ignore_index=True)
    df_all['date'] = pd.to_datetime(df_all['date'])
    
    print(f"   Righe totali: {len(df_all):,}")
    print(f"   Paesi con dati: {df_all['ISO_Code'].nunique()}")
    print(f"   Termini con dati: {df_all['term_category'].nunique()}")
    
    # Salva dati grezzi
    df_all.to_csv(OUTPUT_CSV, index=False)
    print(f"\n   Dati grezzi: {OUTPUT_CSV}")
    
    
    print("\n" + "=" * 65)
    print("   COSTRUZIONE DISINFORMATION INDEX")
    print("=" * 65)
    
    # Per ogni paese e settimana, calcola la media di tutti i termini
    # Questo produce un "Disinformation Search Index" 0-100
    df_weekly = df_all.groupby(['ISO_Code', 'country', 'date']).agg(
        disinfo_index=('search_interest', 'mean'),
        disinfo_max=('search_interest', 'max'),
        disinfo_terms_active=('search_interest', lambda x: (x > 0).sum()),
    ).reset_index()
    
    # Aggiungi anche i sotto-indici per categoria
    categories = {
        'antivax_index': ['antivax', 'vaccine_death', 'microchip'],
        'denialism_index': ['covid_hoax', 'plandemic', 'fake_pandemic'],
        'conspiracy_index': ['5g_covid', 'bill_gates', 'great_reset'],
        'altmed_index': ['ivermectin', 'hydroxychloroquine'],
    }
    
    for idx_name, terms in categories.items():
        cat_data = df_all[df_all['term_category'].isin(terms)]
        if not cat_data.empty:
            cat_agg = cat_data.groupby(['ISO_Code', 'date'])['search_interest'].mean().reset_index()
            cat_agg.rename(columns={'search_interest': idx_name}, inplace=True)
            df_weekly = df_weekly.merge(cat_agg, on=['ISO_Code', 'date'], how='left')
    
    # Rinomina date per merge con dataset principale
    df_weekly.rename(columns={'date': 'Date'}, inplace=True)
    df_weekly['Date'] = df_weekly['Date'].dt.strftime('%Y-%m-%d')
    
    df_weekly.to_csv(OUTPUT_MERGED, index=False)
    print(f"  Index settimanale: {OUTPUT_MERGED}")
    print(f"  {len(df_weekly):,} righe × {df_weekly.shape[1]} colonne")
    
    # ════════════════════════════════════════════════════════════
    # RIEPILOGO
    # ════════════════════════════════════════════════════════════
    print("\n" + "=" * 65)
    print("ESEGUITO")
    print("=" * 65)
    print(f"""
  File creati:
    • {OUTPUT_CSV} (dati grezzi per termine)
    • {OUTPUT_MERGED} (index aggregato settimanale)

  Colonne nell'index settimanale:
    • disinfo_index        — media di tutti i termini (0-100)
    • disinfo_max          — picco massimo tra i termini
    • disinfo_terms_active — quanti termini hanno volume > 0
    • antivax_index        — sotto-indice anti-vaccino
    • denialism_index      — sotto-indice negazionismo
    • conspiracy_index     — sotto-indice cospirazioni
    • altmed_index         — sotto-indice cure alternative

     Esegui:
     1. python 5_merge_trends.py     (mergia con dataset principale)
     2. python 2_parquet_to_mongo.py  (carica in MongoDB)
     3. streamlit run 5_dashboard_wow.py

    Paesi scaricati:""")
    for iso, info in COUNTRIES.items():
        rows = len(df_weekly[df_weekly['ISO_Code'] == info['iso3']])
        print(f"     {info['name']:<15s} ({info['iso3']}) — {rows} settimane di dati")
    
    
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)


if __name__ == "__main__":
    main()