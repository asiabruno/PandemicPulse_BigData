
Prerequisiti

- [Docker](https://www.docker.com/) e Docker Compose
- Python 3.x

---

Comando Avvio Rapido

1. Scaricare la cartella PROGETTO su Desktop poi eseguire in terminale cd Desktop
2. Eseguire cd PROGETTO
3. Eseguire chmod +x start.sh (solo al primo avvio del progetto)
4. Eseguire ./start.sh

Lo script esegue in sequenza:

1. Avvia i container Docker (MongoDB, Kafka, Zookeeper, Neo4j)
2. Installa le dipendenze Python
3. Importa i dati CSV su MongoDB via Spark
4. Avvia l'analisi del grafo Neo4j in background
5. Apre il Kafka Consumer in un nuovo terminale
6. Apre il Kafka Producer in un nuovo terminale
7. Lancia la dashboard Streamlit in foreground

Per avvio manuale: 

1. Avvio dei servizi Docker
docker compose up -d

2. Installazione dipendenze
pip install -r requirements.txt
pip install pyvis

3. Importazione dei dati su MongoDB
python3 2_spark_to_mongo.py

4. Avvio  dell'analisi Neo4j (background)
python3 8_neo4j_graph_analysis.py &

5. Avvio del Kafka Consumer (terminale separato)
python3 7_kafka_consumer_adapted.py

6. Avvio del Kafka Producer (terminale separato)
python3 6_kafka_producer_adapted.py

7. Avvio della dashboard
streamlit run 5_dashboard.py


Struttura del Progetto
PROGETTO
├── docker-compose.yml          # Definizione dei servizi Docker
├── requirements.txt            # Dipendenze Python
├── start.sh                    # Script di avvio automatico
├── data/                       # Dataset CSV da importare
├── 2_spark_to_mongo.py         # Import dati: CSV → Spark → MongoDB
├── 5_dashboard.py              # Dashboard Streamlit
├── 6_kafka_producer_adapted.py # Producer Kafka
├── 7_kafka_consumer_adapted.py # Consumer Kafka
└── 8_neo4j_graph_analysis.py   # Analisi grafo Neo4j

--
Arresto dei Servizi

Per spegnere tutti i container Docker:

docker compose down

Per rimuovere anche i volumi persistenti:

docker compose down -v

--

Autori
REGA Giuseppe
BRUNO Asia
GILIBERTI Felicita