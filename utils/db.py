import psycopg2
import os
from psycopg2.extras import RealDictCursor

def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=RealDictCursor)

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
        user_email TEXT NOT NULL,
        tipo TEXT NOT NULL,
        data DATE NOT NULL,
        importo NUMERIC NOT NULL,
        categoria TEXT
    );
    """)
    conn.commit()
    conn.close()

def add_movimento(user_email, tipo, data, importo, categoria=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO movimenti (user_email, tipo, data, importo, categoria) VALUES (%s, %s, %s, %s, %s)",
        (user_email, tipo, data, importo, categoria)
    )
    conn.commit()
    conn.close()

def get_movimenti(user_email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movimenti WHERE user_email = %s ORDER BY data DESC", (user_email,))
    rows = cur.fetchall()
    conn.close()
    return rows
