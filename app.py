import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.db import init_db, register_user, login_user, add_movimento, get_movimenti
from utils.helpers import clean_importo, format_currency

# --- Inizializza DB ---
init_db()

# --- Gestione sessione ---
if "user" not in st.session_state:
    st.session_state.user = None

def show_login():
    st.title("🔑 Login / Registrazione")

    tab1, tab2 = st.tabs(["Login", "Registrati"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.session_state.user = user
                st.success("Login effettuato!")
                st.rerun()
            else:
                st.error("Credenziali errate.")

    with tab2:
        email = st.text_input("Nuova email")
        password = st.text_input("Nuova password", type="password")
        if st.button("Registrati"):
            ok = register_user(email, password)
            if ok:
                st.success("Registrazione completata! Ora fai login.")
            else:
                st.error("Email già registrata.")

def show_app():
    user = st.session_state.user
    st.sidebar.write(f"👤 Loggato come: {user['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- Carico i dati dal DB ---
    movimenti = get_movimenti(user["id"])
    df = pd.DataFrame(movimenti, columns=["id", "user_id", "Tipo", "Data", "Importo", "Categoria"])

    # --- Totali ---
    spese_importo = clean_importo(df[df["Tipo"] == "Spesa"]["Importo"]) if not df.empty else pd.Series(dtype=float)
    totale_spese = spese_importo.sum() if not df.empty else 0.0

    # --- Titolo ---
    st.title("💰 Gestione Spese e Risparmi")

    # --- Pallina sotto il titolo ---
    colore = "green" if totale_spese < 2000 else "red"
    classe = "blinking" if colore == "red" else ""

    st.markdown(
        f"""
        <style>
        @keyframes blink {{ 50% {{ opacity: 0; }} }}
        .blinking {{ animation: blink 1s infinite; }}
        </style>
        <div style="display:flex;align-items:center;gap:10px;margin-top:5px;">
            <div style="width:20px;height:20px;border-radius:50%;background:{colore};"
                 class="{classe}"></div>
            <span style="font-size:16px;">Totale Spese: {format_currency(totale_spese)} €</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Form spese ---
    st.subheader("➖ Aggiungi Spesa")
    with st.form("spese_form", clear_on_submit=True):
        data_spesa = st.date_input("Data spesa")
        tipo_spesa = st.text_input("Categoria (es. affitto, cibo, bollette)")
        valore_spesa = st.number_input("Importo (€)", min_value=0.0, step=1.0)
        submitted_spesa = st.form_submit_button("Aggiungi Spesa")
        if submitted_spesa and valore_spesa > 0:
            add_movimento(user["id"], "Spesa", data_spesa, valore_spesa, tipo_spesa)
            st.success("Spesa registrata!")
            st.rerun()

    # --- RIEPILOGO SPESE ---
    if not df.empty:
        st.header("📊 Riepilogo Spese")
        spese = df[df["Tipo"] == "Spesa"].copy()
        if not spese.empty:
            spese["Importo_num"] = clean_importo(spese["Importo"])
            spese["Importo"] = spese["Importo_num"].apply(format_currency)
            st.dataframe(spese.drop(columns="Importo_num"))

            totale_spese = spese["Importo_num"].sum()
            st.metric("Totale Spese", format_currency(totale_spese) + " €")

            # (resto del grafico a torta e metriche come nel tuo codice)
            # ...

    # --- Form risparmi ---
    st.subheader("💵 Gestione Risparmi")
    with st.form("risparmi_form", clear_on_submit=True):
        data_risp = st.date_input("Data risparmio/prelievo")
        tipo_risp = st.radio("Tipo movimento", ["Risparmio", "Prelievo"])
        valore_risp = st.number_input("Importo (€)", min_value=0.0, step=1.0)
        submitted_risp = st.form_submit_button("Registra Movimento")
        if submitted_risp and valore_risp > 0:
            if tipo_risp == "Prelievo":
                valore_risp = -valore_risp
            add_movimento(user["id"], "Risparmio", data_risp, valore_risp, tipo_risp)
            st.success(f"{tipo_risp} registrato!")
            st.rerun()

# --- MAIN ---
if st.session_state.user is None:
    show_login()
else:
    show_app()
