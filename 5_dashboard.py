import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestRegressor
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
try:
    from neo4j import GraphDatabase as _Neo4jDriver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

# ═══════════════════════════════════════════════════════
# GONFIGURAZIONE PAGINA
# ═══════════════════════════════════════════════════════
st.set_page_config(page_title="PandemicPulse", layout="wide", page_icon="", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════
# CSS — DARK THEME
# ═══════════════════════════════════════════════════════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&family=Playfair+Display:wght@700;800;900&display=swap');
:root{--bg-0:#06090f;--bg-1:#0c1220;--bg-2:#131c30;--bg-3:#1a2540;--border:#263354;--text-1:#f0f4fc;--text-2:#a0b0cc;--text-3:#607090;--blue:#4d8df7;--blue-b:#78aeff;--red:#ff5c5c;--red-b:#ff8a8a;--green:#34d399;--green-b:#6ee7b7;--amber:#fbbf24;--amber-b:#fde68a;--cyan:#22d3ee;--purple:#c084fc;--pink:#f472b6;--r:8px}
.main,.stApp,section[data-testid="stSidebar"]{background-color:var(--bg-0)!important}
.block-container{padding-top:.5rem!important;max-width:1500px!important}
h1,h2,h3,h4,h5,h6,p,span,div,label,li{font-family:'Inter',sans-serif!important;color:var(--text-1)!important}
h1{font-family:'Playfair Display',serif!important;font-weight:900!important}
section[data-testid="stSidebar"]{border-right:1px solid var(--border)!important}
section[data-testid="stSidebar"] *{color:var(--text-1)!important}
section[data-testid="stSidebar"] .stSelectbox>div>div{background:var(--bg-2)!important;border-color:var(--border)!important}
div[data-testid="stMetric"]{display:none}
#MainMenu,footer,header,div[data-testid="stDecoration"]{display:none!important;visibility:hidden!important}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:var(--bg-0)}::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
.hdr{background:linear-gradient(135deg,#0a1628,#162040,#0a1628);border:1px solid var(--border);border-radius:12px;padding:2rem 2.5rem;margin-bottom:1.5rem;position:relative;overflow:hidden}
.hdr::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 25% 50%,rgba(77,141,247,.1),transparent 60%),radial-gradient(ellipse at 75% 50%,rgba(255,92,92,.06),transparent 60%)}
.hdr *{position:relative;z-index:1}.hdr h1{font-size:2.4rem!important;color:#fff!important;margin:0!important}
.hdr .sub{color:var(--text-2)!important;font-size:.95rem;margin-top:.3rem}
.hdr .tags{display:flex;gap:8px;margin-top:1rem;flex-wrap:wrap}
.hdr .tag{background:rgba(77,141,247,.12);border:1px solid rgba(77,141,247,.3);color:var(--blue-b)!important;padding:4px 14px;border-radius:20px;font-size:.68rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-family:'JetBrains Mono',monospace!important}
.kpi{background:var(--bg-2);border:1px solid var(--border);border-radius:var(--r);padding:1.1rem 1.3rem;transition:all .2s}
.kpi:hover{background:var(--bg-3);transform:translateY(-2px);box-shadow:0 8px 25px rgba(0,0,0,.4)}
.kpi .lab{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3)!important;margin-bottom:.3rem}
.kpi .val{font-size:1.7rem;font-weight:800;color:var(--text-1)!important;line-height:1.1;font-family:'JetBrains Mono',monospace!important}
.kpi .suf{font-size:.75rem;color:var(--text-3)!important;margin-top:.2rem}
.kpi.red{border-left:4px solid var(--red)}.kpi.blue{border-left:4px solid var(--blue)}.kpi.green{border-left:4px solid var(--green)}.kpi.amber{border-left:4px solid var(--amber)}.kpi.cyan{border-left:4px solid var(--cyan)}.kpi.purple{border-left:4px solid var(--purple)}
.pan{background:var(--bg-1);border:1px solid var(--border);border-radius:var(--r);padding:1.4rem;margin-bottom:1.2rem}
.pan .pt{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--blue-b)!important;border-bottom:1px solid var(--border);padding-bottom:.5rem;margin-bottom:1rem;display:flex;align-items:center;gap:8px}
.badge-live{background:rgba(52,211,153,.12);color:var(--green-b)!important;border:1px solid rgba(52,211,153,.3);padding:2px 10px;border-radius:12px;font-size:.68rem;font-weight:700;font-family:'JetBrains Mono',monospace!important;margin-left:auto}
.badge-batch{background:rgba(77,141,247,.12);color:var(--blue-b)!important;border:1px solid rgba(77,141,247,.3);padding:2px 10px;border-radius:12px;font-size:.68rem;font-weight:700;font-family:'JetBrains Mono',monospace!important;margin-left:auto}
.sec-title{font-size:1.1rem!important;font-weight:800!important;color:var(--text-1)!important;margin:1.5rem 0 .8rem;padding-left:.5rem;border-left:4px solid var(--blue)}
.foot{text-align:center;padding:2rem 0 1rem;border-top:1px solid var(--border);margin-top:2rem}
.foot p{font-size:.72rem!important;color:var(--text-3)!important}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# PLOTLY HELPERS
# ═══════════════════════════════════════════════════════
DL = dict(font=dict(family="Inter",size=12,color="#a0b0cc"),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#0c1220",
    margin=dict(l=50,r=20,t=30,b=40),
    xaxis=dict(showgrid=True,gridwidth=1,gridcolor="#1a2540",linecolor="#263354",zeroline=False),
    yaxis=dict(showgrid=True,gridwidth=1,gridcolor="#1a2540",linecolor="#263354",zeroline=False),
    legend=dict(bgcolor="rgba(12,18,32,.9)",bordercolor="#263354",borderwidth=1,font=dict(size=11,color="#a0b0cc")),
    hoverlabel=dict(bgcolor="#1a2540",font_size=12,font_family="Inter",bordercolor="#263354",font_color="#f0f4fc"))

def apl(fig,**ov):
    b={k:v for k,v in DL.items()}
    for k in ov:
        if k in b: del b[k]
    fig.update_layout(**b,**ov)
    return fig

def hleg(**kw):
    return dict(orientation="h",y=1.08,x=0,bgcolor="rgba(0,0,0,0)",font=dict(color="#a0b0cc"),**kw)

C = {"blue":"#4d8df7","red":"#ff5c5c","green":"#34d399","amber":"#fbbf24","cyan":"#22d3ee","purple":"#c084fc","pink":"#f472b6","orange":"#fb923c"}

def kpi_html(cls,lab,val,suf):
    return f'<div class="kpi {cls}"><div class="lab">{lab}</div><div class="val">{val}</div><div class="suf">{suf}</div></div>'

def pan_open(icon,title,badge=None):
    b = f'<span class="badge-{"live" if badge=="live" else "batch"}">{badge.upper()}</span>' if badge else ''
    st.markdown(f'<div class="pan"><div class="pt">{icon} {title}{b}</div>',unsafe_allow_html=True)

def pan_close():
    st.markdown('</div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════
@st.cache_resource
def get_data():
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        client.server_info()
        items = list(client["covid_database"]["historical_data"].find({}, {"_id": 0}))
        df = pd.DataFrame(items)
    except:
        return pd.DataFrame()
    if df.empty:
        return df

    # ── Normalizza nomi colonne al nuovo schema snake_case ──────────────────
    # Il dataset pulito ha già: iso_code, date, confirmed, deaths, continent
    # ma per compatibilità con la dashboard usiamo alias CamelCase internamente
    rename_back = {
        'iso_code':  'ISO_Code',
        'date':      'Date',
        'confirmed': 'Confirmed',
        'deaths':    'Deaths',
        'continent': 'Continent',
    }
    df.rename(columns={k: v for k, v in rename_back.items() if k in df.columns}, inplace=True)

    # ── Parsing data ────────────────────────────────────────────────────────
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df[df['ISO_Code'].astype(str).str.len() == 3].copy()
    df.sort_values(['ISO_Code', 'Date'], inplace=True)

    # ── Colonne derivate ────────────────────────────────────────────────────
    df['New_Cases']  = df.groupby('ISO_Code')['Confirmed'].diff().clip(lower=0).fillna(0)
    df['New_Deaths'] = df.groupby('ISO_Code')['Deaths'].diff().clip(lower=0).fillna(0)
    for cn, src in [('New_Cases_7d', 'New_Cases'), ('New_Deaths_7d', 'New_Deaths')]:
        df[cn] = df.groupby('ISO_Code')[src].transform(lambda x: x.rolling(7, min_periods=1).mean())

    # ── stringency_index unificato (media vax/nonvax se non esiste) ─────────
    if 'stringency_index' not in df.columns:
        if 'stringency_index_vax' in df.columns and 'stringency_index_nonvax' in df.columns:
            df['stringency_index'] = df[['stringency_index_vax', 'stringency_index_nonvax']].mean(axis=1)

    if 'Country' not in df.columns:
        df['Country'] = df['ISO_Code']
    return df

df=get_data()
if df.empty:
    st.markdown('<div class="hdr"><h1>PandemicPulse</h1><p class="sub">Dataset non trovato</p></div>',unsafe_allow_html=True)
    st.error("MongoDB non raggiungibile o collection vuota. Esegui: docker compose up -d && python 2_spark_to_mongo.py")
    st.stop()

# ═══════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div style="text-align:center;padding:1rem 0 .5rem"><div style="font-family:Playfair Display,serif;font-size:1.5rem;font-weight:900;color:#fff">PandemicPulse</div><div style="font-size:.6rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#607090;margin-top:2px">Epidemiological Intelligence</div></div><hr style="border:none;border-top:1px solid #263354;margin:.5rem 0 1rem">',unsafe_allow_html=True)
    if 'sel' not in st.session_state: st.session_state.sel="Vista globale"
    countries=sorted(df['ISO_Code'].unique().tolist())
    opts=["Vista globale"]+countries
    idx=opts.index(st.session_state.sel) if st.session_state.sel in opts else 0
    sel=st.selectbox("Paese (ISO)",opts,index=idx,key="sb")
    st.session_state.sel=sel
    st.markdown("---")
    if st.button("Analisi Grafo Neo4j", use_container_width=True,
                 type="primary" if st.session_state.get("page")=="neo4j" else "secondary"):
        st.session_state["page"] = "neo4j" if st.session_state.get("page") != "neo4j" else None
        st.rerun()
    if 'Date' in df.columns:
        mn,mx=df['Date'].min().date(),df['Date'].max().date()
        dr=st.date_input("Intervallo date",value=(mn,mx),min_value=mn,max_value=mx)
    else: dr=None
    st.markdown("---")
    show_7d=st.toggle("Media mobile 7 giorni",value=True)
    log_scale=st.toggle("Scala logaritmica",value=False)
    st.markdown("---")
    st.markdown("### Architettura")
    st.markdown('<div style="font-size:.75rem;line-height:2"><span style="background:rgba(77,141,247,.15);color:#78aeff;padding:2px 8px;border-radius:4px;font-weight:700;font-family:JetBrains Mono,monospace;font-size:.65rem">BATCH</span> Spark → MongoDB<br><span style="background:rgba(52,211,153,.15);color:#6ee7b7;padding:2px 8px;border-radius:4px;font-weight:700;font-family:JetBrains Mono,monospace;font-size:.65rem">SPEED</span> Kafka<br><span style="background:rgba(251,191,36,.15);color:#fde68a;padding:2px 8px;border-radius:4px;font-weight:700;font-family:JetBrains Mono,monospace;font-size:.65rem">ML</span> Random Forest<br><span style="background:rgba(192,132,252,.15);color:#e9d5ff;padding:2px 8px;border-radius:4px;font-weight:700;font-family:JetBrains Mono,monospace;font-size:.65rem">STORE</span> MongoDB</div>',unsafe_allow_html=True)

if st.session_state.get("page") != "neo4j":
    st_autorefresh(interval=3000,key="ref")

# Filter by date
dff=df.copy()
if dr and len(dr)==2 and 'Date' in dff.columns:
    dff=dff[(dff['Date'].dt.date>=dr[0])&(dff['Date'].dt.date<=dr[1])]

# ╔═══════════════════════════════════════════════════════╗
# ║                  GLOBAL OVERVIEW                      ║
# ╚═══════════════════════════════════════════════════════╝
if st.session_state.sel=="Vista globale" and st.session_state.get("page") != "neo4j":
    st.markdown('<div class="hdr"><h1>PandemicPulse</h1><p class="sub">Intelligence Epidemiologica Globale — 184 Nazioni</p><div class="tags"><span class="tag">Docker</span><span class="tag">Spark</span><span class="tag">Kafka</span><span class="tag">MongoDB</span><span class="tag">Scikit-Learn</span><span class="tag">Streamlit</span></div></div>',unsafe_allow_html=True)

    nc=dff['ISO_Code'].nunique(); ld=dff['Date'].max().strftime('%d %b %Y'); nr=len(dff)
    tc=int(dff.groupby('ISO_Code')['Confirmed'].last().sum()) if 'Confirmed' in dff.columns else 0
    td=int(dff.groupby('ISO_Code')['Deaths'].last().sum()) if 'Deaths' in dff.columns else 0
    cols=st.columns(5)
    for col,c,l,v,s in zip(cols,['blue','green','amber','red','purple'],['Nazioni','Ultimo aggiornamento','Record','Casi','Decessi'],[str(nc),ld,f"{nr:,}",f"{tc:,}",f"{td:,}"],['Codici ISO','Ultimo','Spark','Confermati','Deceduti']):
        col.markdown(kpi_html(c,l,v,s),unsafe_allow_html=True)
    st.markdown('<div style="height:1rem"></div>',unsafe_allow_html=True)

    # Dati più recenti per paese (usati anche da Top 15)
    latest=dff.sort_values('Date').groupby('ISO_Code').last().reset_index()
    if 'New_Cases_7d' in latest.columns and latest['New_Cases_7d'].notna().sum()>10 and latest['New_Cases_7d'].max()>1:
        tgt='New_Cases_7d'
    else:
        tgt='Confirmed'

    # ── TIMELAPSE: propagazione globale nel tempo ─────────────────────────
    pan_open("","DIFFUSIONE PANDEMICA NEL TEMPO","batch")
    st.caption("Animazione mese per mese dei casi confermati cumulativi per paese (scala log₁₀). Premi > Play.")
    # Campiona per mese per mantenere la performance dell'animazione
    tl_data=dff.copy()
    tl_data['YearMonth']=tl_data['Date'].dt.to_period('M').astype(str)
    
    # Prendi il VALORE MASSIMO raggiunto nel mese (più sicuro di .last() in caso di dati mancanti a fine mese)
    tl_monthly=tl_data.groupby(['ISO_Code','YearMonth']).max(numeric_only=True).reset_index()
    tl_monthly=tl_monthly.sort_values('YearMonth')
    # Usa Confirmed (cumulativo) per il timelapse — mostra la crescita
    if 'Confirmed' in tl_monthly.columns and tl_monthly['Confirmed'].notna().sum()>50:
        tl_col='Confirmed'
    else:
        tl_col=tgt
    # Scala log per visualizzare meglio le differenze
    tl_monthly['Cases_Log']=np.log10(tl_monthly[tl_col].clip(lower=1))
    max_log=tl_monthly['Cases_Log'].max()
    fig_tl=px.choropleth(
        tl_monthly,
        locations="ISO_Code",
        color="Cases_Log",
        hover_name="ISO_Code",
        hover_data={tl_col:':,.0f','Cases_Log':False,'YearMonth':True},
        animation_frame="YearMonth",
        color_continuous_scale=[[0,"#0c1220"],[.2,"#1a2540"],[.4,"#1e3a7a"],[.6,"#3b6fd4"],[.8,"#ff5c5c"],[1,"#cc0000"]],
        range_color=[0,max_log],
        labels={'Cases_Log':'Casi (log₁₀)','YearMonth':'Mese'})
    fig_tl.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a0b0cc"),height=520,margin=dict(l=0,r=0,t=30,b=0),
        geo=dict(bgcolor="rgba(0,0,0,0)",landcolor="#131c30",showframe=False,
                 showcoastlines=True,coastlinecolor="#263354",countrycolor="#263354",
                 projection_type="natural earth",showocean=True,oceancolor="#0a0e17"),
        coloraxis_colorbar=dict(
            title=dict(text="Cases (log₁₀)",font=dict(size=11,color="#a0b0cc")),
            tickfont=dict(color="#a0b0cc"),thickness=10,len=.4,outlinewidth=0,
            tickvals=[0,2,4,6,8],ticktext=["1","100","10K","1M","100M"]),
        hoverlabel=dict(bgcolor="#1a2540",font_size=13,font_color="#f0f4fc",bordercolor="#263354"))
    # Stile bottoni animazione
    fig_tl.update_layout(
        sliders=[dict(
            currentvalue=dict(prefix=" ",font=dict(color="#a0b0cc",size=13)),
            font=dict(color="#a0b0cc"),bgcolor="#1a2540",bordercolor="#263354",
            activebgcolor="#4d8df7",len=0.9,x=0.05)],
        updatemenus=[dict(
            type="buttons",bgcolor="#1a2540",bordercolor="#263354",
            font=dict(color="#a0b0cc",size=11),
            buttons=[
                dict(label="> Play",method="animate",args=[None,{"frame":{"duration":400,"redraw":True},"fromcurrent":True}]),
                dict(label="|| Pause",method="animate",args=[[None],{"frame":{"duration":0,"redraw":False},"mode":"immediate"}])
            ],x=0.05,y=0,xanchor="right",yanchor="top")])
    st.plotly_chart(fig_tl,use_container_width=True)
    pan_close()

    # GLOBAL CURVE
    pan_open("","CURVA EPIDEMICA GLOBALE","batch")
    st.caption("Nuovi casi giornalieri sommati globalmente. La linea blu è la media mobile a 7 giorni che liscia le fluttuazioni dei weekend.")
    dg=dff.groupby('Date').agg(New_Cases=('New_Cases','sum'),New_Cases_7d=('New_Cases_7d','sum')).reset_index()
    fig_gc=go.Figure()
    fig_gc.add_trace(go.Bar(x=dg['Date'],y=dg['New_Cases'],name="Daily",marker_color="rgba(77,141,247,.25)",marker_line_width=0))
    if show_7d: fig_gc.add_trace(go.Scatter(x=dg['Date'],y=dg['New_Cases_7d'],name="7d Avg",line=dict(color=C['blue'],width=3)))
    apl(fig_gc,height=380,yaxis_type="log" if log_scale else "linear",legend=hleg())
    st.plotly_chart(fig_gc,use_container_width=True)
    pan_close()

    # TOP 15
    c1,c2=st.columns(2)
    with c1:
        pan_open("","TOP 15 — CASI")
        st.caption("I 15 paesi con il maggior numero di casi confermati cumulativi.")
        t15=latest.nlargest(15,'Confirmed')
        fig=go.Figure(go.Bar(y=t15['ISO_Code'],x=t15['Confirmed'],orientation='h',marker=dict(color=t15['Confirmed'],colorscale=[[0,"#1e3a7a"],[1,"#4d8df7"]],cornerradius=4),hovertemplate="%{y}: %{x:,.0f}<extra></extra>"))
        apl(fig,height=420,yaxis=dict(autorange="reversed",gridcolor="#1a2540",linecolor="#263354",zeroline=False),showlegend=False)
        st.plotly_chart(fig,use_container_width=True); pan_close()
    with c2:
        pan_open("","TOP 15 — DECESSI")
        st.caption("I 15 paesi con il maggior numero di decessi cumulativi.")
        if 'Deaths' in latest.columns:
            t15d=latest.nlargest(15,'Deaths')
            fig=go.Figure(go.Bar(y=t15d['ISO_Code'],x=t15d['Deaths'],orientation='h',marker=dict(color=t15d['Deaths'],colorscale=[[0,"#7a1e1e"],[1,"#ff5c5c"]],cornerradius=4),hovertemplate="%{y}: %{x:,.0f}<extra></extra>"))
            apl(fig,height=420,yaxis=dict(autorange="reversed",gridcolor="#1a2540",linecolor="#263354",zeroline=False),showlegend=False)
            st.plotly_chart(fig,use_container_width=True)
        pan_close()

# ╔═══════════════════════════════════════════════════════╗
# ║              COUNTRY DEEP DIVE (7 SECTIONS)           ║
# ╚═══════════════════════════════════════════════════════╝
elif st.session_state.get("page") != "neo4j":
    iso=st.session_state.sel
    dfc=dff[dff['ISO_Code']==iso].copy()
    if dfc.empty: st.warning(f"Nessun dato per {iso}"); st.stop()
    cont=dfc['Continent'].iloc[-1] if 'Continent' in dfc.columns else 'N/A'

    st.markdown(f'<div class="hdr"><h1> {iso}</h1><p class="sub">Dossier Epidemiologico Nazionale</p><div class="tags"><span class="tag">ISO: {iso}</span><span class="tag">Continent: {cont}</span><span class="tag">{dfc["Date"].min().strftime("%b %Y")} → {dfc["Date"].max().strftime("%b %Y")}</span><span class="tag">{len(dfc):,} obs</span></div></div>',unsafe_allow_html=True)
    if st.button("← Torna alla mappa globale"): st.session_state.sel="Vista globale"; st.rerun()

    lat=dfc.iloc[-1]
    cols=st.columns(5)
    str_val = f"{lat.get('stringency_index', lat.get('containment_health_index', 'N/A')):.1f}" if pd.notna(lat.get('stringency_index', lat.get('containment_health_index'))) else 'N/A'
    vacc_val = lat.get('people_fully_vaccinated_per_hundred', 0)
    rt_val = lat.get('reproduction_rate', 'N/A')
    for col,(c,l,v,s) in zip(cols,[
        ('red',   'Casi totali',  f"{int(lat.get('Confirmed',0)):,}",   'Cumulativi'),
        ('purple','Decessi',      f"{int(lat.get('Deaths',0)):,}",       'Cumulativi'),
        ('amber', 'Stringency',   str_val,                               'Oxford'),
        ('green', 'Vaccinati %',  f"{vacc_val:.1f}%" if pd.notna(vacc_val) else 'N/A', 'Completamente/100'),
        ('cyan',  'Rt',           f"{rt_val:.2f}" if pd.notna(rt_val) else 'N/A', 'Tasso riproduzione')]):
        col.markdown(kpi_html(c,l,v,s),unsafe_allow_html=True)
    st.markdown('<div style="height:.8rem"></div>',unsafe_allow_html=True)

    # ═══════════════════════════════════════════
    # SECTION 1: EPIDEMIC CURVES
    # ═══════════════════════════════════════════
    st.markdown('<div class="sec-title">1 — Curve epidemiche</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        pan_open("","NUOVI CASI")
        st.caption("Nuovi casi giornalieri. Ogni picco corrisponde a un'ondata epidemica.")
        fig=go.Figure()
        fig.add_trace(go.Bar(x=dfc['Date'],y=dfc['New_Cases'],name="Daily",marker_color="rgba(77,141,247,.3)",marker_line_width=0))
        if show_7d and 'New_Cases_7d' in dfc.columns:
            fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc['New_Cases_7d'],name="7d Avg",line=dict(color=C['blue'],width=2.5)))
        apl(fig,height=300,yaxis_type="log" if log_scale else "linear",legend=hleg()); st.plotly_chart(fig,use_container_width=True); pan_close()
    with c2:
        pan_open("","NUOVI DECESSI")
        st.caption("Decessi giornalieri. I picchi seguono quelli dei casi con un ritardo di 2-3 settimane.")
        fig=go.Figure()
        if 'New_Deaths' in dfc.columns:
            fig.add_trace(go.Bar(x=dfc['Date'],y=dfc['New_Deaths'],name="Daily",marker_color="rgba(255,92,92,.3)",marker_line_width=0))
            if 'New_Deaths_7d' in dfc.columns and show_7d:
                fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc['New_Deaths_7d'],name="7d Avg",line=dict(color=C['red'],width=2.5)))
        apl(fig,height=300,yaxis_type="log" if log_scale else "linear",legend=hleg()); st.plotly_chart(fig,use_container_width=True); pan_close()

    # ═══════════════════════════════════════════
    # SECTION 2: REPRODUCTION RATE & TRANSMISSION
    # ═══════════════════════════════════════════
    if 'reproduction_rate' in dfc.columns and dfc['reproduction_rate'].notna().sum()>10:
        st.markdown('<div class="sec-title">2 — Tasso di riproduzione e trasmissione</div>',unsafe_allow_html=True)
        pan_open("","ANDAMENTO TASSO DI RIPRODUZIONE (Rt)")
        st.caption("Rt = numero medio di contagi per infetto. Sopra 1 (linea rossa) l'epidemia cresce, sotto 1 si contrae.")
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc['reproduction_rate'],line=dict(color=C['cyan'],width=2.5),name="Rt"))
        fig.add_hline(y=1,line_dash="dash",line_color="#ff5c5c",line_width=1,annotation_text="Rt = 1 (soglia)",annotation_font_color="#ff5c5c",annotation_font_size=11)
        apl(fig,height=300,yaxis_title="Rt",legend=hleg()); st.plotly_chart(fig,use_container_width=True); pan_close()

        c1,c2=st.columns(2)
        with c1:
            pan_open("","Rt vs INDICE DI STRINGENCY")
            st.caption("Ogni punto = un giorno. Pendenza negativa → restrizioni più severe riducono la trasmissione.")
            si_col = next((c for c in ['stringency_index','containment_health_index','stringency_index_vax'] if c in dfc.columns and dfc[c].notna().sum()>5), None)
            if si_col:
                sdf=dfc[['reproduction_rate',si_col]].dropna()
                if len(sdf)>5:
                    fig=px.scatter(sdf,x=si_col,y='reproduction_rate',trendline="ols",color_discrete_sequence=[C['cyan']],labels={si_col:'Stringency','reproduction_rate':'Rt'})
                    fig.update_traces(marker=dict(size=4,opacity=.5))
                    if len(fig.data)>1: fig.data[1].line.color=C['red']; fig.data[1].line.width=2.5
                    apl(fig,height=300); st.plotly_chart(fig,use_container_width=True)
            pan_close()

    # ═══════════════════════════════════════════
    # SECTION 3: VACCINATION CAMPAIGN
    # ═══════════════════════════════════════════
    vax_cols=[c for c in ['people_fully_vaccinated_per_hundred','people_vaccinated_per_hundred'] if c in dfc.columns and dfc[c].notna().sum()>5]
    if vax_cols:
        st.markdown('<div class="sec-title">3 — Campagna vaccinale</div>',unsafe_allow_html=True)
        pan_open("","AVANZAMENTO VACCINALE")
        st.caption("% della popolazione vaccinata: completamente (verde) e con almeno 1 dose (ciano). Scala 0-100%.")
        fig=go.Figure()
        vc_map={"people_fully_vaccinated_per_hundred":(C['green'],"Completamente vaccinati %"),"people_vaccinated_per_hundred":(C['cyan'],"Almeno 1 dose %")}
        for vc in vax_cols:
            clr,nm=vc_map[vc]
            vdata=dfc[['Date',vc]].dropna(subset=[vc])
            fig.add_trace(go.Scatter(x=vdata['Date'],y=vdata[vc],name=nm,line=dict(color=clr,width=2.5)))
        apl(fig,height=320,legend=hleg(),yaxis_title="Popolazione %",yaxis_range=[0,105])
        st.plotly_chart(fig,use_container_width=True); pan_close()

        if 'new_vaccinations_smoothed' in dfc.columns and dfc['new_vaccinations_smoothed'].notna().sum()>5:
            pan_open("","VELOCITA' VACCINALE GIORNALIERA")
            st.caption("Dosi somministrate al giorno (smoothed). I picchi indicano i periodi di massimo sforzo vaccinale.")
            fig=go.Figure(go.Bar(x=dfc['Date'],y=dfc['new_vaccinations_smoothed'],marker_color="rgba(52,211,153,.4)",marker_line_width=0,name="Giornaliero (smoothed)"))
            apl(fig,height=250,legend=hleg()); st.plotly_chart(fig,use_container_width=True); pan_close()

    # ═══════════════════════════════════════════
    # SECTION 4: HEALTHCARE PRESSURE
    # ═══════════════════════════════════════════
    hosp_cols=[c for c in ['daily_occupancy_icu','daily_occupancy_hosp'] if c in dfc.columns and dfc[c].notna().sum()>5]
    if hosp_cols:
        st.markdown('<div class="sec-title">4 — Pressione sul sistema sanitario</div>',unsafe_allow_html=True)
        pan_open("","OCCUPAZIONE OSPEDALIERA E TERAPIE INTENSIVE")
        st.caption("Occupazione ospedaliera ordinaria (giallo, asse SX) e terapie intensive (rosso, asse DX). I picchi indicano la massima pressione sul sistema sanitario.")
        has_hosp='daily_occupancy_hosp' in dfc.columns and dfc['daily_occupancy_hosp'].notna().sum()>5
        has_icu='daily_occupancy_icu' in dfc.columns and dfc['daily_occupancy_icu'].notna().sum()>5
        if has_hosp and has_icu:
            # Entrambi disponibili → dual y-axis
            fig=make_subplots(specs=[[{"secondary_y":True}]])
            hosp_data=dfc[['Date','daily_occupancy_hosp']].dropna(subset=['daily_occupancy_hosp'])
            icu_data=dfc[['Date','daily_occupancy_icu']].dropna(subset=['daily_occupancy_icu'])
            fig.add_trace(go.Scatter(x=hosp_data['Date'],y=hosp_data['daily_occupancy_hosp'],fill='tozeroy',fillcolor="rgba(251,191,36,.1)",line=dict(color=C['amber'],width=2),name="Ospedale"),secondary_y=False)
            fig.add_trace(go.Scatter(x=icu_data['Date'],y=icu_data['daily_occupancy_icu'],line=dict(color=C['red'],width=2.5),name="TI"),secondary_y=True)
            apl(fig,height=320,legend=hleg())
            fig.update_yaxes(title_text="Ospedale",secondary_y=False,title_font=dict(color=C['amber']))
            fig.update_yaxes(title_text="TI",secondary_y=True,title_font=dict(color=C['red']))
        else:
            # Solo uno dei due → single y-axis
            fig=go.Figure()
            col=hosp_cols[0]
            clean=dfc[['Date',col]].dropna(subset=[col])
            clr=C['amber'] if 'hosp' in col else C['red']
            nm="Ospedale" if 'hosp' in col else "TI"
            fig.add_trace(go.Scatter(x=clean['Date'],y=clean[col],fill='tozeroy',fillcolor=f"rgba({','.join(str(int(clr.lstrip('#')[i:i+2],16)) for i in (0,2,4))},.1)",line=dict(color=clr,width=2.5),name=nm))
            apl(fig,height=320,legend=hleg(),yaxis_title=nm)
        st.plotly_chart(fig,use_container_width=True); pan_close()

    # ═══════════════════════════════════════════
    # SECTION 5: GOVERNMENT RESPONSE
    # ═══════════════════════════════════════════
    policy_detail=[c for c in ['c1m_school_closing','c2m_workplace_closing','c3m_cancel_public_events','c4m_restrictions_on_gatherings','c5m_close_public_transport','c6m_stay_at_home_requirements','c7m_restrictions_on_internal_movement','c8ev_international_travel_controls','h6m_facial_coverings','h7_vaccination_policy'] if c in dfc.columns]
    if policy_detail:
        st.markdown('<div class="sec-title">5 — Risposta governativa</div>',unsafe_allow_html=True)

        # Heatmap
        pan_open("","HEATMAP MISURE DI POLICY (settimanale)")
        st.caption("Righe = misure di policy Oxford, colonne = settimane. Colore più intenso → restrizione più severa (scala 0-5).")
        hw=dfc.set_index('Date')[policy_detail].resample('W').mean().T
        nice_labels = []
        for c in hw.index:
            label = c.replace('_',' ')
            for prefix in ['c1m ','c2m ','c3m ','c4m ','c5m ','c6m ','c7m ','c8ev ','h6m ','h7 ']:
                label = label.replace(prefix, '')
            nice_labels.append(label.title())
        fig=go.Figure(go.Heatmap(z=hw.values,x=hw.columns.strftime('%Y-%m-%d'),y=nice_labels,
            colorscale=[[0,"#0c1220"],[.25,"#1e3a7a"],[.5,"#4d8df7"],[.75,"#ff5c5c"],[1,"#cc0000"]],
            colorbar=dict(title=dict(text="Severity",font=dict(size=11,color="#a0b0cc")),tickfont=dict(color="#a0b0cc"),thickness=10,len=.6),
            hovertemplate="%{x}<br>%{y}: %{z:.1f}<extra></extra>"))
        apl(fig,height=350,margin=dict(l=220,r=20,t=30,b=40)); st.plotly_chart(fig,use_container_width=True); pan_close()

        # Cases vs Stringency dual axis
        pan_open("","CASI vs INDICE DI STRINGENCY")
        st.caption("Casi 7d avg (blu, asse SX) vs indice di severità delle restrizioni Oxford (arancione, asse DX, 0-100). Calcolato come media tra stringency_vax e stringency_nonvax.")
        fig=make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc.get('New_Cases_7d',dfc.get('New_Cases')),fill='tozeroy',fillcolor="rgba(77,141,247,.12)",line=dict(color=C['blue'],width=2),name="Casi (7d)"),secondary_y=False)
        si_col = next((c for c in ['stringency_index','containment_health_index'] if c in dfc.columns), None)
        if si_col:
            fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc[si_col],line=dict(color=C['amber'],width=2.5),name="Stringency"),secondary_y=True)
        apl(fig,height=320,legend=hleg())
        fig.update_yaxes(title_text="Casi",secondary_y=False,title_font=dict(color=C['blue']))
        fig.update_yaxes(title_text="Stringency",secondary_y=True,range=[0,100],title_font=dict(color=C['amber']))
        st.plotly_chart(fig,use_container_width=True); pan_close()

    # ═══════════════════════════════════════════
    # SECTION 6: EXCESS MORTALITY
    # ═══════════════════════════════════════════
    exc_cols=[c for c in ['excess_mortality','estimated_daily_excess_deaths','excess_mortality_cumulative','cumulative_estimated_daily_excess_deaths'] if c in dfc.columns and dfc[c].notna().sum()>3]
    if exc_cols:
        st.markdown('<div class="sec-title">6 — Mortalità in eccesso</div>',unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1:
            if 'estimated_daily_excess_deaths' in dfc.columns and dfc['estimated_daily_excess_deaths'].notna().sum()>5:
                pan_open("","DECESSI IN ECCESSO GIORNALIERI (stima Economist)")
                st.caption("Decessi in eccesso rispetto alla media storica. Sopra zero = più morti del previsto.")
                exc_daily=dfc[['Date','estimated_daily_excess_deaths']].dropna(subset=['estimated_daily_excess_deaths'])
                fig=go.Figure()
                # Colora positivo/negativo diversamente
                fig.add_trace(go.Scatter(x=exc_daily['Date'],y=exc_daily['estimated_daily_excess_deaths'],fill='tozeroy',fillcolor="rgba(192,132,252,.12)",line=dict(color=C['purple'],width=2),name="Eccesso giornaliero"))
                fig.add_hline(y=0,line_dash="dash",line_color="#607090",line_width=1)
                apl(fig,height=280,yaxis_title="Decessi in eccesso/giorno"); st.plotly_chart(fig,use_container_width=True); pan_close()
            elif 'excess_mortality' in dfc.columns and dfc['excess_mortality'].notna().sum()>5:
                pan_open("","MORTALITA' IN ECCESSO %")
                st.caption("Percentuale di mortalità in eccesso rispetto alla media storica.")
                exc_pct=dfc[['Date','excess_mortality']].dropna(subset=['excess_mortality'])
                fig=go.Figure(go.Scatter(x=exc_pct['Date'],y=exc_pct['excess_mortality'],fill='tozeroy',fillcolor="rgba(192,132,252,.12)",line=dict(color=C['purple'],width=2)))
                fig.add_hline(y=0,line_dash="dash",line_color="#607090",line_width=1)
                apl(fig,height=280,yaxis_title="Eccesso %"); st.plotly_chart(fig,use_container_width=True); pan_close()
        with c2:
            # Calcola cumulativa da daily se disponibile, altrimenti usa colonna raw
            cum_col=next((c for c in ['cumulative_estimated_daily_excess_deaths','excess_mortality_cumulative'] if c in dfc.columns and dfc[c].notna().sum()>3),None)
            daily_col='estimated_daily_excess_deaths' if 'estimated_daily_excess_deaths' in dfc.columns else None
            if daily_col and dfc[daily_col].notna().sum()>5:
                pan_open("","DECESSI IN ECCESSO CUMULATIVI")
                st.caption("Somma progressiva dei decessi in eccesso. Pendenza più ripida = periodo di maggiore impatto.")
                exc_cum=dfc[['Date',daily_col]].dropna(subset=[daily_col]).copy()
                # Ricalcola cumulativa come somma progressiva dei daily
                exc_cum['cum_computed']=exc_cum[daily_col].cumsum()
                fig=go.Figure(go.Scatter(x=exc_cum['Date'],y=exc_cum['cum_computed'],line=dict(color=C['pink'],width=2.5),name="Cumulativo",fill='tozeroy',fillcolor="rgba(244,114,182,.06)"))
                apl(fig,height=280,yaxis_title="Decessi in eccesso cumulativi"); st.plotly_chart(fig,use_container_width=True); pan_close()
            elif cum_col:
                pan_open("","DECESSI IN ECCESSO CUMULATIVI")
                st.caption("Somma progressiva dei decessi in eccesso. Pendenza più ripida = periodo di maggiore impatto.")
                exc_c=dfc[['Date',cum_col]].dropna(subset=[cum_col])
                fig=go.Figure(go.Scatter(x=exc_c['Date'],y=exc_c[cum_col],line=dict(color=C['pink'],width=2.5),name="Cumulativo"))
                apl(fig,height=280,yaxis_title="Decessi in eccesso cumulativi"); st.plotly_chart(fig,use_container_width=True); pan_close()

    # ═══════════════════════════════════════════
    # SECTION 7: CROSS-DOMAIN EDA
    # ═══════════════════════════════════════════
    st.markdown('<div class="sec-title">7 — Analisi esplorativa cross-domain</div>',unsafe_allow_html=True)

    
    CATS = {
       "Epidemiologia": [c for c in ['Confirmed','Deaths','New_Cases','New_Deaths','New_Cases_7d','New_Deaths_7d','new_cases_per_million','new_deaths_per_million','total_cases_per_million','total_deaths_per_million','cfr','reproduction_rate','positive_rate','tests_per_case','new_cases_7_day_avg_right','new_deaths_7_day_avg_right'] if c in dfc.columns],
       "Vaccinazione": [c for c in ['people_fully_vaccinated_per_hundred','total_vaccinations_per_hundred','people_vaccinated_per_hundred','total_vaccinations','people_fully_vaccinated','people_vaccinated','total_boosters','new_vaccinations_smoothed','people_unvaccinated','willingness_covid_vaccinate_this_week_pct_pop','unwillingness_covid_vaccinate_this_week_pct_pop','uncertain_covid_vaccinate_this_week_pct_pop'] if c in dfc.columns],
       "Policy (Oxford)": [c for c in ['stringency_index','containment_health_index','stringency_index_vax','stringency_index_nonvax','v2a_vaccine_availability__summary']+policy_detail if c in dfc.columns],
       "Sanita": [c for c in ['daily_occupancy_icu','daily_occupancy_hosp','hospital_beds_per_thousand'] if c in dfc.columns],
       "Mortalita in eccesso": [c for c in exc_cols if c in dfc.columns],
       "Dati demografici": [c for c in ['population','population_density','median_age','gdp_per_capita','life_expectancy','hospital_beds_per_thousand'] if c in dfc.columns],
       "Tamponi e test": [c for c in ['positive_rate','new_tests_7day_smoothed','tests_per_case'] if c in dfc.columns],
       "Infodemica": [c for c in ['disinfo_index','antivax_index','denialism_index','conspiracy_index','altmed_index','proscience_index','provax_action_index','provax_trust_index','info_seeking_index','trust_ratio','sentiment_balance'] if c in dfc.columns],
       "Fact-check": [c for c in ['factcheck_count','factcheck_cumulative'] + [cc for cc in dfc.columns if cc.startswith('fc_')] if c in dfc.columns],
    }
    
    CATS = {k:v for k,v in CATS.items() if len(v)>=2}

    
    pan_open("","MATRICE DI CORRELAZIONE PER CATEGORIA")
    st.caption("Matrice di Pearson tra le variabili del dominio selezionato. Blu = correlazione positiva, rosso = negativa.")
    cat_choice=st.selectbox("Seleziona categoria",list(CATS.keys()),key="cat_corr")
    cat_vars=CATS[cat_choice]
    corr_data=dfc[cat_vars].dropna(how='all')
    if len(corr_data)>5 and len(cat_vars)>=2:
        corr=corr_data.corr()
        labels=[c.replace('_',' ').title()[:25] for c in corr.columns]
        fig=go.Figure(go.Heatmap(z=corr.values,x=labels,y=labels,
            colorscale=[[0,"#ff5c5c"],[.5,"#0c1220"],[1,"#4d8df7"]],zmid=0,zmin=-1,zmax=1,
            text=np.round(corr.values,2),texttemplate="%{text}",textfont=dict(size=9,color="#a0b0cc"),
            hovertemplate="%{x} vs %{y}<br>r = %{z:.3f}<extra></extra>"))
        h=max(400,len(cat_vars)*35)
        apl(fig,height=h,margin=dict(l=180,r=20,t=30,b=100))
        st.plotly_chart(fig,use_container_width=True)
    pan_close()

   # Estrazione delle feature numeriche valide per l'EDA cross-domain successiva
    all_num = [c for c in dfc.select_dtypes(include=[np.number]).columns if dfc[c].std() > 0 and dfc[c].notna().sum() > 20 and c not in ['Year'] and 'annotation' not in c.lower()]

    # Scatter explorer
    pan_open("","ESPLORA RELAZIONI TRA VARIABILI")
    st.caption("Scatter plot interattivo: scegli due variabili. Linea rossa = regressione OLS.")
    st.markdown("Seleziona due variabili per esplorarne la relazione.")
    all_nice={c:c.replace('_',' ').title() for c in all_num}
    disp=[all_nice[c] for c in all_num]
    rev={v:k for k,v in all_nice.items()}
    dx='stringency_index' if 'stringency_index' in all_num else ('containment_health_index' if 'containment_health_index' in all_num else all_num[0])
    dy='New_Cases_7d' if 'New_Cases_7d' in all_num else ('new_cases_7_day_avg_right' if 'new_cases_7_day_avg_right' in all_num else all_num[min(1,len(all_num)-1)])
    cx,cy=st.columns(2)
    with cx: sx=st.selectbox("Asse X",disp,index=disp.index(all_nice[dx]) if all_nice[dx] in disp else 0,key="sx")
    with cy: sy=st.selectbox("Asse Y",disp,index=disp.index(all_nice[dy]) if all_nice[dy] in disp else 0,key="sy")
    vx,vy=rev[sx],rev[sy]
    sdf=dfc[[vx,vy,'Date']].dropna()
    if len(sdf)>5:
        fig=px.scatter(sdf,x=vx,y=vy,trendline="ols",color_discrete_sequence=[C['blue']],labels={vx:sx,vy:sy},hover_data={'Date':'|%d %b %Y'})
        fig.update_traces(marker=dict(size=5,opacity=.5))
        if len(fig.data)>1: fig.data[1].line.color=C['red']; fig.data[1].line.width=2.5
        apl(fig,height=380); st.plotly_chart(fig,use_container_width=True)
        r=sdf[vx].corr(sdf[vy])
        strength="forte" if abs(r)>.7 else "moderata" if abs(r)>.4 else "debole"
        direction="positiva" if r>0 else "negativa"
        st.markdown(f'<div style="background:#131c30;border:1px solid #263354;border-radius:8px;padding:1rem;margin-top:.5rem"><span style="font-family:JetBrains Mono,monospace;font-size:1.1rem;font-weight:700;color:{"#4d8df7" if r>0 else "#ff5c5c"}">r = {r:.4f}</span><span style="color:#a0b0cc;font-size:.85rem;margin-left:1rem">{strength.capitalize()} {direction} correlation</span></div>',unsafe_allow_html=True)
    pan_close()

    
    pan_open("","ANALISI DELLA DISTRIBUZIONE")
    st.caption("Istogramma e boxplot per analizzare la distribuzione della variabile selezionata.")
    dv_n=st.selectbox("Variabile",disp,index=disp.index(all_nice[dy]) if all_nice[dy] in disp else 0,key="dv")
    dv=rev[dv_n]
    ch,cb=st.columns(2)
    with ch:
        fig=go.Figure(go.Histogram(x=dfc[dv].dropna(),nbinsx=50,marker_color="rgba(77,141,247,.6)",marker_line=dict(color="#4d8df7",width=1)))
        apl(fig,height=280,xaxis_title=dv_n,yaxis_title="Frequenza"); st.plotly_chart(fig,use_container_width=True)
    with cb:
        fig=go.Figure(go.Box(y=dfc[dv].dropna(),name=dv_n,marker_color="#4d8df7",line_color="#78aeff",fillcolor="rgba(77,141,247,.2)"))
        apl(fig,height=280,showlegend=False); st.plotly_chart(fig,use_container_width=True)
    ds=dfc[dv].describe()
    st.markdown(f'<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:.5rem"><div class="kpi blue" style="padding:.8rem"><div class="lab">Mean</div><div class="val" style="font-size:1rem">{ds["mean"]:,.2f}</div></div><div class="kpi green" style="padding:.8rem"><div class="lab">Median</div><div class="val" style="font-size:1rem">{ds["50%"]:,.2f}</div></div><div class="kpi amber" style="padding:.8rem"><div class="lab">Std</div><div class="val" style="font-size:1rem">{ds["std"]:,.2f}</div></div><div class="kpi red" style="padding:.8rem"><div class="lab">Min</div><div class="val" style="font-size:1rem">{ds["min"]:,.2f}</div></div><div class="kpi purple" style="padding:.8rem"><div class="lab">Max</div><div class="val" style="font-size:1rem">{ds["max"]:,.2f}</div></div><div class="kpi cyan" style="padding:.8rem"><div class="lab">Count</div><div class="val" style="font-size:1rem">{int(ds["count"]):,}</div></div></div>',unsafe_allow_html=True)
    pan_close()

    # ═══════════════════════════════════════════
    # SECTION 8: INFODEMIC MONITOR (Google Trends)
    # ═══════════════════════════════════════════
    has_disinfo = 'disinfo_index' in dfc.columns and dfc['disinfo_index'].notna().sum() > 3
    has_proscience = 'proscience_index' in dfc.columns and dfc['proscience_index'].notna().sum() > 3

    if has_disinfo or has_proscience:
        st.markdown('<div class="sec-title">8 — Monitor infodemica</div>', unsafe_allow_html=True)

        
        kpi_c = st.columns(5)
        if has_disinfo:
            kpi_c[0].markdown(kpi_html('red','Indice Disinfo',f"{dfc['disinfo_index'].mean():.1f}",'Media ricerche anti-scienza'),unsafe_allow_html=True)
        if has_proscience:
            kpi_c[1].markdown(kpi_html('green','Indice Pro-Scienza',f"{dfc['proscience_index'].mean():.1f}",'Media ricerche pro-scienza'),unsafe_allow_html=True)
        if 'trust_ratio' in dfc.columns and dfc['trust_ratio'].notna().sum()>0:
            tr=dfc['trust_ratio'].mean()
            kpi_c[2].markdown(kpi_html('green' if tr>1 else 'red','Trust Ratio',f"{tr:.2f}",'>1 = la scienza prevale'),unsafe_allow_html=True)
        if 'sentiment_balance' in dfc.columns and dfc['sentiment_balance'].notna().sum()>0:
            sb=dfc['sentiment_balance'].mean()
            kpi_c[3].markdown(kpi_html('green' if sb>0 else 'red','Sentiment',f"{sb:+.1f}",'Pro meno Anti'),unsafe_allow_html=True)
        if 'disinfo_terms_active' in dfc.columns:
            kpi_c[4].markdown(kpi_html('purple','Termini Attivi',f"{dfc['disinfo_terms_active'].mean():.1f}",'Termini disinfo attivi'),unsafe_allow_html=True)
        st.markdown('<div style="height:.5rem"></div>',unsafe_allow_html=True)

        # TRUST RATIO TIMELINE
        if 'trust_ratio_smooth' in dfc.columns and dfc['trust_ratio_smooth'].notna().sum()>3:
            pan_open("","TRUST RATIO — Pro-scienza vs Disinformazione nel tempo")
            st.caption("Trust Ratio = ricerche pro-scienza / ricerche disinformazione. Sopra 1 = la scienza prevale.")
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc['trust_ratio_smooth'],fill='tozeroy',fillcolor="rgba(52,211,153,.08)",line=dict(color=C['green'],width=2.5),name="Trust Ratio (4w smooth)"))
            fig.add_hline(y=1,line_dash="dash",line_color="#ff5c5c",line_width=1.5,annotation_text="Soglia = 1",annotation_font_color="#ff5c5c",annotation_font_size=11)
            apl(fig,height=300,yaxis_title="Trust Ratio",legend=hleg())
            st.plotly_chart(fig,use_container_width=True)
            pan_close()

        # DISINFO vs PROSCIENCE overlay
        if has_disinfo and has_proscience:
            pan_open("","VOLUME RICERCHE: DISINFORMAZIONE vs PRO-SCIENZA")
            st.caption("Confronto diretto con eventi chiave. Linee verticali = eventi che hanno influenzato il dibattito pubblico.")
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc['disinfo_index'],fill='tozeroy',fillcolor="rgba(255,92,92,.15)",line=dict(color=C['red'],width=2),name="Disinfo"))
            fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc['proscience_index'],fill='tozeroy',fillcolor="rgba(52,211,153,.15)",line=dict(color=C['green'],width=2),name="ProScience"))
            # Key events 
            EVT=[("2020-03-11","OMS dichiara la pandemia",C['blue']),("2020-12-08","Primo vaccino (UK)",C['green']),("2021-01-27","Disputa AstraZeneca - UE",C['amber']),("2021-03-15","AstraZeneca sospeso in UE",C['red']),("2021-05-01","Crisi India / variante Delta",C['purple'])]
            for ds,lb,cl in EVT:
                fig.add_vline(x=ds,line_dash="dot",line_color=cl,line_width=1,opacity=.7)
                fig.add_annotation(x=ds,y=1.05,yref="paper",text=lb,showarrow=False,font=dict(size=9,color=cl),textangle=-35)
            apl(fig,height=380,legend=hleg(),yaxis_title="Interesse di ricerca (0-100)",margin=dict(l=50,r=20,t=80,b=40))
            st.plotly_chart(fig,use_container_width=True); pan_close()

        # DISINFO BREAKDOWN
        if has_disinfo:
            pan_open("","DISINFORMAZIONE SUDDIVISA PER NARRATIVA")
            st.caption("Scomposizione per tipo di narrativa: anti-vaccino, negazionismo, cospirazioni (5G, Gates), cure alternative (ivermectina).")
            fig=go.Figure()
            for col,(nm,clr) in [('antivax_index',('Anti-vaccino',C['red'])),('denialism_index',('Negazionismo',C['amber'])),('conspiracy_index',('Cospirazioni',C['purple'])),('altmed_index',('Medicina alternativa',C['cyan']))]:
                if col in dfc.columns and dfc[col].notna().sum()>3:
                    fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc[col],name=nm,line=dict(color=clr,width=2),stackgroup='one'))
            apl(fig,height=300,legend=hleg(),yaxis_title="Interesse cumulato"); st.plotly_chart(fig,use_container_width=True); pan_close()

        # PROSCIENCE BREAKDOWN
        if has_proscience:
            pan_open("","PRO-SCIENZA: Azione vs Fiducia vs Ricerca informazioni")
            st.caption("Azione = prenotare vaccino, dove vaccinarsi. Fiducia = vaccino funziona, efficacia. Info = effetti collaterali, sintomi.")
            fig=go.Figure()
            for col,(nm,clr) in [('provax_action_index',('Prenotazione vaccino',C['green'])),('provax_trust_index',('Fiducia / efficacia',C['blue'])),('info_seeking_index',('Ricerca informazioni',C['amber']))]:
                if col in dfc.columns and dfc[col].notna().sum()>3:
                    fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc[col],name=nm,line=dict(color=clr,width=2),stackgroup='one'))
            apl(fig,height=300,legend=hleg(),yaxis_title="Interesse cumulato"); st.plotly_chart(fig,use_container_width=True); pan_close()

        # DISINFO vs VACCINATION
        if has_disinfo and 'people_fully_vaccinated_per_hundred' in dfc.columns:
            pan_open("","DISINFORMAZIONE vs AVANZAMENTO VACCINALE")
            st.caption("Asse SX: intensità ricerche disinformazione. Asse DX: % popolazione vaccinata. La disinformazione frena le vaccinazioni?")
            fig=make_subplots(specs=[[{"secondary_y":True}]])
            fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc['disinfo_index'],fill='tozeroy',fillcolor="rgba(255,92,92,.1)",line=dict(color=C['red'],width=2),name="Disinfo"),secondary_y=False)
            fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc['people_fully_vaccinated_per_hundred'],line=dict(color=C['green'],width=2.5),name="Vaccinated %"),secondary_y=True)
            apl(fig,height=320,legend=hleg())
            fig.update_yaxes(title_text="Disinfo",secondary_y=False,title_font=dict(color=C['red']))
            fig.update_yaxes(title_text="Vaccinati %",secondary_y=True,title_font=dict(color=C['green']))
            st.plotly_chart(fig,use_container_width=True); pan_close()

        # CORRELATION SCATTER GRID
        sp=[]
        if has_disinfo and 'unwillingness_covid_vaccinate_this_week_pct_pop' in dfc.columns:
            sp.append(('disinfo_index','unwillingness_covid_vaccinate_this_week_pct_pop','Disinfo Index','Unwillingness %',C['red'],'Piu disinfo → piu esitazione?'))
        if has_disinfo and 'daily_vaccinations_smoothed' in dfc.columns:
            sp.append(('disinfo_index','daily_vaccinations_smoothed','Disinfo','Daily Vaccinations',C['purple'],'Piu disinfo → meno vaccini?'))
        if has_proscience and 'daily_vaccinations_smoothed' in dfc.columns:
            sp.append(('provax_action_index','daily_vaccinations_smoothed','Pro-vax Action','Daily Vacc.',C['green'],'Ricerche prenotazione → vaccinazioni?'))
        if 'trust_ratio' in dfc.columns and 'people_fully_vaccinated_per_hundred' in dfc.columns:
            sp.append(('trust_ratio','people_fully_vaccinated_per_hundred','Trust Ratio','Vaccinated %',C['cyan'],'Piu fiducia → piu vaccinazioni?'))
        if sp:
            pan_open("","ESPLORATORE CORRELAZIONI — Infodemica vs Esiti")
            for i in range(0,len(sp),2):
                cs=st.columns(2)
                for j,col in enumerate(cs):
                    ix=i+j
                    if ix>=len(sp): break
                    xv,yv,xl,yl,clr,q=sp[ix]
                    with col:
                        st.markdown(f'<div style="font-size:.8rem;color:#607090;margin-bottom:.3rem">{q}</div>',unsafe_allow_html=True)
                        sd=dfc[[xv,yv]].dropna()
                        if len(sd)>5:
                            fig=px.scatter(sd,x=xv,y=yv,trendline="ols",color_discrete_sequence=[clr],labels={xv:xl,yv:yl})
                            fig.update_traces(marker=dict(size=4,opacity=.5))
                            if len(fig.data)>1: fig.data[1].line.color=C['amber']; fig.data[1].line.width=2.5
                            apl(fig,height=270); st.plotly_chart(fig,use_container_width=True)
                            r=sd[xv].corr(sd[yv])
                            st.markdown(f'<div style="background:#131c30;border:1px solid #263354;border-radius:6px;padding:.5rem;font-size:.78rem"><span style="font-family:JetBrains Mono,monospace;font-weight:700;color:{"#4d8df7" if r>0 else "#ff5c5c"}">r = {r:.4f}</span> <span style="color:#607090">{"positiva" if r>0 else "negativa"}</span></div>',unsafe_allow_html=True)
            pan_close()

        # DISINFO vs CASES
        if has_disinfo:
            pan_open("","LE FAKE NEWS AUMENTANO CON I CASI?")
            st.caption("Le ricerche di disinformazione aumentano quando i casi salgono? O sono indipendenti?")
            fig=make_subplots(specs=[[{"secondary_y":True}]])
            fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc['disinfo_index'],line=dict(color=C['red'],width=2),name="Disinfo"),secondary_y=False)
            cc='New_Cases_7d' if 'New_Cases_7d' in dfc.columns else 'new_cases_7_day_avg_right'
            if cc in dfc.columns:
                fig.add_trace(go.Scatter(x=dfc['Date'],y=dfc[cc],line=dict(color=C['blue'],width=2),name="Casi media 7gg"),secondary_y=True)
            apl(fig,height=300,legend=hleg())
            fig.update_yaxes(title_text="Disinfo",secondary_y=False,title_font=dict(color=C['red']))
            fig.update_yaxes(title_text="Casi",secondary_y=True,title_font=dict(color=C['blue']))
            st.plotly_chart(fig,use_container_width=True); pan_close()

    # ═══════════════════════════════════════════
    # SECTION 9: FACT-CHECK (FakeCovid verified claims)
    # ═══════════════════════════════════════════
    has_fc = 'factcheck_count' in dfc.columns and dfc['factcheck_count'].notna().sum() > 0
    if has_fc:
        st.markdown('<div class="sec-title">9 -- Verified fact-checks (FakeCovid dataset)</div>', unsafe_allow_html=True)
        st.markdown('<div style="background:#131c30;border:1px solid #263354;border-radius:8px;padding:.8rem;font-size:.82rem;color:#a0b0cc;margin-bottom:1rem">FakeCovid dataset: 7,623 notizie fact-checked da 92 siti di fact-checking (Shahi & Nandini, 2020). Copertura temporale: <strong>gennaio - luglio 2020</strong>. I grafici seguenti mostrano i fact-check nel contesto dell\'intera timeline del dataset per evidenziare la concentrazione nei primi mesi della pandemia.</div>', unsafe_allow_html=True)

        # KPIs
        fc_total = int(dfc['factcheck_count'].sum())
        fc_cum = int(dfc['factcheck_cumulative'].max()) if 'factcheck_cumulative' in dfc.columns and dfc['factcheck_cumulative'].notna().any() else fc_total
        fc_data = dfc[dfc['factcheck_count'].notna() & (dfc['factcheck_count'] > 0)]
        fc_start = fc_data['Date'].min().strftime('%b %Y') if not fc_data.empty else 'N/A'
        fc_end = fc_data['Date'].max().strftime('%b %Y') if not fc_data.empty else 'N/A'

        fc_cat_cols = [c for c in dfc.columns if c.startswith('fc_') and dfc[c].notna().sum() > 0 and dfc[c].sum() > 0 and c.replace('fc_','').replace('_',' ').title() not in ('Nan', 'None', '')]
        if fc_cat_cols:
            top_cat = max(fc_cat_cols, key=lambda c: dfc[c].sum())
            top_cat_name = top_cat.replace('fc_', '').replace('_', ' ').title()
            k1, k2, k3 = st.columns(3)
            k1.markdown(kpi_html('amber', 'Totale Fact-check', f"{fc_cum:,}", f'Fake news verificate per {iso}'), unsafe_allow_html=True)
            k2.markdown(kpi_html('blue', 'Periodo di copertura', f"{fc_start} - {fc_end}", 'Periodo dataset FakeCovid'), unsafe_allow_html=True)
            k3.markdown(kpi_html('red', 'Categoria principale', top_cat_name, f'{int(dfc[top_cat].sum())} segnalazioni'), unsafe_allow_html=True)
        else:
            k1, k2 = st.columns(2)
            k1.markdown(kpi_html('amber', 'Totale Fact-check', f"{fc_cum:,}", f'Fake news verificate per {iso}'), unsafe_allow_html=True)
            k2.markdown(kpi_html('blue', 'Periodo di copertura', f"{fc_start} - {fc_end}", 'Periodo dataset FakeCovid'), unsafe_allow_html=True)
        st.markdown('<div style="height:.5rem"></div>', unsafe_allow_html=True)

        

        # Fact-checks vs Google Trends 
        has_disinfo_here = 'disinfo_index' in dfc.columns and dfc['disinfo_index'].notna().sum() > 3
        if has_disinfo_here:
            pan_open("","TRIANGOLAZIONE: Fact-check vs Google Trends (gen-lug 2020)")
            st.caption("Confronto limitato al periodo di copertura FakeCovid (gen-lug 2020). Se le due fonti si muovono insieme, la triangolazione conferma la robustezza dei dati.")
            
            fc_period = dfc[(dfc['Date'] >= '2020-01-01') & (dfc['Date'] <= '2020-07-31')].copy()
            if len(fc_period) > 5:
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x=fc_period['Date'], y=fc_period['factcheck_count'], name="Fact-check (verificati)",
                    marker_color="rgba(251,191,36,.5)", marker_line_width=0), secondary_y=False)
                fig.add_trace(go.Scatter(x=fc_period['Date'], y=fc_period['disinfo_index'], name="Indice Disinfo (Google Trends)",
                    line=dict(color=C['red'], width=2.5)), secondary_y=True)
                apl(fig, height=300, legend=hleg())
                fig.update_yaxes(title_text="Fact-check/settimana", secondary_y=False, title_font=dict(color=C['amber']))
                fig.update_yaxes(title_text="Indice Disinfo", secondary_y=True, title_font=dict(color=C['red']))
                st.plotly_chart(fig, use_container_width=True)
               
                corr_data = fc_period[['factcheck_count','disinfo_index']].dropna()
                if len(corr_data) > 5:
                    r = corr_data['factcheck_count'].corr(corr_data['disinfo_index'])
                    st.markdown(f'<div style="background:#131c30;border:1px solid #263354;border-radius:8px;padding:.8rem;font-size:.82rem"><span style="font-family:JetBrains Mono,monospace;font-weight:700;color:{"#4d8df7" if r>0 else "#ff5c5c"}">r = {r:.4f}</span> <span style="color:#a0b0cc">Correlazione tra fact-check verificati e interesse di ricerca nel periodo gen-lug 2020</span></div>', unsafe_allow_html=True)
            pan_close()

    # ═══════════════════════════════════════════
    # KAFKA + ML (preserved)
    # ═══════════════════════════════════════════
    st.markdown('<div class="sec-title">Real-Time + ML</div>',unsafe_allow_html=True)
    pan_open("","MONITORAGGIO LIVE + PREVISIONE ML","live")
    st.caption("Grigio = storico (batch). Rosso = dati live (Kafka). Blu tratteggiato = fit ML. Verde punteggiato = previsione +60gg.")

    def build_ml_features(d, feature_cols, target='New_Cases_7d', lags=[7,14,21]):
        d = d.copy()
        for c in feature_cols:
            if c in d.columns:
                d[c] = d[c].rolling(7, min_periods=1).mean()
        if target in d.columns:
            for lag in lags:
                d[f'lag_{lag}'] = d[target].shift(lag)
        all_feats = feature_cols + [f'lag_{l}' for l in lags if f'lag_{l}' in d.columns]
        all_feats = [f for f in all_feats if f in d.columns]
        return d, all_feats

    # ── Data di inizio simulazione live (allineata al producer) ─────────────
    SIM_START = pd.Timestamp("2021-02-01")
    sim_start = SIM_START

    try:
        db_ml = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)["covid_database"]
        live_docs = list(db_ml["realtime_data"].find({"ISO_Code":iso},{'_id':0}).sort("received_at",1))
    except: 
        live_docs = []

    if len(live_docs) > 1:
        dlv_all = pd.DataFrame(live_docs)
        if 'Date' in dlv_all.columns:
            dlv_all['Date'] = pd.to_datetime(dlv_all['Date'], format='mixed', errors='coerce')
            dlv_all = dlv_all.dropna(subset=['Date']).drop_duplicates('Date').copy()
            dlv_all = dlv_all[dlv_all['Date'] >= SIM_START].copy()

        # ── Progressione simulazione basata su received_at ────────────────────
        n_total = len(dlv_all)
        if 'received_at' in dlv_all.columns:
            dlv_all['received_at'] = pd.to_datetime(dlv_all['received_at'], format='mixed', errors='coerce', utc=True).dt.tz_localize(None)
            dlv_all = dlv_all.sort_values('received_at').reset_index(drop=True)
            dlv_all['batch'] = dlv_all['received_at'].dt.floor('s')
            batches = dlv_all['batch'].unique()
            n_batches = len(batches)
            
            sim_key = f'sim_batch_{iso}'
            if sim_key not in st.session_state:
                st.session_state[sim_key] = 1
                
            cur_batch = min(st.session_state[sim_key], n_batches)
            st.session_state[sim_key] = min(cur_batch + 1, n_batches)
            
            visible_batches = batches[:cur_batch]
            dlv = dlv_all[dlv_all['batch'].isin(visible_batches)].sort_values('Date').reset_index(drop=True)
            n_days_received = len(dlv)
            last_live_date = dlv['Date'].max() if not dlv.empty else None
        else:
            dlv = dlv_all.sort_values('Date').reset_index(drop=True)
            n_days_received = n_total
            last_live_date = dlv['Date'].max()

        # ── Dati storici come contesto ────────────────────────────────────────
        sim_start_date = sim_start
        hist = dfc[dfc['Date'] < sim_start][['Date','New_Cases_7d']].copy()
        hist_train = dfc[dfc['Date'] < sim_start].copy()

        # ── Calcola New_Cases per i dati live ─────────────────────────────────
        if 'Confirmed' in dlv.columns and not dlv.empty:
            hist_confirmed = dfc[dfc['Date'] < sim_start][['Date','Confirmed','New_Cases_7d']].dropna(subset=['Confirmed'])
            if not hist_confirmed.empty:
                last_hist_confirmed = hist_confirmed['Confirmed'].iloc[-1]
                last_hist_7d = hist_confirmed['New_Cases_7d'].iloc[-1]
            else:
                last_hist_confirmed = dlv['Confirmed'].iloc[0]
                last_hist_7d = 0

            diffs = dlv['Confirmed'].diff()
            pct_pos = (diffs > 0).sum() / max(len(diffs)-1, 1)

            if pct_pos > 0.7:
                confirmed_series = pd.concat([pd.Series([last_hist_confirmed]), dlv['Confirmed'].reset_index(drop=True)], ignore_index=True)
                daily = confirmed_series.diff().iloc[1:].clip(lower=0).reset_index(drop=True)
                warmup = hist_confirmed['New_Cases_7d'].iloc[-6:].reset_index(drop=True)
                combined_for_roll = pd.concat([warmup, daily], ignore_index=True)
                rolled = combined_for_roll.rolling(7, min_periods=1).mean()
                dlv['Live_Target'] = rolled.iloc[len(warmup):].reset_index(drop=True)
            else:
                dlv['Live_Target'] = dlv['Confirmed'].clip(lower=0).reset_index(drop=True)
                if len(dlv) > 0:
                    dlv.loc[dlv.index[0], 'Live_Target'] = last_hist_7d
        else:
            last_hist_7d = hist['New_Cases_7d'].iloc[-1] if not hist.empty else 0
            dlv['Live_Target'] = last_hist_7d

        # ── Barra progresso simulazione ───────────────────────────────────────
        pct = n_days_received / max(n_total, 1)
        last_date_str = dlv['Date'].max().strftime('%d %b %Y') if not dlv.empty else '—'
        sim_pct_str = f"{pct*100:.0f}%"
        st.markdown(f'''<div style="background:#0c1220;border:1px solid #263354;border-radius:8px;padding:.8rem 1rem;margin-bottom:.8rem;display:flex;align-items:center;gap:1rem">
            <div style="flex:1"><div style="height:6px;background:#1a2540;border-radius:3px;overflow:hidden">
            <div style="height:100%;width:{pct*100:.1f}%;background:linear-gradient(90deg,#34d399,#4d8df7);border-radius:3px"></div></div></div>
            <span style="font-family:JetBrains Mono,monospace;font-size:.75rem;color:#34d399;white-space:nowrap">
             {n_days_received}/{n_total} giorni live · ultimo: {last_date_str} · {sim_pct_str}</span>
        </div>''', unsafe_allow_html=True)

        # ── ML: addestra su storico + live combinati, predice nel futuro ────────
        FORECAST_DAYS = 60
        base_feats = [f for f in ['containment_health_index', 'stringency_index', 'c1m_school_closing', 'c2m_workplace_closing', 'c6m_stay_at_home_requirements', 'h6m_facial_coverings', 'people_fully_vaccinated_per_hundred', 'reproduction_rate', 'positive_rate'] if f in dfc.columns]

        score = None
        all_feats = []
        forecast_df = pd.DataFrame()

        if base_feats and not dlv.empty:
            live_for_train = dlv[['Date'] + [c for c in base_feats if c in dlv.columns] + ['Live_Target']].copy()
            live_for_train = live_for_train.rename(columns={'Live_Target': 'New_Cases_7d'})
            for f in base_feats:
                if f not in live_for_train.columns and f in dfc.columns:
                    live_for_train = live_for_train.merge(dfc[['Date', f]].drop_duplicates('Date'), on='Date', how='left')
            
            combined = pd.concat([dfc, live_for_train], ignore_index=True).drop_duplicates('Date').sort_values('Date').reset_index(drop=True)

            combined_feat, all_feats = build_ml_features(combined, base_feats, target='New_Cases_7d')
            train_data = combined_feat.dropna(subset=all_feats + ['New_Cases_7d'])

            if len(train_data) > 30:
                X_all = train_data[all_feats]
                y_all = train_data['New_Cases_7d']
                
                mdl = RandomForestRegressor(n_estimators=200, max_depth=8, min_samples_leaf=5, random_state=42)
                mdl.fit(X_all, y_all)
                
                score = mdl.score(X_all, y_all)

                pred_feats = [f for f in all_feats if f in combined_feat.columns]
                combined_feat['_ml_pred'] = mdl.predict(combined_feat[pred_feats].fillna(0))
                combined_feat['_ml_pred_smooth'] = combined_feat['_ml_pred'].rolling(7, min_periods=1).mean()
                
                live_dates = set(dlv['Date'].values)
                ml_live = combined_feat[combined_feat['Date'].isin(live_dates)][['Date', '_ml_pred_smooth']].copy()
                dlv = dlv.merge(ml_live, on='Date', how='left')
                dlv['ML_Pred'] = dlv['_ml_pred_smooth']
                dlv.drop(columns=['_ml_pred_smooth'], inplace=True, errors='ignore')
                combined_feat.drop(columns=['_ml_pred', '_ml_pred_smooth'], inplace=True, errors='ignore')

                # ══════════════════════════════════════════════════════════
                # 4. Forecast futuro (+60gg) con Exponential Smoothing
                # ══════════════════════════════════════════════════════════
                last_date = dlv['Date'].max()
                future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=FORECAST_DAYS, freq='D')

                last_known = combined_feat.iloc[-1:].copy()
                future_rows = []
                rolling_pred = list(dlv['Live_Target'].values[-21:])
                
                # Fattore di smorzamento (Inerzia: 85% storia recente, 15% nuova predizione)
                alpha_inertia = 0.85 

                for i, fd in enumerate(future_dates):
                    row = last_known.copy()
                    row['Date'] = fd
                    
                    for lag, lag_col in [(7,'lag_7'), (14,'lag_14'), (21,'lag_21')]:
                        if lag_col in all_feats:
                            row[lag_col] = rolling_pred[-lag] if len(rolling_pred) >= lag else 0
                    
                    feat_vals = row[pred_feats].fillna(0)
                    
                    raw_rf_pred = float(mdl.predict(feat_vals)[0])
                    prev_val = rolling_pred[-1]
                    smoothed_pred = (alpha_inertia * prev_val) + ((1 - alpha_inertia) * raw_rf_pred)
                    final_pred = max(smoothed_pred, 0)
                    
                    rolling_pred.append(final_pred)
                    row['ML_Future'] = final_pred
                    future_rows.append(row)

                if future_rows:
                    forecast_df = pd.concat(future_rows, ignore_index=True)
                    forecast_df['ML_Future'] = forecast_df['ML_Future'].rolling(7, min_periods=1).mean()

        # ── Grafico ───────────────────────────────────────────────────────────
        fig = go.Figure()
        
        if not hist.empty:
            hist_ext = hist.copy()
            if not dlv.empty:
                bridge = pd.DataFrame({'Date':[dlv['Date'].iloc[0]], 'New_Cases_7d':[dlv['Live_Target'].iloc[0]]})
                hist_ext = pd.concat([hist_ext, bridge], ignore_index=True)
            fig.add_trace(go.Scatter(
                x=hist_ext['Date'], y=hist_ext['New_Cases_7d'],
                mode='lines', line=dict(color='rgba(160,176,204,0.4)', width=1.5),
                name="Storico (pre-simulazione)", fill='tozeroy',
                fillcolor='rgba(160,176,204,0.05)'))
                
        sim_start_str = sim_start.strftime('%Y-%m-%d')
        fig.add_shape(type="line", x0=sim_start_str, x1=sim_start_str, y0=0, y1=1,
            xref="x", yref="paper", line=dict(color="#fbbf24", width=1.5, dash="dash"))
        fig.add_annotation(x=sim_start_str, y=1, xref="x", yref="paper",
            text="> Inizio live", showarrow=False,
            font=dict(color="#fbbf24", size=10), xanchor="left", yanchor="top")
            
        if not dlv.empty:
            fig.add_trace(go.Scatter(
                x=dlv['Date'], y=dlv['Live_Target'],
                mode='lines', line=dict(color=C['red'], width=2.5),
                name="Osservato live (Kafka)"))
                
        if 'ML_Pred' in dlv.columns:
            fig.add_trace(go.Scatter(
                x=dlv['Date'], y=dlv['ML_Pred'],
                line=dict(color=C['blue'], width=2, dash='dash'),
                name="ML fit (storico+live)"))
                
        if not forecast_df.empty:
            last_live_val = dlv['Live_Target'].iloc[-1] if not dlv.empty else 0
            fig.add_trace(go.Scatter(
                x=[dlv['Date'].iloc[-1]] + list(forecast_df['Date']),
                y=[last_live_val] + list(forecast_df['ML_Future']),
                line=dict(color=C['green'], width=2.5, dash='dot'),
                name=f"Forecast +{FORECAST_DAYS}gg",
                fill='tozeroy', fillcolor='rgba(52,211,153,0.04)'))
            today_sim = dlv['Date'].max().strftime('%Y-%m-%d')
            fig.add_shape(type="line", x0=today_sim, x1=today_sim, y0=0, y1=1,
                xref="x", yref="paper", line=dict(color=C['cyan'], width=1, dash="dot"))
            fig.add_annotation(x=today_sim, y=0.92, xref="x", yref="paper",
                text="* ora", showarrow=False,
                font=dict(color=C['cyan'], size=9), xanchor="left")
                
        apl(fig, height=420, hovermode="x unified", legend=hleg())
        st.plotly_chart(fig, use_container_width=True)
        
        if score is not None and all_feats:
            n_live = len(dlv)
            n_hist = len(dfc)
            st.markdown(f'<div style="background:#131c30;border:1px solid #263354;border-radius:8px;padding:.8rem 1rem;margin-top:.5rem;display:flex;gap:2rem"><span style="font-family:JetBrains Mono,monospace;font-weight:700;color:#4d8df7">In-Sample R² = {score:.3f}</span><span style="color:#a0b0cc;font-size:.85rem">RF · {len(all_feats)} features · training totale: {n_hist} storico + {n_live} live</span></div>', unsafe_allow_html=True)

            try:
                importances = mdl.feature_importances_
                feat_imp = sorted(zip(all_feats, importances), key=lambda x: x[1], reverse=True)
                fi_names = [f.replace('_',' ').title()[:25] for f,_ in reversed(feat_imp)]
                fi_vals = [v for _,v in reversed(feat_imp)]
                fig_fi = go.Figure(go.Bar(
                    y=fi_names, x=fi_vals, orientation='h',
                    marker=dict(color=fi_vals, colorscale=[[0,"#1e3a7a"],[1,"#4d8df7"]], cornerradius=4),
                    hovertemplate="%{y}: %{x:.3f}<extra></extra>"))
                apl(fig_fi, height=max(200, len(feat_imp)*30), showlegend=False,
                    xaxis_title="Importance (Gini)", margin=dict(l=200, r=20, t=10, b=30))
                st.plotly_chart(fig_fi, use_container_width=True)
            except: pass

    else:
        # Fallback senza Kafka
        base_feats = [f for f in ['containment_health_index', 'stringency_index', 'c1m_school_closing', 'reproduction_rate'] if f in dfc.columns]
        if base_feats:
            train_d, all_feats = build_ml_features(dfc.copy(), base_feats, target='New_Cases_7d')
            dt = train_d.dropna(subset=all_feats + ['New_Cases_7d'])
        else:
            dt = pd.DataFrame(); all_feats = []
            
        if len(dt) > 30 and all_feats:
            X_all, y_all = dt[all_feats], dt['New_Cases_7d']
            mdl = RandomForestRegressor(n_estimators=200, max_depth=8, min_samples_leaf=5, random_state=42)
            mdl.fit(X_all, y_all)
            
            pred_d, _ = build_ml_features(dfc.copy(), base_feats, target='New_Cases_7d')
            raw_pred = mdl.predict(pred_d[all_feats].fillna(0))
            dfc_pred = dfc.copy()
            dfc_pred['ML_Pred'] = pd.Series(raw_pred, index=dfc.index).rolling(7, min_periods=1).mean().values
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dfc['Date'], y=dfc['New_Cases_7d'], line=dict(color=C['blue'], width=2), name="Actual 7d Avg"))
            fig.add_trace(go.Scatter(x=dfc['Date'], y=dfc_pred['ML_Pred'], line=dict(color=C['red'], width=2, dash='dash'), name="RF Fit"))
            apl(fig, height=380, hovermode="x unified", legend=hleg())
            st.plotly_chart(fig, use_container_width=True)
            
            score = mdl.score(X_all, y_all)
            st.markdown(f'<div style="background:#131c30;border:1px solid #263354;border-radius:8px;padding:.8rem 1rem;margin-top:.5rem"><span style="font-family:JetBrains Mono,monospace;font-weight:700;color:#4d8df7">In-Sample R² = {score:.3f}</span><span style="color:#a0b0cc;font-size:.85rem;margin-left:1rem">Random Forest · {len(all_feats)} features (policy smoothed 7d + lag 7/14/21)</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align:center;padding:2rem"><div style="font-size:2rem"></div><div style="font-size:.9rem;font-weight:600;color:#f0f4fc;margin-top:.5rem">Dati insufficienti per {iso}</div></div>', unsafe_allow_html=True)
    pan_close()

# ╔═══════════════════════════════════════════════════════╗
# ║               NEO4J GRAPH ANALYSIS                    ║
# ╚═══════════════════════════════════════════════════════╝
elif st.session_state.get("page") == "neo4j":
    st.markdown('''<div class="hdr">
        <h1> Neo4j Graph Analysis</h1>
        <p class="sub">Il grafo epidemiologico modella 184 paesi come nodi collegati da tre tipi di relazione:
        pattern di contagio simili, politiche di contenimento analoghe, e propagazione geografica tra vicini.</p>
        <div class="tags">
            <span class="tag">Neo4j</span><span class="tag">Cypher</span>
            <span class="tag">Graph DB</span><span class="tag">184 Paesi</span>
            <span class="tag">3 Tipi Relazione</span>
        </div>
    </div>''', unsafe_allow_html=True)

    NEO4J_URI  = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASS = "pandemic_pulse_2024"

    @st.cache_resource
    def get_neo4j():
        if not NEO4J_AVAILABLE:
            return None
        try:
            d = _Neo4jDriver.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
            d.verify_connectivity()
            return d
        except Exception:
            return None

    def run_query(driver, cypher, params=None):
        try:
            with driver.session() as s:
                return s.run(cypher, params or {}).data()
        except Exception as e:
            st.error(f"Errore query: {e}")
            return []

    CONT_COLORS = {
        "Europe":"#4d8df7","Asia":"#34d399","Africa":"#fbbf24",
        "North America":"#ff5c5c","South America":"#c084fc",
        "Oceania":"#22d3ee","Unknown":"#607090"
    }

    driver = get_neo4j()

    if not NEO4J_AVAILABLE:
        st.warning("Libreria `neo4j` non installata. Esegui: `pip install neo4j`")
        st.stop()
    elif driver is None:
        st.error("Impossibile connettersi a Neo4j su `bolt://localhost:7687`.")
        st.markdown("""<div style="background:#131c30;border:1px solid #263354;border-radius:8px;
            padding:1rem 1.2rem;margin-top:1rem">
            <div style="font-family:JetBrains Mono,monospace;font-size:.8rem;color:#78aeff">
            URL: http://localhost:7474 &nbsp;·&nbsp; Username: neo4j &nbsp;·&nbsp; Password: pandemic_pulse_2024
            </div></div>""", unsafe_allow_html=True)
    else:
        # ── Schema grafo ──────────────────────────────────────────────
        st.markdown("""<div style="background:#0c1220;border:1px solid #263354;border-radius:10px;
            padding:.9rem 1.4rem;margin-bottom:1.2rem">
            <div style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
            color:#607090;margin-bottom:.6rem">SCHEMA DEL GRAFO</div>
            <div style="font-size:.82rem;color:#a0b0cc;line-height:2">
            Nodo <code style="color:#78aeff;background:#1a2540;padding:1px 6px;border-radius:3px">:Country</code>
            — 184 paesi &nbsp;|&nbsp;
            <span style="color:#4d8df7">&#9632;</span> <b>SIMILAR_EPIDEMIC_PATTERN</b> Pearson ≥ 0.85 &nbsp;|&nbsp;
            <span style="color:#fbbf24">&#9632;</span> <b>SIMILAR_POLICY_RESPONSE</b> Stringency diff &lt; 5 &nbsp;|&nbsp;
            <span style="color:#34d399">&#9632;</span> <b>BORDER_SPREAD</b> Picco entro 14 giorni
            </div></div>""", unsafe_allow_html=True)

        # ── KPI ───────────────────────────────────────────────────────
        col_s = st.columns(4)
        for col, label, cypher, color, suffix in zip(col_s,
            ["Paesi","Pattern simili","Policy simili","Propagazioni"],
            [
                "MATCH (c:Country) RETURN count(c) AS n",
                "MATCH ()-[r:SIMILAR_EPIDEMIC_PATTERN]-() RETURN count(r)/2 AS n",
                "MATCH ()-[r:SIMILAR_POLICY_RESPONSE]-() RETURN count(r)/2 AS n",
                "MATCH ()-[r:BORDER_SPREAD]->() RETURN count(r) AS n",
            ],
            ["blue","blue","amber","green"],
            ["nodi","coppie","coppie","archi"]):
            res = run_query(driver, cypher)
            val = res[0]["n"] if res else "—"
            col.markdown(kpi_html(color, label, str(val), suffix), unsafe_allow_html=True)

        st.markdown('<div style="height:.8rem"></div>', unsafe_allow_html=True)

        tab_graph, tab_hubs, tab_spread, tab_density, tab_centrality = st.tabs([
            " Grafo Interattivo",
            " Hub Epidemiologici",
            " Catene di Diffusione",
            " Densità per Continente",
            " Centralità di Grado",
        ])

       # ── TAB 0 — Grafo interattivo ─────────────────────────────────
        with tab_graph:
            pan_open("", "GRAFO INTERATTIVO — ESPLORAZIONE VISIVA", "batch")
            st.markdown("""<div style="font-size:.85rem;color:#a0b0cc;line-height:1.7;margin-bottom:.8rem">
            Ogni <b>nodo</b> è un paese — colore per continente, dimensione proporzionale alla mortalità per milione.
            Il grafo mostra le relazioni interne tra i <b>Top N paesi</b> più colpiti dal virus. Puoi trascinare i nodi e zoomare.
            <br><span style="font-family:JetBrains Mono,monospace;font-size:.73rem;color:#607090">
            Cypher: MATCH (c:Country) WITH c ORDER BY c.deaths DESC LIMIT n ... MATCH (n)-[r]->(m) WHERE n,m IN top_nodes</span></div>""", unsafe_allow_html=True)

            col_rel, col_lim = st.columns([3,1])
            with col_rel:
                rel_filter = st.multiselect("Tipo di relazione",
                    ["SIMILAR_EPIDEMIC_PATTERN","BORDER_SPREAD","SIMILAR_POLICY_RESPONSE"],
                    default=["SIMILAR_EPIDEMIC_PATTERN","BORDER_SPREAD"], key="graph_rel")
            with col_lim:
                # Modificato da "Max archi" a "Max nodi" (range adattato per una visualizzazione ottimale)
                graph_limit = st.slider("Max nodi (Top Morti/M)", 10, 100, 30, step=5, key="graph_limit")

            if rel_filter:
                rel_clause = "|".join(rel_filter)
                # Lookup ISO -> continente (hardcoded perché il campo continent nel grafo è numerico)
                ISO_CONTINENT = {
                    "AFG":"Asia","ALB":"Europe","DZA":"Africa","AND":"Europe","AGO":"Africa",
                    "ARG":"South America","ARM":"Asia","AUS":"Oceania","AUT":"Europe","AZE":"Asia",
                    "BHS":"North America","BHR":"Asia","BGD":"Asia","BLR":"Europe","BEL":"Europe",
                    "BLZ":"North America","BEN":"Africa","BTN":"Asia","BOL":"South America",
                    "BIH":"Europe","BWA":"Africa","BRA":"South America","BRN":"Asia","BGR":"Europe",
                    "BFA":"Africa","BDI":"Africa","CPV":"Africa","KHM":"Asia","CMR":"Africa",
                    "CAN":"North America","CAF":"Africa","TCD":"Africa","CHL":"South America",
                    "CHN":"Asia","COL":"South America","COM":"Africa","COD":"Africa","COG":"Africa",
                    "CRI":"North America","HRV":"Europe","CUB":"North America","CYP":"Europe",
                    "CZE":"Europe","DNK":"Europe","DJI":"Africa","DOM":"North America","ECU":"South America",
                    "EGY":"Africa","SLV":"North America","GNQ":"Africa","ERI":"Africa","EST":"Europe",
                    "SWZ":"Africa","ETH":"Africa","FJI":"Oceania","FIN":"Europe","FRA":"Europe",
                    "GAB":"Africa","GMB":"Africa","GEO":"Asia","DEU":"Europe","GHA":"Africa",
                    "GRC":"Europe","GTM":"North America","GIN":"Africa","GNB":"Africa","GUY":"South America",
                    "HTI":"North America","HND":"North America","HUN":"Europe","ISL":"Europe","IND":"Asia",
                    "IDN":"Asia","IRN":"Asia","IRQ":"Asia","IRL":"Europe","ISR":"Asia","ITA":"Europe",
                    "JAM":"North America","JPN":"Asia","JOR":"Asia","KAZ":"Asia","KEN":"Africa",
                    "PRK":"Asia","KOR":"Asia","KWT":"Asia","KGZ":"Asia","LAO":"Asia","LVA":"Europe",
                    "LBN":"Asia","LSO":"Africa","LBR":"Africa","LBY":"Africa","LIE":"Europe",
                    "LTU":"Europe","LUX":"Europe","MDG":"Africa","MWI":"Africa","MYS":"Asia",
                    "MDV":"Asia","MLI":"Africa","MLT":"Europe","MRT":"Africa","MUS":"Africa",
                    "MEX":"North America","MDA":"Europe","MCO":"Europe","MNG":"Asia","MNE":"Europe",
                    "MAR":"Africa","MOZ":"Africa","MMR":"Asia","NAM":"Africa","NPL":"Asia",
                    "NLD":"Europe","NZL":"Oceania","NIC":"North America","NER":"Africa","NGA":"Africa",
                    "MKD":"Europe","NOR":"Europe","OMN":"Asia","PAK":"Asia","PAN":"North America",
                    "PNG":"Oceania","PRY":"South America","PER":"South America","PHL":"Asia",
                    "POL":"Europe","PRT":"Europe","QAT":"Asia","ROU":"Europe","RUS":"Europe",
                    "RWA":"Africa","SAU":"Asia","SEN":"Africa","SRB":"Europe","SLE":"Africa",
                    "SVK":"Europe","SVN":"Europe","SOM":"Africa","ZAF":"Africa","SSD":"Africa",
                    "ESP":"Europe","LKA":"Asia","SDN":"Africa","SUR":"South America","SWE":"Europe",
                    "CHE":"Europe","SYR":"Asia","TWN":"Asia","TJK":"Asia","TZA":"Africa","THA":"Asia",
                    "TLS":"Asia","TGO":"Africa","TTO":"North America","TUN":"Africa","TUR":"Asia",
                    "TKM":"Asia","UGA":"Africa","UKR":"Europe","ARE":"Asia","GBR":"Europe",
                    "USA":"North America","URY":"South America","UZB":"Asia","VEN":"South America",
                    "VNM":"Asia","YEM":"Asia","ZMB":"Africa","ZWE":"Africa","SYC":"Africa",
                    "BHS":"North America","VCT":"North America","ATG":"North America","BRB":"North America",
                    "DMA":"North America","GRD":"North America","KNA":"North America","LCA":"North America",
                    "TTO":"North America","AND":"Europe","LIE":"Europe","MCO":"Europe","SMR":"Europe",
                    "VAT":"Europe","MNE":"Europe","XKX":"Europe","SLB":"Oceania","VUT":"Oceania",
                    "WSM":"Oceania","TON":"Oceania","KIR":"Oceania","FSM":"Oceania","PLW":"Oceania",
                    "MHL":"Oceania","NRU":"Oceania","TUV":"Oceania","MSR":"North America",
                    "AZE":"Asia","ARM":"Asia","GEO":"Asia","CYP":"Europe","MLT":"Europe",
                    "BHS":"North America","JAM":"North America","HTI":"North America","CUB":"North America",
                }

                # Cypher query aggiornata per selezionare i Top Nodi per morti e le loro interconnessioni
                raw = run_query(driver, f"""
                    MATCH (c:Country)
                    WHERE c.total_deaths_per_million IS NOT NULL
                    WITH c
                    ORDER BY c.total_deaths_per_million DESC
                    LIMIT {graph_limit}
                    WITH collect(c) AS top_nodes
                    MATCH (n:Country)-[r:{rel_clause}]->(m:Country)
                    WHERE n IN top_nodes AND m IN top_nodes
                    RETURN n.iso_code AS src_iso, n.total_deaths_per_million AS src_deaths,
                           m.iso_code AS tgt_iso, m.total_deaths_per_million AS tgt_deaths,
                           type(r) AS rel_type
                """)
                
                if raw:
                    try:
                        from pyvis.network import Network
                        import tempfile, os as _os
                        nodes_map = {}
                        edges_list = []
                        for row in raw:
                            for iso, deaths in [
                                (row["src_iso"], row["src_deaths"]),
                                (row["tgt_iso"], row["tgt_deaths"])
                            ]:
                                if iso and iso not in nodes_map:
                                    nodes_map[iso] = {"deaths": deaths or 0}
                            if row["src_iso"] and row["tgt_iso"]:
                                edges_list.append((row["src_iso"], row["tgt_iso"], row["rel_type"]))

                        net = Network(height="520px", width="100%", bgcolor="#0c1220",
                                      font_color="#a0b0cc", directed=False)
                        net.set_options("""{
                          "physics":{"enabled":false},
                          "edges":{"smooth":{"type":"continuous"}},
                          "interaction":{"hover":true,"tooltipDelay":100}
                        }""")
                        for iso, nd in nodes_map.items():
                            cont = ISO_CONTINENT.get(iso, "Unknown")
                            col_nd = CONT_COLORS.get(cont, "#607090")
                            size_nd = max(10, min(38, int(nd["deaths"]/80))) if nd["deaths"] else 12
                            title_nd = f"<b>{iso}</b><br>{cont}<br>Morti/M: {int(nd['deaths']):,}" if nd["deaths"] else f"<b>{iso}</b><br>{cont}"
                            net.add_node(iso, label=iso, color=col_nd, size=size_nd,
                                         title=title_nd, font={"size":11,"color":"#f0f4fc"})
                        edge_colors = {"SIMILAR_EPIDEMIC_PATTERN":"rgba(77,141,247,0.4)",
                                       "BORDER_SPREAD":"rgba(52,211,153,0.4)",
                                       "SIMILAR_POLICY_RESPONSE":"rgba(251,191,36,0.4)"}
                        for src, tgt, rtype in edges_list:
                            net.add_edge(src, tgt, color=edge_colors.get(rtype,"rgba(38,51,84,0.5)"), width=1.5)

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
                            net.save_graph(f.name)
                            html_graph = open(f.name).read()
                        _os.unlink(f.name)
                        html_graph = html_graph.replace("background-color:#ffffff","background-color:#0c1220")
                        html_graph = html_graph.replace("background-color: #ffffff","background-color:#0c1220")
                        st.components.v1.html(html_graph, height=540, scrolling=False)

                        # Legenda continenti
                        legend_html = "".join([
                            f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px">'
                            f'<span style="width:10px;height:10px;border-radius:50%;background:{c};display:inline-block"></span>'
                            f'<span style="font-size:.72rem;color:#a0b0cc">{cont}</span></span>'
                            for cont, c in CONT_COLORS.items() if cont != "Unknown"])
                        st.markdown(f'<div style="margin-top:.4rem">{legend_html}</div>', unsafe_allow_html=True)
                        st.caption(f"{len(edges_list)} archi · {len(nodes_map)} nodi visualizzati (top per mortalità)")
                    except Exception as ex:
                        st.error(f"Errore visualizzazione grafo: {ex}")
                        st.info("Assicurati che `pyvis` sia installato: `pip install pyvis`")
                else:
                    st.info("Nessuna connessione trovata tra i top nodi selezionati con questi filtri.")
            else:
                st.info("Seleziona almeno un tipo di relazione.")
            pan_close()

        # ── TAB 1 — Hub epidemiologici ────────────────────────────────
        with tab_hubs:
            pan_open("", "HUB EPIDEMIOLOGICI", "batch")
            st.markdown("""<div style="font-size:.85rem;color:#a0b0cc;line-height:1.7;margin-bottom:.8rem">
            Un <b>hub epidemiologico</b> è un paese la cui curva di contagio è fortemente correlata
            (Pearson ≥ 0.85) con molti altri. I paesi con più connessioni fungono da benchmark epidemiologico.
            <br><span style="font-family:JetBrains Mono,monospace;font-size:.73rem;color:#607090">
            Cypher: MATCH (c:Country)-[r:SIMILAR_EPIDEMIC_PATTERN]-() RETURN c.iso_code, COUNT(r) AS Connessioni ORDER BY Connessioni DESC</span>
            </div>""", unsafe_allow_html=True)

            limit = st.slider("Numero di paesi da mostrare", 5, 30, 15, key="hub_limit")
            rows = run_query(driver, """
                MATCH (c:Country)-[r:SIMILAR_EPIDEMIC_PATTERN]-()
                RETURN c.iso_code AS Paese, c.continent AS Continente,
                       c.total_confirmed AS Casi,
                       round(c.total_deaths_per_million) AS Morti_per_M,
                       COUNT(r) AS Connessioni
                ORDER BY Connessioni DESC LIMIT $lim
            """, {"lim": limit})
            if rows:
                df_hub = pd.DataFrame(rows)
                fig = go.Figure(go.Bar(
                    x=df_hub["Paese"], y=df_hub["Connessioni"],
                    marker=dict(color=[CONT_COLORS.get(c,"#607090") for c in df_hub["Continente"]],
                                cornerradius=5),
                    customdata=df_hub[["Continente","Morti_per_M","Casi"]],
                    hovertemplate=(
                        "<b>%{x}</b><br>Connessioni: <b>%{y}</b><br>"
                        "Continente: %{customdata[0]}<br>"
                        "Morti/M: %{customdata[1]:,.0f}<br>"
                        "Casi: %{customdata[2]:,}<extra></extra>")
                ))
                apl(fig, height=380, showlegend=False,
                    xaxis_title="Paese (ISO)", yaxis_title="N° connessioni simili")
                st.plotly_chart(fig, use_container_width=True)
                df_show = df_hub[["Paese","Casi","Morti_per_M","Connessioni"]].copy()
                df_show["Casi"] = df_show["Casi"].apply(lambda x: f"{int(x):,}" if pd.notna(x) and x else "—")
                df_show["Morti_per_M"] = df_show["Morti_per_M"].apply(lambda x: f"{int(x):,}" if pd.notna(x) and x else "—")
                st.dataframe(df_show.rename(columns={"Morti_per_M":"Morti/M"}),
                             use_container_width=True, hide_index=True)
            pan_close()

        # ── TAB 2 — Catene di diffusione ──────────────────────────────
        with tab_spread:
            pan_open("", "CATENE DI DIFFUSIONE — BORDER_SPREAD", "batch")
            st.markdown("""<div style="font-size:.85rem;color:#a0b0cc;line-height:1.7;margin-bottom:.8rem">
            Paesi dello stesso continente con picco epidemico entro 14 giorni l'uno dall'altro.
            Il nodo <b style="color:#fbbf24">giallo</b> è la sorgente, i colori indicano la distanza in hop.
            <br><span style="font-family:JetBrains Mono,monospace;font-size:.73rem;color:#607090">
            Cypher: MATCH path=(src)-[:BORDER_SPREAD*1..3]->(tgt) WHERE src.iso_code='ITA' RETURN path</span>
            </div>""", unsafe_allow_html=True)

            col_src, col_hops = st.columns([2,1])
            with col_src:
                all_isos = sorted([r["iso"] for r in run_query(driver,
                    "MATCH (c:Country) RETURN c.iso_code AS iso ORDER BY iso")])
                src_iso = st.selectbox("Paese sorgente", all_isos,
                    index=all_isos.index("ITA") if "ITA" in all_isos else 0, key="spread_src")
            with col_hops:
                max_hops = st.slider("Max hop", 1, 3, 3, key="spread_hops")

            rows = run_query(driver, f"""
                MATCH path = (src:Country {{iso_code: $iso}})-[:BORDER_SPREAD*1..{max_hops}]->(tgt:Country)
                WITH tgt, min(length(path)) AS hops
                RETURN tgt.iso_code AS Paese, hops AS Hop
                ORDER BY hops, Paese
            """, {"iso": src_iso})

            edge_rows = run_query(driver, f"""
                MATCH path = (src:Country {{iso_code: $iso}})-[:BORDER_SPREAD*1..{max_hops}]->(tgt:Country)
                WITH relationships(path) AS rels, nodes(path) AS nds
                UNWIND range(0, size(rels)-1) AS i
                RETURN nds[i].iso_code AS src_iso, nds[i].total_deaths_per_million AS src_d,
                       nds[i+1].iso_code AS tgt_iso, nds[i+1].total_deaths_per_million AS tgt_d
            """, {"iso": src_iso})

            if edge_rows:
                try:
                    from pyvis.network import Network
                    import tempfile, os as _os
                    hop_map = {r["Paese"]: r["Hop"] for r in rows} if rows else {}
                    hop_colors = {0:"#fbbf24",1:"#34d399",2:"#4d8df7",3:"#c084fc",4:"#f472b6"}
                    nodes_map2 = {}
                    edges2 = []
                    for row in edge_rows:
                        for iso, d in [(row["src_iso"],row["src_d"]),(row["tgt_iso"],row["tgt_d"])]:
                            if iso and iso not in nodes_map2:
                                nodes_map2[iso] = {"deaths": d or 0}
                        if row["src_iso"] and row["tgt_iso"]:
                            edges2.append((row["src_iso"], row["tgt_iso"]))

                    net2 = Network(height="460px", width="100%", bgcolor="#0c1220",
                                   font_color="#a0b0cc", directed=True)
                    net2.set_options("""{
                      "physics":{"enabled":false},
                      "edges":{"arrows":{"to":{"enabled":true,"scaleFactor":0.7}},
                        "smooth":{"type":"curvedCW","roundness":0.2}},
                      "interaction":{"hover":true}
                    }""")
                    for iso, nd in nodes_map2.items():
                        h = 0 if iso == src_iso else hop_map.get(iso, 99)
                        col_nd = "#fbbf24" if iso == src_iso else hop_colors.get(h, "#607090")
                        size_nd = 28 if iso == src_iso else 16
                        net2.add_node(iso, label=iso, color=col_nd, size=size_nd,
                                      title=f"<b>{iso}</b><br>{'Sorgente' if iso==src_iso else f'Hop {h}'}",
                                      font={"size":11,"color":"#f0f4fc"})
                    for s, t in edges2:
                        net2.add_edge(s, t, color="rgba(52,211,153,0.5)", width=2)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f2:
                        net2.save_graph(f2.name)
                        html2 = open(f2.name).read()
                    _os.unlink(f2.name)
                    html2 = html2.replace("background-color:#ffffff","background-color:#0c1220")
                    html2 = html2.replace("background-color: #ffffff","background-color:#0c1220")
                    st.components.v1.html(html2, height=480, scrolling=False)
                    # Legenda hop
                    legend_hop = "".join([
                        f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:12px">'
                        f'<span style="width:10px;height:10px;border-radius:50%;background:{hop_colors.get(h,"#607090")};display:inline-block"></span>'
                        f'<span style="font-size:.72rem;color:#a0b0cc">{"Sorgente" if h==0 else f"Hop {h}"}</span></span>'
                        for h in range(max_hops+1)])
                    st.markdown(legend_hop, unsafe_allow_html=True)
                except Exception as ex:
                    st.error(f"Errore grafo: {ex}")

            if rows:
                df_spread = pd.DataFrame(rows)
                st.markdown('<div class="sec-title"> Paesi raggiunti</div>', unsafe_allow_html=True)
                st.dataframe(df_spread, use_container_width=True, hide_index=True)
                st.caption(f"{len(df_spread)} paesi raggiungibili da {src_iso} in max {max_hops} hop.")
            elif not edge_rows:
                st.info(f"Nessuna catena BORDER_SPREAD trovata da {src_iso} in {max_hops} hop.")
            pan_close()


        # ── TAB 4 — Densità connessioni per continente ────────────────
        with tab_density:
            pan_open("", "DENSITÀ DI CONNESSIONE PER CONTINENTE", "batch")
            st.markdown("""<div style="font-size:.85rem;color:#a0b0cc;line-height:1.7;margin-bottom:.8rem">
            Numero di connessioni <b>SIMILAR_EPIDEMIC_PATTERN</b> tra paesi dello stesso continente.
            Un valore alto indica che i paesi del continente hanno seguito curve epidemiche molto simili tra loro.
            <br><span style="font-family:JetBrains Mono,monospace;font-size:.73rem;color:#607090">
            Cypher: MATCH (a:Country)-[:SIMILAR_EPIDEMIC_PATTERN]-(b:Country) WHERE a.iso_code &lt;&gt; b.iso_code RETURN a.iso_code, b.iso_code</span>
            </div>""", unsafe_allow_html=True)

            # Il campo continent nel grafo è numerico → usiamo la lookup ISO→continente
            ISO_CONT_MAP = {
                "AFG":"Asia","ALB":"Europe","DZA":"Africa","AND":"Europe","AGO":"Africa",
                "ARG":"South America","ARM":"Asia","AUS":"Oceania","AUT":"Europe","AZE":"Asia",
                "BHS":"North America","BHR":"Asia","BGD":"Asia","BLR":"Europe","BEL":"Europe",
                "BLZ":"North America","BEN":"Africa","BTN":"Asia","BOL":"South America",
                "BIH":"Europe","BWA":"Africa","BRA":"South America","BRN":"Asia","BGR":"Europe",
                "BFA":"Africa","BDI":"Africa","CPV":"Africa","KHM":"Asia","CMR":"Africa",
                "CAN":"North America","CAF":"Africa","TCD":"Africa","CHL":"South America",
                "CHN":"Asia","COL":"South America","COM":"Africa","COD":"Africa","COG":"Africa",
                "CRI":"North America","HRV":"Europe","CUB":"North America","CYP":"Europe",
                "CZE":"Europe","DNK":"Europe","DJI":"Africa","DOM":"North America","ECU":"South America",
                "EGY":"Africa","SLV":"North America","GNQ":"Africa","ERI":"Africa","EST":"Europe",
                "SWZ":"Africa","ETH":"Africa","FJI":"Oceania","FIN":"Europe","FRA":"Europe",
                "GAB":"Africa","GMB":"Africa","GEO":"Asia","DEU":"Europe","GHA":"Africa",
                "GRC":"Europe","GTM":"North America","GIN":"Africa","GNB":"Africa","GUY":"South America",
                "HTI":"North America","HND":"North America","HUN":"Europe","ISL":"Europe","IND":"Asia",
                "IDN":"Asia","IRN":"Asia","IRQ":"Asia","IRL":"Europe","ISR":"Asia","ITA":"Europe",
                "JAM":"North America","JPN":"Asia","JOR":"Asia","KAZ":"Asia","KEN":"Africa",
                "PRK":"Asia","KOR":"Asia","KWT":"Asia","KGZ":"Asia","LAO":"Asia","LVA":"Europe",
                "LBN":"Asia","LSO":"Africa","LBR":"Africa","LBY":"Africa","LIE":"Europe",
                "LTU":"Europe","LUX":"Europe","MDG":"Africa","MWI":"Africa","MYS":"Asia",
                "MDV":"Asia","MLI":"Africa","MLT":"Europe","MRT":"Africa","MUS":"Africa",
                "MEX":"North America","MDA":"Europe","MCO":"Europe","MNG":"Asia","MNE":"Europe",
                "MAR":"Africa","MOZ":"Africa","MMR":"Asia","NAM":"Africa","NPL":"Asia",
                "NLD":"Europe","NZL":"Oceania","NIC":"North America","NER":"Africa","NGA":"Africa",
                "MKD":"Europe","NOR":"Europe","OMN":"Asia","PAK":"Asia","PAN":"North America",
                "PNG":"Oceania","PRY":"South America","PER":"South America","PHL":"Asia",
                "POL":"Europe","PRT":"Europe","QAT":"Asia","ROU":"Europe","RUS":"Europe",
                "RWA":"Africa","SAU":"Asia","SEN":"Africa","SRB":"Europe","SLE":"Africa",
                "SVK":"Europe","SVN":"Europe","SOM":"Africa","ZAF":"Africa","SSD":"Africa",
                "ESP":"Europe","LKA":"Asia","SDN":"Africa","SUR":"South America","SWE":"Europe",
                "CHE":"Europe","SYR":"Asia","TWN":"Asia","TJK":"Asia","TZA":"Africa","THA":"Asia",
                "TLS":"Asia","TGO":"Africa","TTO":"North America","TUN":"Africa","TUR":"Asia",
                "TKM":"Asia","UGA":"Africa","UKR":"Europe","ARE":"Asia","GBR":"Europe",
                "USA":"North America","URY":"South America","UZB":"Asia","VEN":"South America",
                "VNM":"Asia","YEM":"Asia","ZMB":"Africa","ZWE":"Africa","SYC":"Africa",
                "VCT":"North America","ATG":"North America","BRB":"North America",
                "DMA":"North America","GRD":"North America","KNA":"North America","LCA":"North America",
                "SMR":"Europe","VAT":"Europe","XKX":"Europe","SLB":"Oceania","VUT":"Oceania",
                "WSM":"Oceania","TON":"Oceania","KIR":"Oceania","FSM":"Oceania","PLW":"Oceania",
                "MHL":"Oceania","NRU":"Oceania","TUV":"Oceania","MSR":"North America",
            }

            # Query: recupera tutte le coppie con iso_code di entrambi i nodi
            rows_density_raw = run_query(driver, """
                MATCH (a:Country)-[:SIMILAR_EPIDEMIC_PATTERN]-(b:Country)
                WHERE a.iso_code < b.iso_code
                RETURN a.iso_code AS iso_a, b.iso_code AS iso_b
            """)

            if rows_density_raw:
                from collections import Counter
                cont_counts = Counter()
                for row in rows_density_raw:
                    ca = ISO_CONT_MAP.get(row["iso_a"], "Unknown")
                    cb = ISO_CONT_MAP.get(row["iso_b"], "Unknown")
                    if ca == cb:
                        cont_counts[ca] += 1

                if cont_counts:
                    df_density = pd.DataFrame(
                        sorted(cont_counts.items(), key=lambda x: -x[1]),
                        columns=["continent", "internal_links"]
                    )
                    fig_density = go.Figure(go.Bar(
                        x=df_density["continent"],
                        y=df_density["internal_links"],
                        marker=dict(
                            color=[CONT_COLORS.get(c, "#607090") for c in df_density["continent"]],
                            cornerradius=6
                        ),
                        hovertemplate="<b>%{x}</b><br>Connessioni interne: <b>%{y}</b><extra></extra>"
                    ))
                    apl(fig_density, height=380, showlegend=False,
                        xaxis_title="Continente", yaxis_title="N° connessioni interne")
                    st.plotly_chart(fig_density, use_container_width=True)

                    df_density_show = df_density.rename(columns={"continent": "Continente", "internal_links": "Connessioni interne"})
                    st.dataframe(df_density_show, use_container_width=True, hide_index=True)
                else:
                    st.info("Nessuna coppia con stesso continente trovata.")
            else:
                st.info("Nessun dato trovato per la densità di connessione.")
            pan_close()

        # ── TAB 5 — Centralità di grado ───────────────────────────────
        with tab_centrality:
            pan_open("", "CENTRALITÀ DI GRADO", "batch")
            st.markdown("""<div style="font-size:.85rem;color:#a0b0cc;line-height:1.7;margin-bottom:.8rem">
            Il <b>grado</b> di un nodo misura quante relazioni (di qualsiasi tipo) possiede nel grafo.
            I paesi con grado più alto sono i più "centrali" nell'ecosistema epidemiologico globale:
            condividono pattern, policy e propagazioni geografiche con il maggior numero di altri nodi.
            <br><span style="font-family:JetBrains Mono,monospace;font-size:.73rem;color:#607090">
            Cypher: MATCH (c:Country)-[r]-() RETURN c.iso_code, COUNT(r) AS degree ORDER BY degree DESC LIMIT 10</span>
            </div>""", unsafe_allow_html=True)

            top_n_cent = st.slider("Numero di paesi da mostrare", 5, 20, 10, key="centrality_limit")

            rows_cent = run_query(driver, """
                MATCH (c:Country)-[r]-()
                RETURN c.iso_code AS country,
                       COUNT(r) AS degree
                ORDER BY degree DESC LIMIT $lim
            """, {"lim": top_n_cent})

            if rows_cent:
                df_cent = pd.DataFrame(rows_cent)
                # Risolvi continente via lookup ISO (c.continent nel grafo è numerico)
                df_cent["continent"] = df_cent["country"].apply(lambda iso: ISO_CONT_MAP.get(iso, "Unknown"))

                fig_cent = go.Figure(go.Bar(
                    x=df_cent["country"],
                    y=df_cent["degree"],
                    marker=dict(
                        color=[CONT_COLORS.get(c, "#607090") for c in df_cent["continent"]],
                        cornerradius=6
                    ),
                    customdata=df_cent[["continent"]],
                    hovertemplate=(
                        "<b>%{x}</b><br>Grado: <b>%{y}</b><br>"
                        "Continente: %{customdata[0]}<extra></extra>")
                ))
                apl(fig_cent, height=380, showlegend=False,
                    xaxis_title="Paese (ISO)", yaxis_title="Grado (tutte le relazioni)")
                st.plotly_chart(fig_cent, use_container_width=True)

                # Legenda continenti presenti
                conts_present = df_cent["continent"].unique().tolist()
                legend_cent = "".join([
                    f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:14px">'
                    f'<span style="width:10px;height:10px;border-radius:50%;background:{CONT_COLORS.get(c,"#607090")};display:inline-block"></span>'
                    f'<span style="font-size:.72rem;color:#a0b0cc">{c}</span></span>'
                    for c in conts_present])
                st.markdown(f'<div style="margin-top:.4rem;margin-bottom:.8rem">{legend_cent}</div>', unsafe_allow_html=True)

                df_cent_show = df_cent.rename(columns={"country": "Paese", "continent": "Continente", "degree": "Grado"})
                st.dataframe(df_cent_show, use_container_width=True, hide_index=True)
            else:
                st.info("Nessun dato trovato per la centralità di grado.")
            pan_close()


st.markdown(f'<div class="foot"><p><strong>PandemicPulse</strong> | Spark · Kafka · MongoDB · Docker | Information Systems for Big Data | {datetime.now().year}</p></div>',unsafe_allow_html=True)
