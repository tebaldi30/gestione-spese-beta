import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import locale
from utils.db import init_db, register_user, login_user, add_movimento, get_movimenti, get_user_by_id

# --- Inizializza DB ---
init_db()

# --- Stato sessione ---
if "user" not in st.session_state:
    st.session_state.user = None

# Funzione helper per formattare valuta in stile italiano
def format_currency(value):
    try:
        locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
    except locale.Error:
        # fallback se locale italiano non disponibile
        return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    return locale.currency(value, grouping=True).replace("€", "€").strip()

# Funzione per recuperare email da id utente
def get_user_email(user_id):
    user = get_user_by_id(user_id)
    if user:
        return user['email']
    return "Utente"

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
            user_record = login_user(email, password)
            if user_record:
                st.session_state.user = user_record['id']  # memorizza solo l'id
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
    user_email = get_user_email(st.session_state.user)
    st.title("💰 Gestione Spese e Risparmi")
    st.write(f"👋 Benvenuto, utente **{user_email}**")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # --- Carica i dati dal DB ---
    df = pd.DataFrame(get_movimenti(st.session_state.user))

    # Se non ci sono dati ancora o mancano colonne
    if df.empty or "tipo" not in df.columns:
        st.info("Nessun dato ancora inserito.")

        # Mostra comunque i form per inserire dati anche a utente nuovo
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

        # Non procedere oltre per riepiloghi se dataset vuoto
        return

    # Dataframe ha dati e colonne
    df["importo"] = pd.to_numeric(df["importo"], errors="coerce")

    if "tipo" in df.columns:
        # --- RIEPILOGO SPESE E ANDAMENTO MENSILE ---
        spese = df[df["tipo"] == "Spesa"].copy()
        if not spese.empty:
            spese["importo"] = pd.to_numeric(spese["importo"], errors="coerce")
            totale_spese = spese["importo"].sum()
            totale_spese_formatted = format_currency(totale_spese)

            st.header("📊 Riepilogo Spese")
            st.dataframe(
                spese[["data", "categoria", "importo"]].assign(
                    importo=spese["importo"].apply(format_currency)
                )
            )

            st.metric("Totale Spese", totale_spese_formatted)

            soglia_massima = 2500.0
            importo_da_mostrare = totale_spese if totale_spese <= soglia_massima else soglia_massima
            restante = soglia_massima - importo_da_mostrare

            valori = [importo_da_mostrare, restante]
            colori = ["#e74c3c", "#27ae60"]

            percent_speso = (importo_da_mostrare / soglia_massima) * 100 if soglia_massima else 0
            percent_disp = 100 - percent_speso

            st.subheader("📈 Andamento Mensile")

            fig, ax = plt.subplots()
            fig.patch.set_alpha(0.0)
            ax.patch.set_alpha(0.0)

            wedges, texts, autotexts = ax.pie(
                valori,
                colors=colori,
                autopct='%1.1f%%',
                pctdistance=1.1,
                labeldistance=1.2,
                startangle=90,
                counterclock=False,
                wedgeprops={'edgecolor': 'white', 'linewidth': 2},
                textprops={'color': 'black', 'weight': 'bold'}
            )

            for text in texts:
                text.set_text('')

            ax.axis('equal')
            st.pyplot(fig)

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="Speso",
                    value=f"{percent_speso:.1f}%",
                    delta=-importo_da_mostrare,
                    delta_color="normal"
                )
                st.caption(f"{format_currency(importo_da_mostrare)} € su {format_currency(soglia_massima)} €")

            with col2:
                st.metric(
                    label="Disponibile",
                    value=f"{percent_disp:.1f}%",
                    delta=restante,
                    delta_color="normal"
                )
                st.caption(f"{format_currency(restante)} € disponibile")
        else:
            st.info("Nessuna spesa registrata.")

        # --- RIEPILOGO RISPARMI ---
        risp = df[df["tipo"] == "Risparmio"].copy()
        if not risp.empty:
            risp["importo"] = pd.to_numeric(risp["importo"], errors="coerce")
            totale_risparmi = risp["importo"].sum()
            totale_risparmi_formatted = format_currency(totale_risparmi)

            st.header("💰 Riepilogo Risparmi")
            st.dataframe(
                risp[["data", "categoria", "importo"]].assign(
                    importo=risp["importo"].apply(format_currency)
                )
            )

            st.metric("Saldo Risparmi", totale_risparmi_formatted)

            obiettivo_risparmio = 30000.0
            percentuale_raggiunta = totale_risparmi / obiettivo_risparmio * 100 if obiettivo_risparmio else 0
            st.subheader("🎯 Percentuale Obiettivo Risparmi")
            st.metric(
                label="Risparmio raggiunto",
                value=f"{percentuale_raggiunta:.1f}%",
                delta=f"{totale_risparmi_formatted} € su {format_currency(obiettivo_risparmio)} €"
            )
        else:
            st.info("Nessun risparmio registrato.")
    else:
        st.info("Nessun dato disponibile.")

    # --- Form risparmi (sempre visibile anche se dati assenti) ---
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

# ================================
# ROUTING
# ================================
if st.session_state.user is None:
    show_login_page()
else:
    show_dashboard()
