
"""
═══════════════════════════════════════════════════════════════════════════════
PandemicPulse™ — Neo4j Graph Analysis
═══════════════════════════════════════════════════════════════════════════════

GRAFO in Neo4j che modella le relazioni
epidemiologiche tra paesi durante la pandemia COVID-19.
Requisiti:
  pip install neo4j pandas pyarrow numpy

Uso:
  python 8_neo4j_graph_analysis.py

  Neo4j Browser: http://localhost:7474
  Credenziali:   neo4j / pandemic_pulse_2024
═══════════════════════════════════════════════════════════════════════════════
"""

from neo4j import GraphDatabase
import pandas as pd
import numpy as np
import os
import sys


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "pandemic_pulse_2024")

# Soglie per la creazione di relazioni
EPIDEMIC_CORR_THRESHOLD = 0.85   # Correlazione minima per SIMILAR_EPIDEMIC_PATTERN
POLICY_DIFF_THRESHOLD = 5.0      # Differenza max stringency per SIMILAR_POLICY_RESPONSE
PEAK_LAG_MAX_DAYS = 14           # Finestra max per BORDER_SPREAD (giorni)


def load_data():
    """Carica il dataset da MongoDB (covid_database.historical_data)."""
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.server_info()
        print("📂 Connessione a MongoDB riuscita")
        items = list(client["covid_database"]["historical_data"].find({}, {'_id': 0}))
        df = pd.DataFrame(items)
        print(f"   {len(df):,} documenti caricati da MongoDB")
    except Exception as e:
        print(f"MongoDB non raggiungibile: {e}")
        sys.exit(1)

    # Normalizza nomi colonne
    rename = {
        'iso_code': 'ISO_Code', 'date': 'Date',
        'confirmed': 'Confirmed', 'deaths': 'Deaths',
        'continent': 'Continent',
    }
    df.rename(columns={k: v for k, v in rename.items() if k in df.columns}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df[df['ISO_Code'].astype(str).str.len() == 3].copy()
    df.sort_values(['ISO_Code', 'Date'], inplace=True)

    
    df['New_Cases'] = df.groupby('ISO_Code')['Confirmed'].diff().clip(lower=0).fillna(0)
    df['New_Cases_7d'] = df.groupby('ISO_Code')['New_Cases'].transform(
        lambda x: x.rolling(7, min_periods=1).mean())

    print(f"   {df['ISO_Code'].nunique()} paesi · "
          f"{df['Date'].min().date()} → {df['Date'].max().date()}")
    return df


def compute_country_metrics(df):
    """Calcola le metriche aggregate per ogni paese (attributi dei nodi)."""
    latest = df.sort_values('Date').groupby('ISO_Code').last().reset_index()

    metrics = []
    for _, row in latest.iterrows():
        iso = row['ISO_Code']
        country_data = df[df['ISO_Code'] == iso]
        peak_row = country_data.loc[country_data['New_Cases_7d'].idxmax()] if country_data['New_Cases_7d'].notna().any() else None

        m = {
            'iso_code': iso,
            'continent': row.get('Continent', 'Unknown'),
            'total_confirmed': int(row.get('Confirmed', 0)),
            'total_deaths': int(row.get('Deaths', 0)),
            'population': float(row.get('population', 0)),
            'population_density': float(row.get('population_density', 0)) if pd.notna(row.get('population_density')) else 0,
            'median_age': float(row.get('median_age', 0)) if pd.notna(row.get('median_age')) else 0,
            'gdp_per_capita': float(row.get('gdp_per_capita', 0)) if pd.notna(row.get('gdp_per_capita')) else 0,
            'life_expectancy': float(row.get('life_expectancy', 0)) if pd.notna(row.get('life_expectancy')) else 0,
            'total_cases_per_million': float(row.get('total_cases_per_million', 0)) if pd.notna(row.get('total_cases_per_million')) else 0,
            'total_deaths_per_million': float(row.get('total_deaths_per_million', 0)) if pd.notna(row.get('total_deaths_per_million')) else 0,
            'peak_date': peak_row['Date'].isoformat() if peak_row is not None and pd.notna(peak_row.get('Date')) else None,
            'peak_cases_7d': float(peak_row['New_Cases_7d']) if peak_row is not None and pd.notna(peak_row.get('New_Cases_7d')) else 0,
        }

        # Media stringency (per SIMILAR_POLICY_RESPONSE)
        for col in ['containment_health_index', 'stringency_index_vax', 'stringency_index_nonvax']:
            if col in country_data.columns:
                m[f'avg_{col}'] = float(country_data[col].mean()) if country_data[col].notna().sum() > 0 else 0
            else:
                m[f'avg_{col}'] = 0

        metrics.append(m)
    return metrics


def compute_epidemic_correlations(df, threshold=EPIDEMIC_CORR_THRESHOLD):
    """
    Calcola la correlazione tra le curve epidemiche (7d avg) di ogni coppia di paesi.
    Restituisce solo le coppie con correlazione >= threshold.
    """
    print(f" Calcolo correlazioni epidemiche (soglia r ≥ {threshold})...")

    # Pivot: una colonna per paese, righe = date, valori = New_Cases_7d
    pivot = df.pivot_table(index='Date', columns='ISO_Code', values='New_Cases_7d')
    # Richiedi almeno 60 giorni di dati per il calcolo
    valid_cols = [c for c in pivot.columns if pivot[c].notna().sum() >= 60]
    pivot = pivot[valid_cols]

    corr_matrix = pivot.corr()
    edges = []
    seen = set()
    for i, c1 in enumerate(corr_matrix.columns):
        for j, c2 in enumerate(corr_matrix.columns):
            if i >= j:
                continue
            r = corr_matrix.iloc[i, j]
            if not np.isnan(r) and abs(r) >= threshold:
                key = tuple(sorted([c1, c2]))
                if key not in seen:
                    seen.add(key)
                    edges.append({
                        'source': c1, 'target': c2,
                        'correlation': round(float(r), 4)
                    })

    print(f"   → {len(edges)} coppie con r ≥ {threshold}")
    return edges


def compute_policy_similarity(metrics, threshold=POLICY_DIFF_THRESHOLD):
    """Trova paesi con politiche di contenimento simili."""
    print(f" Calcolo similarità di policy (diff < {threshold})...")

    edges = []
    seen = set()
    for i, a in enumerate(metrics):
        for j, b in enumerate(metrics):
            if i >= j:
                continue
            avg_a = a.get('avg_containment_health_index', 0)
            avg_b = b.get('avg_containment_health_index', 0)
            if avg_a > 0 and avg_b > 0:
                diff = abs(avg_a - avg_b)
                if diff < threshold:
                    key = tuple(sorted([a['iso_code'], b['iso_code']]))
                    if key not in seen:
                        seen.add(key)
                        edges.append({
                            'source': a['iso_code'],
                            'target': b['iso_code'],
                            'stringency_diff': round(diff, 2)
                        })

    print(f"   → {len(edges)} coppie con policy simile")
    return edges


def compute_border_spread(metrics, max_lag=PEAK_LAG_MAX_DAYS):
    """
    Trova paesi nello stesso continente con picco epidemico entro N giorni
    l'uno dall'altro (suggerisce propagazione geografica).
    """
    print(f" Calcolo propagazione regionale (lag picco < {max_lag}gg)...")

    edges = []
    seen = set()
    for i, a in enumerate(metrics):
        for j, b in enumerate(metrics):
            if i >= j:
                continue
            if a['continent'] != b['continent'] or a['continent'] in ('Unknown', ''):
                continue
            if a['peak_date'] and b['peak_date']:
                try:
                    da = pd.Timestamp(a['peak_date'])
                    db = pd.Timestamp(b['peak_date'])
                    lag = (db - da).days
                    if 0 < abs(lag) <= max_lag:
                        key = tuple(sorted([a['iso_code'], b['iso_code']]))
                        if key not in seen:
                            seen.add(key)
                            # La direzione va dal paese con picco precedente
                            src, tgt = (a, b) if lag > 0 else (b, a)
                            edges.append({
                                'source': src['iso_code'],
                                'target': tgt['iso_code'],
                                'peak_lag_days': abs(lag),
                                'peak_date_source': min(da, db).isoformat(),
                                'peak_date_target': max(da, db).isoformat(),
                            })
                except:
                    pass

    print(f"   → {len(edges)} coppie con propagazione regionale")
    return edges


# ═══════════════════════════════════════════════════════════════════════════════
# COSTRUZIONE GRAFO IN NEO4J
# ═══════════════════════════════════════════════════════════════════════════════
class PandemicGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f" Connesso a Neo4j: {uri}")

    def close(self):
        self.driver.close()

    def clear_graph(self):
        """Pulisce il grafo esistente."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("🧹 Grafo pulito.")

    def create_constraints(self):
        """Crea vincoli di unicità e indici."""
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Country) REQUIRE c.iso_code IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (co:Continent) REQUIRE co.name IS UNIQUE")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Country) ON (c.continent)")
        print("🔑 Vincoli e indici creati.")

    def create_continents(self, continents):
        """Crea i nodi Continent."""
        with self.driver.session() as session:
            for cont in continents:
                session.run("MERGE (co:Continent {name: $name})", name=cont)
        print(f" {len(continents)} continenti creati.")

    def create_countries(self, metrics):
        """Crea i nodi Country con tutti gli attributi."""
        with self.driver.session() as session:
            for m in metrics:
                session.run("""
                    MERGE (c:Country {iso_code: $iso_code})
                    SET c.continent = $continent,
                        c.total_confirmed = $total_confirmed,
                        c.total_deaths = $total_deaths,
                        c.population = $population,
                        c.population_density = $population_density,
                        c.median_age = $median_age,
                        c.gdp_per_capita = $gdp_per_capita,
                        c.life_expectancy = $life_expectancy,
                        c.total_cases_per_million = $total_cases_per_million,
                        c.total_deaths_per_million = $total_deaths_per_million,
                        c.peak_date = $peak_date,
                        c.peak_cases_7d = $peak_cases_7d,
                        c.avg_containment_health_index = $avg_chi,
                        c.avg_stringency_vax = $avg_svax,
                        c.avg_stringency_nonvax = $avg_snvax
                """, iso_code=m['iso_code'], continent=m['continent'],
                    total_confirmed=m['total_confirmed'], total_deaths=m['total_deaths'],
                    population=m['population'], population_density=m['population_density'],
                    median_age=m['median_age'], gdp_per_capita=m['gdp_per_capita'],
                    life_expectancy=m['life_expectancy'],
                    total_cases_per_million=m['total_cases_per_million'],
                    total_deaths_per_million=m['total_deaths_per_million'],
                    peak_date=m['peak_date'], peak_cases_7d=m['peak_cases_7d'],
                    avg_chi=m['avg_containment_health_index'],
                    avg_svax=m['avg_stringency_index_vax'],
                    avg_snvax=m['avg_stringency_index_nonvax'])

                # Relazione BELONGS_TO verso il continente
                if m['continent'] and m['continent'] != 'Unknown':
                    session.run("""
                        MATCH (c:Country {iso_code: $iso})
                        MATCH (co:Continent {name: $cont})
                        MERGE (c)-[:BELONGS_TO]->(co)
                    """, iso=m['iso_code'], cont=m['continent'])

        print(f"  {len(metrics)} paesi creati con relazioni BELONGS_TO.")

    def create_epidemic_edges(self, edges):
        """Crea le relazioni SIMILAR_EPIDEMIC_PATTERN."""
        with self.driver.session() as session:
            for e in edges:
                session.run("""
                    MATCH (a:Country {iso_code: $src})
                    MATCH (b:Country {iso_code: $tgt})
                    MERGE (a)-[r:SIMILAR_EPIDEMIC_PATTERN]-(b)
                    SET r.correlation = $corr
                """, src=e['source'], tgt=e['target'], corr=e['correlation'])
        print(f" {len(edges)} relazioni SIMILAR_EPIDEMIC_PATTERN create.")

    def create_policy_edges(self, edges):
        """Crea le relazioni SIMILAR_POLICY_RESPONSE."""
        with self.driver.session() as session:
            for e in edges:
                session.run("""
                    MATCH (a:Country {iso_code: $src})
                    MATCH (b:Country {iso_code: $tgt})
                    MERGE (a)-[r:SIMILAR_POLICY_RESPONSE]-(b)
                    SET r.stringency_diff = $diff
                """, src=e['source'], tgt=e['target'], diff=e['stringency_diff'])
        print(f" {len(edges)} relazioni SIMILAR_POLICY_RESPONSE create.")

    def create_spread_edges(self, edges):
        """Crea le relazioni BORDER_SPREAD (dirette: dal primo picco al secondo)."""
        with self.driver.session() as session:
            for e in edges:
                session.run("""
                    MATCH (a:Country {iso_code: $src})
                    MATCH (b:Country {iso_code: $tgt})
                    MERGE (a)-[r:BORDER_SPREAD]->(b)
                    SET r.peak_lag_days = $lag,
                        r.peak_date_source = $pd_src,
                        r.peak_date_target = $pd_tgt
                """, src=e['source'], tgt=e['target'], lag=e['peak_lag_days'],
                    pd_src=e['peak_date_source'], pd_tgt=e['peak_date_target'])
        print(f" {len(edges)} relazioni BORDER_SPREAD create.")

    def print_summary(self):
        """Stampa le statistiche del grafo."""
        with self.driver.session() as session:
            nodes = session.run("MATCH (n) RETURN labels(n)[0] AS label, COUNT(*) AS cnt").data()
            edges = session.run("MATCH ()-[r]->() RETURN type(r) AS type, COUNT(*) AS cnt").data()

        print("\n" + "═" * 60)
        print("RIEPILOGO GRAFO")
        print("═" * 60)
        print("\nNodi:")
        for n in nodes:
            print(f"  :{n['label']}  →  {n['cnt']}")
        print("\nRelazioni:")
        for e in edges:
            print(f"  :{e['type']}  →  {e['cnt']}")

    def run_demo_queries(self):
        """Esegue query dimostrative e stampa i risultati."""
        print("\n" + "═" * 60)
        print("🔍 QUERY DIMOSTRATIVE")
        print("═" * 60)

        with self.driver.session() as session:

            # 1. Hub epidemiologici
            print("\n TOP 10 — Hub epidemiologici (più connessioni simili):")
            result = session.run("""
                MATCH (c:Country)-[r:SIMILAR_EPIDEMIC_PATTERN]-()
                RETURN c.iso_code AS country, c.continent AS continent,
                       COUNT(r) AS connections
                ORDER BY connections DESC LIMIT 10
            """).data()
            for r in result:
                cont = str(r['continent'] or 'Unknown')
                print(f"   {r['country']:5s} ({cont:15s}) → {r['connections']} connessioni")

            # 2. Catene di diffusione dall'Italia
            print("\n Catene di diffusione dall'Italia (fino a 3 hop):")
            result = session.run("""
                MATCH path = (src:Country {iso_code:'ITA'})-[:BORDER_SPREAD*1..3]->(tgt:Country)
                WITH tgt, min(length(path)) AS hops
                RETURN tgt.iso_code AS country, hops
                ORDER BY hops, country LIMIT 15
            """).data()
            for r in result:
                print(f"   ITA {'→ ' * r['hops']}{r['country']} ({r['hops']} hop)")

            # 3. Policy simile ma esiti diversi
            print("\n  Policy simile, esiti diversi (diff deaths/M > 500):")
            result = session.run("""
                MATCH (a:Country)-[:SIMILAR_POLICY_RESPONSE]-(b:Country)
                WHERE a.total_deaths_per_million > 0 AND b.total_deaths_per_million > 0
                  AND abs(a.total_deaths_per_million - b.total_deaths_per_million) > 500
                RETURN a.iso_code AS country_a,
                       round(a.total_deaths_per_million) AS deaths_M_a,
                       b.iso_code AS country_b,
                       round(b.total_deaths_per_million) AS deaths_M_b
                ORDER BY abs(a.total_deaths_per_million - b.total_deaths_per_million) DESC
                LIMIT 10
            """).data()
            for r in result:
                print(f"   {r['country_a']} ({r['deaths_M_a']:.0f}/M) vs "
                      f"{r['country_b']} ({r['deaths_M_b']:.0f}/M)")

            # 4. Continenti con più connessioni interne
            print("\n Densità di connessione per continente:")
            result = session.run("""
                MATCH (a:Country)-[:SIMILAR_EPIDEMIC_PATTERN]-(b:Country)
                WHERE a.continent = b.continent
                RETURN a.continent AS continent, COUNT(*) AS internal_links
                ORDER BY internal_links DESC
            """).data()
            for r in result:
                cont = str(r['continent'] or 'Unknown')
                print(f"   {cont:20s} → {r['internal_links']} connessioni interne")

            # 5. PageRank-like: centralità di grado
            print("\n Centralità di grado (tutte le relazioni):")
            result = session.run("""
                MATCH (c:Country)-[r]-()
                RETURN c.iso_code AS country, c.continent AS continent,
                       COUNT(r) AS degree
                ORDER BY degree DESC LIMIT 10
            """).data()
            for r in result:
                cont = str(r['continent'] or 'Unknown')
                print(f"   {r['country']:5s} ({cont:15s}) → grado {r['degree']}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 60)
    print("🧬 PandemicPulse™ — Neo4j Graph Builder")
    print("═" * 60)

    # 1. Carica dati
    df = load_data()

    # 2. Calcola metriche per paese
    print("\n Calcolo metriche per paese...")
    metrics = compute_country_metrics(df)
    continents = list(set(m['continent'] for m in metrics if m['continent'] and m['continent'] != 'Unknown'))
    print(f"   {len(metrics)} paesi · {len(continents)} continenti")

    # 3. Calcola relazioni
    print()
    epidemic_edges = compute_epidemic_correlations(df)
    policy_edges = compute_policy_similarity(metrics)
    spread_edges = compute_border_spread(metrics)

    # 4. Costruisci grafo in Neo4j
    print(f"\n Connessione a Neo4j ({NEO4J_URI})...")
    graph = PandemicGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

    try:
        graph.clear_graph()
        graph.create_constraints()
        graph.create_continents(continents)
        graph.create_countries(metrics)
        graph.create_epidemic_edges(epidemic_edges)
        graph.create_policy_edges(policy_edges)
        graph.create_spread_edges(spread_edges)
        graph.print_summary()
        graph.run_demo_queries()
    finally:
        graph.close()

    print("\n  Grafo costruito con successo!")
    print("   → Apri Neo4j Browser: http://localhost:7474")
    print("   → Credenziali: neo4j / pandemic_pulse_2024")
    print("   → Prova: MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100")
