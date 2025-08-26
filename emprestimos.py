import sqlite3
import uuid
from supabase_utils import baixar_emprestimos, enviar_emprestimos
from config import get_local_db_path

# Lista que vai guardar os empréstimos em memória
emprestimos = []


# 🔹 Carregar empréstimos do banco local
def carregar_emprestimos():
    print("DEBUG - Carregando empréstimos do banco...")
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()
    cur.execute("SELECT * FROM emprestimos")
    dados = cur.fetchall()
    conn.close()

    print("DEBUG - Empréstimos encontrados no banco:", dados)

    global emprestimos
    emprestimos = dados
    return dados


# 🔹 Salvar todos os empréstimos no banco local
def salvar_emprestimos():
    global emprestimos
    conn = sqlite3.connect(get_local_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM emprestimos")
    for emprestimo in emprestimos:
        # Se não tiver ID, gera um novo UUID
        if not emprestimo[0]:
            emprestimo = (str(uuid.uuid4()),) + emprestimo[1:]
        cursor.execute("INSERT INTO emprestimos VALUES (?, ?, ?, ?, ?, ?)", emprestimo)
    conn.commit()
    conn.close()


# 🔹 Criar e salvar um novo empréstimo
def adicionar_emprestimo(id_cliente, valor, data_inicio, parcelas, observacao=""):
    """
    Cria um novo empréstimo com UUID e salva no banco.
    Retorna o registro criado como tupla.
    """
    global emprestimos

    novo_id = str(uuid.uuid4())
    novo_emprestimo = (novo_id, id_cliente, valor, data_inicio, parcelas, observacao)

    emprestimos.append(novo_emprestimo)
    salvar_emprestimos()

    print(f"✅ Novo empréstimo criado: {novo_emprestimo}")
    return novo_emprestimo


# 🔹 Baixar da nuvem
def sincronizar_emprestimos_download():
    global emprestimos
    emprestimos = baixar_emprestimos()


# 🔹 Enviar para a nuvem
def sincronizar_emprestimos_upload():
    global emprestimos
    enviar_emprestimos(emprestimos)
