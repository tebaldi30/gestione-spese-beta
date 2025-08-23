import psycopg2
import psycopg2.extras
import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash

def get_connection():
    conn = psycopg2.connect(st.secrets["DATABASE_URL"], sslmode="require")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Tabella utenti
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    """)

    # Tabella movimenti (spese/risparmi)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS movimenti (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        tipo TEXT NOT NULL,
        data DATE NOT NULL,
        importo NUMERIC NOT NULL,
        categoria TEXT
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

# --- Gestione utenti ---
def register_user(email, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (email, password) VALUES (%s, %s) RETURNING id",
                    (email, generate_password_hash(password)))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def login_user(email, password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and check_password_hash(user["password"], password):
        return dict(user)
    return None

# --- Movimenti ---
def add_movimento(user_id, tipo, data, importo, categoria=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO movimenti (user_id, tipo, data, importo, categoria) VALUES (%s, %s, %s, %s, %s)",
        (user_id, tipo, data, importo, categoria)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_movimenti(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM movimenti WHERE user_id = %s ORDER BY data DESC", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
