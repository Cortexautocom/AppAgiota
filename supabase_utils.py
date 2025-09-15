from supabase import create_client, Client
import sqlite3
import os
from dotenv import load_dotenv
import bcrypt

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
        "campos": ["id_cliente", "nome", "cpf", "telefone", "endereco", "cidade", "indicacao", "id_usuario"],
        "chave": "id_cliente"
    },
    "emprestimos": {
        "local": "emprestimos",
        "remota": "emprestimos",
        "campos": ["id", "id_cliente", "valor", "data_inicio", "parcelas",
                "observacao", "juros", "prestacao", "id_usuario", "ativo"],
        "chave": "id"
    },
    "parcelas": {
        "local": "parcelas",
        "remota": "parcelas",
        "campos": [
            "id", "id_emprestimo", "numero", "valor", "vencimento",
            "juros", "desconto", "pg_principal", "pg_juros",
            "valor_pago", "residual", "data_pagamento", "id_usuario"
        ],
        "chave": "id"
    },
    "garantias": {
        "local": "garantias",
        "remota": "garantias",
        "campos": ["id", "id_cliente", "descricao", "valor", "id_usuario"],
        "chave": "id"
    },
}

LOCAL_DB = "dados.db"

# ==========================
# 🔹 FUNÇÕES GENÉRICAS
# ==========================
def baixar_tabela(nome):
    """Baixa dados de uma tabela específica do Supabase."""
    try:
        config = TABELAS[nome]        
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
        return data

    except Exception as e:
        print(f"⚠ Erro ao baixar {nome}: {e}")
        return []


def enviar_tabela(nome, registros):
    """Envia dados de uma tabela específica para o Supabase."""
    try:
        config = TABELAS[nome]
        if not registros:            
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

        supabase.table(config["remota"]).upsert(
            registros_validos,
            on_conflict=[config["chave"]]
        ).execute()
        
        return True

    except Exception as e:
        print(f"⚠ Erro ao enviar {nome}: {e}")
        return False

# ==========================
# 🔹 FUNÇÕES ESPECÍFICAS POR MÓDULO
# ==========================
def baixar_clientes(id_usuario):
    """Baixa somente os clientes do usuário informado e salva no SQLite local."""
    try:        
        response = supabase.table("clientes").select("*").eq("id_usuario", id_usuario).execute()
        data = response.data if hasattr(response, "data") else []

        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()

        # Confirma se a tabela existe
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
        if not cur.fetchone():
            raise RuntimeError("⚠ A tabela local 'clientes' não existe! Rode verificar_tabelas() antes.")

        # Limpa e insere dados
        cur.execute("DELETE FROM clientes")
        for item in data:
            valores = [item.get(c, "") for c in TABELAS["clientes"]["campos"]]
            placeholders = ", ".join(["?"] * len(valores))
            cur.execute(f"""
                INSERT INTO clientes ({', '.join(TABELAS["clientes"]["campos"])})
                VALUES ({placeholders})
            """, valores)

        conn.commit()
        conn.close()
        
        return data

    except Exception as e:
        print(f"⚠ Erro ao baixar clientes: {e}")
        return []


def enviar_clientes(registros):
    return enviar_tabela("clientes", registros)


def baixar_emprestimos(id_usuario):
    """Baixa apenas os empréstimos do usuário informado."""
    try:
        response = supabase.table("emprestimos").select("*").eq("id_usuario", id_usuario).execute()
        data = response.data if hasattr(response, "data") else []

        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM emprestimos")
        for item in data:
            valores = [item.get(c, "") for c in TABELAS["emprestimos"]["campos"]]
            placeholders = ", ".join(["?"] * len(valores))
            cur.execute(f"""
                INSERT INTO emprestimos ({', '.join(TABELAS["emprestimos"]["campos"])})
                VALUES ({placeholders})
            """, valores)
        conn.commit()
        conn.close()
        return data
    except Exception as e:
        print(f"⚠ Erro ao baixar emprestimos: {e}")
        return []
    

def enviar_emprestimos(registros):
    return enviar_tabela("emprestimos", registros)


def baixar_parcelas(id_usuario):
    """Baixa apenas as parcelas do usuário informado."""
    try:
        response = supabase.table("parcelas").select("*").eq("id_usuario", id_usuario).execute()
        data = response.data if hasattr(response, "data") else []

        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM parcelas")
        for item in data:
            valores = [item.get(c, "") for c in TABELAS["parcelas"]["campos"]]
            placeholders = ", ".join(["?"] * len(valores))
            cur.execute(f"""
                INSERT INTO parcelas ({', '.join(TABELAS["parcelas"]["campos"])})
                VALUES ({placeholders})
            """, valores)
        conn.commit()
        conn.close()
        return data
    except Exception as e:
        print(f"⚠ Erro ao baixar parcelas: {e}")
        return []
    

def enviar_parcelas(registros):
    return enviar_tabela("parcelas", registros)


def baixar_garantias(id_usuario):
    """Baixa apenas as garantias do usuário informado."""
    try:
        response = supabase.table("garantias").select("*").eq("id_usuario", id_usuario).execute()
        data = response.data if hasattr(response, "data") else []

        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()
        cur.execute("DELETE FROM garantias")
        for item in data:
            valores = [item.get(c, "") for c in TABELAS["garantias"]["campos"]]
            placeholders = ", ".join(["?"] * len(valores))
            cur.execute(f"""
                INSERT INTO garantias ({', '.join(TABELAS["garantias"]["campos"])})
                VALUES ({placeholders})
            """, valores)
        conn.commit()
        conn.close()
        return data
    except Exception as e:
        print(f"⚠ Erro ao baixar garantias: {e}")
        return []


def enviar_garantias(registros):
    return enviar_tabela("garantias", registros)


# ==========================
# 🔹 USUÁRIOS (LOGIN)
# ==========================
def criar_usuario(nome, cpf, email, whatsapp, senha):
    """Cria um novo usuário com senha criptografada e dados extras."""
    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    novo_usuario = {
        "nome": nome,
        "cpf": cpf,
        "email": email,
        "whatsapp": whatsapp,
        "senha_hash": senha_hash
    }

    try:
        response = supabase.table("usuarios").insert(novo_usuario).execute()
        return response.data
    except Exception as e:
        print(f"⚠ Erro ao criar usuário: {e}")
        return None


def validar_login(email, senha):
    """Valida login comparando senha com hash armazenado no Supabase."""
    try:
        response = supabase.table("usuarios").select("*").eq("email", email).execute()
        if not response.data:
            return None  # usuário não encontrado

        usuario = response.data[0]
        senha_ok = bcrypt.checkpw(senha.encode("utf-8"), usuario["senha_hash"].encode("utf-8"))

        if senha_ok:
            return usuario  # retorna dados do usuário (inclusive id_empresa)
        else:
            return None
    except Exception as e:
        print(f"⚠ Erro ao validar login: {e}")
        return None


def redefinir_senha(email, nova_senha):
    """Atualiza a senha de um usuário existente."""
    
    try:
        response = supabase.table("usuarios").select("id").eq("email", email).execute()
        if not response.data:
            return False  # usuário não encontrado

        senha_hash = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        supabase.table("usuarios").update({"senha_hash": senha_hash}).eq("email", email).execute()
        return True
    except Exception as e:
        print(f"⚠ Erro ao redefinir senha: {e}")
        return False
