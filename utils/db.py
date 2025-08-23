import psycopg2
import os
from psycopg2.extras import RealDictCursor
import hashlib

# Connessione a PostgreSQL (Render)
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", 5432),
        cursor_factory=RealDictCursor
    )

# Creazione tabelle se non esistono
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimenti (
            id SERIAL PRIMARY KEY,
            user_email TEXT REFERENCES users(email),
            tipo TEXT NOT NULL,
            data DATE NOT NULL,
            importo NUMERIC NOT NULL,
            categoria TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Hash password semplice
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Registrazione utente
def register_user(email, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hash_password(password)))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()

# Login utente
def login_user(email, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, hash_password(password)))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None

# Aggiungi movimento (spesa/risparmio)
def add_movimento(user_email, tipo, data, importo, categoria):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO movimenti (user_email, tipo, data, importo, categoria) VALUES (%s, %s, %s, %s, %s)",
        (user_email, tipo, data, importo, categoria)
    )
    conn.commit()
    cur.close()
    conn.close()

# Recupera tutti i movimenti utente
def get_movimenti(user_email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movimenti WHERE user_email = %s ORDER BY data DESC", (user_email,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
