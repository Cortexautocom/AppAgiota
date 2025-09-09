import bcrypt
import uuid
from supabase_utils import supabase

def criar_usuario_interativo():
    print("=== Criar novo usuário no Supabase ===")

    nome = input("Nome completo: ").strip()
    cpf = input("CPF (apenas números): ").strip()
    email = input("Email: ").strip()
    whatsapp = input("Whatsapp: ").strip()
    senha = input("Senha: ").strip()

    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    id_usuario = str(uuid.uuid4())

    novo_usuario = {
        "id": id_usuario,
        "nome": nome,
        "cpf": cpf,
        "email": email,
        "whatsapp": whatsapp,
        "senha_hash": senha_hash
    }

    try:
        supabase.table("usuarios").insert(novo_usuario).execute()
        print("✅ Usuário criado com sucesso!")
        print("🔹 ID usuário:", id_usuario)
    except Exception as e:
        print("⚠ Erro ao criar usuário:", e)


if __name__ == "__main__":
    criar_usuario_interativo()
