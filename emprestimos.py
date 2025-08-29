import sqlite3
import uuid
from supabase_utils import baixar_emprestimos, enviar_emprestimos
from config import get_local_db_path

# Lista que vai guardar os empréstimos em memória
emprestimos = []


# 🔹 Carregar empréstimos do banco local
def carregar_emprestimos():
    
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()
    cur.execute("SELECT * FROM emprestimos")
    dados = cur.fetchall()
    conn.close()

    

    global emprestimos
    emprestimos = dados
    return dados


# 🔹 Salvar todos os empréstimos no banco local
def salvar_emprestimos():
    global emprestimos
    conn = sqlite3.connect(get_local_db_path())
    cursor = conn.cursor()

    for emprestimo in emprestimos:
        # Garante que o ID nunca será nulo
        if not emprestimo[0] or emprestimo[0] == "null":
            emprestimo = (str(uuid.uuid4()),) + emprestimo[1:]

        cursor.execute("""
            INSERT OR REPLACE INTO emprestimos (id, id_cliente, valor, data_inicio, parcelas, observacao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, emprestimo)

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
    emprestimos_corrigidos = []
    for e in emprestimos:
        if not e[0] or e[0] == "null":
            novo_id = str(uuid.uuid4())
            e = (novo_id,) + e[1:]
        emprestimos_corrigidos.append(e)
    emprestimos = emprestimos_corrigidos
    enviar_emprestimos(emprestimos)
