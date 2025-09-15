import sqlite3
import uuid
from supabase_utils import baixar_garantias, enviar_garantias
from config import get_local_db_path

# Lista que vai guardar as garantias em memória
garantias = []


# 🔹 Carregar garantias do banco local
def carregar_garantias(id_usuario=None):
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()

    if id_usuario:
        cur.execute("SELECT * FROM garantias WHERE id_usuario = ?", (id_usuario,))
    else:
        cur.execute("SELECT * FROM garantias")

    dados = cur.fetchall()
    conn.close()

    global garantias
    garantias = dados
    return dados


# 🔹 Salvar todas as garantias no banco local
def salvar_garantias(lista=None):
    global garantias
    if lista is not None:
        garantias = lista

    conn = sqlite3.connect(get_local_db_path())
    cursor = conn.cursor()

    for g in garantias:
        if not g[0] or g[0] == "null":
            g = (str(uuid.uuid4()),) + g[1:]

        cursor.execute("""
            INSERT OR REPLACE INTO garantias (
                id, id_cliente, descricao, valor, id_usuario
            ) VALUES (?, ?, ?, ?, ?)
        """, g)

    conn.commit()
    conn.close()


# 🔹 Criar uma nova garantia
def adicionar_garantia(id_cliente, descricao, valor, id_usuario=""):
    global garantias

    novo_id = str(uuid.uuid4())
    nova = (novo_id, id_cliente, descricao, valor, id_usuario)

    garantias.append(nova)
    salvar_garantias()

    return nova


# 🔹 Baixar da nuvem
def sincronizar_garantias_download(id_usuario):
    global garantias
    garantias = baixar_garantias(id_usuario)


# 🔹 Enviar para a nuvem
def sincronizar_garantias_upload():
    global garantias
    enviar_garantias(garantias)

def excluir_garantia(id_garantia):
    """Exclui uma garantia do SQLite e do Supabase"""
    import sqlite3
    from config import get_local_db_path
    from supabase_utils import supabase

    # Excluir do banco local
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()
    cur.execute("DELETE FROM garantias WHERE id = ?", (id_garantia,))
    conn.commit()
    conn.close()

    # Excluir do Supabase
    try:
        supabase.table("garantias").delete().eq("id", id_garantia).execute()
    except Exception as e:
        print(f"⚠ Erro ao excluir garantia no Supabase: {e}")

    # Atualizar lista em memória
    global garantias
    garantias = [g for g in garantias if g[0] != id_garantia]
