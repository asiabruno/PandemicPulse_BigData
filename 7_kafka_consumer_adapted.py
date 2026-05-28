from confluent_kafka import Consumer
from pymongo import MongoClient
from datetime import datetime, timezone
import json


conf = {
    'bootstrap.servers': 'localhost:29092',
    'group.id': 'covid-live-group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
topic = 'covid_realtime'
consumer.subscribe([topic])

# 2. MongoDB - collection realtime_data
client = MongoClient("mongodb://localhost:27017/")
db = client["covid_database"]
collection = db["realtime_data"]


collection.create_index(
    [("ISO_Code", 1), ("Date", 1)],
    unique=True,
    name="idx_iso_date_unique"
)

collection.create_index([("received_at", 1)], name="idx_received_at")

print("Indici verificati su realtime_data.")
print(f"In ascolto in diretta sul canale: {topic}...")
print("Premi Ctrl+C per fermare la ricezione.\n")

try:
    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print(f"❌ Errore Kafka: {msg.error()}")
            continue

        bollettino = json.loads(msg.value().decode('utf-8'))

        # ── Normalizzazione campi chiave ──────────────────────────────────────
        if 'iso_code' in bollettino and 'ISO_Code' not in bollettino:
            bollettino['ISO_Code'] = bollettino.pop('iso_code')
        if 'date' in bollettino and 'Date' not in bollettino:
            bollettino['Date'] = bollettino.pop('date')

        casi  = bollettino.get('New_Confirmed', bollettino.get('Confirmed', 0))
        paese = bollettino.get('ISO_Code', 'Unknown')
        data  = bollettino.get('Date', 'N/A')

        bollettino['New_Confirmed'] = casi

        # ── Timestamp di ricezione reale ──────────────────────────────────────
        now_utc = datetime.now(timezone.utc)

        collection.update_one(
            {"ISO_Code": paese, "Date": data},
            {
                "$set": bollettino,
                "$setOnInsert": {"received_at": now_utc}
            },
            upsert=True
        )

        print(f" {paese} | {data} | Casi: {casi} | ricevuto: {now_utc.strftime('%H:%M:%S')}")

except KeyboardInterrupt:
    print("\n🛑 Ricevitore spento.")

finally:
    consumer.close()
    print("Connessione chiusa.")
