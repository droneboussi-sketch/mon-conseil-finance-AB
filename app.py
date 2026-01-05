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

# Titre principal et CSS personnalisé (CORRIGÉ)
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
# DONNÉES : TON PLAN D'INVESTISSEMENT
# -----------------------------------------------------------------------------

# Liste pour le Tracker (Affichage des cours)
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

# Ton Plan d'Achat (Ticker, Quantité par mois approximative, Devise)
# Calcul fréquence : 1/semaine = 4.33/mois. 1/2semaines = 2.16/mois.
MY_PLAN = [
    {"nom": "Nasdaq 100", "ticker": "CNDX.L", "qt_mois": 4.33, "devise": "USD"},  # 1/semaine
    {"nom": "Berkshire B", "ticker": "BRK-B", "qt_mois": 8.66, "devise": "USD"},   # 2/semaine
    {"nom": "Take-Two", "ticker": "TTWO", "qt_mois": 13.0, "devise": "USD"},       # 3/semaine
    {"nom": "Saint-Gobain", "ticker": "SGO.PA", "qt_mois": 4.33, "devise": "EUR"}, # 2 toutes les 2 semaines (~4/mois)
    {"nom": "Burberry", "ticker": "BRBY.L", "qt_mois": 4.33, "devise": "GBP"},     # 1/semaine
    {"nom": "MSCI India", "ticker": "CIN.PA", "qt_mois": 2.16, "devise": "EUR"},   # 1 toutes les 2 semaines
    {"nom": "Apple", "ticker": "AAPL", "qt_mois": 4.33, "devise": "USD"},          # 1/semaine
    {"nom": "Dow Jones", "ticker": "DIA", "qt_mois": 4.33, "devise": "USD"},       # 2 toutes les 2 semaines
    {"nom": "Microsoft", "ticker": "MSFT", "qt_mois": 2.0, "devise": "USD"},       # 1 deux fois par mois
    {"nom": "Future Defense", "ticker": "NATO.PA", "qt_mois": 1.0, "devise": "EUR"}, # Supposé 1/mois
    {"nom": "Air Liquide", "ticker": "AI.PA", "qt_mois": 1.0, "devise": "EUR"},    # 1/mois
    {"nom": "Nasdaq x3", "ticker": "TQQQ", "qt_mois": 2.0, "devise": "USD"},       # 2/mois
    {"nom": "Véolia", "ticker": "VIE.PA", "qt_mois": 4.0, "devise": "EUR"},        # 2 deux fois par mois
    {"nom": "World ex-USA", "ticker": "ACWX", "qt_mois": 3.0, "devise": "USD"},    # 3 par mois
]

# Taux de change fixes (Approximation pour la rapidité)
FX_RATES = {"EUR": 1.0, "USD": 0.95, "GBP": 1.20} 

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
def get_current_price(ticker):
    """Récupère le dernier prix pour le calcul du plan."""
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return 0.0
    except:
        return 0.0

def calculate_dca(initial, periodic, years, rate):
    months = years * 12
    rate_periodic = (1 + rate/100)**(1/12) - 1
    
    data = []
    current_portfolio = initial
    total_invested = initial
    
    for year in range(years + 1):
        data.append({
            "Année": year,
            "Total Investi": round(total_invested, 2),
            "Valeur Portefeuille": round(current_portfolio, 2)
        })
        if year < years:
            for _ in range(12):
                current_portfolio = current_portfolio * (1 + rate_periodic) + periodic
                total_invested += periodic
                
    return pd.DataFrame(data)

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("Navigation")
# On enlève le 3ème onglet ici
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
                    y_axis_title = "Base 100"
                else:
                    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name=name))
                    y_axis_title = "Prix"

        fig.update_layout(title="Comparaison (5 ans)", yaxis_title=y_axis_title, height=500)
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 2 : SIMULATEUR PLAN BOUSSIBROKE
# -----------------------------------------------------------------------------
elif page == "Simulateur Plan BoussiBroke":
    st.header("🚀 Projection du Plan d'Achat")
    st.markdown("Cette page calcule automatiquement le coût mensuel de ton plan d'achat (Apple 1/sem, etc.) au prix d'aujourd'hui et projette la richesse future.")

    # 1. Calcul du coût mensuel du plan
    total_monthly_investment = 0
    details_text = ""

    # On utilise un expander pour pas prendre toute la place si on veut voir les détails
    with st.expander("Voir le détail du coût mensuel calculé"):
        st.write("Calcul basé sur les derniers cours de clôture :")
        for item in MY_PLAN:
            price = get_current_price(item["ticker"])
            
            # Correction spécifique pour Londres (souvent en pence, il faut diviser par 100)
            if item["ticker"].endswith(".L"):
                price = price / 100

            cost_native = price * item["qt_mois"]
            cost_eur = cost_native * FX_RATES.get(item["devise"], 1.0)
            
            total_monthly_investment += cost_eur
            st.write(f"- **{item['nom']}** ({item['qt_mois']:.1f}/mois) : Prix {price:.2f} {item['devise']} ➡️ Coût mensuel : {cost_eur:.2f} €")

    st.markdown("---")
    
    # 2. Paramètres de simulation
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Paramètres")
        st.info(f"💰 **Investissement Mensuel Calculé : {int(total_monthly_investment)} €**")
        
        # On laisse l'utilisateur ajuster si besoin, mais par défaut c'est le calcul
        monthly_inv = st.number_input("Montant investi par mois (€)", value=int(total_monthly_investment))
        initial_inv = st.number_input("Capital de départ (€)", value=0)
        rate = st.slider("Rendement annuel espéré (%)", 5, 15, 9) # 9% car beaucoup d'actions US/Tech
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
        
        fig_sim.update_layout(title=f"Projection sur {years} ans", xaxis_title="Années", yaxis_title="Montant (€)")
        st.plotly_chart(fig_sim, use_container_width=True)

    st.warning("Note : Le montant mensuel est une estimation basée sur les prix d'aujourd'hui. Dans la réalité, si les actions montent, le coût mensuel pour acheter le même nombre d'actions augmentera aussi.")
