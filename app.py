import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & STYLE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BoussiBroke Investissement",
    page_icon="📈",
    layout="wide"
)

# CSS CORRIGÉ POUR LE MODE SOMBRE
# On force la couleur du texte (#2c3e50 ou #000000) avec !important
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    h1 { color: #2c3e50; }
    
    /* --- METRIQUES (Cartes avec prix) --- */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    /* Force le titre en noir */
    div[data-testid="stMetric"] label { 
        color: #000000 !important; 
    }
    /* Force la valeur en noir */
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { 
        color: #000000 !important; 
    }
    
    /* --- SIDEBAR NEWS --- */
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
        color: #2c3e50 !important; /* Force le lien en foncé */
        font-weight: bold;
        font-size: 14px;
        display: block;
        margin-bottom: 4px;
    }
    a.news-link:hover { color: #00CC96 !important; }
    .news-meta { 
        font-size: 11px; 
        color: #666666 !important; /* Force le gris foncé */
        display: flex; 
        justify-content: space-between; 
    }

    /* --- CONSEILS (Cartes Avis) --- */
    .advice-card {
        background-color: white;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 10px;
        border-top: 5px solid #636EFA;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        color: #2c3e50 !important; /* Force le texte global en foncé */
    }
    .advice-card h3 {
        color: #2c3e50 !important; /* Titre en foncé */
        margin-top: 0;
    }
    .advice-card p {
        color: #333333 !important; /* Paragraphe en gris foncé */
    }
    .advice-date {
        color: #666666 !important;
        font-size: 0.9em;
        font-style: italic;
        margin-bottom: 10px;
    }
    .advice-tag {
        background-color: #e0f2f1;
        color: #00695c !important;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
    }

    /* --- FOOTER AFFILIATION --- */
    .footer-cta {
        margin-top: 50px;
        padding: 30px;
        background: linear-gradient(135deg, #ffffff 0%, #f0f2f6 100%);
        border-radius: 15px;
        text-align: center;
        border: 1px solid #d1d5db;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        color: #111111 !important; /* Force texte noir */
    }
    .footer-cta h3 {
        color: #111111 !important;
        margin-bottom: 10px;
    }
    .footer-cta p {
        color: #333333 !important;
    }
    .cta-button {
        display: inline-block;
        background-color: #111; 
        color: white !important;
        padding: 12px 25px;
        border-radius: 50px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 15px;
        transition: transform 0.2s;
    }
    .cta-button:hover {
        transform: scale(1.05);
        background-color: #333;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 BoussiBroke Investissement")
st.markdown("Bienvenue ! Données financières ajustées (dividendes inclus) et actualités en direct.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 2. DONNÉES & PARAMÈTRES
# -----------------------------------------------------------------------------

FREQ_MAP = {
    "1x / semaine": 4.33,
    "1x / 2 semaines": 2.16,
    "1x / mois": 1.0,
    "2x / mois": 2.0,
    "3x / mois": 3.0
}

CURRENCY_MAP = {
    "CNDX.L": "USD", "BRK-B": "USD", "TTWO": "USD", "SGO.PA": "EUR",
    "BRBY.L": "GBP", "CIN.PA": "EUR", "AAPL": "USD", "DIA": "USD",
    "MSFT": "USD", "NATO.PA": "EUR", "AI.PA": "EUR", "TQQQ": "USD",
    "VIE.PA": "EUR", "ACWX": "USD",
    "PLTR": "USD", "GLD": "USD", "GOOGL": "USD"
}

TICKERS_TRACKER = {
    "🇺🇸 Nasdaq 100 (iShares)": "CNDX.L", 
    "🇺🇸 Berkshire Hathaway B": "BRK-B",
    "🇺🇸 Take-Two Interactive": "TTWO",
    "🇫🇷 Saint-Gobain": "SGO.PA",
    "🇬🇧 Burberry Group": "BRBY.L",
    "🇮🇳 MSCI India (Amundi)": "CIN.PA",
    "🇺🇸 Apple": "AAPL",
    "🇺🇸 Dow Jones Ind.": "DIA",
    "🇺🇸 Microsoft": "MSFT",
    "🇪🇺 Future of Defense": "NATO.PA",
    "🇫🇷 Air Liquide": "AI.PA",
    "🇺🇸 Nasdaq Levier x3": "TQQQ",
    "🇫🇷 Véolia": "VIE.PA",
    "🌍 World ex-USA": "ACWX",
    "🇺🇸 Palantir": "PLTR",
    "🟡 Gold (Or USD)": "GLD",
    "🇺🇸 Alphabet (Google)": "GOOGL"
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
        "date": "03 Janvier 2026",
        "titre": "Pourquoi j'achète du Palantir (PLTR) maintenant ?",
        "tag": "Tech / IA",
        "contenu": """
        Palantir vient de signer un contrat majeur avec le gouvernement. L'analyse technique montre un support solide.
        Je pense que l'IA n'est pas une bulle mais une révolution industrielle.
        **Ma décision :** J'augmente ma position de 3€/semaine.
        """,
        "lien": "https://www.palantir.com"
    },
    {
        "date": "15 Décembre 2025",
        "titre": "L'Or : Ma protection contre l'inflation",
        "tag": "Valeur Refuge",
        "contenu": """
        Avec les taux directeurs qui bougent, l'or reste une valeur sûre. 
        J'utilise l'ETF GLD pour ne pas avoir à stocker des lingots chez moi !
        C'est un bon moyen de diversifier hors de la Tech.
        """
    }
]

# -----------------------------------------------------------------------------
# 3. FONCTIONS UTILITAIRES
# -----------------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_stock_data(ticker_symbol, period="5y"):
    try:
        stock = yf.Ticker(ticker_symbol)
        history = stock.history(period=period, auto_adjust=True)
        if history.empty: return None
        return history
    except: return None

@st.cache_data(ttl=900) 
def get_market_news():
    rss_url = "https://news.google.com/rss/search?q=Bourse+Economie&hl=fr&gl=FR&ceid=FR:fr"
    news_list = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(rss_url, headers=headers, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall('./channel/item')[:8]:
                title = item.find('title').text if item.find('title') is not None else "Pas de titre"
                link = item.find('link').text if item.find('link') is not None else "#"
                source_name = "Actualité"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source_name = parts[1]
                news_list.append({'title': title, 'link': link, 'publisher': source_name})
        return news_list
    except: return []

@st.cache_data(ttl=600)
def compute_backtest_robust(plan_df, years=5):
    plan_df["Budget_Ligne"] = plan_df["Montant (€)"] * plan_df["Fréquence"].map(FREQ_MAP).fillna(1.0)
    total_budget = plan_df["Budget_Ligne"].sum()
    if total_budget == 0: return None
    plan_df["Poids"] = plan_df["Budget_Ligne"] / total_budget

    tickers = plan_df["Ticker"].unique().tolist()
    tickers_api = list(set(tickers + ["EURUSD=X", "EURGBP=X"]))

    try:
        raw_data = yf.download(tickers_api, period=f"{years}y", progress=False, auto_adjust=True)
        if isinstance(raw_data.columns, pd.MultiIndex):
            if 'Close' in raw_data.columns.get_level_values(0): data = raw_data['Close']
            elif 'Adj Close' in raw_data.columns.get_level_values(0): data = raw_data['Adj Close']
            else: data = raw_data.droplevel(0, axis=1)
        else:
            data = raw_data['Close'] if 'Close' in raw_data else raw_data
        data = data.ffill()
    except: return None

    portfolio_curve = pd.Series(0.0, index=data.index)
    valid_components = 0
    start_dates = []

    for idx, row in plan_df.iterrows():
        ticker = row["Ticker"]
        weight = row["Poids"]
        currency = CURRENCY_MAP.get(ticker, "EUR")
        if ticker in data.columns:
            series = data[ticker].copy()
            if currency == "USD" and "EURUSD=X" in data.columns: series = series / data["EURUSD=X"]
            elif currency == "GBP" and "EURGBP=X" in data.columns: series = series / data["EURGBP=X"]
            
            first_idx = series.first_valid_index()
            if first_idx:
                start_dates.append(first_idx)
                if series.iloc[-1] > 0:
                    normalized = (series / series.iloc[-1]) 
                    portfolio_curve = portfolio_curve.add(normalized * weight, fill_value=0)
                    valid_components += 1

    if valid_components == 0 or not start_dates: return None
    global_start_date = max(start_dates)
    final_curve = portfolio_curve[global_start_date:]
    if not final_curve.empty and final_curve.iloc[0] > 0:
        final_curve = (final_curve / final_curve.iloc[0]) * 100
        return final_curve
    return None

def calculate_projection_table(initial, monthly_amount, rate):
    rate_monthly = (1 + rate/100)**(1/12) - 1
    horizons = {"1 Jour": 1/30, "1 Semaine": 1/4.33, "1 Mois": 1, "6 Mois": 6, "1 An": 12, "3 Ans": 36, "5 Ans": 60, "10 Ans": 120}
    results = []
    for label, months in horizons.items():
        fv_initial = initial * (1 + rate_monthly)**months
        if rate_monthly == 0: fv_series = monthly_amount * months
        else: fv_series = monthly_amount * ((1 + rate_monthly)**months - 1) / rate_monthly
        total_val = fv_initial + fv_series
        total_invested = initial + (monthly_amount * months)
        results.append({"Période": label, "Total Versé (€)": total_invested, "Valeur Estimée (€)": total_val, "Plus-Value (€)": total_val - total_invested})
    return pd.DataFrame(results)

def calculate_dca_curve(initial, monthly_amount, years, rate):
    rate_monthly = (1 + rate/100)**(1/12) - 1
    data = []
    current_portfolio = initial
    total_invested = initial
    for year in range(years + 1):
        data.append({"Année": year, "Total Investi": round(total_invested, 2), "Valeur Portefeuille": round(current_portfolio, 2)})
        if year < years:
            for _ in range(12):
                current_portfolio = current_portfolio * (1 + rate_monthly) + monthly_amount
                total_invested += monthly_amount
    return pd.DataFrame(data)

# -----------------------------------------------------------------------------
# 4. INTERFACE SIDEBAR & NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Menu :", ["Suivi des Marchés", "Simulateur Futur", "🔙 Backtest & Performance", "💡 Conseils & Tendances"])
st.sidebar.markdown("---")

# Section Soutien (Ko-Fi)
st.sidebar.header("☕ Soutenir le projet")
st.sidebar.markdown("[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/)") 

st.sidebar.markdown("---")
st.sidebar.header("📰 Les Échos des Marchés")

news_data = get_market_news()
if news_data:
    for news in news_data:
        st.sidebar.markdown(
            f"""
            <div class="news-card">
                <a href="{news['link']}" target="_blank" class="news-link">{news['title']}</a>
                <div class="news-meta">
                    <span>{news['publisher']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.sidebar.caption("Actualisation...")
    if st.sidebar.button("Réessayer"):
        st.cache_data.clear()

# -----------------------------------------------------------------------------
# 5. PAGE : SUIVI DES MARCHÉS
# -----------------------------------------------------------------------------
if page == "Suivi des Marchés":
    st.header("📊 Suivi des Cours en Direct")
    
    if st.button("🔄 Actualiser les données maintenant"):
        st.cache_data.clear()
        
    selected_indices = st.multiselect("Sélectionner les actifs :", list(TICKERS_TRACKER.keys()), default=["🇺🇸 Palantir", "🟡 Gold (Or USD)"])
    
    if selected_indices:
        cols = st.columns(len(selected_indices))
        fig = go.Figure()
        for idx, name in enumerate(selected_indices):
            ticker = TICKERS_TRACKER[name]
            data = get_stock_data(ticker)
            if data is not None:
                last_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2]
                day_change = ((last_price - prev_price) / prev_price) * 100
                with cols[idx]:
                    st.metric(label=name, value=f"{last_price:,.2f}", delta=f"{day_change:.2f}%")
                
                base_val = data['Close'].iloc[0]
                normalized = (data['Close'] / base_val) * 100
                fig.add_trace(go.Scatter(x=data.index, y=normalized, name=name))
        
        fig.update_layout(height=500, title="Comparaison Base 100 (Dividendes inclus)", yaxis_title="Base 100")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. PAGE : SIMULATEUR FUTUR
# -----------------------------------------------------------------------------
elif page == "Simulateur Futur":
    st.header("🚀 Plan d'Achat & Futur")
    df_base = pd.DataFrame(DEFAULT_PLAN)
    edited_df = st.data_editor(
        df_base,
        column_config={
            "Action": st.column_config.TextColumn("Action", disabled=True),
            "Ticker": st.column_config.TextColumn("Ticker", disabled=True),
            "Montant (€)": st.column_config.NumberColumn("Montant (€)", format="%d €"),
            "Fréquence": st.column_config.SelectboxColumn("Fréquence", options=list(FREQ_MAP.keys()), required=True)
        },
        hide_index=True, use_container_width=True, num_rows="fixed"
    )

    total_monthly = sum([row["Montant (€)"] * FREQ_MAP.get(row["Fréquence"], 1.0) for i, row in edited_df.iterrows()])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.success(f"💰 **Mensuel : {int(total_monthly)} €**")
        monthly_inv = st.number_input("Retenu (€)", value=int(total_monthly))
        initial_inv = st.number_input("Départ (€)", value=0)
        rate = st.slider("Rendement (%)", 5, 15, 9)
        years = st.slider("Années", 5, 30, 15)

    with col2:
        df_graph = calculate_dca_curve(initial_inv, monthly_inv, years, rate)
        final = df_graph.iloc[-1]["Valeur Portefeuille"]
        st.subheader(f"Final: {final:,.0f} €")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_graph["Année"], y=df_graph["Valeur Portefeuille"], fill='tozeroy', name='Portefeuille', line=dict(color='#00CC96')))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📅 Détail des gains")
    df_proj = calculate_projection_table(initial_inv, monthly_inv, rate)
    try:
        st.dataframe(df_proj.style.format({"Total Versé (€)": "{:,.0f} €", "Valeur Estimée (€)": "{:,.0f} €", "Plus-Value (€)": "{:+,.0f} €"}).background_gradient(subset=["Plus-Value (€)"], cmap="Greens"), use_container_width=True, hide_index=True)
    except:
        st.dataframe(df_proj.style.format({"Total Versé (€)": "{:,.0f} €", "Valeur Estimée (€)": "{:,.0f} €", "Plus-Value (€)": "{:+,.0f} €"}), use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# 7. PAGE : BACKTEST (S&P500)
# -----------------------------------------------------------------------------
elif page == "🔙 Backtest & Performance":
    st.header("⏳ Voyage dans le temps (Backtest)")
    st.markdown("Simulation basée sur votre panier actuel (BoussiBroke) vs **S&P 500**.")
    st.info("ℹ️ Performance 'Total Return' (Dividendes réinvestis).")

    with st.spinner("Récupération des données ajustées (Dividendes inclus)..."):
        df_bt = pd.DataFrame(DEFAULT_PLAN)
        portfolio_curve = compute_backtest_robust(df_bt, years=5)
        
        # Benchmark S&P 500
        sp500_raw = get_stock_data("^GSPC", period="5y")
        
        if portfolio_curve is not None and sp500_raw is not None:
            if portfolio_curve.index.tz is not None: portfolio_curve.index = portfolio_curve.index.tz_localize(None)
            if sp500_raw.index.tz is not None: sp500_raw.index = sp500_raw.index.tz_localize(None)

            start_date = portfolio_curve.index[0]
            sp500_aligned = sp500_raw['Close'][start_date:]
            
            if not sp500_aligned.empty:
                sp500_norm = (sp500_aligned / sp500_aligned.iloc[0]) * 100
                
                perf_pf = portfolio_curve.iloc[-1] - 100
                perf_sp500 = sp500_norm.iloc[-1] - 100
                
                k1, k2 = st.columns(2)
                k1.metric("BoussiBroke", f"+{perf_pf:.1f}%")
                k2.metric("S&P 500", f"+{perf_sp500:.1f}%")
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=portfolio_curve.index, y=portfolio_curve, name='BoussiBroke', line=dict(color='#00CC96', width=3)))
                fig.add_trace(go.Scatter(x=sp500_norm.index, y=sp500_norm, name='S&P 500', line=dict(color='gray', dash='dot')))
                fig.update_layout(title="Performance Historique (Base 100)", yaxis_title="Base 100")
                st.plotly_chart(fig, use_container_width=True)
            else: st.error("Erreur alignement dates S&P 500.")
        else: st.error("Impossible de construire le backtest. Données manquantes.")

# -----------------------------------------------------------------------------
# 8. PAGE : CONSEILS (NOUVEAU)
# -----------------------------------------------------------------------------
elif page == "💡 Conseils & Tendances":
    st.header("💡 L'avis de BoussiBroke")
    st.markdown("Analyses personnelles, tendances à surveiller et articles marquants.")
    
    for advice in MY_ADVICE:
        with st.container():
            st.markdown(f"""
            <div class="advice-card">
                <div class="advice-date">{advice['date']}</div>
                <h3>{advice['titre']} <span class="advice-tag">{advice['tag']}</span></h3>
                <p>{advice['contenu']}</p>
            </div>
            """, unsafe_allow_html=True)
            if "lien" in advice:
                st.markdown(f"👉 [Lire l'article source ou voir le graphique]({advice['lien']})")

    st.warning("⚠️ **Avertissement :** Je partage ici mon avis personnel. Ce ne sont pas des conseils financiers.")

# -----------------------------------------------------------------------------
# 9. PIED DE PAGE : AFFILIATION (Affiché sur TOUTES les pages)
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div class="footer-cta">
    <h3>🚀 Passez à l'action !</h3>
    <p>Pour mettre en place cette stratégie d'investissement programmée (DCA) sans frais, j'utilise <strong>Trade Republic</strong>.</p>
    <a href="https://refnocode.trade.re/nvmzgmsh" target="_blank" class="cta-button">
        Ouvrir un compte & recevoir une action offerte 🎁
    </a>
    <p style="font-size: 12px; margin-top: 15px; color: #666;">
        *Lien affilié : Cela soutient le développement de BoussiBroke sans coût pour vous.
    </p>
</div>
""", unsafe_allow_html=True)
