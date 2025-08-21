import sqlite3
from supabase_utils import baixar_clientes, enviar_clientes
from config import get_local_db_path

# Lista que vai guardar os clientes em memória
clientes = []

# 🔹 Função para carregar os clientes do banco local
def carregar_clientes():    
    conn = sqlite3.connect(get_local_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes_db = cursor.fetchall()
    conn.close()    

    # Atualiza a variável global
    global clientes
    clientes = clientes_db

    # E também retorna a lista, caso alguém queira usar
    return clientes_db


# 🔹 Função para salvar os clientes no banco local (agora recebe a lista como argumento)
def salvar_clientes(lista_clientes):
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()

    # Limpa a tabela antes de salvar os dados atualizados
    cur.execute("DELETE FROM clientes")

    for cliente in lista_clientes:
        cur.execute("""
            INSERT INTO clientes (
                id_cliente, nome, cpf, telefone, endereco, cidade, indicacao
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, cliente)

    conn.commit()

    # 🔹 Debug: conferir se realmente gravou
    cur.execute("SELECT * FROM clientes")    

    conn.close()


# 🔹 Função para baixar clientes da nuvem (Supabase)
def sincronizar_clientes_download():
    global clientes
    clientes = baixar_clientes()

# 🔹 Função para enviar clientes para a nuvem (Supabase)
def sincronizar_clientes_upload():
    global clientes
    enviar_clientes(clientes)
