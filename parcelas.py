import sqlite3
import uuid
from supabase_utils import baixar_parcelas, enviar_parcelas
from config import get_local_db_path

# Lista que vai guardar as parcelas em memória
parcelas = []

# 🔹 Carregar parcelas do banco local
def carregar_parcelas():
    print("DEBUG - Carregando parcelas do banco...")
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()
    cur.execute("SELECT * FROM parcelas")
    dados = cur.fetchall()
    conn.close()

    print("DEBUG - Parcelas encontradas no banco:", dados)

    global parcelas
    parcelas = dados
    return dados

# 🔹 Salvar parcelas no banco local
def salvar_parcelas():
    global parcelas
    conn = sqlite3.connect(get_local_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM parcelas")
    for parcela in parcelas:
        # Se não tiver ID, gera um novo UUID
        if not parcela[0]:
            parcela = (str(uuid.uuid4()),) + parcela[1:]
        cursor.execute("INSERT INTO parcelas VALUES (?, ?, ?, ?, ?, ?, ?)", parcela)
    conn.commit()
    conn.close()

# 🔹 Baixar da nuvem
def sincronizar_parcelas_download():
    global parcelas
    parcelas = baixar_parcelas()

# 🔹 Enviar para a nuvem
def sincronizar_parcelas_upload():
    global parcelas
    enviar_parcelas(parcelas)
