import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import datetime
import streamlit.components.v1 as components

# On importe les librairies lourdes dans un bloc sécurisé
try:
    import yfinance as yf
    import requests
    import xml.etree.ElementTree as ET
except ImportError:
    st.error("Erreur critique : Librairies manquantes. Vérifiez requirements.txt")
    st.stop()

# -----------------------------------------------------------------------------
# 1. CONFIGURATION (OBLIGATOIRE EN PREMIER)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BoussiBroke | Conseils Bourse",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. CSS (CORRECTIF VISUEL DÉFINITIF)
# -----------------------------------------------------------------------------
# On force le texte en NOIR (#000000) pour qu'il soit visible même si le navigateur est en mode sombre
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    h1, h2, h3 { color: #111111 !important; }
    p, span, div { color: #333333; }
    
    /* Force le fond blanc et texte noir pour les métriques */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    div[data-testid="stMetric"] label { color: #000000 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #000000 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] { font-weight: bold; }

    /* Cartes Conseils */
    .advice-card {
        background-color: white;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 10px;
        border-top: 5px solid #636EFA;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .advice-title { color: #000000 !important; font-size: 1.3em; font-weight: 800; }
    .advice-content { color: #333333 !important; line-height: 1.6; }
    .advice-date { color: #666 !important; font-size: 0.8em; font-style: italic; }
    
    /* Footer */
    .footer-cta {
        margin-top: 40px;
        padding: 25px;
        background: white;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #ddd;
    }
    .footer-cta h3 { color: #000 !important; }
    .cta-button {
        display: inline-block;
        background-color: #000;
        color: #fff !important;
        padding: 10px 20px;
        border-radius: 50px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. DONNÉES STATIQUES (Légères)
# -----------------------------------------------------------------------------
FREQ_MAP = {"1x / semaine": 4.33, "1x / 2 semaines": 2.16, "1x / mois": 1.0, "2x / mois": 2.0, "3x / mois": 3.0}
CURRENCY_MAP = {"CNDX.L": "USD", "BRK-B": "USD", "TTWO": "USD", "SGO.PA": "EUR", "BRBY.L": "GBP", "CIN.PA": "EUR", "AAPL": "USD", "DIA": "USD", "MSFT": "USD", "NATO.PA": "EUR", "AI.PA": "EUR", "TQQQ": "USD", "VIE.PA": "EUR", "ACWX": "USD", "PLTR": "USD", "GLD": "USD", "GOOGL": "USD"}

TICKERS_TRACKER = {
    "🇺🇸 Nasdaq 100": "CNDX.L", "🇺🇸 Berkshire B": "BRK-B", "🇺🇸 Take-Two": "TTWO", 
    "🇫🇷 Saint-Gobain": "SGO.PA", "🇬🇧 Burberry": "BRBY.L", "🇮🇳 MSCI India": "CIN.PA", 
    "🇺🇸 Apple": "AAPL", "🇺🇸 Dow Jones": "DIA", "🇺🇸 Microsoft": "MSFT", 
    "🇪🇺 Defense": "NATO.PA", "🇫🇷 Air Liquide": "AI.PA", "🇺🇸 Nasdaq x3": "TQQQ", 
    "🇫🇷 Véolia": "VIE.PA", "🌍 World ex-USA": "ACWX", "🇺🇸 Palantir": "PLTR", 
    "🟡 Or (Gold)": "GLD", "🇺🇸 Google": "GOOGL"
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
    {"date": "12 Jan 2026", "ticker": "🇬🇧 Burberry", "titre": "Le pari du redressement", "contenu": "Le luxe est cyclique. C'est un point d'entrée value rare.", "action": "🟢 Achat"},
    {"date": "10 Jan 2026", "ticker": "🇮🇳 MSCI India", "titre": "L'Inde > La Chine", "contenu": "Démographie et croissance PIB à 7%. L'avenir est là-bas.", "action": "🟢 Achat"},
    {"date": "03 Jan 2026", "ticker": "🇺🇸 Palantir", "titre": "La machine de guerre IA", "contenu": "Leur logiciel AIP est une révolution pour les entreprises.", "action": "🚀 Conviction"}
]

# -----------------------------------------------------------------------------
# 4. FONCTIONS SÉCURISÉES (Anti-Crash)
# -----------------------------------------------------------------------------

# Fonction très légère pour récupérer juste le prix actuel
@st.cache_data(ttl=600)
def get_current_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="5d")
        if not data.empty:
            return data['Close'].iloc[-1], data['Close'].iloc[-2]
    except: pass
    return None, None

# Fonction Backtest lourde (mise en cache longue durée)
@st.cache_data(ttl=14400)
def compute_backtest_heavy(plan_df):
    plan_df["Budget_Ligne"] = plan_df["Montant (€)"] * plan_df["Fréquence"].map(FREQ_MAP).fillna(1.0)
    total = plan_df["Budget_Ligne"].sum()
    if total == 0: return None
    plan_df["Poids"] = plan_df["Budget_Ligne"] / total
    
    tickers = plan_df["Ticker"].unique().tolist()
    # On ajoute S&P500 pour comparer
    tickers_api = list(set(tickers + ["^GSPC", "EURUSD=X", "EURGBP=X"]))
    
    try:
        # threads=False évite de surcharger la RAM du serveur gratuit
        data = yf.download(tickers_api, period="2y", progress=False, threads=False, auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
             # Simplification structure de données
             if 'Close' in data.columns.get_level_values(0): data = data['Close']
             else: data = data.droplevel(0, axis=1)
        
        data = data.ffill().dropna()
        if data.empty: return None
        
        # Calcul Portefeuille Simplifié (Indice base 100)
        # On fait une moyenne pondérée des performances relatives
        perf_df = data.apply(lambda x: x / x.iloc[0] * 100)
        
        # On reconstitue le portefeuille (approx)
        portfolio = pd.Series(0, index=perf_df.index)
        for idx, row in plan_df.iterrows():
            if row['Ticker'] in perf_df.columns:
                portfolio += perf_df[row['Ticker']] * row['Poids']
        
        return portfolio, perf_df.get('^GSPC', None)
        
    except Exception as e:
        return None, None

def calculate_dca_curve(initial, monthly, years, rate):
    rate_m = (1 + rate/100)**(1/12) - 1
    data = []
    curr = initial
    invested = initial
    for y in range(years + 1):
        data.append({"Année": y, "Valeur Portefeuille": round(curr, 2), "Total Investi": round(invested, 2)})
        if y < years:
            for _ in range(12):
                curr = curr * (1 + rate_m) + monthly
                invested += monthly
    return pd.DataFrame(data)

# -----------------------------------------------------------------------------
# 5. INTERFACE UTILISATEUR
# -----------------------------------------------------------------------------

st.sidebar.header("Navigation")
page = st.sidebar.radio("Menu", ["Suivi des Marchés", "Simulateur Futur", "🔙 Backtest (Sur demande)", "💡 Conseils"])
st.sidebar.markdown("---")
st.sidebar.caption("Données fournies par Yahoo Finance.")

# --- PAGE 1: SUIVI ---
if page == "Suivi des Marchés":
    st.header("📊 Suivi des Cours")
    selected = st.multiselect("Choisir les actifs :", list(TICKERS_TRACKER.keys()), default=["🇺🇸 Palantir", "🟡 Or (Gold)"])
    
    if st.button("🔄 Actualiser les prix"):
        st.cache_data.clear()
        
    if selected:
        cols = st.columns(len(selected))
        for i, name in enumerate(selected):
            ticker = TICKERS_TRACKER[name]
            price, prev = get_current_price(ticker)
            with cols[i]:
                if price:
                    delta = (price - prev) / prev * 100
                    st.metric(name, f"{price:.2f}", f"{delta:+.2f}%")
                else:
                    st.warning(f"{name}: N/A")

# --- PAGE 2: SIMULATEUR ---
elif page == "Simulateur Futur":
    st.header("🚀 Simulateur d'Intérêts Composés")
    c1, c2 = st.columns(2)
    with c1:
        monthly = st.number_input("Investissement Mensuel (€)", value=200, step=10)
        initial = st.number_input("Capital de départ (€)", value=0)
    with c2:
        rate = st.slider("Rendement annuel (%)", 2, 15, 8)
        years = st.slider("Durée (Années)", 5, 40, 20)
        
    df_sim = calculate_dca_curve(initial, monthly, years, rate)
    final_val = df_sim.iloc[-1]['Valeur Portefeuille']
    total_inv = df_sim.iloc[-1]['Total Investi']
    
    st.metric("Capital Final Estimé", f"{final_val:,.0f} €", delta=f"Plus-value: {final_val - total_inv:,.0f} €")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sim['Année'], y=df_sim['Valeur Portefeuille'], fill='tozeroy', name='Portefeuille', line=dict(color='#00CC96')))
    fig.add_trace(go.Scatter(x=df_sim['Année'], y=df_sim['Total Investi'], fill='tozeroy', name='Versé de votre poche', line=dict(color='#636EFA')))
    st.plotly_chart(fig, use_container_width=True)

# --- PAGE 3: BACKTEST ---
elif page == "🔙 Backtest (Sur demande)":
    st.header("⏳ Voyage dans le temps")
    st.info("Cliquez ci-dessous pour calculer la performance passée. (Cela peut prendre 10s)")
    
    # On ne lance le calcul QUE si l'utilisateur clique (évite le crash au démarrage)
    if st.button("Lancer le Backtest 5 ans"):
        with st.spinner("Téléchargement des données historiques..."):
            portf, sp500 = compute_backtest_heavy(pd.DataFrame(DEFAULT_PLAN))
            
            if portf is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=portf.index, y=portf, name='BoussiBroke', line=dict(color='#00CC96', width=3)))
                if sp500 is not None:
                    # Normalisation du SP500 pour qu'il commence à 100 comme le portefeuille
                    sp500_norm = sp500 / sp500.iloc[0] * 100
                    fig.add_trace(go.Scatter(x=sp500_norm.index, y=sp500_norm, name='S&P 500', line=dict(color='gray', dash='dot')))
                
                fig.update_layout(title="Performance Base 100 (2 ans)", yaxis_title="Base 100")
                st.plotly_chart(fig, use_container_width=True)
                
                perf = portf.iloc[-1] - 100
                st.success(f"Performance sur la période : +{perf:.1f}%")
            else:
                st.error("Données indisponibles actuellement. Yahoo finance limite peut-être les requêtes.")

# --- PAGE 4: CONSEILS ---
elif page == "💡 Conseils":
    st.header("💡 L'avis de BoussiBroke")
    for advice in MY_ADVICE:
        st.markdown(f"""
        <div class="advice-card">
            <div class="advice-date">{advice['date']}</div>
            <div class="advice-title">{advice['titre']} <span style="background:#e0f2f1; font-size:0.6em; padding:3px 8px; border-radius:10px; color:#00695c;">{advice['ticker']}</span></div>
            <div class="advice-content">{advice['contenu']}</div>
            <div class="advice-action">{advice['action']}</div>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FOOTER (Toujours visible)
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div class="footer-cta">
    <h3>🚀 Passez à l'action !</h3>
    <p>Pour mettre en place cette stratégie sans frais :</p>
    <a href="https://refnocode.trade.re/nvmzgmsh" target="_blank" class="cta-button">
        Ouvrir un compte Trade Republic 🎁
    </a>
</div>
""", unsafe_allow_html=True)

# Hack SEO silencieux en fin de fichier
try:
    components.html(f"""<script>var meta=document.createElement('meta');meta.name="google-site-verification";meta.content="1LsUrDCW7NK4ag6jlsjBUk6qw-DPBdv9uq1NXQ9Z1nU";document.getElementsByTagName('head')[0].appendChild(meta);</script>""", height=0)
except: pass
