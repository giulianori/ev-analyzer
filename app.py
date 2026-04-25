import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="EV Analyzer", layout="wide")

st.title("🚗 Analisi Consumi EV (stile Tesla)")

# Upload file
uploaded_file = st.file_uploader("daticsv2.csv", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()

    # conversione numerica
    for col in ['Km', 'Distanza', 'Consumo', 'Velocita']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna()

    # =========================
    # CALCOLI
    # =========================
    df['Energia_Wh'] = df['Distanza'] / 1000 * df['Consumo'] * 10

    df['Energia_pos'] = df['Energia_Wh'].clip(lower=0)
    df['Energia_neg'] = df['Energia_Wh'].clip(upper=0)

    df['Energia_cum_kWh'] = df['Energia_Wh'].cumsum() / 1000

    energia_tot = df['Energia_pos'].sum() / 1000
    energia_rec = abs(df['Energia_neg'].sum() / 1000)
    energia_netta = energia_tot - energia_rec

    distanza = df['Km'].iloc[-1]

    consumo_reale = energia_netta / distanza * 100

    # input batteria
    batteria = st.sidebar.slider("Capacità batteria (kWh)", 30, 100, 44)

    autonomia = batteria / consumo_reale * 100

    # smoothing velocità
    df['Velocita_smooth'] = df['Velocita'].rolling(5).mean()
    df = df.dropna()

    # =========================
    # METRICHE
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Distanza", f"{distanza:.1f} km")
    col2.metric("Consumo", f"{energia_tot:.2f} kWh")
    col3.metric("Recupero", f"{energia_rec:.2f} kWh")
    col4.metric("Autonomia", f"{autonomia:.0f} km")

    st.metric("Consumo medio", f"{consumo_reale:.1f} kWh/100km")

    # =========================
    # GRAFICO
    # =========================
    fig, ax1 = plt.subplots(figsize=(10,5))

    # aree
    ax1.fill_between(df['Km'], 0, df['Energia_pos'].cumsum()/1000, alpha=0.3)
    ax1.fill_between(df['Km'], 0, df['Energia_neg'].cumsum()/1000, alpha=0.3)

    # linea energia
    ax1.plot(df['Km'], df['Energia_cum_kWh'], linewidth=2)

    ax1.set_xlabel("Km")
    ax1.set_ylabel("Energia (kWh)")
    ax1.grid()

    # velocità
    ax2 = ax1.twinx()
    ax2.plot(df['Km'], df['Velocita_smooth'], linestyle='--')
    ax2.set_ylabel("Velocità")

    st.pyplot(fig)

else:
    st.info("Carica un file CSV per iniziare")