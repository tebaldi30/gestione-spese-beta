import os
from sqlalchemy import create_engine
import pandas as pd

# Connessione al database PostgreSQL (variabile ambiente su Streamlit Cloud)
DB_URL = os.environ.get("postgresql://gestione_spese_db_user:SYsP3JeKxJX66Toq1BXnJSciX2gUx6EE@dpg-d2l2k8v5r7bs73d91ar0-a.oregon-postgres.render.com/gestione_spese_db")
engine = create_engine(DB_URL)

# --- Funzioni per utenti ---
def get_user(email):
    """Restituisce l'utente se esiste, altrimenti None"""
    query = f"SELECT * FROM utenti WHERE email='{email}'"
    result = pd.read_sql(query, engine)
    return result.iloc[0] if not result.empty else None

def create_user(email):
    """Crea un nuovo utente e restituisce l'id"""
    query = f"INSERT INTO utenti (email) VALUES ('{email}') RETURNING id"
    result = engine.execute(query).fetchone()
    return result[0]

# --- Funzioni per movimenti ---
def get_movimenti(user_id):
    """Restituisce tutti i movimenti di un utente ordinati per data"""
    query = f"SELECT * FROM movimenti WHERE user_id={user_id} ORDER BY data DESC"
    return pd.read_sql(query, engine)

def salva_dato(user_id, tipo, data, importo, categoria=""):
    """Salva un nuovo movimento"""
    query = f"""
    INSERT INTO movimenti (user_id, tipo, data, importo, categoria)
    VALUES ({user_id}, '{tipo}', '{data}', {importo}, '{categoria}')
    """
    engine.execute(query)
