import sqlite3
from supabase_utils import baixar_movimentacoes, enviar_movimentacoes
from config import get_local_db_path

# Lista que vai guardar as movimentações em memória
movimentacoes = []

# 🔹 Carregar movimentações do banco local
def carregar_movimentacoes():
    print("DEBUG - Carregando movimentações do banco...")
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()
    cur.execute("SELECT * FROM movimentacoes")
    dados = cur.fetchall()
    conn.close()

    print("DEBUG - Movimentações encontradas no banco:", dados)

    global movimentacoes
    movimentacoes = dados
    return dados

# 🔹 Salvar movimentações no banco local
def salvar_movimentacoes():
    global movimentacoes
    conn = sqlite3.connect(get_local_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movimentacoes")
    for mov in movimentacoes:
        cursor.execute("INSERT INTO movimentacoes VALUES (?, ?, ?, ?, ?, ?)", mov)
    conn.commit()
    conn.close()

# 🔹 Baixar da nuvem
def sincronizar_movimentacoes_download():
    global movimentacoes
    movimentacoes = baixar_movimentacoes()

# 🔹 Enviar para a nuvem
def sincronizar_movimentacoes_upload():
    global movimentacoes
    enviar_movimentacoes(movimentacoes)
