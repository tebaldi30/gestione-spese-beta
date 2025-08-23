import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from utils.db import get_user, create_user, get_movimenti, salva_dato

# --- Configurazione pagina ---
st.set_page_config(page_title="💰 Gestione Spese e Risparmi", layout="wide")
st.title("💰 Gestione Spese e Risparmi")

# --- LOGIN via email ---
if "user_id" not in st.session_state:
    email = st.text_input("Inserisci la tua email per accedere:")
    if st.button("Accedi"):
        user = get_user(email)
        if user is None:
            user_id = create_user(email)
            st.success("Account creato!")
        else:
            user_id = user['id']
            st.success("Login effettuato!")
        st.session_state.user_id = user_id

# --- Funzione helper ---
def clean_importo(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace("€", "")
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip(),
        errors="coerce"
    )

def format_currency(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Main app solo se loggato ---
if "user_id" in st.session_state:
    user_id = st.session_state.user_id

    # --- Carica i dati ---
    df = get_movimenti(user_id)

    # --- Pallina sotto il titolo ---
    spese_importo = clean_importo(df[df["tipo"] == "Spesa"]["importo"]) if not df.empty else pd.Series(dtype=float)
    totale_spese = spese_importo.sum() if not df.empty else 0.0

    colore = "green" if totale_spese < 2000 else "red"
    classe = "blinking" if colore == "red" else ""

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;margin-top:5px;">
            <div style="width:20px;height:20px;border-radius:50%;background:{colore};"
                 class="{classe}"></div>
            <span style="font-size:16px;">Totale Spese: {format_currency(totale_spese)} €</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Form Spese ---
    st.subheader("➖ Aggiungi Spesa")
    with st.form("spese_form", clear_on_submit=True):
        data_spesa = st.date_input("Data spesa")
        tipo_spesa = st.text_input("Categoria (es. affitto, cibo, bollette)")
        valore_spesa = st.number_input("Importo (€)", min_value=0.0, step=1.0)
        submitted_spesa = st.form_submit_button("Aggiungi Spesa")
        if submitted_spesa and valore_spesa > 0:
            salva_dato(user_id, "Spesa", data_spesa, valore_spesa, tipo_spesa)
            st.success("Spesa registrata!")

    # --- Form Risparmi/Prelievi ---
    st.subheader("💵 Gestione Risparmi")
    with st.form("risparmi_form", clear_on_submit=True):
        data_risp = st.date_input("Data risparmio/prelievo")
        tipo_risp = st.radio("Tipo movimento", ["Risparmio", "Prelievo"])
        valore_risp = st.number_input("Importo (€)", min_value=0.0, step=1.0)
        submitted_risp = st.form_submit_button("Registra Movimento")
        if submitted_risp and valore_risp > 0:
            if tipo_risp == "Prelievo":
                valore_risp = -valore_risp
            salva_dato(user_id, "Risparmio", data_risp, valore_risp, tipo_risp)
            st.success(f"{tipo_risp} registrato!")

    # --- Riepilogo Movimenti ---
    st.header("📊 Riepilogo Movimenti")
    if not df.empty:
        df["Importo"] = clean_importo(df["importo"]).apply(format_currency)
        st.dataframe(df[["data", "tipo", "categoria", "Importo"]])

        # Totale spese e risparmi
        totale_spese = clean_importo(df[df["tipo"]=="Spesa"]["importo"]).sum()
        totale_risparmi = clean_importo(df[df["tipo"]=="Risparmio"]["importo"]).sum()
        st.metric("Totale Spese", format_currency(totale_spese) + " €")
        st.metric("Saldo Risparmi", format_currency(totale_risparmi) + " €")

        # Grafico a torta spese vs disponibile
        soglia_massima = 2500.0
        totale_spese_valore = min(totale_spese, soglia_massima)
        restante = soglia_massima - totale_spese_valore

        valori = [totale_spese_valore, restante]
        colori = ["#e74c3c", "#27ae60"]

        fig, ax = plt.subplots()
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        wedges, texts, autotexts = ax.pie(
            valori, colors=colori, autopct='%1.1f%%',
            pctdistance=1.1, startangle=90, counterclock=False,
            wedgeprops={'edgecolor':'white','linewidth':2},
            textprops={'color':'black','weight':'bold'}
        )
        for text in texts:
            text.set_text('')
        ax.axis('equal')
        st.subheader("📈 Andamento Mensile")
        st.pyplot(fig)
    else:
        st.info("Nessun movimento registrato.")
