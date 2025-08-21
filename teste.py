from config import criar_tabelas_local, get_local_db_path
import sqlite3

criar_tabelas_local()

conn = sqlite3.connect(get_local_db_path())
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("🧾 Tabelas disponíveis:", cur.fetchall())
conn.close()
