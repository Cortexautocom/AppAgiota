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
# 🔹 BAIXAR DO SUPABASE
# ==========================
def baixar_do_supabase():
    """Baixa todos os clientes do Supabase e salva no banco local SQLite."""
    try:
        print("☁️ Baixando dados do Supabase...")
        response = supabase.table(REMOTE_TABLE).select("*").execute()

        if hasattr(response, "data"):
            data = response.data
        else:
            data = response.get("data", [])

        if not data:
            print("⚠ Nenhum dado encontrado no Supabase.")
            return False

        print(f"✅ {len(data)} registros encontrados no Supabase.")

        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()

        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {LOCAL_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nome TEXT,
            CPF TEXT,
            Endereço TEXT,
            Cidade TEXT,
            Telefone TEXT,
            Indicação TEXT
        )
        """)
        conn.commit()

        # Limpa e insere novos dados
        cur.execute(f"DELETE FROM {LOCAL_TABLE}")
        for c in data:
            cur.execute(f"""
                INSERT INTO {LOCAL_TABLE} (Nome, CPF, Endereço, Cidade, Telefone, Indicação)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                c.get("Nome", ""),
                c.get("CPF", ""),
                c.get("Endereço", ""),
                c.get("Cidade", ""),
                c.get("Telefone", ""),
                c.get("Indicação", "")
            ))

        conn.commit()
        conn.close()

        print("💾 Dados importados para o banco local com sucesso!")
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

        # Remove todos os dados antigos no Supabase
        supabase.table(REMOTE_TABLE).delete().neq("id", 0).execute()

        # Insere todos os dados novos
        registros = []
        for d in dados:
            registros.append({
                "Nome": d[0],
                "CPF": d[1],
                "Endereço": d[2],
                "Cidade": d[3],
                "Telefone": d[4],
                "Indicação": d[5]
            })

        supabase.table(REMOTE_TABLE).insert(registros).execute()

        print(f"✅ {len(registros)} registros enviados para o Supabase com sucesso!")
        return True

    except Exception as e:
        print(f"⚠ Erro ao salvar no Supabase: {e}")
        return False
