import os
import sqlite3

DB_PATH = os.path.join("data", "app.db")


def get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
