import os
from sqlalchemy import create_engine, text
import pandas as pd

# Connessione al database PostgreSQL tramite variabile d'ambiente
DB_URL = os.environ.get("DATABASE_URL")  # Assicurati di aver impostato DATABASE_URL su Streamlit Cloud
engine = create_engine(DB_URL, echo=True)

# --- Funzioni per utenti ---
def get_user(email):
    """Restituisce l'utente se esiste, altrimenti None"""
    query = text("SELECT * FROM utenti WHERE email = :email")
    result = pd.read_sql(query, engine, params={"email": email})
    return result.iloc[0] if not result.empty else None

def create_user(email):
    """Crea un nuovo utente e restituisce l'id"""
    query = text("INSERT INTO utenti (email) VALUES (:email) RETURNING id")
    with engine.connect() as conn:
        result = conn.execute(query, {"email": email}).fetchone()
        conn.commit()
        return result[0]

# --- Funzioni per movimenti ---
def get_movimenti(user_id):
    """Restituisce tutti i movimenti di un utente ordinati per data"""
    query = text("SELECT * FROM movimenti WHERE user_id = :user_id ORDER BY data DESC")
    return pd.read_sql(query, engine, params={"user_id": user_id})

def salva_dato(user_id, tipo, data, importo, categoria=""):
    """Salva un nuovo movimento"""
    query = text("""
        INSERT INTO movimenti (user_id, tipo, data, importo, categoria)
        VALUES (:user_id, :tipo, :data, :importo, :categoria)
    """)
    with engine.connect() as conn:
        conn.execute(query, {
            "user_id": user_id,
            "tipo": tipo,
            "data": data,
            "importo": importo,
            "categoria": categoria
        })
        conn.commit()
