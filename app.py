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
st.markdown("Bienvenue ! Voici les conseils d'un amateur boursier. Ce tableau est interactif : **modifiez les montants** ci-dessous pour simuler votre propre budget.")
st.markdown("---")

# -----------------------------------------------------------------------------
# DONNÉES INITIALES
# -----------------------------------------------------------------------------

# Dictionnaire pour convertir les textes de fréquence en nombre par mois
FREQ_MAP = {
    "1x / semaine": 4.33,
    "1x / 2 semaines": 2.16,
    "1x / mois": 1.0,
    "2x / mois": 2.0,
    "3x / mois": 3.0
}

# Liste des tickers pour le tracker
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

# Données par défaut du tableau (Ton plan à toi)
DEFAULT_PLAN = [
    {"Action": "Nasdaq 100", "Montant (€)": 1, "Fréquence": "1x / semaine"},
    {"Action": "Berkshire B", "Montant (€)": 2, "Fréquence": "1x / semaine"},
    {"Action": "Take-Two", "Montant (€)": 3, "Fréquence": "1x / semaine"},
    {"Action": "Saint-Gobain", "Montant (€)": 2, "Fréquence": "1x / 2 semaines"},
    {"Action": "Burberry", "Montant (€)": 1, "Fréquence": "1x / semaine"},
    {"Action": "MSCI India", "Montant (€)": 1, "Fréquence": "1x / 2 semaines"},
    {"Action": "Apple", "Montant (€)": 1, "Fréquence": "1x / semaine"},
    {"Action": "Dow Jones", "Montant (€)": 2, "Fréquence": "1x / 2 semaines"},
    {"Action": "Microsoft", "Montant (€)": 1, "Fréquence": "2x / mois"},
    {"Action": "Future Defense", "Montant (€)": 1, "Fréquence": "1x / mois"},
    {"Action": "Air Liquide", "Montant (€)": 1, "Fréquence": "1x / mois"},
    {"Action": "Nasdaq x3", "Montant (€)": 2, "Fréquence": "1x / mois"},
    {"Action": "Véolia", "Montant (€)": 2, "Fréquence": "2x / mois"},
    {"Action": "World ex-USA", "Montant (€)": 3, "Fréquence": "1x / mois"},
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
    rate_monthly = (1 + rate/100)**(1/12) - 1
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
                current_portfolio = current_portfolio * (1 + rate_monthly) + monthly_amount
                total_invested += monthly_amount
    return pd.DataFrame(data)

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Aller vers :", ["Suivi des Marchés", "Simulateur Interactif"])

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

        fig.update_layout(title="Comparaison (5 ans)", yaxis_title=y_axis_title, height=500)
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 2 : SIMULATEUR INTERACTIF
# -----------------------------------------------------------------------------
elif page == "Simulateur Interactif":
    st.header("🚀 Personnalisez votre Plan d'Achat")
    st.info("👇 **Tableau Interactif :** Cliquez sur les cases ci-dessous pour modifier les montants ou les fréquences. Le calcul se fera automatiquement.")

    # 1. Création du DataFrame éditable
    df_base = pd.DataFrame(DEFAULT_PLAN)
    
    # Configuration de l'éditeur (Liste déroulante pour la fréquence)
    edited_df = st.data_editor(
        df_base,
        column_config={
            "Action": st.column_config.TextColumn("Action", disabled=True), # On empêche de modifier le nom
            "Montant (€)": st.column_config.NumberColumn("Montant (€)", min_value=0, step=1, format="%d €"),
            "Fréquence": st.column_config.SelectboxColumn(
                "Fréquence",
                help="Combien de fois achetez-vous cette fraction ?",
                width="medium",
                options=list(FREQ_MAP.keys()), # Liste des choix possibles
                required=True
            )
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed" # On empêche d'ajouter des lignes pour garder la liste fixe
    )

    # 2. Calcul du total mensuel dynamique
    total_monthly_investment = 0
    
    # On parcourt le tableau modifié par l'utilisateur
    for index, row in edited_df.iterrows():
        montant = row["Montant (€)"]
        freq_text = row["Fréquence"]
        coeff = FREQ_MAP.get(freq_text, 1.0) # On récupère le coeff (ex: 4.33 pour semaine)
        
        total_monthly_investment += montant * coeff

    st.markdown("---")
    
    # 3. Paramètres & Résultats
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Paramètres")
        st.success(f"💰 **Total Mensuel Calculé : {int(total_monthly_investment)} €**")
        st.caption("Ce montant est calculé à partir du tableau ci-dessus.")
        
        # On permet d'ajuster l'arrondi si besoin
        monthly_inv = st.number_input("Montant retenu pour la simu (€)", value=int(total_monthly_investment))
        initial_inv = st.number_input("Capital de départ (€)", value=0)
        rate = st.slider("Rendement annuel (%)", 5, 15, 9) 
        years = st.slider("Durée (Années)", 5, 30, 15)

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
        fig_sim.add_trace(go.Scatter(x=df_sim["Année"], y=df_sim["Valeur Portefeuille"], fill='tozeroy', name='Portefeuille', line=dict(color='#00CC96')))
        fig_sim.add_trace(go.Scatter(x=df_sim["Année"], y=df_sim["Total Investi"], fill='tozeroy', name='Argent de poche', line=dict(color='#636EFA')))
        
        fig_sim.update_layout(title=f"Projection de richesse sur {years} ans", xaxis_title="Années", yaxis_title="Montant (€)")
        st.plotly_chart(fig_sim, use_container_width=True)
