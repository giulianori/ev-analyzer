import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="EV Analyzer", layout="wide")

st.title("🚗 EV Energy Analyzer")
st.markdown("""
Analizza i dati del tuo veicolo elettrico:
- ⚡ Consumo reale
- 🔋 Energia recuperata
- 📊 Storico viaggi
""")
# =========================
# STORICO PERSONALE (sessione utente)
# =========================
if "storico" not in st.session_state:
    st.session_state["storico"] = pd.DataFrame(columns=[
        "ID_Viaggio",
        "Data",
        "Distanza_km",
        "Consumo_kWh",
        "Recupero_kWh",
        "Netto_kWh",
        "Consumo_reale_kWh_100km",
        "Autonomia_km"
    ])

# =========================
# UPLOAD
# =========================
uploaded_file = st.file_uploader("Carica file CSV", type=["csv"])

if uploaded_file:

    st.success("File caricato correttamente ✔️")

    # =========================
    # LETTURA
    # =========================
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()

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

    batteria = st.sidebar.slider("Capacità batteria (kWh)", 30, 120, 50)

    autonomia = batteria / consumo_reale * 100

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
    # GRAFICO VIAGGIO
    # =========================
    fig, ax1 = plt.subplots(figsize=(10,5))

    ax1.plot(df['Km'], df['Energia_cum_kWh'], linewidth=3)
    ax1.fill_between(df['Km'], 0, df['Energia_pos'].cumsum()/1000, alpha=0.2)
    ax1.fill_between(df['Km'], 0, df['Energia_neg'].cumsum()/1000, alpha=0.2)

    ax1.set_xlabel("Distanza (km)")
    ax1.set_ylabel("Energia (kWh)")
    ax1.grid()

    ax2 = ax1.twinx()
    ax2.plot(df['Km'], df['Velocita_smooth'], linestyle='--')
    ax2.set_ylabel("Velocità (km/h)")

    st.pyplot(fig)

# =========================
# SALVA STORICO PERSONALE + ANTI-DUPLICATO
# =========================
if uploaded_file is not None and not df.empty:

    # Firma univoca del viaggio
    id_viaggio = f"{round(distanza,2)}_{round(energia_tot,2)}_{round(energia_rec,2)}"

    nuovo_viaggio = pd.DataFrame([{
        "ID_Viaggio": id_viaggio,
        "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Distanza_km": round(distanza, 2),
        "Consumo_kWh": round(energia_tot, 2),
        "Recupero_kWh": round(energia_rec, 2),
        "Netto_kWh": round(energia_netta, 2),
        "Consumo_reale_kWh_100km": round(consumo_reale, 2),
        "Autonomia_km": round(autonomia, 0)
    }])

    if id_viaggio not in st.session_state["storico"]["ID_Viaggio"].values:
        st.session_state["storico"] = pd.concat(
            [st.session_state["storico"], nuovo_viaggio],
            ignore_index=True
        )
        st.success("Viaggio salvato nello storico ✔️")
    else:
        st.warning("Questo viaggio è già presente nello storico ⚠️")
# =========================
# MOSTRA STORICO PERSONALE
# =========================
storico = st.session_state["storico"]

if not storico.empty:

    st.subheader("📚 Storico Viaggi (solo tua sessione)")
    st.dataframe(storico)

    # Download CSV personale
    csv = storico.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Scarica Storico CSV",
        csv,
        "storico_viaggi.csv",
        "text/csv"
    )

    # Trend consumi
    st.subheader("📈 Trend Consumo Reale")

    fig2, ax = plt.subplots(figsize=(10, 4))
    ax.plot(
        storico.index + 1,
        storico["Consumo_reale_kWh_100km"],
        marker="o"
    )

    ax.set_xlabel("Viaggio #")
    ax.set_ylabel("kWh/100km")
    ax.grid()

    st.pyplot(fig2)

else:
    st.info("Carica un file CSV per iniziare")


   
    
