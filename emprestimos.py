import sqlite3
import uuid
from supabase_utils import baixar_emprestimos, enviar_emprestimos
from config import get_local_db_path

# Lista que vai guardar os empréstimos em memória
emprestimos = []


# 🔹 Carregar empréstimos do banco local
def carregar_emprestimos(id_usuario=None, incluir_inativos=False):
    """
    Carrega os empréstimos do banco local.
    Se incluir_inativos=True, traz todos.
    Caso contrário, só os ativos (ativo='sim').
    """
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()

    if incluir_inativos:
        if id_usuario:
            cur.execute("SELECT * FROM emprestimos WHERE id_usuario = ?", (id_usuario,))
        else:
            cur.execute("SELECT * FROM emprestimos")
    else:
        if id_usuario:
            cur.execute("SELECT * FROM emprestimos WHERE id_usuario = ? AND ativo = 'sim'", (id_usuario,))
        else:
            cur.execute("SELECT * FROM emprestimos WHERE ativo = 'sim'")

    dados = cur.fetchall()
    conn.close()

    global emprestimos
    emprestimos = dados
    return dados



# 🔹 Salvar todos os empréstimos no banco local
def salvar_emprestimos(lista=None):
    global emprestimos
    if lista is not None:
        emprestimos = lista    

    conn = sqlite3.connect(get_local_db_path())
    cursor = conn.cursor()

    # Garante que cada empréstimo tenha 9 colunas
    for idx, emp in enumerate(emprestimos, start=1):
        if len(emp) != 9:
            emp = emp + tuple("" for _ in range(9 - len(emp)))                   

        cursor.execute("""
            INSERT OR REPLACE INTO emprestimos (
                id, id_cliente, valor, data_inicio, parcelas,
                observacao, juros, prestacao, id_usuario, ativo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, emp)

    conn.commit()

    # Contar registros atuais
    cursor.execute("SELECT COUNT(*) FROM emprestimos")
    
    conn.close()

# 🔹 Criar e salvar um novo empréstimo
def adicionar_emprestimo(id_cliente, valor, data_inicio, parcelas, observacao="", juros="0", prestacao="0", id_usuario=""):
    global emprestimos

    novo_id = str(uuid.uuid4())
    novo_emprestimo = (
        novo_id,
        id_cliente,
        valor,
        data_inicio,
        parcelas,
        observacao,
        juros,
        prestacao,
        id_usuario,
        "sim"  # 🔹 ativo sempre começa como "sim"
    )

    emprestimos.append(novo_emprestimo)
    salvar_emprestimos()

    return novo_emprestimo




# 🔹 Baixar da nuvem
def sincronizar_emprestimos_download(id_usuario):
    global emprestimos
    emprestimos = baixar_emprestimos(id_usuario)


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

def arquivar_emprestimo(id_emprestimo):
    """
    Marca um empréstimo como arquivado (ativo='não').
    Ele some dos relatórios e da tela financeira, mas continua no banco.
    """
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()
    cur.execute("UPDATE emprestimos SET ativo = 'não' WHERE id = ?", (id_emprestimo,))
    conn.commit()
    conn.close()

    # Atualiza a lista em memória
    global emprestimos
    emprestimos = [e if e[0] != id_emprestimo else e[:-1] + ("não",) for e in emprestimos]

    # 🔹 Sincroniza com o Supabase
    from emprestimos import sincronizar_emprestimos_upload
    sincronizar_emprestimos_upload()

    return True

