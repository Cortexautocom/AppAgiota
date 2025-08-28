from supabase import create_client, Client
import sqlite3
import os
from dotenv import load_dotenv

# ==========================
# 🔹 CONFIGURAÇÕES DO SUPABASE
# ==========================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================
# 🔹 TABELAS LOCAIS E REMOTAS
# ==========================
TABELAS = {
    "clientes": {
        "local": "clientes",
        "remota": "clientes",
        "campos": ["id_cliente", "nome", "cpf", "telefone", "endereco", "cidade", "indicacao"],
        "chave": "id_cliente"
    },
    "emprestimos": {
        "local": "emprestimos",
        "remota": "emprestimos",
        "campos": ["id", "id_cliente", "valor", "data_inicio", "parcelas", "observacao"],  # ✅ inclui id
        "chave": "id"
    },
    "parcelas": {
        "local": "parcelas",
        "remota": "parcelas",
        "campos": [
            "id", "id_emprestimo", "numero", "valor", "vencimento",
            "juros", "desconto", "parcela_atualizada", "valor_pago",
            "residual", "pago", "data_pagamento"
        ],
        "chave": "id"
    },

    "movimentacoes": {
        "local": "movimentacoes",
        "remota": "movimentacoes",
        "campos": ["id", "tipo", "valor", "data", "descricao", "id_relacionado", "origem"],  # ✅ inclui id
        "chave": "id"
    }
}

LOCAL_DB = "dados.db"

# ==========================
# 🔹 FUNÇÕES GENÉRICAS
# ==========================
def baixar_tabela(nome):
    """Baixa dados de uma tabela específica do Supabase."""
    try:
        config = TABELAS[nome]
        print(f"☁️ Baixando {nome} do Supabase...")
        response = supabase.table(config["remota"]).select("*").execute()
        data = response.data if hasattr(response, "data") else []

        if not data:
            print(f"⚠ Nenhum dado encontrado em {config['remota']}.")
            return []

        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()

        # Confirma se a tabela existe
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{config['local']}'")
        if not cur.fetchone():
            raise RuntimeError(f"⚠ A tabela local '{config['local']}' não existe! Rode verificar_tabelas() antes.")

        # Limpa e insere dados
        cur.execute(f"DELETE FROM {config['local']}")
        for item in data:
            valores = [item.get(c, "") for c in config["campos"]]
            placeholders = ", ".join(["?"] * len(valores))
            cur.execute(f"""
                INSERT INTO {config['local']} ({', '.join(config['campos'])})
                VALUES ({placeholders})
            """, valores)

        conn.commit()
        conn.close()
        print(f"✅ {len(data)} registros de {nome} salvos localmente.")
        return data

    except Exception as e:
        print(f"⚠ Erro ao baixar {nome}: {e}")
        return []


def enviar_tabela(nome, registros):
    """Envia dados de uma tabela específica para o Supabase."""
    try:
        config = TABELAS[nome]
        if not registros:
            print(f"⚠ Nenhum dado de {nome} para enviar.")
            return False

        registros_validos = []
        for r in registros:
            if isinstance(r, tuple):
                # Converte tupla para dict com todos os campos, inclusive o ID
                r_dict = {c: r[i] for i, c in enumerate(config["campos"])}
            else:
                r_dict = r

            # Aceita registros mesmo que algum campo seja vazio, desde que o ID exista
            if r_dict.get(config["chave"]):
                registros_validos.append(r_dict)

        if not registros_validos:
            print(f"⚠ Nenhum registro válido de {nome} para enviar.")
            return False

        response = supabase.table(config["remota"]).upsert(
            registros_validos,
            on_conflict=[config["chave"]]
        ).execute()

        enviados = len(response.data) if response.data else len(registros_validos)
        print(f"✅ {enviados} registros de {nome} enviados ao Supabase.")
        return True

    except Exception as e:
        print(f"⚠ Erro ao enviar {nome}: {e}")
        return False

# ==========================
# 🔹 FUNÇÕES ESPECÍFICAS POR MÓDULO
# ==========================
def baixar_clientes():
    return baixar_tabela("clientes")

def enviar_clientes(registros):
    return enviar_tabela("clientes", registros)

def baixar_emprestimos():
    return baixar_tabela("emprestimos")

def enviar_emprestimos(registros):
    return enviar_tabela("emprestimos", registros)

def baixar_parcelas():
    return baixar_tabela("parcelas")

def enviar_parcelas(registros):
    return enviar_tabela("parcelas", registros)

def baixar_movimentacoes():
    return baixar_tabela("movimentacoes")

def enviar_movimentacoes(registros):
    return enviar_tabela("movimentacoes", registros)
