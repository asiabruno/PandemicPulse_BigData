"""
═══════════════════════════════════════════════════════════════════
GOOGLE TRENDS — PRO-SCIENCE & POSITIVE SEARCH TERMS
═══════════════════════════════════════════════════════════════════
Complemento allo script disinfo: scarica termini di ricerca
positivi/pro-scienza per costruire il Trust Ratio.

Uso:
    cd ~/Desktop/PROJECT
    python 4b_google_trends_proscience.py

Tempo: ~20 minuti
Output: data_lake/raw/google_trends_proscience.csv
═══════════════════════════════════════════════════════════════════
"""

import pandas as pd
import time
import os
import sys
import json

try:
    from pytrends.request import TrendReq
except ImportError:
    print("❌ pip install pytrends"); sys.exit(1)

OUTPUT_CSV    = "data_lake/raw/google_trends_proscience.csv"
OUTPUT_MERGED = "data_lake/raw/google_trends_proscience_weekly.csv"
PROGRESS_FILE = "data_lake/raw/_gt_proscience_progress.json"
TIMEFRAME     = "2020-01-01 2023-12-31"
SLEEP_BETWEEN = 12

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

# ════════════════════════════════════════════════════════════════
# TERMINI PRO-SCIENZA / POSITIVI / INFORMATIVI
# ════════════════════════════════════════════════════════════════
SEARCH_TERMS = {
    # ── PRO-VACCINE (azione concreta: voglio vaccinarmi) ──
    "book_vaccine": {
        "default": "book vaccine appointment",
        "it": "prenotare vaccino",
        "pt": "agendar vacina",
        "fr": "prendre rendez-vous vaccin",
        "de": "Impftermin buchen",
        "es": "cita vacuna covid",
        "tr": "aşı randevusu",
        "ru": "записаться на вакцинацию",
        "pl": "rejestracja na szczepienie",
        "ro": "programare vaccin",
    },
    "where_vaccine": {
        "default": "where to get vaccinated",
        "it": "dove vaccinarsi",
        "pt": "onde vacinar",
        "fr": "où se faire vacciner",
        "de": "wo impfen lassen",
        "es": "donde vacunarse",
        "tr": "nerede aşı olabilirim",
        "ru": "где сделать прививку",
        "pl": "gdzie się zaszczepić",
        "ro": "unde ma vaccinez",
    },
    "booster_dose": {
        "default": "booster dose covid",
        "it": "dose booster",
        "pt": "dose reforço covid",
        "fr": "dose rappel covid",
        "de": "Booster Impfung",
        "es": "dosis refuerzo covid",
    },
    # ── PRO-SCIENCE (fiducia nella scienza) ──
    "vaccine_works": {
        "default": "vaccine works",
        "it": "vaccino funziona",
        "pt": "vacina funciona",
        "fr": "vaccin efficace",
        "de": "Impfung wirkt",
        "es": "vacuna funciona",
    },
    "vaccine_efficacy": {
        "default": "vaccine efficacy data",
        "it": "efficacia vaccino",
        "pt": "eficácia vacina",
        "fr": "efficacité vaccin",
        "de": "Impfstoff Wirksamkeit",
        "es": "eficacia vacuna",
    },
    "mrna_how": {
        "default": "mRNA how it works",
        "it": "mRNA come funziona",
        "pt": "mRNA como funciona",
        "fr": "ARNm comment ça marche",
        "de": "mRNA wie funktioniert",
        "es": "ARNm cómo funciona",
    },
    # ── INFORMATIONAL (ricerca neutra, voler capire) ──
    "is_vaccine_safe": {
        "default": "is covid vaccine safe",
        "it": "vaccino covid sicuro",
        "pt": "vacina covid segura",
        "fr": "vaccin covid sûr",
        "de": "covid Impfung sicher",
        "es": "vacuna covid segura",
    },
    "vaccine_side_effects": {
        "default": "covid vaccine side effects",
        "it": "effetti collaterali vaccino covid",
        "pt": "efeitos colaterais vacina covid",
        "fr": "effets secondaires vaccin covid",
        "de": "Nebenwirkungen covid Impfung",
        "es": "efectos secundarios vacuna covid",
    },
    "covid_symptoms": {
        "default": "covid symptoms",
        "it": "sintomi covid",
        "pt": "sintomas covid",
        "fr": "symptômes covid",
        "de": "covid Symptome",
        "es": "síntomas covid",
        "tr": "covid belirtileri",
        "ru": "симптомы ковид",
        "pl": "objawy covid",
        "ro": "simptome covid",
    },
}


def get_term(term_dict, lang):
    return term_dict.get(lang, term_dict["default"])

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f: return json.load(f)
    return {"completed": []}

def save_progress(p):
    with open(PROGRESS_FILE, 'w') as f: json.dump(p, f)

def fetch_trend(pytrends, keyword, geo, timeframe, max_retries=3):
    for attempt in range(max_retries):
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
            df = pytrends.interest_over_time()
            if df.empty: return None
            df = df.drop(columns=['isPartial'], errors='ignore')
            df = df.rename(columns={keyword: 'search_interest'})
            df['keyword'] = keyword
            df.index.name = 'date'
            return df.reset_index()
        except Exception as e:
            wait = SLEEP_BETWEEN * (attempt + 1)
            print(f"           Retry {attempt+1}: {e}, wait {wait}s")
            time.sleep(wait)
    return None


def main():
    print("=" * 65)
    print("GOOGLE TRENDS — PRO-SCIENCE & POSITIVE TERMS")
    print("=" * 65)
    total = len(COUNTRIES) * len(SEARCH_TERMS)
    print(f"  Paesi: {len(COUNTRIES)} | Termini: {len(SEARCH_TERMS)} | Query: {total}")
    print(f"  Tempo stimato: ~{total * SLEEP_BETWEEN / 60:.0f} minuti\n")

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    pytrends = TrendReq(hl='en-US', tz=0, timeout=(10, 30))
    progress = load_progress()
    all_results = []
    n = 0

    for geo, info in COUNTRIES.items():
        print(f"\n  🌍 {info['name']} ({geo} → {info['iso3']})")
        print(f"  {'─' * 50}")
        for tid, td in SEARCH_TERMS.items():
            qk = f"{geo}_{tid}"
            n += 1
            if qk in progress["completed"]:
                print(f"     ✓ {tid:<25s} (già scaricato)")
                continue
            kw = get_term(td, info['lang'])
            pct = n / total * 100
            print(f"     [{pct:5.1f}%] {tid:<25s} → \"{kw}\"", end="", flush=True)
            df = fetch_trend(pytrends, kw, geo, TIMEFRAME)
            if df is not None and not df.empty:
                df['geo'] = geo
                df['ISO_Code'] = info['iso3']
                df['country'] = info['name']
                df['term_category'] = tid
                all_results.append(df)
                print(f"  {len(df)} punti")
            else:
                print(f"  ⬚ no data")
            progress["completed"].append(qk)
            save_progress(progress)
            time.sleep(SLEEP_BETWEEN)

    if not all_results:
        print("\n❌ Nessun dato."); sys.exit(1)

    # Combina
    df_all = pd.concat(all_results, ignore_index=True)
    df_all['date'] = pd.to_datetime(df_all['date'])
    print(f"\n   Righe totali: {len(df_all):,}")

    df_all.to_csv(OUTPUT_CSV, index=False)
    print(f"   Dati grezzi: {OUTPUT_CSV}")

    # Indice settimanale
    df_weekly = df_all.groupby(['ISO_Code', 'country', 'date']).agg(
        proscience_index=('search_interest', 'mean'),
        proscience_max=('search_interest', 'max'),
    ).reset_index()

    # Sotto-indici
    cats = {
        'provax_action_index': ['book_vaccine', 'where_vaccine', 'booster_dose'],
        'provax_trust_index': ['vaccine_works', 'vaccine_efficacy', 'mrna_how'],
        'info_seeking_index': ['is_vaccine_safe', 'vaccine_side_effects', 'covid_symptoms'],
    }
    for idx_name, terms in cats.items():
        cd = df_all[df_all['term_category'].isin(terms)]
        if not cd.empty:
            ca = cd.groupby(['ISO_Code', 'date'])['search_interest'].mean().reset_index()
            ca.rename(columns={'search_interest': idx_name}, inplace=True)
            df_weekly = df_weekly.merge(ca, on=['ISO_Code', 'date'], how='left')

    df_weekly.rename(columns={'date': 'Date'}, inplace=True)
    df_weekly['Date'] = df_weekly['Date'].dt.strftime('%Y-%m-%d')
    df_weekly.to_csv(OUTPUT_MERGED, index=False)

    print(f"  💾 Index settimanale: {OUTPUT_MERGED}")
    print(f"\n{'='*65}")
    print(f"   FATTO!")
    print(f"{'='*65}")
    print(f"""
  Nuove colonne:
    • proscience_index       — media tutti i termini positivi (0-100)
    • proscience_max         — picco massimo
    • provax_action_index    — "prenotare vaccino", "dove vaccinarsi"
    • provax_trust_index     — "vaccino funziona", "efficacia"
    • info_seeking_index     — "effetti collaterali", "sintomi", "è sicuro?"

     Esegui:
     python 5_merge_trends.py
     python 2_parquet_to_mongo.py
""")
    if os.path.exists(PROGRESS_FILE): os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    main()
