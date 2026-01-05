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

# Ton plan par défaut
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

def calculate_projection_table(initial, monthly_amount, rate):
    """Calcule les projections pour des périodes fixes."""
    # Taux mensuel équivalent
    rate_monthly = (1 + rate/100)**(1/12) - 1
    
    # Liste des horizons temporels (Label : nombre de mois)
    # 1 jour = 0.033 mois, 1 semaine = 0.23 mois
    horizons = {
        "1 Jour": 1/30,
        "1 Semaine": 1/4.33,
        "1 Mois": 1,
        "6 Mois": 6,
        "1 An": 12,
        "3 Ans": 36,
        "5 Ans": 60,
        "7 Ans": 84,
        "10 Ans": 120,
        "15 Ans": 180,
        "20 Ans": 240,
        "30 Ans": 360
    }
    
    results = []
    
    for label, months in horizons.items():
        # Formule Valeur Future (FV) avec versements mensuels
        # FV = P * (1+r)^n + PMT * [ ((1+r)^n - 1) / r ]
        
        # 1. Intérêts sur le capital de départ
        fv_initial = initial * (1 + rate_monthly)**months
        
        # 2. Intérêts sur les versements périodiques
        if rate_monthly == 0:
            fv_series = monthly_amount * months
        else:
            fv_series = monthly_amount * ((1 + rate_monthly)**months - 1) / rate_monthly
            
        total_val = fv_initial + fv_series
        total_invested = initial + (monthly_amount * months)
        gain = total_val - total_invested
        
        results.append({
            "Période": label,
            "Total Versé (€)": total_invested,
            "Valeur Estimée (€)": total_val,
            "Plus-Value (€)": gain
        })
        
    return pd.DataFrame(results)

def calculate_dca_curve(initial, monthly_amount, years, rate):
    """Calcule la courbe d'évolution année par année."""
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
    st.info("👇 **Tableau Interactif :** Modifiez les montants pour voir l'impact sur le futur.")

    # 1. Tableau éditable
    df_base = pd.DataFrame(DEFAULT_PLAN)
    edited_df = st.data_editor(
        df_base,
        column_config={
            "Action": st.column_config.TextColumn("Action", disabled=True),
            "Montant (€)": st.column_config.NumberColumn("Montant (€)", min_value=0, step=1, format="%d €"),
            "Fréquence": st.column_config.SelectboxColumn("Fréquence", options=list(FREQ_MAP.keys()), required=True)
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed"
    )

    # 2. Calcul du total mensuel
    total_monthly_investment = 0
    for index, row in edited_df.iterrows():
        total_monthly_investment += row["Montant (€)"] * FREQ_MAP.get(row["Fréquence"], 1.0)

    st.markdown("---")
    
    # 3. Paramètres
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Paramètres")
        st.success(f"💰 **Total Mensuel : {int(total_monthly_investment)} €**")
        
        monthly_inv = st.number_input("Montant retenu (€)", value=int(total_monthly_investment))
        initial_inv = st.number_input("Capital de départ (€)", value=0)
        rate = st.slider("Rendement annuel (%)", 5, 15, 9) 
        years_graph = st.slider("Durée Graphique (Années)", 5, 30, 15)

    # 4. Graphique
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
        fig_sim.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_sim, use_container_width=True)

    # 5. NOUVEAU : Tableau Détaillé des Périodes
    st.markdown("---")
    st.subheader("📅 Détail des gains : Jour après Jour, Année après Année")
    st.markdown("Voici exactement ce que deviendrait votre argent sur différentes périodes.")

    # Calcul du tableau complet
    df_proj = calculate_projection_table(initial_inv, monthly_inv, rate)

    # Mise en forme pour l'affichage (Arrondi et ajout du symbole €)
    # On crée une copie pour l'affichage pour garder les chiffres bruts si besoin
    df_display = df_proj.copy()
    df_display["Total Versé (€)"] = df_display["Total Versé (€)"].apply(lambda x: f"{x:,.0f} €")
    df_display["Valeur Estimée (€)"] = df_display["Valeur Estimée (€)"].apply(lambda x: f"{x:,.0f} €")
    
    # On met une couleur sur la plus-value pour que ce soit joli
    def color_gain(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'

    # Affichage avec Pandas Styler (plus joli que st.table simple)
    st.dataframe(
        df_proj.style.format({
            "Total Versé (€)": "{:,.0f} €", 
            "Valeur Estimée (€)": "{:,.0f} €", 
            "Plus-Value (€)": "{:+,.0f} €"
        }).background_gradient(subset=["Plus-Value (€)"], cmap="Greens"),
        use_container_width=True,
        hide_index=True,
        height=500 
    )
