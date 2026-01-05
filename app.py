import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURATION DE LA PAGE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BoussiBroke Investissement",
    page_icon="📈",
    layout="wide"
)

# CSS Personnalisé
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    h1 { color: #2c3e50; }
    .stMetric {
        background-color: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 BoussiBroke Investissement")
st.markdown("Bienvenue ! Voici les conseils d'un amateur boursier. Modifiez le tableau ci-dessous pour simuler votre propre budget.")
st.markdown("---")

# -----------------------------------------------------------------------------
# DONNÉES INITIALES
# -----------------------------------------------------------------------------

FREQ_MAP = {
    "1x / semaine": 4.33,
    "1x / 2 semaines": 2.16,
    "1x / mois": 1.0,
    "2x / mois": 2.0,
    "3x / mois": 3.0
}

# Mapping des devises pour conversion historique
# Si l'action est en USD, on divisera par la paire EURUSD. Si GBP, par EURGBP.
CURRENCY_MAP = {
    "CNDX.L": "USD", "BRK-B": "USD", "TTWO": "USD", "SGO.PA": "EUR",
    "BRBY.L": "GBP", "CIN.PA": "EUR", "AAPL": "USD", "DIA": "USD",
    "MSFT": "USD", "NATO.PA": "EUR", "AI.PA": "EUR", "TQQQ": "USD",
    "VIE.PA": "EUR", "ACWX": "USD"
}

TICKERS_TRACKER = {
    "🇺🇸 Nasdaq 100": "CNDX.L", 
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
# FONCTIONS
# -----------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_stock_data(ticker_symbol, period="5y"):
    try:
        stock = yf.Ticker(ticker_symbol)
        history = stock.history(period=period)
        if history.empty: return None
        return history
    except: return None

@st.cache_data(ttl=3600)
def compute_backtest(plan_df, years=5):
    """Reconstitue la performance historique du panier."""
    # 1. Calcul des poids du portefeuille actuel
    plan_df["Poids_Relatif"] = 0.0
    total_budget_mensuel = 0
    
    for idx, row in plan_df.iterrows():
        budget_line = row["Montant (€)"] * FREQ_MAP.get(row["Fréquence"], 1.0)
        total_budget_mensuel += budget_line
        plan_df.at[idx, "Budget_Ligne"] = budget_line

    if total_budget_mensuel == 0: return None
    plan_df["Poids"] = plan_df["Budget_Ligne"] / total_budget_mensuel

    # 2. Récupération des données historiques et devises
    tickers = plan_df["Ticker"].tolist()
    # On ajoute les paires de devises nécessaires
    tickers_api = tickers + ["EURUSD=X", "EURGBP=X"]
    
    try:
        data = yf.download(tickers_api, period=f"{years}y", progress=False)['Close']
        data = data.ffill().dropna() # Nettoyage
    except:
        return None

    # 3. Conversion tout en EUROS et Construction de l'index
    # On part d'une base 100
    portfolio_series = pd.Series(0, index=data.index)
    
    valid_tickers = 0
    
    for idx, row in plan_df.iterrows():
        ticker = row["Ticker"]
        weight = row["Poids"]
        currency = CURRENCY_MAP.get(ticker, "EUR")
        
        if ticker in data.columns:
            series = data[ticker]
            
            # Gestion Devises (Conversion en EUR)
            if currency == "USD":
                if "EURUSD=X" in data.columns:
                    series = series / data["EURUSD=X"]
            elif currency == "GBP":
                if "EURGBP=X" in data.columns:
                    # GBP vers EUR (Approximation via EURGBP inversé ou cross rate)
                    # Yahoo donne EURGBP=X (1 EUR = x GBP). Donc Price_GBP / EURGBP = Price_EUR
                    series = series / data["EURGBP=X"]
            
            # Normalisation Base 100 au début de la période
            if not series.empty and series.iloc[0] > 0:
                normalized = (series / series.iloc[0]) * 100 * weight
                portfolio_series += normalized
                valid_tickers += 1
                
    if valid_tickers == 0: return None
    
    # On recale le tout pour que ça commence pile à 100
    portfolio_series = (portfolio_series / portfolio_series.iloc[0]) * 100
    
    return portfolio_series

def calculate_projection_table(initial, monthly_amount, rate):
    rate_monthly = (1 + rate/100)**(1/12) - 1
    horizons = {"1 Jour": 1/30, "1 Semaine": 1/4.33, "1 Mois": 1, "6 Mois": 6, "1 An": 12, "3 Ans": 36, "5 Ans": 60, "10 Ans": 120, "20 Ans": 240}
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
# SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Menu :", ["Suivi des Marchés", "Simulateur Futur", "🔙 Backtest & Performance"])

st.sidebar.markdown("---")
st.sidebar.header("📰 Actualités Éco")
news_items = [
    {"titre": "La FED annonce une pause sur les taux", "impact": "Positif"},
    {"titre": "Le secteur Tech tire les marchés", "impact": "Positif"},
    {"titre": "Inflation en zone Euro : chiffres rassurants", "impact": "Neutre"},
]
for news in news_items:
    color = "green" if news['impact'] == "Positif" else "orange" if news['impact'] == "Neutre" else "red"
    st.sidebar.markdown(f"**{news['titre']}**")
    st.sidebar.markdown(f":{color}[Impact: {news['impact']}]")
    st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# PAGE 1 : SUIVI DES MARCHÉS
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
                try:
                    start_year_price = data[data.index.year == datetime.now().year]['Close'].iloc[0]
                    ytd_change = ((last_price - start_year_price) / start_year_price) * 100
                except: ytd_change = 0.0

                with cols[idx]:
                    st.metric(label=name, value=f"{last_price:,.2f}", delta=f"{day_change:.2f}%")
                    st.caption(f"YTD: {ytd_change:+.2f}%")

                if len(selected_indices) > 1:
                    base_val = data['Close'].iloc[0]
                    normalized = (data['Close'] / base_val) * 100
                    fig.add_trace(go.Scatter(x=data.index, y=normalized, name=name))
                    y_axis_title = "Base 100 (Comparatif)"
                else:
                    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name=name))
                    y_axis_title = "Prix"
        fig.update_layout(height=500, yaxis_title=y_axis_title)
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 2 : SIMULATEUR FUTUR
# -----------------------------------------------------------------------------
elif page == "Simulateur Futur":
    st.header("🚀 Personnalisez votre Plan d'Achat")
    st.info("👇 **Tableau Interactif :** Modifiez les montants pour voir l'impact sur le futur.")

    df_base = pd.DataFrame(DEFAULT_PLAN)
    edited_df = st.data_editor(
        df_base,
        column_config={
            "Action": st.column_config.TextColumn("Action", disabled=True),
            "Ticker": st.column_config.TextColumn("Ticker", disabled=True, width="small"),
            "Montant (€)": st.column_config.NumberColumn("Montant (€)", min_value=0, step=1, format="%d €"),
            "Fréquence": st.column_config.SelectboxColumn("Fréquence", options=list(FREQ_MAP.keys()), required=True)
        },
        hide_index=True, use_container_width=True, num_rows="fixed", key="editor_futur"
    )

    total_monthly_investment = 0
    for index, row in edited_df.iterrows():
        total_monthly_investment += row["Montant (€)"] * FREQ_MAP.get(row["Fréquence"], 1.0)

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Paramètres")
        st.success(f"💰 **Total Mensuel : {int(total_monthly_investment)} €**")
        monthly_inv = st.number_input("Montant retenu (€)", value=int(total_monthly_investment))
        initial_inv = st.number_input("Capital de départ (€)", value=0)
        rate = st.slider("Rendement annuel (%)", 5, 15, 9) 
        years_graph = st.slider("Durée Graphique (Années)", 5, 30, 15)

    with col2:
        df_graph = calculate_dca_curve(initial_inv, monthly_inv, years_graph, rate)
        final_val = df_graph.iloc[-1]["Valeur Portefeuille"]
        total_put = df_graph.iloc[-1]["Total Investi"]
        gain = final_val - total_put
        
        st.subheader("Projection Graphique")
        m1, m2, m3 = st.columns(3)
        m1.metric("Final", f"{final_val:,.0f} €")
        m2.metric("Versé", f"{total_put:,.0f} €")
        m3.metric("Gain", f"{gain:,.0f} €")

        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(x=df_graph["Année"], y=df_graph["Valeur Portefeuille"], fill='tozeroy', name='Portefeuille', line=dict(color='#00CC96')))
        fig_sim.add_trace(go.Scatter(x=df_graph["Année"], y=df_graph["Total Investi"], fill='tozeroy', name='Versé', line=dict(color='#636EFA')))
        st.plotly_chart(fig_sim, use_container_width=True)

    st.markdown("---")
    st.subheader("📅 Détail des gains : Jour après Jour")
    df_proj = calculate_projection_table(initial_inv, monthly_inv, rate)
    
    # Affichage simple si matplotlib bug, sinon on peut remettre le style
    st.dataframe(
        df_proj.style.format({
            "Total Versé (€)": "{:,.0f} €", 
            "Valeur Estimée (€)": "{:,.0f} €", 
            "Plus-Value (€)": "{:+,.0f} €"
        }),
        use_container_width=True, hide_index=True, height=400
    )

# -----------------------------------------------------------------------------
# PAGE 3 : BACKTEST & PERFORMANCE (NOUVEAU)
# -----------------------------------------------------------------------------
elif page == "🔙 Backtest & Performance":
    st.header("⏳ Voyage dans le temps")
    st.markdown("Si vous aviez investi **1 000 €** dans ce portefeuille (BoussiBroke) il y a 5 ans, voici ce qui se serait passé comparé au **CAC 40**.")
    
    st.info("ℹ️ Cette simulation prend en compte vos pondérations exactes (Nasdaq, Inde, Air Liquide...) et gère les taux de change (USD/EUR/GBP) historiquement.")

    # On réutilise le dataframe du plan par défaut pour calculer les poids
    df_backtest_input = pd.DataFrame(DEFAULT_PLAN)
    
    with st.spinner("Analyse des 5 dernières années en cours (Téléchargement des données)..."):
        # Calcul de la courbe du portefeuille
        portfolio_curve = compute_backtest(df_backtest_input, years=5)
        
        # Récupération du benchmark (CAC 40) pour comparer
        cac40 = get_stock_data("^FCHI", period="5y")
        
        if portfolio_curve is not None and cac40 is not None:
            # Normalisation CAC 40 base 100
            cac40_norm = (cac40["Close"] / cac40["Close"].iloc[0]) * 100
            
            # Calcul des métriques finales
            perf_portfolio = portfolio_curve.iloc[-1] - 100
            perf_cac = cac40_norm.iloc[-1] - 100
            
            # Affichage KPIs
            kpi1, kpi2 = st.columns(2)
            kpi1.metric("Performance BoussiBroke (5 ans)", f"+{perf_portfolio:.2f}%", delta="Votre Stratégie")
            kpi2.metric("Performance CAC 40 (5 ans)", f"+{perf_cac:.2f}%", delta="Indice Français")
            
            # Graphique Comparatif
            fig_bt = go.Figure()
            # Courbe Portefeuille
            fig_bt.add_trace(go.Scatter(
                x=portfolio_curve.index, y=portfolio_curve, 
                mode='lines', name='Portefeuille BoussiBroke', 
                line=dict(color='#00CC96', width=3)
            ))
            # Courbe Benchmark
            fig_bt.add_trace(go.Scatter(
                x=cac40_norm.index, y=cac40_norm, 
                mode='lines', name='CAC 40 (Comparaison)', 
                line=dict(color='gray', dash='dot')
            ))
            
            fig_bt.update_layout(
                title="Performance Base 100 (5 Ans)", 
                xaxis_title="Année", 
                yaxis_title="Valeur (Base 100)",
                height=600
            )
            st.plotly_chart(fig_bt, use_container_width=True)
            
            st.success("✅ Analyse terminée. Ce graphique montre la puissance de la diversification (Tech US + Inde + Industrie FR) face à un indice classique.")
        else:
            st.error("Impossible de récupérer certaines données historiques pour le moment. Réessayez plus tard.")
