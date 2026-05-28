"""
═══════════════════════════════════════════════════════════════════
DOWNLOAD 14 DATASET OWID + MERGE CON MASTER_TOTAL 
═══════════════════════════════════════════════════════════════════
Uso:
    cd ~/Desktop/PROJECT
    pip install pandas pyarrow requests
    python 1_download_and_merge.py
═══════════════════════════════════════════════════════════════════
"""

import pandas as pd
import os
import sys
import time
import requests
from io import StringIO


MASTER_CSV     = "master_total.csv"
OUTPUT_CSV     = "master_merged_complete.csv"
OUTPUT_PARQUET = "data_lake/gold/master_covid_gold.parquet"
DOWNLOAD_DIR   = "data_lake/raw/owid_downloads"

DATASETS = {
    "cases_deaths": "https://catalog.ourworldindata.org/garden/covid/latest/cases_deaths/cases_deaths.csv",
    "excess_mortality": "https://catalog.ourworldindata.org/garden/excess_mortality/latest/excess_mortality/excess_mortality.csv",
    "excess_mortality_economist": "https://catalog.ourworldindata.org/garden/excess_mortality/latest/excess_mortality_economist/excess_mortality_economist.csv",
    "hospital": "https://catalog.ourworldindata.org/garden/covid/latest/hospital/hospital.csv",
    "vaccinations_global": "https://catalog.ourworldindata.org/garden/covid/latest/vaccinations_global/vaccinations_global.csv",
    "vaccinations_age": "https://catalog.ourworldindata.org/garden/covid/latest/vaccinations_age/vaccinations_age.csv",
    "vaccinations_manufacturer": "https://catalog.ourworldindata.org/garden/covid/latest/vaccinations_manufacturer/vaccinations_manufacturer.csv",
    "vaccinations_us": "https://catalog.ourworldindata.org/garden/covid/latest/vaccinations_us/vaccinations_us.csv",
    "testing": "https://catalog.ourworldindata.org/garden/covid/latest/testing/testing.csv",
    "tracking_r": "https://catalog.ourworldindata.org/garden/covid/latest/tracking_r/tracking_r.csv",
    "oxcgrt_policy": "https://catalog.ourworldindata.org/garden/covid/latest/oxcgrt_policy/oxcgrt_policy.csv",
    "yougov_composite": "https://catalog.ourworldindata.org/garden/covid/latest/yougov/yougov_composite.csv",
    "covax": "https://catalog.ourworldindata.org/garden/covid/latest/covax/covax.csv",
    "compact": "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv",
}

# ════════════════════════════════════════════════════════════════
# COUNTRY NAME → ISO 3166-1 ALPHA-3 
# ════════════════════════════════════════════════════════════════
COUNTRY_TO_ISO = {
    "Afghanistan": "AFG", "Albania": "ALB", "Algeria": "DZA", "Andorra": "AND",
    "Angola": "AGO", "Antigua and Barbuda": "ATG", "Argentina": "ARG", "Armenia": "ARM",
    "Aruba": "ABW", "Australia": "AUS", "Austria": "AUT", "Azerbaijan": "AZE",
    "Bahamas": "BHS", "Bahrain": "BHR", "Bangladesh": "BGD", "Barbados": "BRB",
    "Belarus": "BLR", "Belgium": "BEL", "Belize": "BLZ", "Benin": "BEN",
    "Bermuda": "BMU", "Bhutan": "BTN", "Bolivia": "BOL", "Bosnia and Herzegovina": "BIH",
    "Botswana": "BWA", "Brazil": "BRA", "Brunei": "BRN", "Bulgaria": "BGR",
    "Burkina Faso": "BFA", "Burundi": "BDI", "Cambodia": "KHM", "Cameroon": "CMR",
    "Canada": "CAN", "Cape Verde": "CPV", "Cabo Verde": "CPV",
    "Central African Republic": "CAF", "Chad": "TCD", "Chile": "CHL", "China": "CHN",
    "Colombia": "COL", "Comoros": "COM", "Congo": "COG",
    "Democratic Republic of Congo": "COD", "Costa Rica": "CRI",
    "Cote d'Ivoire": "CIV", "Ivory Coast": "CIV",
    "Croatia": "HRV", "Cuba": "CUB", "Curacao": "CUW", "Cyprus": "CYP",
    "Czechia": "CZE", "Czech Republic": "CZE",
    "Denmark": "DNK", "Djibouti": "DJI", "Dominica": "DMA",
    "Dominican Republic": "DOM", "Ecuador": "ECU", "Egypt": "EGY",
    "El Salvador": "SLV", "Equatorial Guinea": "GNQ", "Eritrea": "ERI",
    "Estonia": "EST", "Eswatini": "SWZ", "Swaziland": "SWZ",
    "Ethiopia": "ETH", "Faeroe Islands": "FRO", "Faroe Islands": "FRO",
    "Fiji": "FJI", "Finland": "FIN", "France": "FRA",
    "Gabon": "GAB", "Gambia": "GMB", "Georgia": "GEO", "Germany": "DEU",
    "Ghana": "GHA", "Gibraltar": "GIB", "Greece": "GRC", "Greenland": "GRL",
    "Grenada": "GRD", "Guatemala": "GTM", "Guernsey": "GGY", "Guinea": "GIN",
    "Guinea-Bissau": "GNB", "Guyana": "GUY", "Haiti": "HTI", "Honduras": "HND",
    "Hong Kong": "HKG", "Hungary": "HUN", "Iceland": "ISL", "India": "IND",
    "Indonesia": "IDN", "Iran": "IRN", "Iraq": "IRQ", "Ireland": "IRL",
    "Isle of Man": "IMN", "Israel": "ISR", "Italy": "ITA", "Jamaica": "JAM",
    "Japan": "JPN", "Jersey": "JEY", "Jordan": "JOR", "Kazakhstan": "KAZ",
    "Kenya": "KEN", "Kiribati": "KIR", "Kosovo": "XKX",
    "Kuwait": "KWT", "Kyrgyzstan": "KGZ", "Laos": "LAO", "Latvia": "LVA",
    "Lebanon": "LBN", "Lesotho": "LSO", "Liberia": "LBR", "Libya": "LBY",
    "Liechtenstein": "LIE", "Lithuania": "LTU", "Luxembourg": "LUX",
    "Macao": "MAC", "Macau": "MAC", "Madagascar": "MDG", "Malawi": "MWI",
    "Malaysia": "MYS", "Maldives": "MDV", "Mali": "MLI", "Malta": "MLT",
    "Marshall Islands": "MHL", "Mauritania": "MRT", "Mauritius": "MUS",
    "Mexico": "MEX", "Micronesia (country)": "FSM", "Moldova": "MDA",
    "Monaco": "MCO", "Mongolia": "MNG", "Montenegro": "MNE", "Morocco": "MAR",
    "Mozambique": "MOZ", "Myanmar": "MMR", "Namibia": "NAM", "Nauru": "NRU",
    "Nepal": "NPL", "Netherlands": "NLD", "New Caledonia": "NCL",
    "New Zealand": "NZL", "Nicaragua": "NIC", "Niger": "NER", "Nigeria": "NGA",
    "North Korea": "PRK", "North Macedonia": "MKD", "Macedonia": "MKD",
    "Norway": "NOR", "Oman": "OMN",
    "Pakistan": "PAK", "Palestine": "PSE", "Panama": "PAN",
    "Papua New Guinea": "PNG", "Paraguay": "PRY", "Peru": "PER",
    "Philippines": "PHL", "Poland": "POL", "Portugal": "PRT", "Qatar": "QAT",
    "Romania": "ROU", "Russia": "RUS", "Rwanda": "RWA",
    "Saint Kitts and Nevis": "KNA", "Saint Lucia": "LCA",
    "Saint Vincent and the Grenadines": "VCT", "Samoa": "WSM",
    "San Marino": "SMR", "Sao Tome and Principe": "STP",
    "Saudi Arabia": "SAU", "Senegal": "SEN", "Serbia": "SRB",
    "Seychelles": "SYC", "Sierra Leone": "SLE", "Singapore": "SGP",
    "Sint Maarten (Dutch part)": "SXM", "Slovakia": "SVK", "Slovenia": "SVN",
    "Solomon Islands": "SLB", "Somalia": "SOM", "South Africa": "ZAF",
    "South Korea": "KOR", "South Sudan": "SSD", "Spain": "ESP",
    "Sri Lanka": "LKA", "Sudan": "SDN", "Suriname": "SUR", "Sweden": "SWE",
    "Switzerland": "CHE", "Syria": "SYR", "Taiwan": "TWN",
    "Tajikistan": "TJK", "Tanzania": "TZA", "Thailand": "THA",
    "Timor": "TLS", "East Timor": "TLS", "Timor-Leste": "TLS",
    "Togo": "TGO", "Tonga": "TON", "Trinidad and Tobago": "TTO",
    "Tunisia": "TUN", "Turkey": "TUR", "Turkiye": "TUR",
    "Turkmenistan": "TKM", "Tuvalu": "TUV",
    "Uganda": "UGA", "Ukraine": "UKR", "United Arab Emirates": "ARE",
    "United Kingdom": "GBR", "United States": "USA", "Uruguay": "URY",
    "Uzbekistan": "UZB", "Vanuatu": "VUT", "Vatican": "VAT",
    "Venezuela": "VEN", "Vietnam": "VNM", "Viet Nam": "VNM",
    "Yemen": "YEM", "Zambia": "ZMB", "Zimbabwe": "ZWE",
    # Territori e varianti OWID
    "Anguilla": "AIA", "British Virgin Islands": "VGB",
    "Cayman Islands": "CYM", "Cook Islands": "COK",
    "Falkland Islands": "FLK", "French Polynesia": "PYF",
    "Guam": "GUM", "Montserrat": "MSR", "Niue": "NIU",
    "Northern Cyprus": "CYP", "Pitcairn": "PCN",
    "Puerto Rico": "PRI", "Saint Helena": "SHN",
    "Tokelau": "TKL", "Turks and Caicos Islands": "TCA",
    "United States Virgin Islands": "VIR",
    "Wallis and Futuna": "WLF", "Western Sahara": "ESH",
    "Bonaire Sint Eustatius and Saba": "BES",
    "South Georgia and the South Sandwich Islands": "SGS",
}


def hdr(t):
    print("\n" + "=" * 65)
    print(f"  {t}")
    print("=" * 65)


# ════════════════════════════════════════════════════════════════
# STEP 1: CARICA MASTER
# ════════════════════════════════════════════════════════════════
hdr("STEP 1: Caricamento master_total.csv")

if not os.path.exists(MASTER_CSV):
    print(f"  Non trovo: {MASTER_CSV}")
    print(f"  Sei nella cartella PROJECT? → cd ~/Desktop/PROJECT")
    sys.exit(1)

df_master = pd.read_csv(MASTER_CSV, low_memory=False)
df_master['Date'] = pd.to_datetime(df_master['Date'], errors='coerce')
df_master = df_master[df_master['ISO_Code'].astype(str).str.len() == 3].copy()
df_master = df_master.sort_values(['ISO_Code', 'Date']).reset_index(drop=True)

print(f"   {df_master.shape[0]:,} righe × {df_master.shape[1]} col")
print(f"   {df_master['ISO_Code'].nunique()} paesi")

master_original_cols = set(df_master.columns)

# ════════════════════════════════════════════════════════════════
# STEP 2: SCARICA 14 DATASET DAL SITO OUR WORLD IN DATA
# ════════════════════════════════════════════════════════════════
hdr("STEP 2: Download 14 dataset OWID")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
downloaded = {}

for name, url in DATASETS.items():
    local_path = os.path.join(DOWNLOAD_DIR, f"{name}.csv")
    
    if os.path.exists(local_path):
        print(f"\n   {name}: locale")
        try:
            df = pd.read_csv(local_path, low_memory=False)
            downloaded[name] = df
            print(f"      {df.shape[0]:,} × {df.shape[1]}")
            continue
        except Exception as e:
            print(f"       Errore, riscarico: {e}")
    
    print(f"\n  🌐 {name}: download...")
    try:
        t0 = time.time()
        resp = requests.get(url, timeout=180)
        resp.raise_for_status()
        mb = len(resp.content) / (1024*1024)
        print(f"      {mb:.1f} MB in {time.time()-t0:.1f}s")
        
        with open(local_path, 'wb') as f:
            f.write(resp.content)
        
        df = pd.read_csv(StringIO(resp.text), low_memory=False)
        downloaded[name] = df
        print(f"      {df.shape[0]:,} × {df.shape[1]} | {list(df.columns[:5])}...")
    except Exception as e:
        print(f"      {e}")

print(f"\n   Scaricati: {len(downloaded)}/{len(DATASETS)}")

# ════════════════════════════════════════════════════════════════
# STEP 3: MERGE PROGRESSIVO
# ════════════════════════════════════════════════════════════════
hdr(" STEP 3: Merge progressivo")
print(f"   Mappa country→ISO: {len(COUNTRY_TO_ISO)} nomi mappati")

df_merged = df_master.copy()
total_added = 0
skipped = []

for name, df_owid in downloaded.items():
    print(f"\n   {name}")
    df_owid = df_owid.copy()
    
    # ── Trova colonna DATE ──
    date_col = next((c for c in ['date', 'Date', 'year'] if c in df_owid.columns), None)
    if not date_col:
        print(f"       No colonna data → SKIP")
        skipped.append(name)
        continue
    df_owid[date_col] = pd.to_datetime(df_owid[date_col], errors='coerce')
    df_owid.rename(columns={date_col: 'Date'}, inplace=True)
    
    # ── Trova/crea colonna ISO ──
    iso_col = next((c for c in ['iso_code', 'ISO_Code', 'country_code'] if c in df_owid.columns), None)
    
    if iso_col:
        df_owid.rename(columns={iso_col: 'ISO_Code'}, inplace=True)
    else:
        loc_col = next((c for c in ['country', 'location', 'entity'] if c in df_owid.columns), None)
        if not loc_col:
            print(f"       No colonna paese/ISO → SKIP")
            skipped.append(name)
            continue
        
        # Mappa country name → ISO
        df_owid['ISO_Code'] = df_owid[loc_col].map(COUNTRY_TO_ISO)
        mapped = df_owid['ISO_Code'].notna().sum()
        total = len(df_owid)
        unmapped_names = df_owid[df_owid['ISO_Code'].isna()][loc_col].unique()[:5]
        print(f"      Mappati: {mapped:,}/{total:,} ({mapped/total*100:.0f}%)")
        if len(unmapped_names) > 0:
            print(f"       Non mappati (esempi): {list(unmapped_names)}")
        df_owid = df_owid.dropna(subset=['ISO_Code'])
    
    # Filtra ISO validi
    df_owid = df_owid[df_owid['ISO_Code'].astype(str).str.len() == 3]
    df_owid = df_owid[~df_owid['ISO_Code'].astype(str).str.startswith('OWI')]
    
    if df_owid.empty:
        print(f"       0 righe dopo filtro → SKIP")
        skipped.append(name)
        continue
    
    # ── Dataset disaggregati → SKIP ──
    disagg = {'age_group', 'age', 'vaccine', 'manufacturer', 'state'}
    found_disagg = [c for c in disagg if c in df_owid.columns]
    if found_disagg:
        print(f"       Disaggregato per {found_disagg} → SKIP (non allineabile 1:1)")
        skipped.append(name)
        continue
    
    # ── Dataset con formato lungo (indicator+value) → PIVOT ──
    if 'indicator' in df_owid.columns and 'value' in df_owid.columns:
        print(f"      Formato lungo → pivot...")
        try:
            df_owid = df_owid.drop_duplicates(subset=['ISO_Code', 'Date', 'indicator'])
            df_owid = df_owid.pivot_table(
                index=['ISO_Code', 'Date'], columns='indicator',
                values='value', aggfunc='first'
            ).reset_index()
            df_owid.columns.name = None
            df_owid.columns = [str(c).strip().replace(' ', '_') for c in df_owid.columns]
            print(f"      Pivot → {df_owid.shape[1]-2} colonne")
        except Exception as e:
            print(f"      Pivot fallito: {e} → SKIP")
            skipped.append(name)
            continue
    
    # ── Identifica colonne NUOVE ──
    existing = set(df_merged.columns)
    skip_names = {'ISO_Code', 'Date', 'country', 'location', 'entity', 'continent',
                  'Continent', 'Country', 'year', 'date', 'iso_code', 'country_code'}
    new_cols = [c for c in df_owid.columns if c not in existing and c not in skip_names]
    
    if not new_cols:
        print(f"       0 colonne nuove → SKIP")
        continue
    
    # ── MERGE ──
    subset = df_owid[['ISO_Code', 'Date'] + new_cols].drop_duplicates(subset=['ISO_Code', 'Date'])
    for c in new_cols:
        subset[c] = pd.to_numeric(subset[c], errors='coerce')
    
    before = df_merged.shape[1]
    df_merged = df_merged.merge(subset, on=['ISO_Code', 'Date'], how='left', suffixes=('', f'__dup'))
    
    # Rimuovi duplicati
    dups = [c for c in df_merged.columns if c.endswith('__dup')]
    if dups:
        df_merged.drop(columns=dups, inplace=True)
    
    added = df_merged.shape[1] - before
    total_added += added
    
    # Calcola match rate
    match = subset.merge(df_merged[['ISO_Code', 'Date']].drop_duplicates(), on=['ISO_Code', 'Date'], how='inner').shape[0]
    print(f"      +{added} colonne nuove | Match: {match:,} righe")
    if added > 0:
        for c in new_cols[:5]:
            if c in df_merged.columns:
                fill = (1 - df_merged[c].isna().mean()) * 100
                print(f"        • {c} ({fill:.0f}% dati)")
        if len(new_cols) > 5:
            print(f"        • ... +{len(new_cols)-5} altre")

# ════════════════════════════════════════════════════════════════
# STEP 4: PULIZIA
# ════════════════════════════════════════════════════════════════
hdr("STEP 4: Pulizia")

empty = [c for c in df_merged.columns if df_merged[c].isna().all()]
if empty:
    print(f"    {len(empty)} colonne vuote rimosse")
    df_merged.drop(columns=empty, inplace=True)

df_merged = df_merged.sort_values(['ISO_Code', 'Date']).reset_index(drop=True)
print(f"   Finale: {df_merged.shape[0]:,} righe × {df_merged.shape[1]} colonne")

# ════════════════════════════════════════════════════════════════
# STEP 5: SALVA
# ════════════════════════════════════════════════════════════════
hdr("STEP 5: Salvataggio")

df_merged.to_csv(OUTPUT_CSV, index=False)
print(f"   CSV: {OUTPUT_CSV} ({os.path.getsize(OUTPUT_CSV)/1024/1024:.1f} MB)")

os.makedirs(os.path.dirname(OUTPUT_PARQUET), exist_ok=True)
for col in df_merged.select_dtypes(include=['object']).columns:
    if col not in ['ISO_Code', 'Country', 'Continent']:
        df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce')

df_merged.to_parquet(OUTPUT_PARQUET, engine='pyarrow', index=False, compression='snappy')
print(f"  Parquet: {OUTPUT_PARQUET} ({os.path.getsize(OUTPUT_PARQUET)/1024/1024:.1f} MB)")

# ════════════════════════════════════════════════════════════════
# RIEPILOGO
# ════════════════════════════════════════════════════════════════
hdr("PROCESSO COMPLETATO")

new_col_list = [c for c in df_merged.columns if c not in master_original_cols]
print(f"""
  PRIMA:  {len(master_original_cols)} colonne
  DOPO:   {df_merged.shape[1]} colonne (+{len(new_col_list)} nuove)
  RIGHE:  {df_merged.shape[0]:,}
  PAESI:  {df_merged['ISO_Code'].nunique()}

  Dataset saltati: {', '.join(skipped) if skipped else 'nessuno'}

     Esegui:
     python 2_parquet_to_mongo.py
""")

if new_col_list:
    print("NUOVE COLONNE:")
    print("  " + "-" * 55)
    for i, c in enumerate(new_col_list, 1):
        fill = (1 - df_merged[c].isna().mean()) * 100
        print(f"     {i:2d}. {c:<45s} ({fill:.0f}% dati)")
