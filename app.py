{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import yfinance as yf\
import pandas as pd\
import plotly.graph_objects as go\
import plotly.express as px\
import numpy as np\
from datetime import datetime, timedelta\
\
# -----------------------------------------------------------------------------\
# CONFIGURATION DE LA PAGE\
# -----------------------------------------------------------------------------\
st.set_page_config(\
    page_title="Investir Sereinement - Dashboard Famille",\
    page_icon="\uc0\u55357 \u56520 ",\
    layout="wide"\
)\
\
# Titre principal et CSS personnalis\'e9 pour un look \'e9pur\'e9\
st.markdown("""\
<style>\
    .main \{\
        background-color: #f5f5f5;\
    \}\
    h1 \{\
        color: #2c3e50;\
    \}\
    .stMetric \{\
        background-color: white;\
        padding: 10px;\
        border-radius: 5px;\
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);\
    \}\
</style>\
""", unsafe_allow_html=True)\
\
st.title("\uc0\u55357 \u56520  Dashboard d'Investissement Familial")\
st.markdown("Bienvenue ! Ce tableau de bord est con\'e7u pour vous aider \'e0 visualiser l'\'e9volution des march\'e9s et planifier vos investissements long terme.")\
st.markdown("---")\
\
# -----------------------------------------------------------------------------\
# DONN\'c9ES & CONFIGURATION (MODIFIABLES)\
# -----------------------------------------------------------------------------\
\
# Dictionnaire des indices/ETF \'e0 suivre. \
# Cl\'e9 = Nom affich\'e9, Valeur = Ticker Yahoo Finance\
# Astuce: '^GSPC' = S&P500, 'URTH' = MSCI World (ETF proxy), '^FCHI' = CAC40\
TICKERS = \{\
    "S&P 500 (USA)": "^GSPC",\
    "MSCI World (Monde)": "URTH", \
    "NASDAQ (Tech)": "^IXIC",\
    "CAC 40 (France)": "^FCHI",\
    "Bitcoin (Crypto)": "BTC-USD"\
\}\
\
# Allocation recommand\'e9e pour le comparateur (80% Actions, 20% Obligations)\
STRATEGY_ALLOCATION = \{\
    "Actions (MSCI World)": \{"ticker": "URTH", "poids": 0.8\},\
    "Obligations (US Agg)": \{"ticker": "AGG", "poids": 0.2\}\
\}\
\
# -----------------------------------------------------------------------------\
# FONCTIONS UTILITAIRES\
# -----------------------------------------------------------------------------\
\
@st.cache_data(ttl=3600) # Cache les donn\'e9es pour 1 heure pour \'e9viter de recharger tout le temps\
def get_stock_data(ticker_symbol, period="5y"):\
    """R\'e9cup\'e8re l'historique d'un ticker via Yahoo Finance."""\
    try:\
        stock = yf.Ticker(ticker_symbol)\
        # On r\'e9cup\'e8re l'historique\
        history = stock.history(period=period)\
        if history.empty:\
            return None\
        return history\
    except Exception as e:\
        st.error(f"Erreur lors de la r\'e9cup\'e9ration de \{ticker_symbol\}: \{e\}")\
        return None\
\
def calculate_dca(initial, periodic, frequency, rate, years):\
    """Calcule l'\'e9volution d'un investissement progressif (DCA)."""\
    months = years * 12\
    periods_per_year = 52 if frequency == "Hebdomadaire" else 365\
    \
    # Conversion du taux annuel en taux p\'e9riodique\
    rate_periodic = (1 + rate/100)**(1/periods_per_year) - 1\
    \
    data = []\
    current_portfolio = initial\
    total_invested = initial\
    \
    # On simule semaine par semaine (ou jour par jour) mais on agr\'e8ge par ann\'e9e pour le graphe\
    # Pour simplifier le graphique, on va g\'e9n\'e9rer des points annuels\
    for year in range(years + 1):\
        data.append(\{\
            "Ann\'e9e": year,\
            "Total Investi (Cash)": round(total_invested, 2),\
            "Valeur Portefeuille (Int\'e9r\'eats compos\'e9s)": round(current_portfolio, 2)\
        \})\
        \
        # Simulation de l'ann\'e9e suivante\
        if year < years:\
            for _ in range(periods_per_year):\
                current_portfolio = current_portfolio * (1 + rate_periodic) + periodic\
                total_invested += periodic\
                \
    return pd.DataFrame(data)\
\
# -----------------------------------------------------------------------------\
# SIDEBAR : NAVIGATION & ACTUS\
# -----------------------------------------------------------------------------\
st.sidebar.header("Navigation")\
page = st.sidebar.radio("Aller vers :", ["Suivi des March\'e9s", "Simulateur Plan (DCA)", "Ma Strat\'e9gie vs R\'e9alit\'e9"])\
\
st.sidebar.markdown("---")\
st.sidebar.header("\uc0\u55357 \u56560  Actualit\'e9s \'c9co")\
\
# Simulation de flux d'actualit\'e9s (Pour \'e9viter les cl\'e9s API complexes pour l'instant)\
news_items = [\
    \{"titre": "La FED annonce une pause sur les taux directeurs", "impact": "Positif"\},\
    \{"titre": "Le secteur technologique tire le S&P500 vers le haut", "impact": "Positif"\},\
    \{"titre": "Inflation en zone Euro : chiffres rassurants", "impact": "Neutre"\},\
    \{"titre": "Nouvelles r\'e9gulations sur les crypto-monnaies en Asie", "impact": "Volatil"\},\
    \{"titre": "Les r\'e9sultats trimestriels des GAFAM d\'e9passent les attentes", "impact": "Positif"\},\
]\
\
for news in news_items:\
    color = "green" if news['impact'] == "Positif" else "orange" if news['impact'] == "Neutre" else "red"\
    st.sidebar.markdown(f"**\{news['titre']\}**")\
    st.sidebar.markdown(f":\{color\}[Impact estim\'e9: \{news['impact']\}]")\
    st.sidebar.markdown("---")\
\
# -----------------------------------------------------------------------------\
# PAGE 1 : SUIVI DES MARCH\'c9S\
# -----------------------------------------------------------------------------\
if page == "Suivi des March\'e9s":\
    st.header("\uc0\u55357 \u56522  Suivi des March\'e9s Cl\'e9s")\
    \
    selected_indices = st.multiselect("Quels indices voulez-vous afficher ?", list(TICKERS.keys()), default=["S&P 500 (USA)", "CAC 40 (France)"])\
    \
    if selected_indices:\
        # Cr\'e9ation des colonnes pour les m\'e9triques (KPIs)\
        cols = st.columns(len(selected_indices))\
        \
        # Graphique global\
        fig = go.Figure()\
\
        for idx, name in enumerate(selected_indices):\
            ticker = TICKERS[name]\
            data = get_stock_data(ticker)\
            \
            if data is not None:\
                # Calcul des variations\
                last_price = data['Close'].iloc[-1]\
                prev_price = data['Close'].iloc[-2]\
                day_change = ((last_price - prev_price) / prev_price) * 100\
                \
                # Variation depuis le d\'e9but de l'ann\'e9e (YTD)\
                start_year_price = data[data.index.year == datetime.now().year]['Close'].iloc[0]\
                ytd_change = ((last_price - start_year_price) / start_year_price) * 100\
\
                # Affichage des KPIs\
                with cols[idx]:\
                    st.metric(\
                        label=name,\
                        value=f"\{last_price:,.2f\}",\
                        delta=f"\{day_change:.2f\}% (Jour)",\
                    )\
                    st.caption(f"YTD (Depuis 1er Janv): \{ytd_change:+.2f\}%")\
\
                # Ajout au graphique (Normalis\'e9 en % pour comparaison facile si plusieurs courbes)\
                # On normalise par rapport \'e0 la premi\'e8re date affich\'e9e (base 100)\
                if len(selected_indices) > 1:\
                    base_value = data['Close'].iloc[0]\
                    normalized_data = (data['Close'] / base_value) * 100\
                    fig.add_trace(go.Scatter(x=data.index, y=normalized_data, mode='lines', name=name))\
                    y_axis_title = "Performance Base 100"\
                else:\
                    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name=name))\
                    y_axis_title = "Prix"\
\
        fig.update_layout(title="\'c9volution Compar\'e9e (5 Ans)", xaxis_title="Date", yaxis_title=y_axis_title, height=500)\
        st.plotly_chart(fig, use_container_width=True)\
        \
        if len(selected_indices) > 1:\
            st.info("\uc0\u8505 \u65039  Le graphique ci-dessus est en 'Base 100' pour permettre de comparer des actifs qui n'ont pas du tout le m\'eame prix.")\
    else:\
        st.warning("Veuillez s\'e9lectionner au moins un indice.")\
\
# -----------------------------------------------------------------------------\
# PAGE 2 : SIMULATEUR PLAN (DCA)\
# -----------------------------------------------------------------------------\
elif page == "Simulateur Plan (DCA)":\
    st.header("\uc0\u55356 \u57137  La puissance des int\'e9r\'eats compos\'e9s")\
    st.markdown("Simulez ce que votre \'e9pargne pourrait devenir en investissant r\'e9guli\'e8rement.")\
\
    col1, col2 = st.columns([1, 2])\
\
    with col1:\
        st.subheader("Param\'e8tres")\
        initial_amount = st.number_input("Montant initial (\'80)", min_value=0, value=1000, step=100)\
        periodic_amount = st.number_input("Montant p\'e9riodique (\'80)", min_value=0, value=50, step=10)\
        frequency = st.selectbox("Fr\'e9quence d'ajout", ["Hebdomadaire", "Journalier"])\
        rate = st.slider("Rendement annuel moyen estim\'e9 (%)", 1, 15, 7)\
        duration = st.slider("Dur\'e9e de simulation (Ann\'e9es)", 5, 40, 20)\
\
    with col2:\
        # Calcul\
        df_dca = calculate_dca(initial_amount, periodic_amount, frequency, rate, duration)\
        \
        # R\'e9sultat final\
        final_val = df_dca.iloc[-1]["Valeur Portefeuille (Int\'e9r\'eats compos\'e9s)"]\
        total_inv = df_dca.iloc[-1]["Total Investi (Cash)"]\
        gain = final_val - total_inv\
        \
        st.subheader("R\'e9sultats")\
        c1, c2, c3 = st.columns(3)\
        c1.metric("Capital Final", f"\{final_val:,.0f\} \'80")\
        c2.metric("Total Vers\'e9", f"\{total_inv:,.0f\} \'80")\
        c3.metric("Int\'e9r\'eats Gagn\'e9s", f"\{gain:,.0f\} \'80", delta=f"x \{final_val/total_inv:.2f\}")\
\
        # Graphique Aire\
        fig_dca = go.Figure()\
        fig_dca.add_trace(go.Scatter(\
            x=df_dca["Ann\'e9e"], y=df_dca["Valeur Portefeuille (Int\'e9r\'eats compos\'e9s)"],\
            fill='tozeroy', mode='lines', name='Valeur Portefeuille', line=dict(color='#00CC96')\
        ))\
        fig_dca.add_trace(go.Scatter(\
            x=df_dca["Ann\'e9e"], y=df_dca["Total Investi (Cash)"],\
            fill='tozeroy', mode='lines', name='Argent sorti de poche', line=dict(color='#636EFA')\
        ))\
        \
        fig_dca.update_layout(title="Projection de patrimoine", xaxis_title="Ann\'e9es", yaxis_title="Valeur (\'80)")\
        st.plotly_chart(fig_dca, use_container_width=True)\
\
# -----------------------------------------------------------------------------\
# PAGE 3 : MA STRAT\'c9GIE VS R\'c9ALIT\'c9\
# -----------------------------------------------------------------------------\
elif page == "Ma Strat\'e9gie vs R\'e9alit\'e9":\
    st.header("\uc0\u55357 \u57057 \u65039  Testez ma recommandation")\
    st.markdown(f"On simule ici une allocation classique : **\{int(STRATEGY_ALLOCATION['Actions (MSCI World)']['poids']*100)\}% Actions** et **\{int(STRATEGY_ALLOCATION['Obligations (US Agg)']['poids']*100)\}% Obligations** sur les 12 derniers mois.")\
\
    invest_amount = st.number_input("Combien auriez-vous investi il y a 1 an ? (\'80)", value=10000, step=500)\
    \
    if st.button("Lancer la simulation"):\
        with st.spinner("Calcul en cours..."):\
            # R\'e9cup\'e9ration des donn\'e9es 1 an\
            df_portfolio = pd.DataFrame()\
            \
            try:\
                # R\'e9cup\'e9ration Actions\
                ticker_actions = STRATEGY_ALLOCATION["Actions (MSCI World)"]["ticker"]\
                data_actions = get_stock_data(ticker_actions, period="1y")['Close']\
                \
                # R\'e9cup\'e9ration Obligations\
                ticker_oblig = STRATEGY_ALLOCATION["Obligations (US Agg)"]["ticker"]\
                data_oblig = get_stock_data(ticker_oblig, period="1y")['Close']\
\
                # Alignement des dates (au cas o\'f9 il manque des jours de cotation)\
                combined = pd.concat([data_actions, data_oblig], axis=1).dropna()\
                combined.columns = ["Actions", "Obligations"]\
                \
                # Normalisation base 1 (Performance relative)\
                combined["Perf_Actions"] = combined["Actions"] / combined["Actions"].iloc[0]\
                combined["Perf_Obligations"] = combined["Obligations"] / combined["Obligations"].iloc[0]\
                \
                # Calcul de la valeur du portefeuille\
                part_actions = invest_amount * STRATEGY_ALLOCATION["Actions (MSCI World)"]["poids"]\
                part_oblig = invest_amount * STRATEGY_ALLOCATION["Obligations (US Agg)"]["poids"]\
                \
                combined["Valeur_Portefeuille"] = (part_actions * combined["Perf_Actions"]) + (part_oblig * combined["Perf_Obligations"])\
                \
                # Affichage R\'e9sultats\
                final_pf_value = combined["Valeur_Portefeuille"].iloc[-1]\
                perf_abs = final_pf_value - invest_amount\
                perf_pct = (perf_abs / invest_amount) * 100\
                \
                col_res1, col_res2 = st.columns(2)\
                col_res1.metric("Valeur Aujourd'hui", f"\{final_pf_value:,.2f\} \'80")\
                col_res2.metric("Plus-value / Moins-value", f"\{perf_abs:+.2f\} \'80", f"\{perf_pct:+.2f\}%")\
                \
                # Graphique\
                fig_strat = px.line(combined, y="Valeur_Portefeuille", title="\'c9volution de vos 10 000\'80 (Allocation 80/20)")\
                fig_strat.update_traces(line_color='#AB63FA')\
                st.plotly_chart(fig_strat, use_container_width=True)\
                \
                st.success("Cette simulation montre l'importance de la diversification. M\'eame si les actions chutent, les obligations peuvent amortir le choc (et inversement).")\
\
            except Exception as e:\
                st.error(f"Erreur lors de la simulation : \{e\}. V\'e9rifiez votre connexion internet.")\
\
# Pied de page\
st.markdown("---")\
st.markdown("*Ceci est un outil p\'e9dagogique et ne constitue pas un conseil financier certifi\'e9. Les performances pass\'e9es ne pr\'e9jugent pas des performances futures.*")}