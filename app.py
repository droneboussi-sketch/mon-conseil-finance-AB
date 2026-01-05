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
st.markdown("Bienvenue ! Voici les conseils d'un amateur boursier qui investit des fractions d'actions sur son temps libre.")
st.markdown("---")

# -----------------------------------------------------------------------------
# DONNÉES
# -----------------------------------------------------------------------------

# Pour le Tracker (Affichage des cours)
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

# TON PLAN D'INVESTISSEMENT (En Euros fixes)
# coeff_mensuel permet de ramener la fréquence à un mois (ex: hebdo = x4.33)
MY_PLAN = [
    {"nom": "Nasdaq 100", "montant": 1, "freq": "1x / semaine", "coeff": 4.33},
    {"nom": "Berkshire B", "montant": 2, "freq": "1x / semaine", "coeff": 4.33},
    {"nom": "Take-Two", "montant": 3, "freq": "1x / semaine", "coeff": 4.33},
    {"nom": "Saint-Gobain", "montant": 2, "freq": "1x / 2 semaines", "coeff": 2.16},
    {"nom": "Burberry", "montant": 1, "freq": "1x / semaine", "coeff": 4.33},
    {"nom": "MSCI India", "montant": 1, "freq": "1x / 2 semaines", "coeff": 2.16},
    {"nom": "Apple", "montant": 1, "freq": "1x / semaine", "coeff": 4.33},
    {"nom": "Dow Jones", "montant": 2, "freq": "1x / 2 semaines", "coeff": 2.16},
    {"nom": "Microsoft", "montant": 1, "freq": "2x / mois", "coeff": 2.0},
    {"nom": "Future Defense", "montant": 1, "freq": "1x / mois (Est.)", "coeff": 1.0}, # Supposé 1/mois
    {"nom": "Air Liquide", "montant": 1, "freq": "1x / mois", "coeff": 1.0},
    {"nom": "Nasdaq x3", "montant": 2, "freq": "1x / mois", "coeff": 1.0},
    {"nom": "Véolia", "montant": 2, "freq": "2x / mois", "coeff": 2.0},
    {"nom": "World ex-USA", "montant": 3, "freq": "1x / mois", "coeff": 1.0},
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

def calculate_dca(initial, monthly_amount, years, rate):
    """Calcule l'intérêt composé avec apport mensuel fixe"""
    rate_monthly = (1 + rate/100)**(1/12) - 1
    
    data = []
    current_portfolio = initial
    total_invested = initial
    
    # On génère les points année par année
    for year in range(years + 1):
        data.append({
            "Année": year,
            "Total Investi": round(total_invested, 2),
            "Valeur Portefeuille": round(current_portfolio, 2)
        })
        
        # Simulation des 12 mois de l'année suivante
        if year < years:
            for _ in range(12):
                current_portfolio = current_portfolio * (1 + rate_monthly) + monthly_amount
                total_invested += monthly_amount
                
    return pd.DataFrame(data)

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Aller vers :", ["Suivi des Marchés", "Simulateur Plan BoussiBroke"])

st.sidebar.markdown("---")
st.sidebar.header("📰 Actualités Éco")

news_items = [
    {"titre": "La FED annonce une pause sur les taux directeurs", "impact": "Positif"},
    {"titre": "Le secteur Tech tire les marchés vers le haut", "impact": "Positif"},
    {"titre": "Inflation en zone Euro : chiffres rassurants", "impact": "Neutre"},
    {"titre": "Volatilité sur les marchés asiatiques", "impact": "Volatil"},
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
    st.header("📊 Suivi des Cours")
    st.markdown("Visualisez l'évolution des actions de votre plan.")
    
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
                    # Note: Le prix affiché est celui de l'action entière
                    st.metric(label=name, value=f"{last_price:,.2f}", delta=f"{day_change:.2f}%")
                    st.caption(f"YTD: {ytd_change:+.2f}%")

                if len(selected_indices) > 1:
                    base_val = data['Close'].iloc[0]
                    normalized = (data['Close'] / base_val) * 100
                    fig.add_trace(go.Scatter(x=data.index, y=normalized, name=name))
                    y_axis_title = "Base 100 (Comparatif)"
                else:
                    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name=name))
                    y_axis_title = "Prix de l'action"

        fig.update_layout(title="Comparaison (5 ans)", yaxis_title=y_axis_title, height=500)
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 2 : SIMULATEUR PLAN BOUSSIBROKE
# -----------------------------------------------------------------------------
elif page == "Simulateur Plan BoussiBroke":
    st.header("🚀 Projection du Plan d'Achat")
    st.markdown("Simulation basée sur des investissements en **fractions d'actions** (sommes fixes en Euros).")

    # 1. Calcul du total mensuel
    total_monthly_investment = 0
    
    with st.expander("📝 Voir le détail de votre plan mensuel"):
        st.table(pd.DataFrame(MY_PLAN)[['nom', 'montant', 'freq']].rename(columns={'nom': 'Action', 'montant': 'Montant (€)', 'freq': 'Fréquence'}))
        
    # Calcul mathématique simple
    for item in MY_PLAN:
        monthly_cost = item["montant"] * item["coeff"]
        total_monthly_investment += monthly_cost

    st.markdown("---")
    
    # 2. Paramètres de simulation
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Paramètres")
        st.info(f"💰 **Investissement Mensuel Total : {total_monthly_investment:.2f} €**")
        
        monthly_inv = st.number_input("Arrondi mensuel (€)", value=int(total_monthly_investment))
        initial_inv = st.number_input("Capital de départ (€)", value=0)
        rate = st.slider("Rendement annuel espéré (%)", 5, 15, 9) 
        years = st.slider("Durée (Années)", 5, 30, 15)

    # 3. Calculs et Graphique
    with col2:
        df_sim = calculate_dca(initial_inv, monthly_inv, years, rate)
        
        final_val = df_sim.iloc[-1]["Valeur Portefeuille"]
        total_put = df_sim.iloc[-1]["Total Investi"]
        gain = final_val - total_put
        
        st.subheader("Résultats Futurs")
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital Final", f"{final_val:,.0f} €")
        m2.metric("Total Versé", f"{total_put:,.0f} €")
        m3.metric("Plus-Value", f"{gain:,.0f} €", delta=f"x {final_val/total_put:.2f}")

        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(x=df_sim["Année"], y=df_sim["Valeur Portefeuille"], fill='tozeroy', name='Valeur Portefeuille', line=dict(color='#00CC96')))
        fig_sim.add_trace(go.Scatter(x=df_sim["Année"], y=df_sim["Total Investi"], fill='tozeroy', name='Argent Sorti', line=dict(color='#636EFA')))
        
        fig_sim.update_layout(title=f"Projection de richesse sur {years} ans", xaxis_title="Années", yaxis_title="Montant (€)")
        st.plotly_chart(fig_sim, use_container_width=True)
