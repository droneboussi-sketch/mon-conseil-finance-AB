import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE & STYLE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BoussiBroke Investissement",
    page_icon="📈",
    layout="wide"
)

# CSS pour un look épuré
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
st.markdown("Bienvenue ! Voici les conseils d'un amateur boursier. Ce tableau de bord permet de suivre les cours, simuler votre richesse future et vérifier les performances passées.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 2. DONNÉES & PARAMÈTRES
# -----------------------------------------------------------------------------

# Conversion Fréquence texte -> Nombre par mois
FREQ_MAP = {
    "1x / semaine": 4.33,
    "1x / 2 semaines": 2.16,
    "1x / mois": 1.0,
    "2x / mois": 2.0,
    "3x / mois": 3.0
}

# Mapping des devises pour conversion historique (Backtest)
CURRENCY_MAP = {
    "CNDX.L": "USD", "BRK-B": "USD", "TTWO": "USD", "SGO.PA": "EUR",
    "BRBY.L": "GBP", "CIN.PA": "EUR", "AAPL": "USD", "DIA": "USD",
    "MSFT": "USD", "NATO.PA": "EUR", "AI.PA": "EUR", "TQQQ": "USD",
    "VIE.PA": "EUR", "ACWX": "USD"
}

# Liste pour le menu déroulant (Tracker)
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

# Ton plan par défaut (Modifiable par l'utilisateur dans l'interface)
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
def compute_backtest(plan_df, years=5):
    """
    Reconstitue la performance historique du panier de manière ROBUSTE.
    Gère les actions récentes en coupant le graphique au moment où tout est disponible.
    """
    # 1. Calcul des poids cibles en fonction du budget mensuel
    plan_df["Budget_Ligne"] = plan_df["Montant (€)"] * plan_df["Fréquence"].map(FREQ_MAP).fillna(1.0)
    total_budget = plan_df["Budget_Ligne"].sum()
    
    if total_budget == 0: return None
    plan_df["Poids"] = plan_df["Budget_Ligne"] / total_budget

    # 2. Récupération des données (Actions + Taux de change)
    tickers = plan_df["Ticker"].tolist()
    tickers_api = list(set(tickers + ["EURUSD=X", "EURGBP=X"]))
    
    try:
        # On télécharge tout en vrac
        data = yf.download(tickers_api, period=f"{years}y", progress=False)['Close']
        # On remplit les trous de cotation (jours fériés)
        data = data.ffill().bfill() 
    except Exception as e:
        return None

    # 3. Conversion et Pondération
    # On va créer une Série pour chaque action convertie en EUR
    series_list = []
    
    for idx, row in plan_df.iterrows():
        ticker = row["Ticker"]
        weight = row["Poids"]
        currency = CURRENCY_MAP.get(ticker, "EUR")
        
        if ticker in data.columns:
            series = data[ticker].copy()
            
            # Conversion Devises vers EUR
            if currency == "USD" and "EURUSD=X" in data.columns:
                series = series / data["EURUSD=X"]
            elif currency == "GBP" and "EURGBP=X" in data.columns:
                series = series / data["EURGBP=X"]
            
            # On stocke la série pondérée
            series_list.append(series)

    if not series_list: return None

    # 4. Alignement des dates (Le cœur de la correction)
    # On crée un DataFrame avec toutes les séries propres
    df_clean = pd.concat(series_list, axis=1)
    
    # On supprime les lignes où il manque au moins une donnée (avant la création de l'ETF le plus récent)
    df_clean = df_clean.dropna()
    
    if df_clean.empty:
        st.warning("Pas assez de données historiques communes.")
        return None

    # 5. Calcul de l'indice composite
    # On normalise chaque colonne base 100 au début de la période commune
    df_normalized = df_clean.apply(lambda x: (x / x.iloc[0]) * 100)
    
    # On applique les poids (Attention : il faut que l'ordre corresponde)
    # Pour simplifier ici : on recalcule la somme pondérée sur le df aligné
    portfolio_series = pd.Series(0.0, index=df_clean.index)
    
    for idx, row in plan_df.iterrows():
        ticker = row["Ticker"]
        weight = row["Poids"]
        # On retrouve la colonne (parfois Yahoo change les noms, mais ici l'index aligné aide)
        # Simplification : On refait la boucle sur le df aligné
        # Note : Cette méthode est une approximation "Panier Fixe"
        pass 

    # Méthode plus directe sur le df_clean aligné :
    # On calcule la valeur du portefeuille jour par jour
    # Somme (Prix_jour / Prix_depart * Poids)
    
    # Re-boucle propre sur le dataframe nettoyé
    final_curve = pd.Series(0.0, index=df_clean.index)
    
    # On a besoin de mapper le nom de colonne Yahoo au poids
    # C'est complexe car Yahoo renvoie parfois des Tuples.
    # Approche simplifiée robuste :
    
    current_val = 0
    # On initialise à 100
    
    # On va faire une moyenne pondérée des performances relatives
    weighted_perf = pd.Series(0.0, index=df_clean.index)
    
    # On doit être sûr de l'ordre. On refait un tour simple.
    for idx, row in plan_df.iterrows():
        ticker = row["Ticker"]
        weight = row["Poids"]
        
        # On cherche la colonne qui correspond au ticker dans nos données téléchargées
        # (Parfois c'est juste le Ticker, parfois (Ticker, 'Close'))
        col_name = ticker
        
        # Astuce pour retrouver la donnée dans df_clean (qui n'a pas les noms de colonnes originaux mais des index 0,1,2...)
        # On va simplifier : On reprend data, on coupe aux dates de df_clean
        
        series = data[ticker].loc[df_clean.index]
        if CURRENCY_MAP.get(ticker) == "USD": series = series / data["EURUSD=X"].loc[df_clean.index]
        if CURRENCY_MAP.get(ticker) == "GBP": series = series / data["EURGBP=X"].loc[df_clean.index]
        
        # Perf relative
        rel_perf = (series / series.iloc[0])
        weighted_perf += rel_perf * weight

    # Base 100
    return weighted_perf * 100

def calculate_projection_table(initial, monthly_amount, rate):
    """Génère le tableau détaillé des périodes."""
    rate_monthly = (1 + rate/100)**(1/12) - 1
    horizons = {
        "1 Jour": 1/30, "1 Semaine": 1/4.33, "1 Mois": 1, "6 Mois": 6, 
        "1 An": 12, "3 Ans": 36, "5 Ans": 60, "10 Ans": 120, "20 Ans": 240, "30 Ans": 360
    }
    results = []
    for label, months in horizons.items():
        fv_initial = initial * (1 + rate_monthly)**months
        if rate_monthly == 0: fv_series = monthly_amount * months
        else: fv_series = monthly_amount * ((1 + rate_monthly)**months - 1) / rate_monthly
        
        total_val = fv_initial + fv_series
        total_invested = initial + (monthly_amount * months)
        results.append({
            "Période": label, 
            "Total Versé (€)": total_invested, 
            "Valeur Estimée (€)": total_val, 
            "Plus-Value (€)": total_val - total_invested
        })
    return pd.DataFrame(results)

def calculate_dca_curve(initial, monthly_amount, years, rate):
    """Génère les données pour le graphique futur."""
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
# 6. PAGE : SIMULATEUR FUTUR
# -----------------------------------------------------------------------------
elif page == "Simulateur Futur":
    st.header("🚀 Personnalisez votre Plan d'Achat")
    st.info("👇 **Tableau Interactif :** Modifiez les montants pour voir l'impact sur le futur.")

    # Editeur de données
    df_base = pd.DataFrame(DEFAULT_PLAN)
    edited_df = st.data_editor(
        df_base,
        column_config={
            "Action": st.column_config.TextColumn("Action", disabled=True),
            "Ticker": st.column_config.TextColumn("Ticker", disabled=True), # Caché ou visible
            "Montant (€)": st.column_config.NumberColumn("Montant (€)", min_value=0, step=1, format="%d €"),
            "Fréquence": st.column_config.SelectboxColumn("Fréquence", options=list(FREQ_MAP.keys()), required=True)
        },
        hide_index=True, use_container_width=True, num_rows="fixed", key="editor_futur"
    )

    # Calcul Budget
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
    
    # Affichage du tableau avec gestion d'erreur si matplotlib manque
    try:
        st.dataframe(
            df_proj.style.format({
                "Total Versé (€)": "{:,.0f} €", 
                "Valeur Estimée (€)": "{:,.0f} €", 
                "Plus-Value (€)": "{:+,.0f} €"
            }).background_gradient(subset=["Plus-Value (€)"], cmap="Greens"),
            use_container_width=True, hide_index=True, height=400
        )
    except:
        # Fallback si pas de matplotlib
        st.dataframe(
            df_proj.style.format({
                "Total Versé (€)": "{:,.0f} €", 
                "Valeur Estimée (€)": "{:,.0f} €", 
                "Plus-Value (€)": "{:+,.0f} €"
            }),
            use_container_width=True, hide_index=True, height=400
        )

# -----------------------------------------------------------------------------
# 7. PAGE : BACKTEST (CORRIGÉE)
# -----------------------------------------------------------------------------
elif page == "🔙 Backtest & Performance":
    st.header("⏳ Voyage dans le temps")
    st.markdown("Simulation de votre portefeuille **réel** (BoussiBroke) sur le passé face au **CAC 40**.")
    
    st.info("ℹ️ Le graphique commence à la date où **toutes** vos actions existent (environ mi-2023 à cause de l'ETF Défense).")

    df_backtest_input = pd.DataFrame(DEFAULT_PLAN)
    
    with st.spinner("Récupération des données historiques et calculs..."):
        portfolio_curve = compute_backtest(df_backtest_input, years=5)
        
        # Benchmark CAC 40
        cac40 = get_stock_data("^FCHI", period="5y")
        
        if portfolio_curve is not None and cac40 is not None:
            # Alignement des dates : on coupe le CAC40 pour qu'il commence en même temps que le portefeuille
            start_date = portfolio_curve.index[0]
            cac40_aligned = cac40["Close"][start_date:]
            
            # Normalisation CAC 40 base 100
            cac40_norm = (cac40_aligned / cac40_aligned.iloc[0]) * 100
            
            # KPI
            perf_portfolio = portfolio_curve.iloc[-1] - 100
            perf_cac = cac40_norm.iloc[-1] - 100
            
            kpi1, kpi2 = st.columns(2)
            kpi1.metric("Performance BoussiBroke", f"+{perf_portfolio:.2f}%", delta="Votre Stratégie")
            kpi2.metric("Performance CAC 40", f"+{perf_cac:.2f}%", delta="Indice de référence")
            
            # Graphique
            fig_bt = go.Figure()
            fig_bt.add_trace(go.Scatter(x=portfolio_curve.index, y=portfolio_curve, mode='lines', name='BoussiBroke', line=dict(color='#00CC96', width=3)))
            fig_bt.add_trace(go.Scatter(x=cac40_norm.index, y=cac40_norm, mode='lines', name='CAC 40', line=dict(color='gray', dash='dot')))
            
            fig_bt.update_layout(title="Comparaison Base 100", xaxis_title="Date", yaxis_title="Valeur (Base 100)", height=600)
            st.plotly_chart(fig_bt, use_container_width=True)
        else:
            st.error("Données insuffisantes pour le backtest (Vérifiez la connexion ou les tickers).")
