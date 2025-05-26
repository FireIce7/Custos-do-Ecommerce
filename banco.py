import sqlite3

def get_connection():
    return sqlite3.connect("data.db")

def get_calc_var(name):
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT value FROM production_variables WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row[0] if row else None