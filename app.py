import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & STYLE (CORRIGÉ POUR LISIBILITÉ)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BoussiBroke Investissement",
    page_icon="📈",
    layout="wide"
)

# CSS CORRIGÉ : On force le texte en noir dans les boites blanches
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    h1 { color: #2c3e50; }
    
    /* Style des métriques (cartes) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* FORCE LE TEXTE EN NOIR À L'INTÉRIEUR DES MÉTRIQUES */
    div[data-testid="stMetric"] label {
        color: #000000 !important; /* Le titre (ex: Air Liquide) */
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #000000 !important; /* La valeur (ex: 157.00) */
    }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
        /* On laisse la couleur par défaut (vert/rouge) pour le pourcentage */
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 BoussiBroke Investissement")
st.markdown("Bienvenue ! Voici les conseils d'un amateur boursier. Ce tableau de bord permet de suivre les cours, simuler votre richesse future et vérifier les performances passées.")
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

# Mapping devises
CURRENCY_MAP = {
    "CNDX.L": "USD", "BRK-B": "USD", "TTWO": "USD", "SGO.PA": "EUR",
    "BRBY.L": "GBP", "CIN.PA": "EUR", "AAPL": "USD", "DIA": "USD",
    "MSFT": "USD", "NATO.PA": "EUR", "AI.PA": "EUR", "TQQQ": "USD",
    "VIE.PA": "EUR", "ACWX": "USD"
}

# Liste Tracker
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
    "🌍 World ex-USA": "ACWX"
}

# Plan par défaut
DEFAULT_PLAN = [
    {"Action": "Nasdaq 100", "Ticker": "CNDX.L", "Montant (€)": 1, "Fréquence": "1x / semaine"},
    {"Action": "Berkshire B", "Ticker": "BRK-B", "Montant (€)": 2, "Fréquence": "1x / semaine"},
    {"Action": "Take-Two", "Ticker": "TTWO", "Montant (€)": 3, "Fréquence": "1x / semaine"},
    {"Action": "Saint-Gobain", "Ticker": "SGO.PA", "Montant (€)": 2, "Fréquence": "1x / 2 semaines"},
    {"Action": "Burberry", "Ticker": "BRBY.L", "Montant (€)": 1, "Fréquence": "1x / semaine"},
    {"Action": "MSCI India", "Ticker": "CIN.PA", "Montant (€)": 1, "Fréquence": "1x / 2 semaines"},
    {"Action": "Apple", "Ticker": "AAPL", "Montant (€)": 1, "Fréquence": "1x / semaine"},
    {"Action": "Dow Jones", "Ticker": "DIA", "Montant (€)": 2, "Fréquence": "1x / 2 semaines"},
    {"Action": "Microsoft", "Ticker": "MSFT", "Montant (€)": 1, "Fréquence": "2x / mois"},
    {"Action": "Future Defense", "Ticker": "NATO.PA", "Montant (€)": 1, "Fréquence": "1x / mois"},
    {"Action": "Air Liquide", "Ticker": "AI.PA", "Montant (€)": 1, "Fréquence": "1x / mois"},
    {"Action": "Nasdaq x3", "Ticker": "TQQQ", "Montant (€)": 2, "Fréquence": "1x / mois"},
    {"Action": "Véolia", "Ticker": "VIE.PA", "Montant (€)": 2, "Fréquence": "2x / mois"},
    {"Action": "World ex-USA", "Ticker": "ACWX", "Montant (€)": 3, "Fréquence": "1x / mois"},
]

# -----------------------------------------------------------------------------
# 3. FONCTIONS UTILITAIRES
# -----------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_stock_data(ticker_symbol, period="5y"):
    """Récupère les données brutes pour le tracker."""
    try:
        stock = yf.Ticker(ticker_symbol)
        history = stock.history(period=period)
        if history.empty: return None
        return history
    except: return None

@st.cache_data(ttl=3600)
def compute_backtest_robust(plan_df, years=5):
    """
    Version ultra-robuste du backtest.
    Gère les multi-index de yfinance et les tickers manquants.
    """
    # 1. Calcul des poids cibles
    plan_df["Budget_Ligne"] = plan_df["Montant (€)"] * plan_df["Fréquence"].map(FREQ_MAP).fillna(1.0)
    total_budget = plan_df["Budget_Ligne"].sum()
    if total_budget == 0: return None
    plan_df["Poids"] = plan_df["Budget_Ligne"] / total_budget

    # 2. Préparation des Tickers
    tickers = plan_df["Ticker"].unique().tolist()
    # On ajoute les devises
    tickers_api = list(set(tickers + ["EURUSD=X", "EURGBP=X"]))

    try:
        # Téléchargement en masse
        raw_data = yf.download(tickers_api, period=f"{years}y", progress=False)
        
        # --- CORRECTION CRITIQUE YFINANCE ---
        # Si yfinance renvoie un MultiIndex (ex: ('Close', 'AAPL')), on ne garde que 'Close'
        if isinstance(raw_data.columns, pd.MultiIndex):
            try:
                # On essaie de récupérer le niveau 'Close' ou 'Adj Close'
                if 'Close' in raw_data.columns.get_level_values(0):
                    data = raw_data['Close']
                elif 'Adj Close' in raw_data.columns.get_level_values(0):
                    data = raw_data['Adj Close']
                else:
                    # Fallback : on prend le niveau 0 si structure bizarre
                    data = raw_data.droplevel(0, axis=1) 
            except:
                data = raw_data # On prie
        else:
            data = raw_data['Close'] if 'Close' in raw_data else raw_data

        # Nettoyage de base (Forward Fill pour les jours fériés)
        data = data.ffill()
        
    except Exception as e:
        return None

    # 3. Construction de la courbe composite
    # On commence à 0 et on additionne les contributions pondérées
    portfolio_curve = pd.Series(0.0, index=data.index)
    valid_components = 0
    
    # Pour déterminer quand commencer le graphique (quand on a assez de données)
    start_dates = []

    for idx, row in plan_df.iterrows():
        ticker = row["Ticker"]
        weight = row["Poids"]
        currency = CURRENCY_MAP.get(ticker, "EUR")

        if ticker in data.columns:
            series = data[ticker].copy()
            
            # Gestion Devises simple
            if currency == "USD" and "EURUSD=X" in data.columns:
                series = series / data["EURUSD=X"]
            elif currency == "GBP" and "EURGBP=X" in data.columns:
                series = series / data["EURGBP=X"]

            # On note quand cette action commence à avoir des données
            first_idx = series.first_valid_index()
            if first_idx:
                start_dates.append(first_idx)
                
                # Normalisation base 100 à la fin pour aligner les échelles
                if series.iloc[-1] > 0:
                    normalized = (series / series.iloc[-1]) 
                    # On ajoute au panier global
                    portfolio_curve = portfolio_curve.add(normalized * weight, fill_value=0)
                    valid_components += 1

    if valid_components == 0 or not start_dates:
        return None

    # 4. Coupure propre du graphique
    # On prend la date la plus récente parmi les dates de début (le facteur limitant)
    # Ex: Si tout commence en 2020 mais NATO.PA en 2023, on coupe en 2023.
    global_start_date = max(start_dates)
    
    # On coupe
    final_curve = portfolio_curve[global_start_date:]
    
    # On remet en base 100 au début de la période visible
    if not final_curve.empty and final_curve.iloc[0] > 0:
        final_curve = (final_curve / final_curve.iloc[0]) * 100
        return final_curve
    else:
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
# 4. INTERFACE SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Menu :", ["Suivi des Marchés", "Simulateur Futur", "🔙 Backtest & Performance"])
st.sidebar.markdown("---")
st.sidebar.header("📰 Actualités Éco")
news_items = [{"titre": "La FED annonce une pause", "impact": "Positif"}, {"titre": "Secteur Tech en hausse", "impact": "Positif"}]
for news in news_items:
    st.sidebar.markdown(f"**{news['titre']}**")
    st.sidebar.markdown(f":green[Impact: {news['impact']}]")
    st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# 5. PAGE : SUIVI DES MARCHÉS
# -----------------------------------------------------------------------------
if page == "Suivi des Marchés":
    st.header("📊 Suivi des Cours en Direct")
    selected_indices = st.multiselect("Sélectionner les actifs :", list(TICKERS_TRACKER.keys()), default=["🇺🇸 Apple", "🇫🇷 Air Liquide"])
    
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
                
                # Graphique
                base_val = data['Close'].iloc[0]
                normalized = (data['Close'] / base_val) * 100
                fig.add_trace(go.Scatter(x=data.index, y=normalized, name=name))
        
        fig.update_layout(height=500, title="Comparaison Base 100", yaxis_title="Base 100")
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
    # Affichage sécurisé (sans matplotlib obligatoire)
    st.dataframe(df_proj.style.format({"Total Versé (€)": "{:,.0f} €", "Valeur Estimée (€)": "{:,.0f} €", "Plus-Value (€)": "{:+,.0f} €"}), use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# 7. PAGE : BACKTEST (CORRIGÉE & ROBUSTE)
# -----------------------------------------------------------------------------
elif page == "🔙 Backtest & Performance":
    st.header("⏳ Voyage dans le temps (Backtest)")
    st.markdown("Simulation basée sur votre panier actuel (BoussiBroke) vs CAC 40.")
    st.info("ℹ️ Le graphique démarre automatiquement à la date de l'action la plus récente de votre portefeuille.")

    with st.spinner("Récupération et alignement des données historiques..."):
        # On utilise le plan par défaut pour le backtest
        df_bt = pd.DataFrame(DEFAULT_PLAN)
        portfolio_curve = compute_backtest_robust(df_bt, years=5)
        
        # Benchmark CAC40
        cac40_raw = get_stock_data("^FCHI", period="5y")
        
        if portfolio_curve is not None and cac40_raw is not None:
            # Alignement CAC40 sur la même date de départ
            start_date = portfolio_curve.index[0]
            cac40_aligned = cac40_raw['Close'][start_date:]
            
            # Base 100
            if not cac40_aligned.empty:
                cac40_norm = (cac40_aligned / cac40_aligned.iloc[0]) * 100
                
                # KPIs
                perf_pf = portfolio_curve.iloc[-1] - 100
                perf_cac = cac40_norm.iloc[-1] - 100
                
                k1, k2 = st.columns(2)
                k1.metric("BoussiBroke", f"+{perf_pf:.1f}%")
                k2.metric("CAC 40", f"+{perf_cac:.1f}%")
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=portfolio_curve.index, y=portfolio_curve, name='BoussiBroke', line=dict(color='#00CC96', width=3)))
                fig.add_trace(go.Scatter(x=cac40_norm.index, y=cac40_norm, name='CAC 40', line=dict(color='gray', dash='dot')))
                fig.update_layout(title="Performance Historique (Base 100)", yaxis_title="Base 100")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Erreur alignement dates CAC40.")
        else:
            st.error("Impossible de construire le backtest. Une des actions bloque le téléchargement (souvent les tickers de Londres .L).")
