import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.db import init_db, add_movimento, get_movimenti, register_user, login_user

# Inizializza DB (crea tabelle se non esistono)
init_db()

# ========================
# --- LOGIN / REGISTRAZIONE
# ========================
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔑 Autenticazione")

    menu = st.sidebar.selectbox("Menu", ["Login", "Registrati"])
    if menu == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Accedi"):
            if login_user(email, password):
                st.session_state.user = email
                st.success("✅ Login effettuato!")
                st.experimental_rerun()
            else:
                st.error("❌ Credenziali non valide")
    elif menu == "Registrati":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Crea account"):
            if register_user(email, password):
                st.success("✅ Registrazione completata, ora fai login")
            else:
                st.error("❌ Email già registrata")
    st.stop()

# ========================
# --- INTERFACCIA PRINCIPALE
# ========================
st.title("💰 Gestione Spese e Risparmi")

# Carico i dati dal DB
dati = get_movimenti(st.session_state.user)
df = pd.DataFrame(dati)

# Pulizia numerica importi
def clean_importo(series):
    return pd.to_numeric(series, errors="coerce")

def format_currency(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
        st.experimental_rerun()

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
        st.experimental_rerun()

# ========================
# --- RIEPILOGO SPESE
# ========================
if not df.empty:
    st.header("📊 Riepilogo Spese")
    spese = df[df["tipo"] == "Spesa"].copy()
    if not spese.empty:
        spese["Importo_num"] = clean_importo(spese["importo"])
        spese["Importo_fmt"] = spese["Importo_num"].apply(format_currency)
        st.dataframe(spese[["data", "categoria", "Importo_fmt"]])

        totale_spese = spese["Importo_num"].sum()
        st.metric("Totale Spese", format_currency(totale_spese) + " €")

        soglia_massima = 2500.0
        totale_spese_valore = totale_spese if totale_spese <= soglia_massima else soglia_massima
        restante = soglia_massima - totale_spese_valore

        valori = [totale_spese_valore, restante]
        colori = ["#e74c3c", "#27ae60"]

        percent_speso = (totale_spese_valore / soglia_massima) * 100 if soglia_massima else 0
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
            st.metric("Speso", f"{percent_speso:.1f}%", delta=-totale_spese_valore)
        with col2:
            st.metric("Disponibile", f"{percent_disp:.1f}%", delta=restante)

    else:
        st.info("Nessuna spesa registrata.")

    # ========================
    # --- RIEPILOGO RISPARMI
    # ========================
    st.header("💰 Riepilogo Risparmi")
    risp = df[df["tipo"] == "Risparmio"].copy()
    if not risp.empty:
        risp["Importo_num"] = clean_importo(risp["importo"])
        risp["Importo_fmt"] = risp["Importo_num"].apply(format_currency)
        st.dataframe(risp[["data", "categoria", "Importo_fmt"]])

        totale_risparmi = risp["Importo_num"].sum()
        st.metric("Saldo Risparmi", format_currency(totale_risparmi) + " €")

        obiettivo_risparmio = 30000.0
        percentuale_raggiunta = totale_risparmi / obiettivo_risparmio * 100 if obiettivo_risparmio else 0
        st.subheader("🎯 Percentuale Obiettivo Risparmi")
        st.metric(
            label="Risparmio raggiunto",
            value=f"{percentuale_raggiunta:.1f}%",
            delta=f"{format_currency(totale_risparmi)} € su {format_currency(obiettivo_risparmio)} €"
        )
    else:
        st.info("Nessun risparmio registrato.")
else:
    st.info("Nessun dato ancora inserito.")
