from confluent_kafka import Producer
from pymongo import MongoClient
from datetime import datetime
import json
import time


conf = {'bootstrap.servers': 'localhost:29092', 'client.id': 'covid-daily-producer'}
producer = Producer(conf)
topic = 'covid_realtime'

client = MongoClient("mongodb://localhost:27017/")
db = client["covid_database"]
storico = db["historical_data"]


SIM_START_DATE = "2021-02-01"

print(f" Simulazione live dal: {SIM_START_DATE}")


sample = storico.find_one({})
if sample:
    date_field = 'date' if 'date' in sample else 'Date'
    iso_field  = 'iso_code' if 'iso_code' in sample else 'ISO_Code'
    
    sample_date = sample.get(date_field)
    if isinstance(sample_date, datetime):
        sim_start_val = datetime.strptime(SIM_START_DATE, "%Y-%m-%d")
        print("Tipo date in MongoDB: datetime")
    else:
        sim_start_val = SIM_START_DATE
        print("Tipo date in MongoDB: stringa")
else:
    date_field, iso_field = 'Date', 'ISO_Code'
    sim_start_val = SIM_START_DATE

print(f"Schema rilevato → date='{date_field}', iso='{iso_field}'")


pipeline = [
    {"$group": {"_id": f"${date_field}"}},
    {"$match": {"_id": {"$gte": sim_start_val}}},
    {"$sort": {"_id": 1}}
]
ultime_date = [d["_id"] for d in storico.aggregate(pipeline)]

print(f" Inizio Replay: {len(ultime_date)} giorni da {SIM_START_DATE}...")


def normalize_doc(doc):
    """Normalizza il documento al formato Pascal_Case (maiuscola iniziale + underscore) atteso dalla dashboard."""
    doc.pop('_id', None)
    renames = {
        'iso_code':  'ISO_Code',
        'date':      'Date',
        'confirmed': 'Confirmed',
        'deaths':    'Deaths',
        'continent': 'Continent',
    }
    for old, new in renames.items():
        if old in doc and new not in doc:
            doc[new] = doc.pop(old)
    doc['New_Confirmed'] = doc.get('New_Confirmed', doc.get('Confirmed', 0))
    return doc


try:
    for data_target in ultime_date:
        bollettini_giorno = list(storico.find({date_field: data_target}))

        print(f" Inviando: {data_target} ({len(bollettini_giorno)} paesi)...")

        for doc in bollettini_giorno:
            doc = normalize_doc(doc)
            producer.produce(topic, value=json.dumps(doc, default=str))

        producer.flush()
        print(f" {data_target} completato.")

        time.sleep(3)  # 3 secondi tra un giorno e l'altro

except KeyboardInterrupt:
    print("\n🛑 Stop.")
