from supabase import create_client, Client
import sqlite3
import os

# ==========================
# 🔹 CONFIGURAÇÕES DO SUPABASE
# ==========================
SUPABASE_URL = "https://zqvbgfqzdcejgxthdmht.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpxdmJnZnF6ZGNlamd4dGhkbWh0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUxMTI5ODAsImV4cCI6MjA3MDY4ODk4MH0.e4NhuarlGNnXrXUWKdLmGoa1DGejn2jmgpbRR_Ztyqw"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Nome do banco local
LOCAL_DB = "clientes.db"
LOCAL_TABLE = "clientes"
REMOTE_TABLE = "Clientes"


# ==========================
# 🔹 INSERÇÃO LOCAL COM VALIDAÇÃO
# ==========================
def inserir_cliente(nome, cpf, endereco, cidade, telefone, indicacao):
    """Insere cliente no banco local validando campos e CPF duplicado."""
    try:
        if not all([nome.strip(), cpf.strip(), endereco.strip(), cidade.strip(), telefone.strip(), indicacao.strip()]):
            return "⚠ Todos os campos são obrigatórios."

        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()

        # Verifica duplicidade de CPF
        cur.execute(f"SELECT COUNT(*) FROM {LOCAL_TABLE} WHERE CPF = ?", (cpf.strip(),))
        existe = cur.fetchone()[0]
        if existe > 0:
            conn.close()
            return "⚠ Este CPF já está cadastrado!"

        # Insere novo cliente
        cur.execute(f"""
            INSERT INTO {LOCAL_TABLE} (Nome, CPF, Endereço, Cidade, Telefone, Indicação)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome.strip(), cpf.strip(), endereco.strip(), cidade.strip(), telefone.strip(), indicacao.strip()))
        conn.commit()
        conn.close()
        return "✅ Cliente inserido com sucesso!"

    except Exception as e:
        return f"⚠ Erro ao inserir cliente: {e}"


# ==========================
# 🔹 BAIXAR DO SUPABASE
# ==========================
def baixar_do_supabase():
    """Baixa todos os clientes do Supabase e substitui o banco local."""
    try:
        print("☁️ Baixando dados do Supabase...")
        response = supabase.table(REMOTE_TABLE).select("*").execute()
        data = response.data if hasattr(response, "data") else []

        if not data:
            print("⚠ Nenhum dado encontrado no Supabase.")
            return False

        print(f"✅ {len(data)} registros encontrados no Supabase.")

        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()

        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {LOCAL_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nome TEXT NOT NULL,
            CPF TEXT NOT NULL UNIQUE,
            Endereço TEXT NOT NULL,
            Cidade TEXT NOT NULL,
            Telefone TEXT NOT NULL,
            Indicação TEXT NOT NULL
        )
        """)
        conn.commit()

        # Substitui completamente o banco local
        cur.execute(f"DELETE FROM {LOCAL_TABLE}")
        for c in data:
            cur.execute(f"""
                INSERT INTO {LOCAL_TABLE} (Nome, CPF, Endereço, Cidade, Telefone, Indicação)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                c.get("Nome", "").strip(),
                c.get("CPF", "").strip(),
                c.get("Endereço", "").strip(),
                c.get("Cidade", "").strip(),
                c.get("Telefone", "").strip(),
                c.get("Indicação", "").strip()
            ))

        conn.commit()
        conn.close()

        print("💾 Banco local atualizado com sucesso!")
        return True

    except Exception as e:
        print(f"⚠ Erro ao baixar do Supabase: {e}")
        return False


# ==========================
# 🔹 SALVAR NO SUPABASE
# ==========================
def salvar_no_supabase():
    """Envia todos os clientes do banco local para o Supabase."""
    try:
        if not os.path.exists(LOCAL_DB):
            print("⚠ Banco de dados local não encontrado.")
            return False

        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()
        cur.execute(f"SELECT Nome, CPF, Endereço, Cidade, Telefone, Indicação FROM {LOCAL_TABLE}")
        dados = cur.fetchall()
        conn.close()

        if not dados:
            print("⚠ Nenhum dado para enviar ao Supabase.")
            return False

        # 🔎 Monta registros únicos por CPF (evita erro de conflito duplo)
        registros_unicos = {}
        for d in dados:
            if not all(d):  # ignora campos vazios
                continue
            cpf = d[1].strip()
            registros_unicos[cpf] = {
                "Nome": d[0].strip(),
                "CPF": cpf,
                "Endereço": d[2].strip(),
                "Cidade": d[3].strip(),
                "Telefone": d[4].strip(),
                "Indicação": d[5].strip()
            }

        registros = list(registros_unicos.values())
        if not registros:
            print("⚠ Nenhum registro válido para enviar.")
            return False

        # 🔄 UPSERT por CPF
        response = supabase.table(REMOTE_TABLE).upsert(
            registros,
            on_conflict=["CPF"]
        ).execute()

        enviados = len(response.data) if response.data else len(registros)
        print(f"✅ {enviados} registros enviados/atualizados no Supabase!")
        return True

    except Exception as e:
        print(f"⚠ Erro ao salvar no Supabase: {e}")
        return False
