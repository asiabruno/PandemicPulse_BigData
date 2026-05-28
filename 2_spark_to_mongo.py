"""
======================================================================
SPARK → MONGODB LOADER 
======================================================================
Spark legge il CSV finale, effettua trasformazioni e quality checks,
poi carica direttamente in MongoDB.

Pipeline:  CSV → Spark (processing) → MongoDB → Dashboard

Uso:
    cd ~/Desktop/PROJECT
    python 2_spark_to_mongo.py

Prerequisiti:
    - Docker con MongoDB attivo (docker-compose up -d)
    - master_merged_complete.csv nella directory corrente
    - pip install pyspark pymongo
======================================================================
"""

import os
import sys
import time
import numpy as np
from datetime import datetime

# ── Verifica file input ──────────────────────────────────────────────
INPUT_CSV = "master_merged_complete.csv"
if not os.path.exists(INPUT_CSV):
    print(f"File {INPUT_CSV} non trovato.")
    print("Esegui prima gli script di preprocessing (1, 3, 5, 6).")
    sys.exit(1)

print("=" * 65)
print("  SPARK to MONGODB — Direct CSV Pipeline")
print("=" * 65)
print(f"  Input:  {INPUT_CSV}")
print(f"  Output: MongoDB covid_database.historical_data")
print()

# ── Avvia Spark ──────────────────────────────────────────────────────
from pyspark.sql import SparkSession

spark = (SparkSession.builder
    .appName("PandemicPulse_CSV_to_MongoDB")
    .config("spark.driver.memory", "4g")
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
    .getOrCreate())

spark.sparkContext.setLogLevel("WARN")

# ── Step 1: Lettura CSV con Spark ────────────────────────────────────
print("STEP 1 | Lettura CSV tramite Spark...")
t0 = time.time()

df_spark = spark.read.csv(
    INPUT_CSV,
    header=True,
    inferSchema=True,
    multiLine=True,
    escape='"'
)

n_rows = df_spark.count()
n_cols = len(df_spark.columns)
print(f"         {n_rows:,} righe x {n_cols} colonne ({time.time()-t0:.1f}s)")

# ── Step 2: Quality checks e trasformazioni Spark ────────────────────
print("STEP 2 | Processing Spark (quality checks + trasformazioni)...")
t1 = time.time()

from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType

# 2a. Assicura che Date sia stringa pulita (YYYY-MM-DD)
if 'Date' in df_spark.columns:
    df_spark = df_spark.withColumn('Date',
        F.regexp_extract(F.col('Date').cast('string'), r'(\d{4}-\d{2}-\d{2})', 1))
    # Rimuovi righe senza data valida
    df_spark = df_spark.filter(F.col('Date') != '')

# 2b. Filtra solo ISO codes validi (3 caratteri)
if 'ISO_Code' in df_spark.columns:
    df_spark = df_spark.filter(F.length(F.col('ISO_Code')) == 3)

# 2c. Cast colonne numeriche (tutte tranne le categoriche)
categorical = {'ISO_Code', 'Date', 'Country', 'Continent'}
for col_name in df_spark.columns:
    if col_name not in categorical:
        df_spark = df_spark.withColumn(col_name, F.col(col_name).cast(DoubleType()))

# 2d. Conta valori nulli per colonne chiave
key_cols = ['ISO_Code', 'Date', 'Confirmed', 'Deaths']
for kc in key_cols:
    if kc in df_spark.columns:
        null_count = df_spark.filter(F.col(kc).isNull()).count()
        pct = null_count / n_rows * 100
        status = "OK" if pct < 5 else "WARN" if pct < 30 else "HIGH"
        print(f"         Quality: {kc:<30s} nulls: {null_count:>6,} ({pct:.1f}%) [{status}]")

# 2e. Conta paesi e range date
n_countries = df_spark.select('ISO_Code').distinct().count()
date_range = df_spark.agg(F.min('Date'), F.max('Date')).collect()[0]
print(f"         Paesi: {n_countries} | Date: {date_range[0]} -> {date_range[1]}")

# 2f. Verifica presenza colonne disinformazione
disinfo_cols = [c for c in df_spark.columns if 'disinfo' in c or 'trust' in c or 'proscience' in c]
fc_cols = [c for c in df_spark.columns if 'factcheck' in c]
print(f"         Colonne disinfo: {len(disinfo_cols)} | Colonne fact-check: {len(fc_cols)}")

print(f"         Processing completato ({time.time()-t1:.1f}s)")

# ── Step 3: Conversione Spark → Pandas → MongoDB ────────────────────
print("STEP 3 | Conversione Spark -> Pandas...")
t2 = time.time()

df_pandas = df_spark.toPandas()
print(f"         {len(df_pandas):,} righe convertite ({time.time()-t2:.1f}s)")

# ── Step 4: Pulizia per MongoDB ──────────────────────────────────────
print("STEP 4 | Pulizia NaN/Inf per MongoDB...")
t3 = time.time()

def clean_value(v):
    """Pulisce un singolo valore per compatibilita MongoDB."""
    if v is None:
        return None
    if isinstance(v, float):
        if np.isnan(v) or np.isinf(v):
            return None
    # Converti tipi numpy in tipi Python nativi
    if hasattr(v, 'item'):
        try:
            v = v.item()
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                return None
        except (ValueError, OverflowError):
            return None
    return v

records = df_pandas.to_dict('records')
cleaned = []
for rec in records:
    cleaned.append({k: clean_value(v) for k, v in rec.items()})

print(f"         {len(cleaned):,} record puliti ({time.time()-t3:.1f}s)")

# ── Step 5: Inserimento MongoDB ──────────────────────────────────────
print("STEP 5 | Caricamento in MongoDB...")
t4 = time.time()

from pymongo import MongoClient

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    client.server_info()
except Exception as e:
    print(f"         MongoDB non raggiungibile: {e}")
    print("         Esegui: docker-compose up -d")
    spark.stop()
    sys.exit(1)

db = client["covid_database"]
collection = db["historical_data"]

# Drop collection esistente
collection.drop()
print("         Collection svuotata")

# Inserisci in chunk da 2000
CHUNK = 2000
total = len(cleaned)
for i in range(0, total, CHUNK):
    chunk = cleaned[i:i+CHUNK]
    collection.insert_many(chunk)
    pct = min((i + CHUNK) / total * 100, 100)
    print(f"         [{pct:5.1f}%] {min(i+CHUNK, total):,} / {total:,}")

elapsed = time.time() - t4
print(f"         Inserimento completato ({elapsed:.1f}s)")

# ── Step 6: Verifica finale ──────────────────────────────────────────
print("STEP 6 | Verifica finale...")
count = collection.count_documents({})
sample = collection.find_one({}, {'_id': 0})
sample_keys = list(sample.keys()) if sample else []

# Verifica dati disinfo
disinfo_count = collection.count_documents({'disinfo_index': {'$exists': True, '$ne': None}})
fc_count = collection.count_documents({'factcheck_count': {'$exists': True, '$ne': None}})

print(f"""
{'='*65}
  COMPLETATO
{'='*65}

  Database:    covid_database
  Collection:  historical_data
  Documenti:   {count:,}
  Colonne:     {len(sample_keys)}
  Disinfo:     {disinfo_count:,} documenti con dati Google Trends
  Fact-check:  {fc_count:,} documenti con dati FakeCovid

  Tempo totale: {time.time()-t0:.1f}s

  Prossimo step:
     streamlit run 5_dashboard.py
""")

spark.stop()
