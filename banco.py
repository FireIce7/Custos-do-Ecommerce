import sqlite3


def get_connection():
    return sqlite3.connect("data.db")


def get_calc_var(name):
    conn = get_connection()
    c = conn.cursor()
    row = c.execute(
        "SELECT value FROM production_variables WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row[0] if row else None


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Tabela de variáveis da calculadora
    c.execute("""
        CREATE TABLE IF NOT EXISTS production_variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            value REAL
        )
    """)

    # Tabela de categorias
    c.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    # Tabela de variáveis de custos
    c.execute("""
        CREATE TABLE IF NOT EXISTS variaveis_custos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor REAL,
            categoria_id INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)

    # Tabela de produtos
    c.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria_id INTEGER,
            formula TEXT,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    """)

    conn.commit()
    conn.close()
