def show_dashboard():
    user_email = get_user_email(st.session_state.user)
    st.title("💰 Gestione Spese e Risparmi")
    st.write(f"👋 Benvenuto, utente **{user_email}**")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # Carica dati
    df = pd.DataFrame(get_movimenti(st.session_state.user))
    has_data = not df.empty and "tipo" in df.columns

    if has_data:
        df["importo"] = pd.to_numeric(df["importo"], errors="coerce")

    # --- Form spese (sempre visibile) ---
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

    # --- Form risparmi (sempre visibile) ---
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

    if not has_data:
        st.info("Nessun dato ancora inserito.")
        return

    # --- Riepilogo spese e risparmi e andamento mensile ---
    # (qui tutto il codice riepilogo e grafici, come nel precedente esempio)
    # ...
