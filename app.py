import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.db import init_db, register_user, login_user, add_movimento, get_movimenti

# --- Inizializza DB ---
init_db()

# --- Stato sessione ---
if "user" not in st.session_state:
    st.session_state.user = None


# ================================
# LOGIN / REGISTRAZIONE
# ================================
def show_login_page():
    st.title("🔑 Gestione Spese - Login")

    tab_login, tab_register = st.tabs(["Login", "Registrati"])

    # --- LOGIN ---
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Accedi"):
            user_id = login_user(email, password)
            if user_id:
                st.session_state.user = user_id
                st.success("✅ Login effettuato con successo!")
                st.rerun()
            else:
                st.error("❌ Email o password errati")

    # --- REGISTRAZIONE ---
    with tab_register:
        new_email = st.text_input("Nuova Email", key="register_email")
        new_password = st.text_input("Nuova Password", type="password", key="register_password")
        if st.button("Registrati"):
            if register_user(new_email, new_password):
                st.success("✅ Registrazione completata, ora puoi fare login")
            else:
                st.error("⚠️ Email già registrata")


# ================================
# DASHBOARD
# ================================
def show_dashboard():
    st.title("💰 Gestione Spese e Risparmi")
    st.write(f"👋 Benvenuto, utente **{st.session_state.user}**")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- Carica i dati dal DB ---
    df = pd.DataFrame(get_movimenti(st.session_state.user))

    # Se non ci sono dati ancora
    if df.empty:
        st.info("Nessun dato ancora inserito.")
    else:
        # Conversione numerica importi
        df["importo"] = pd.to_numeric(df["importo"], errors="coerce")

    # --- Form spese ---
    st.subheader("➖ Aggiungi Spesa")
    with st.form("spese_form", clear_on_submit=True):
        data_spesa = st.date_input("Data spesa")
        tipo_spesa = st.text_input("Categoria (es. affitto, cibo, bollette)")
        valore_spesa = st.number_input("Importo (€)", min_value=0.0, step=1.0)
        submitted_spesa = st.form_submit_button("Aggiungi Spesa")
        if submitted_spesa and valore_spesa > 0:
            add_movimento(st.session_state.user, "Spesa", data_spesa, valore_spesa, tipo_spesa)
            st.success("Spesa registrata!")
            st.rerun()

    # --- Aggiorna dati ---
    df = pd.DataFrame(get_movimenti(st.session_state.user))
    if not df.empty:
        df["importo"] = pd.to_numeric(df["importo"], errors="coerce")

    # --- RIEPILOGO SPESE ---
    if not df.empty:
        st.header("📊 Riepilogo Spese")
        spese = df[df["tipo"] == "Spesa"].copy()
        if not spese.empty:
            st.dataframe(spese[["data", "categoria", "importo"]])

            totale_spese = spese["importo"].sum()
            st.metric("Totale Spese", f"{totale_spese:,.2f} €")

            # Grafico a torta
            soglia_massima = 2500.0
            restante = max(0, soglia_massima - totale_spese)
            valori = [totale_spese, restante]
            colori = ["#e74c3c", "#27ae60"]

            st.subheader("📈 Andamento Mensile")
            fig, ax = plt.subplots()
            wedges, texts, autotexts = ax.pie(
                valori,
                colors=colori,
                autopct='%1.1f%%',
                startangle=90,
                counterclock=False
            )
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.info("Nessuna spesa registrata.")

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
            add_movimento(st.session_state.user, "Risparmio", data_risp, valore_risp, tipo_risp)
            st.success(f"{tipo_risp} registrato!")
            st.rerun()

    # --- RIEPILOGO RISPARMI ---
    st.header("💰 Riepilogo Risparmi")
    risp = df[df["tipo"] == "Risparmio"].copy()
    if not risp.empty:
        st.dataframe(risp[["data", "categoria", "importo"]])
        totale_risparmi = risp["importo"].sum()
        st.metric("Saldo Risparmi", f"{totale_risparmi:,.2f} €")

        obiettivo_risparmio = 30000.0
        percentuale_raggiunta = totale_risparmi / obiettivo_risparmio * 100 if obiettivo_risparmio else 0
        st.subheader("🎯 Percentuale Obiettivo Risparmi")
        st.metric(
            label="Risparmio raggiunto",
            value=f"{percentuale_raggiunta:.1f}%",
            delta=f"{totale_risparmi:,.2f} € su {obiettivo_risparmio:,.2f} €"
        )
    else:
        st.info("Nessun risparmio registrato.")


# ================================
# ROUTING
# ================================
if st.session_state.user is None:
    show_login_page()
else:
    show_dashboard()
