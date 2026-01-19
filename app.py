import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
import xml.etree.ElementTree as ET
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# 1. CONFIGURATION (OBLIGATOIRE EN PREMIER)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BoussiBroke | Conseils Bourse",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. DESIGN & CSS (MODE SOMBRE COMPATIBLE)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    h1, h2, h3 { color: #111111 !important; }
    p, span, div { color: #333333; }
    
    /* Cartes Métriques (Prix) */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
    }
    div[data-testid="stMetric"] label { color: #000000 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #000000 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] { font-weight: bold; }

    /* Cartes News Sidebar */
    .news-card {
        background-color: white;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
        border-left: 4px solid #00CC96;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    a.news-link {
        text-decoration: none;
        color: #2c3e50 !important;
        font-weight: bold;
        font-size: 13px;
        display: block;
        margin-bottom: 4px;
    }
    a.news-link:hover { color: #00CC96 !important; }
    
    /* Cartes Conseils */
    .advice-card {
        background-color: white;
        padding: 25px;
        margin-bottom: 25px;
        border-radius: 12px;
        border-top: 5px solid #636EFA;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .advice-title { color: #000 !important; font-size: 1.4em; font-weight: 800; margin-bottom: 10px; }
    .advice-content { color: #444 !important; line-height: 1.6; text-align: justify; }
    .advice-date { color: #666 !important; font-size: 0.85em; font-style: italic; margin-bottom: 5px;}
    .advice-action { margin-top: 15px; padding: 10px; background-color: #f0fdf4; border-left: 4px solid #2ecc71; font-weight: bold; color: #14532d !important; }

    /* Footer */
    .footer-cta {
        margin-top: 50px;
        padding: 30px;
        background: white;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #ddd;
    }
    .cta-button {
        display: inline-block;
        background-color: #000;
        color: #fff !important;
        padding: 12px 25px;
        border-radius: 50px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 BoussiBroke Investissement")
st.markdown("Bienvenue ! Votre tableau de bord financier personnel.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 3. DONNÉES
# -----------------------------------------------------------------------------
FREQ_MAP = {"1x / semaine": 4.33, "1x / 2 semaines": 2.16, "1x / mois": 1.0, "2x / mois": 2.0, "3x / mois": 3.0}
CURRENCY_MAP = {"CNDX.L": "USD", "BRK-B": "USD", "TTWO": "USD", "SGO.PA": "EUR", "BRBY.L": "GBP", "CIN.PA": "EUR", "AAPL": "USD", "DIA": "USD", "MSFT": "USD", "NATO.PA": "EUR", "AI.PA": "EUR", "TQQQ": "USD", "VIE.PA": "EUR", "ACWX": "USD", "PLTR": "USD", "GLD": "USD", "GOOGL": "USD"}

TICKERS_TRACKER = {
    "🇺🇸 Nasdaq 100": "CNDX.L", "🇺🇸 Berkshire B": "BRK-B", "🇺🇸 Take-Two": "TTWO", 
    "🇫🇷 Saint-Gobain": "SGO.PA", "🇬🇧 Burberry": "BRBY.L", "🇮🇳 MSCI India": "CIN.PA", 
    "🇺🇸 Apple": "AAPL", "🇺🇸 Dow Jones": "DIA", "🇺🇸 Microsoft": "MSFT", 
    "🇪🇺 Defense": "NATO.PA", "🇫🇷 Air Liquide": "AI.PA", "🇺🇸 Nasdaq x3": "TQQQ", 
    "🇫🇷 Véolia": "VIE.PA", "🌍 World ex-USA": "ACWX", "🇺🇸 Palantir": "PLTR", 
    "🟡 Or (Gold)": "GLD", "🇺🇸 Alphabet": "GOOGL"
}

DEFAULT_PLAN = [
    {"Action": "Nasdaq 100", "Ticker": "CNDX.L", "Montant (€)": 5, "Fréquence": "1x / semaine"},
    {"Action": "Berkshire B", "Ticker": "BRK-B", "Montant (€)": 3, "Fréquence": "1x / semaine"},
    {"Action": "Take-Two", "Ticker": "TTWO", "Montant (€)": 5, "Fréquence": "1x / semaine"},
    {"Action": "Saint-Gobain", "Ticker": "SGO.PA", "Montant (€)": 2, "Fréquence": "1x / 2 semaines"},
    {"Action": "Burberry", "Ticker": "BRBY.L", "Montant (€)": 5, "Fréquence": "1x / semaine"},
    {"Action": "MSCI India", "Ticker": "CIN.PA", "Montant (€)": 2, "Fréquence": "1x / 2 semaines"},
    {"Action": "Apple", "Ticker": "AAPL", "Montant (€)": 3, "Fréquence": "1x / semaine"},
    {"Action": "Dow Jones", "Ticker": "DIA", "Montant (€)": 3, "Fréquence": "1x / 2 semaines"},
    {"Action": "Microsoft", "Ticker": "MSFT", "Montant (€)": 5, "Fréquence": "2x / mois"},
    {"Action": "Future Defense", "Ticker": "NATO.PA", "Montant (€)": 6, "Fréquence": "1x / mois"},
    {"Action": "Air Liquide", "Ticker": "AI.PA", "Montant (€)": 8, "Fréquence": "1x / mois"},
    {"Action": "Nasdaq x3", "Ticker": "TQQQ", "Montant (€)": 9, "Fréquence": "1x / mois"},
    {"Action": "Véolia", "Ticker": "VIE.PA", "Montant (€)": 2, "Fréquence": "2x / mois"},
    {"Action": "World ex-USA", "Ticker": "ACWX", "Montant (€)": 7, "Fréquence": "1x / mois"},
    {"Action": "Palantir", "Ticker": "PLTR", "Montant (€)": 3, "Fréquence": "1x / semaine"},
    {"Action": "Gold (Or USD)", "Ticker": "GLD", "Montant (€)": 3, "Fréquence": "1x / semaine"},
    {"Action": "Alphabet (Google)", "Ticker": "GOOGL", "Montant (€)": 3, "Fréquence": "1x / semaine"},
]

MY_ADVICE = [
    {
        "date": "12 Janvier 2026",
        "ticker": "🇬🇧 Burberry (BRBY)",
        "titre": "Le pari du redressement (Turnaround)",
        "contenu": "Burberry est une marque iconique massacrée en bourse. Le luxe est cyclique. J'achète l'hypothèse d'un rachat ou d'un redressement.",
        "action": "🟢 Achat : 5€ / semaine"
    },
    {
        "date": "10 Janvier 2026",
        "ticker": "🇮🇳 MSCI India",
        "titre": "L'Inde : La nouvelle locomotive",
        "contenu": "Démographie explosive, croissance à 7%. C'est la Chine d'il y a 20 ans. Incontournable pour diversifier.",
        "action": "🟢 Renforcement"
    },
    {
        "date": "03 Janvier 2026",
        "ticker": "🇺🇸 Palantir (PLTR)",
        "titre": "L'IA appliquée au réel",
        "contenu": "Leur logiciel AIP permet aux entreprises d'utiliser vraiment l'IA. Croissance folle, forte volatilité mais gros potentiel.",
        "action": "🚀 Conviction : 3€ / semaine"
    }
]

# -----------------------------------------------------------------------------
# 4. FONCTIONS OPTIMISÉES (STABILITÉ + VITESSE)
# -----------------------------------------------------------------------------

# Cache 1h pour les news
@st.cache_data(ttl=3600)
def get_market_news():
    try:
        rss_url = "https://news.google.com/rss/search?q=Bourse+Economie&hl=fr&gl=FR&ceid=FR:fr"
        response = requests.get(rss_url, timeout=4)
        root = ET.fromstring(response.content)
        news = []
        for item in root.findall('./channel/item')[:6]:
            news.append({
                'title': item.find('title').text,
                'link': item.find('link').text,
                'source': "Actualité"
            })
        return news
    except: return []

# Cache 30 min pour les prix actuels (METHODE BATCH - TRÈS RAPIDE)
@st.cache_data(ttl=1800)
def get_batch_data_1mo():
    """Télécharge 1 mois de données pour TOUS les tickers d'un coup."""
    tickers = list(TICKERS_TRACKER.values())
    try:
        # On télécharge tout d'un coup pour éviter 17 appels API
        data = yf.download(tickers, period="1mo", group_by='ticker', progress=False, threads=False)
        return data
    except: return None

# Cache 4h pour le Backtest (Lourd)
@st.cache_data(ttl=14400)
def compute_backtest_robust(plan_df):
    plan_df["Budget_Ligne"] = plan_df["Montant (€)"] * plan_df["Fréquence"].map(FREQ_MAP).fillna(1.0)
    total = plan_df["Budget_Ligne"].sum()
    if total == 0: return None
    plan_df["Poids"] = plan_df["Budget_Ligne"] / total
    
    tickers = plan_df["Ticker"].unique().tolist()
    api_tickers = list(set(tickers + ["^GSPC"]))
    
    try:
        # Téléchargement optimisé
        raw = yf.download(api_tickers, period="5y", progress=False, threads=False, auto_adjust=True)
        # Gestion multi-index complexe de yfinance
        if isinstance(raw.columns, pd.MultiIndex):
            # On essaie d'extraire 'Close' proprement
            try: data = raw['Close']
            except: data = raw.xs('Close', axis=1, level=0, drop_level=True)
        else:
            data = raw
            
        data = data.ffill().dropna()
        if data.empty: return None
        
        # Calcul Portefeuille
        # Base 100 pour chaque action
        normalized = data.apply(lambda x: x / x.iloc[0] * 100)
        
        # Construction indice pondéré
        portfolio = pd.Series(0, index=normalized.index)
        for _, row in plan_df.iterrows():
            t = row['Ticker']
            if t in normalized.columns:
                portfolio += normalized[t] * row['Poids']
                
        sp500 = normalized.get('^GSPC', None)
        return portfolio, sp500
    except Exception as e:
        return None, None

def calculate_dca(initial, monthly, years, rate):
    r = (1 + rate/100)**(1/12) - 1
    data = []
    val = initial
    invested = initial
    for y in range(years + 1):
        data.append({"Année": y, "Portfolio": round(val), "Investi": round(invested)})
        if y < years:
            for _ in range(12):
                val = val * (1 + r) + monthly
                invested += monthly
    return pd.DataFrame(data)

# -----------------------------------------------------------------------------
# 5. SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Menu", ["Suivi des Marchés", "Simulateur Futur", "🔙 Backtest & Performance", "💡 Conseils"])
st.sidebar.markdown("---")

st.sidebar.header("📰 Actualités")
news = get_market_news()
if news:
    for n in news:
        st.sidebar.markdown(f"<div class='news-card'><a href='{n['link']}' target='_blank' class='news-link'>{n['title']}</a></div>", unsafe_allow_html=True)
else:
    st.sidebar.caption("Chargement...")

st.sidebar.markdown("---")
st.sidebar.markdown("[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/)")

# -----------------------------------------------------------------------------
# 6. PAGES
# -----------------------------------------------------------------------------

# --- PAGE 1: SUIVI (RESTITUÉE AVEC GRAPHIQUES) ---
if page == "Suivi des Marchés":
    st.header("📊 Suivi des Cours (1 Mois)")
    
    # Chargement unique des données
    with st.spinner("Récupération des cours..."):
        batch_data = get_batch_data_1mo()
    
    if batch_data is not None:
        # On affiche en grilles de 3 colonnes
        cols = st.columns(3)
        tickers_list = list(TICKERS_TRACKER.items())
        
        for idx, (name, ticker) in enumerate(tickers_list):
            with cols[idx % 3]:
                # Extraction des données pour ce ticker spécifique
                try:
                    # Gestion du format complexe de yfinance (parfois DataFrame, parfois Series)
                    if isinstance(batch_data.columns, pd.MultiIndex):
                        try:
                            # Essai 1 : Accès direct par Ticker
                            stock_df = batch_data[ticker]
                        except KeyError:
                            continue # Ticker pas trouvé
                    else:
                        stock_df = batch_data # Fallback si 1 seul ticker
                    
                    # On s'assure d'avoir la colonne Close ou Adj Close
                    if 'Close' in stock_df.columns:
                        series = stock_df['Close']
                    elif 'Adj Close' in stock_df.columns:
                        series = stock_df['Adj Close']
                    else:
                        series = stock_df # Si c'est déjà une Série
                    
                    # Nettoyage
                    series = series.dropna()
                    
                    if not series.empty:
                        last = series.iloc[-1]
                        prev = series.iloc[-2]
                        delta = (last - prev) / prev * 100
                        
                        st.metric(label=name, value=f"{last:.2f}", delta=f"{delta:+.2f}%")
                        # Petit graphique (Sparkline)
                        st.line_chart(series, height=100)
                    else:
                        st.warning(f"{name}: Pas de données")
                except Exception as e:
                    # On continue même si une action plante pour ne pas casser la page
                    st.caption(f"Erreur données: {name}")
    else:
        st.error("Impossible de récupérer les cours (Yahoo Finance sature). Réessayez plus tard.")

# --- PAGE 2: SIMULATEUR ---
elif page == "Simulateur Futur":
    st.header("🚀 Simulateur DCA")
    c1, c2 = st.columns(2)
    with c1:
        monthly = st.number_input("Investissement Mensuel (€)", value=200, step=10)
        years = st.slider("Années", 5, 40, 20)
    with c2:
        rate = st.slider("Rendement annuel (%)", 2, 15, 8)
        initial = st.number_input("Capital départ (€)", value=0)
        
    df = calculate_dca(initial, monthly, years, rate)
    final = df.iloc[-1]['Portfolio']
    gain = final - df.iloc[-1]['Investi']
    
    st.metric("Capital Final", f"{final:,.0f} €", delta=f"Gains: {gain:,.0f} €")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Année'], y=df['Portfolio'], fill='tozeroy', name='Capital', line=dict(color='#00CC96')))
    fig.add_trace(go.Scatter(x=df['Année'], y=df['Investi'], fill='tozeroy', name='Versé', line=dict(color='#636EFA')))
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 3: BACKTEST ---
elif page == "🔙 Backtest & Performance":
    st.header("⏳ Voyage dans le temps (5 ans)")
    st.info("Le calcul se lance manuellement pour économiser les ressources.")
    
    if st.button("Lancer la simulation"):
        with st.spinner("Téléchargement de l'historique complet..."):
            pf, sp500 = compute_backtest_robust(pd.DataFrame(DEFAULT_PLAN))
            
            if pf is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=pf.index, y=pf, name='BoussiBroke', line=dict(color='#00CC96', width=3)))
                if sp500 is not None:
                    fig.add_trace(go.Scatter(x=sp500.index, y=sp500, name='S&P 500', line=dict(color='gray', dash='dot')))
                
                fig.update_layout(title="Base 100 (5 ans)", yaxis_title="Valeur")
                st.plotly_chart(fig, use_container_width=True)
                
                perf = pf.iloc[-1] - 100
                st.success(f"Performance Totale : +{perf:.1f}%")
            else:
                st.error("Données indisponibles. Réessayez plus tard.")

# --- PAGE 4: CONSEILS ---
elif page == "💡 Conseils":
    st.header("💡 L'avis de BoussiBroke")
    for a in MY_ADVICE:
        st.markdown(f"""
        <div class="advice-card">
            <div class="advice-date">{a['date']} <span class="advice-ticker">{a['ticker']}</span></div>
            <div class="advice-title">{a['titre']}</div>
            <div class="advice-content">{a['contenu']}</div>
            <div class="advice-action">{a['action']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div class="footer-cta">
    <h3>🚀 Passez à l'action !</h3>
    <p>Pour investir sans frais :</p>
    <a href="https://refnocode.trade.re/nvmzgmsh" target="_blank" class="cta-button">Ouvrir un compte Trade Republic 🎁</a>
</div>
""", unsafe_allow_html=True)

# Hack SEO silencieux
try:
    components.html(f"""<script>var meta=document.createElement('meta');meta.name="google-site-verification";meta.content="1LsUrDCW7NK4ag6jlsjBUk6qw-DPBdv9uq1NXQ9Z1nU";document.getElementsByTagName('head')[0].appendChild(meta);</script>""", height=0)
except: pass
