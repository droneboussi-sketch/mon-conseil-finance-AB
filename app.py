import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# CONFIGURATION DE LA PAGE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BoussiBroke Investissement ",
    page_icon="📈",
    layout="wide"
)

# Titre principal et CSS personnalisé
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    h1 {
        color: #2c3e50;
    }
    .stMetric {
        background-color: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 BoussiBroke Investissement")
st.markdown("Bienvenue ! Voici les conseils d'un amateur boursier qui fait ça sur son temps libre.")
st.markdown("---")

# -----------------------------------------------------------------------------
# DONNÉES & CONFIGURATION
# -----------------------------------------------------------------------------

TICKERS = {
   "🇺🇸 Nasdaq 100": "^NDX",
    "🇺🇸 Apple": "AAPL",
    "🇺🇸 Microsoft": "MSFT",
    "🇺🇸 Berkshire Hathaway B": "BRK-B",
    "🇺🇸 Take-Two Interactive": "TTWO",
    "🇺🇸 Dow Jones Ind.": "^DJI",
    "🇺🇸 Nasdaq Levier x3 (TQQQ)": "TQQQ",
    "🌍 MSCI World ex-USA": "ACWX",
    "🇫🇷 Air Liquide": "AI.PA",
    "🇫🇷 Saint-Gobain": "SGO.PA",
    "🇫🇷 Véolia": "VIE.PA",
    "🇮🇳 MSCI India (Amundi)": "CIN.PA",
    "🇬🇧 Burberry Group": "BRBY.L",
    "🇪🇺 Future of Defense": "NATO.PA" 
}

STRATEGY_ALLOCATION = {
    "Nasdaq 100": {"ticker": "CNDX.L", "poids": 0.07},
    "Berkshire": {"ticker": "BRK-B", "poids": 0.07},
    "Take-Two": {"ticker": "TTWO", "poids": 0.07},
    "St Gobain": {"ticker": "SGO.PA", "poids": 0.07},
    "Burberry": {"ticker": "BRBY.L", "poids": 0.07},
    "India": {"ticker": "CIN.PA", "poids": 0.07},
    "Apple": {"ticker": "AAPL", "poids": 0.07},
    "Dow Jones": {"ticker": "DIA", "poids": 0.07},
    "Microsoft": {"ticker": "MSFT", "poids": 0.07},
    "Defense": {"ticker": "NATO.PA", "poids": 0.07},
    "Air Liquide": {"ticker": "AI.PA", "poids": 0.07},
    "Nasdaq x3": {"ticker": "TQQQ", "poids": 0.07},
    "Véolia": {"ticker": "VIE.PA", "poids": 0.07},
    "World ex-USA": {"ticker": "ACWX", "poids": 0.09}
}

# -----------------------------------------------------------------------------
# FONCTIONS UTILITAIRES
# -----------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_stock_data(ticker_symbol, period="5y"):
    try:
        stock = yf.Ticker(ticker_symbol)
        history = stock.history(period=period)
        if history.empty:
            return None
        return history
    except Exception as e:
        return None

def calculate_dca(initial, periodic, frequency, rate, years):
    months = years * 12
    periods_per_year = 52 if frequency == "Hebdomadaire" else 365
    rate_periodic = (1 + rate/100)**(1/periods_per_year) - 1
    
    data = []
    current_portfolio = initial
    total_invested = initial
    
    for year in range(years + 1):
        data.append({
            "Année": year,
            "Total Investi (Cash)": round(total_invested, 2),
            "Valeur Portefeuille (Intérêts composés)": round(current_portfolio, 2)
        })
        if year < years:
            for _ in range(periods_per_year):
                current_portfolio = current_portfolio * (1 + rate_periodic) + periodic
                total_invested += periodic
                
    return pd.DataFrame(data)

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Aller vers :", ["Suivi des Marchés", "Simulateur Plan (DCA)", "Ma Stratégie vs Réalité"])

st.sidebar.markdown("---")
st.sidebar.header("📰 Actualités Éco")

news_items = [
    {"titre": "La FED annonce une pause sur les taux directeurs", "impact": "Positif"},
    {"titre": "Le secteur technologique tire le S&P500 vers le haut", "impact": "Positif"},
    {"titre": "Inflation en zone Euro : chiffres rassurants", "impact": "Neutre"},
    {"titre": "Nouvelles régulations sur les crypto-monnaies en Asie", "impact": "Volatil"},
    {"titre": "Les résultats trimestriels des GAFAM dépassent les attentes", "impact": "Positif"},
]

for news in news_items:
    color = "green" if news['impact'] == "Positif" else "orange" if news['impact'] == "Neutre" else "red"
    st.sidebar.markdown(f"**{news['titre']}**")
    st.sidebar.markdown(f":{color}[Impact estimé: {news['impact']}]")
    st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# PAGE 1 : SUIVI DES MARCHÉS
# -----------------------------------------------------------------------------
if page == "Suivi des Marchés":
    st.header("📊 Suivi des Marchés Clés")
    selected_indices = st.multiselect("Quels indices voulez-vous afficher ?", list(TICKERS.keys()), default=["S&P 500 (USA)", "CAC 40 (France)"])
    
    if selected_indices:
        cols = st.columns(len(selected_indices))
        fig = go.Figure()

        for idx, name in enumerate(selected_indices):
            ticker = TICKERS[name]
            data = get_stock_data(ticker)
            
            if data is not None:
                last_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2]
                day_change = ((last_price - prev_price) / prev_price) * 100
                start_year_price = data[data.index.year == datetime.now().year]['Close'].iloc[0]
                ytd_change = ((last_price - start_year_price) / start_year_price) * 100

                with cols[idx]:
                    st.metric(label=name, value=f"{last_price:,.2f}", delta=f"{day_change:.2f}% (Jour)")
                    st.caption(f"YTD: {ytd_change:+.2f}%")

                if len(selected_indices) > 1:
                    base_value = data['Close'].iloc[0]
                    normalized_data = (data['Close'] / base_value) * 100
                    fig.add_trace(go.Scatter(x=data.index, y=normalized_data, mode='lines', name=name))
                    y_axis_title = "Performance Base 100"
                else:
                    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name=name))
                    y_axis_title = "Prix"

        fig.update_layout(title="Évolution Comparée (5 Ans)", xaxis_title="Date", yaxis_title=y_axis_title, height=500)
        st.plotly_chart(fig, use_container_width=True)
        if len(selected_indices) > 1:
            st.info("ℹ️ Le graphique est en 'Base 100' pour comparer les performances.")

# -----------------------------------------------------------------------------
# PAGE 2 : SIMULATEUR PLAN (DCA)
# -----------------------------------------------------------------------------
elif page == "Simulateur Plan (DCA)":
    st.header("🌱 La puissance des intérêts composés")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Paramètres")
        initial_amount = st.number_input("Montant initial (€)", min_value=0, value=1000, step=100)
        periodic_amount = st.number_input("Montant périodique (€)", min_value=0, value=50, step=10)
        frequency = st.selectbox("Fréquence", ["Hebdomadaire", "Journalier"])
        rate = st.slider("Rendement annuel (%)", 1, 15, 7)
        duration = st.slider("Durée (Années)", 5, 40, 20)

    with col2:
        df_dca = calculate_dca(initial_amount, periodic_amount, frequency, rate, duration)
        final_val = df_dca.iloc[-1]["Valeur Portefeuille (Intérêts composés)"]
        total_inv = df_dca.iloc[-1]["Total Investi (Cash)"]
        gain = final_val - total_inv
        
        st.subheader("Résultats")
        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Final", f"{final_val:,.0f} €")
        c2.metric("Total Versé", f"{total_inv:,.0f} €")
        c3.metric("Intérêts Gagnés", f"{gain:,.0f} €")

        fig_dca = go.Figure()
        fig_dca.add_trace(go.Scatter(x=df_dca["Année"], y=df_dca["Valeur Portefeuille (Intérêts composés)"], fill='tozeroy', name='Portefeuille'))
        fig_dca.add_trace(go.Scatter(x=df_dca["Année"], y=df_dca["Total Investi (Cash)"], fill='tozeroy', name='Cash Investi'))
        st.plotly_chart(fig_dca, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 3 : MA STRATÉGIE VS RÉALITÉ
# -----------------------------------------------------------------------------
elif page == "Ma Stratégie vs Réalité":
    st.header("🛡️ Testez ma recommandation (80% Actions / 20% Oblig)")
    invest_amount = st.number_input("Montant à simuler (€)", value=10000)
    
    if st.button("Lancer la simulation"):
        with st.spinner("Calcul..."):
            try:
                ticker_actions = STRATEGY_ALLOCATION["Actions (MSCI World)"]["ticker"]
                data_actions = get_stock_data(ticker_actions, period="1y")['Close']
                ticker_oblig = STRATEGY_ALLOCATION["Obligations (US Agg)"]["ticker"]
                data_oblig = get_stock_data(ticker_oblig, period="1y")['Close']

                combined = pd.concat([data_actions, data_oblig], axis=1).dropna()
                combined.columns = ["Actions", "Obligations"]
                combined["Perf_Actions"] = combined["Actions"] / combined["Actions"].iloc[0]
                combined["Perf_Obligations"] = combined["Obligations"] / combined["Obligations"].iloc[0]
                
                part_actions = invest_amount * STRATEGY_ALLOCATION["Actions (MSCI World)"]["poids"]
                part_oblig = invest_amount * STRATEGY_ALLOCATION["Obligations (US Agg)"]["poids"]
                combined["Valeur_Portefeuille"] = (part_actions * combined["Perf_Actions"]) + (part_oblig * combined["Perf_Obligations"])
                
                final_pf_value = combined["Valeur_Portefeuille"].iloc[-1]
                perf_abs = final_pf_value - invest_amount
                
                col1, col2 = st.columns(2)
                col1.metric("Valeur Aujourd'hui", f"{final_pf_value:,.2f} €")
                col2.metric("Plus/Moins-value", f"{perf_abs:+.2f} €")
                
                fig_strat = px.line(combined, y="Valeur_Portefeuille", title="Évolution portefeuille")
                st.plotly_chart(fig_strat, use_container_width=True)

            except Exception as e:
                st.error("Erreur de récupération des données.")
