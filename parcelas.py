import sqlite3
import uuid
from supabase_utils import baixar_parcelas, enviar_parcelas
from config import get_local_db_path

# Lista que vai guardar as parcelas em memória
parcelas = []


# 🔹 Carregar todas as parcelas do banco local
def carregar_parcelas():
    print("DEBUG - Carregando todas as parcelas do banco...")
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()
    cur.execute("SELECT * FROM parcelas")
    dados = cur.fetchall()
    conn.close()

    print("DEBUG - Parcelas encontradas no banco:", dados)

    global parcelas
    parcelas = dados
    return dados


# 🔹 Carregar parcelas de um empréstimo específico
def carregar_parcelas_por_emprestimo(id_emprestimo):
    """Retorna todas as parcelas de um empréstimo específico"""
    print(f"DEBUG - Carregando parcelas do empréstimo {id_emprestimo}...")
    conn = sqlite3.connect(get_local_db_path())
    cur = conn.cursor()
    cur.execute("SELECT * FROM parcelas WHERE id_emprestimo = ?", (id_emprestimo,))
    dados = cur.fetchall()
    conn.close()

    print("DEBUG - Parcelas encontradas:", dados)

    global parcelas
    parcelas = dados
    return dados


# 🔹 Salvar todas as parcelas no banco local
def salvar_parcelas(lista=None):
    global parcelas
    if lista is not None:
        parcelas = lista

    conn = sqlite3.connect(get_local_db_path())
    cursor = conn.cursor()

    for parcela in parcelas:
        if not parcela[0] or parcela[0] == "null":
            parcela = (str(uuid.uuid4()),) + parcela[1:]

        cursor.execute("""
            INSERT OR REPLACE INTO parcelas (
                id, id_emprestimo, numero, valor, vencimento,
                juros, desconto, parcela_atualizada, valor_pago,
                residual, pago, data_pagamento
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, parcela)

    conn.commit()
    conn.close()
    print(f"✅ {len(parcelas)} parcelas salvas no banco local.")


# 🔹 Criar ou atualizar uma parcela
def adicionar_ou_atualizar_parcela(
    id_emprestimo, numero, valor, vencimento,
    juros="", desconto="", parcela_atualizada="",
    valor_pago="", residual="", pago="Não", data_pagamento=""
):
    """
    Adiciona ou atualiza parcela com todos os campos novos.
    """
    global parcelas

    # Verifica se já existe
    existente = None
    for p in parcelas:
        if p[1] == id_emprestimo and str(p[2]) == str(numero):
            existente = p
            break

    if existente:
        parcela_id = existente[0]
        nova_parcela = (
            parcela_id, id_emprestimo, numero, valor, vencimento,
            juros, desconto, parcela_atualizada, valor_pago,
            residual, pago, data_pagamento
        )
        parcelas = [nova_parcela if p[0] == parcela_id else p for p in parcelas]
        print(f"🔄 Parcela atualizada: {nova_parcela}")
    else:
        parcela_id = str(uuid.uuid4())
        nova_parcela = (
            parcela_id, id_emprestimo, numero, valor, vencimento,
            juros, desconto, parcela_atualizada, valor_pago,
            residual, pago, data_pagamento
        )
        parcelas.append(nova_parcela)
        print(f"✅ Nova parcela criada: {nova_parcela}")

    salvar_parcelas()
    return nova_parcela



# 🔹 Baixar da nuvem
def sincronizar_parcelas_download():
    global parcelas
    parcelas = baixar_parcelas()
    print(f"⬇️ {len(parcelas)} parcelas baixadas do Supabase.")


# 🔹 Enviar para a nuvem
def sincronizar_parcelas_upload():
    global parcelas
    parcelas_corrigidas = []
    for p in parcelas:
        if not p[0] or p[0] == "null":
            novo_id = str(uuid.uuid4())
            p = (novo_id,) + p[1:]
        parcelas_corrigidas.append(p)
    parcelas = parcelas_corrigidas
    enviar_parcelas(parcelas)
    print(f"⬆️ {len(parcelas)} parcelas enviadas ao Supabase.")

