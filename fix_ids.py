import sqlite3, uuid
from config import get_local_db_path

conn = sqlite3.connect(get_local_db_path())
cur = conn.cursor()

# Corrigir empréstimos sem ID
cur.execute("SELECT rowid, * FROM emprestimos WHERE id IS NULL OR id = ''")
rows = cur.fetchall()
for r in rows:
    rowid = r[0]
    new_id = str(uuid.uuid4())
    cur.execute("UPDATE emprestimos SET id = ? WHERE rowid = ?", (new_id, rowid))
    print(f"🔧 Corrigido empréstimo rowid {rowid} -> {new_id}")

# Corrigir parcelas sem ID
cur.execute("SELECT rowid, * FROM parcelas WHERE id IS NULL OR id = ''")
rows = cur.fetchall()
for r in rows:
    rowid = r[0]
    new_id = str(uuid.uuid4())
    cur.execute("UPDATE parcelas SET id = ? WHERE rowid = ?", (new_id, rowid))
    print(f"🔧 Corrigida parcela rowid {rowid} -> {new_id}")

conn.commit()
conn.close()
print("✅ Todos os registros agora têm IDs válidos")
