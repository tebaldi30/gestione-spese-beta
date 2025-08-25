import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

# --- Connessione al DB usando DATABASE_URL ---
def get_connection():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )

# --- Creazione tabelle se non esistono ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Tabella utenti
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            telefono TEXT UNIQUE
        );
    """)

    # Tabella movimenti
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimenti (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            tipo VARCHAR(50) NOT NULL,
            data DATE NOT NULL,
            importo NUMERIC(10,2) NOT NULL,
            categoria VARCHAR(100)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

# --- Gestione utenti ---
def register_user(email, password, telefono=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (email, password, telefono)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (email, generate_password_hash(password), telefono))
        user_id = cur.fetchone()["id"]
        conn.commit()
        return user_id
    except Exception:
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()

def login_user(email, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and check_password_hash(user["password"], password):
        return user
    return None

# --- Recupera utente da id ---
def get_user_by_id(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, email, telefono FROM users WHERE id = %s;", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

# --- Recupera utente da telefono (per WhatsApp bot) ---
def get_user_by_phone(telefono):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, email, telefono FROM users WHERE telefono = %s;", (telefono,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

# --- Aggiorna numero di telefono ---
def update_user_phone(user_id, telefono):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET telefono = %s WHERE id = %s;", (telefono, user_id))
    conn.commit()
    cur.close()
    conn.close()

# --- Gestione movimenti ---
def add_movimento(user_id, tipo, data, importo, categoria):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO movimenti (user_id, tipo, data, importo, categoria)
        VALUES (%s, %s, %s, %s, %s);
    """, (user_id, tipo, data, importo, categoria))
    conn.commit()
    cur.close()
    conn.close()

def get_movimenti(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movimenti WHERE user_id = %s ORDER BY data DESC;", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
