import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import datetime

# -----------------------------------------------------------------------------
# 1. CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BoussiBroke | Mode Démo",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. FONCTIONS DE SIMULATION (Au lieu de Yahoo)
# -----------------------------------------------------------------------------
def generate_fake_data(ticker):
    """Génère une courbe réaliste pour éviter de bloquer sur Yahoo"""
    dates = pd.date_range(end=datetime.datetime.today(), periods=30)
    # Départ aléatoire entre 100 et 200
    start = np.random.uniform(100, 200)
    # Marche aléatoire
    changes = np.random.normal(0, 1, size=30)
    prices = start + np.cumsum(changes)
    return pd.Series(prices, index=dates)

# -----------------------------------------------------------------------------
# 3. INTERFACE
# -----------------------------------------------------------------------------
st.title("📈 BoussiBroke (Mode Démo / Test)")
st.warning("⚠️ Ceci est une version de test. Les données sont simulées pour vérifier que le site fonctionne.")

st.markdown("---")

# DASHBOARD
st.header("📊 Tableau de Bord")

tickers = ["Palantir", "Apple", "Tesla", "Air Liquide", "S&P 500"]
cols = st.columns(len(tickers))

for i, ticker in enumerate(tickers):
    # On génère des fausses données instantanément
    data = generate_fake_data(ticker)
    last_price = data.iloc[-1]
    prev_price = data.iloc[-2]
    delta = (last_price - prev_price) / prev_price * 100
    
    with cols[i]:
        st.metric(label=ticker, value=f"{last_price:.2f} €", delta=f"{delta:+.2f}%")
        st.line_chart(data, height=100)

st.markdown("---")

# CALCULATEUR DCA
st.header("🚀 Simulateur Intérêts Composés")
col1, col2 = st.columns(2)
with col1:
    monthly = st.number_input("Versement mensuel (€)", 200)
    years = st.slider("Années", 5, 40, 20)
with col2:
    rate = st.slider("Taux (%)", 2, 12, 8)
    initial = st.number_input("Capital départ", 1000)

# Calcul mathématique simple (ne plante jamais)
future_val = initial * (1 + rate/100)**years + monthly * 12 * ((1 + rate/100)**years - 1) / (rate/100)

st.metric("Résultat dans {} ans".format(years), f"{future_val:,.0f} €")

st.success("✅ Si vous voyez cette page, votre application Streamlit fonctionne parfaitement ! Le problème vient bien de la connexion à Yahoo Finance qui est bloquée.")
