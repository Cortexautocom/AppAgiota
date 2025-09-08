import bcrypt
import uuid
from supabase_utils import supabase

def criar_usuario_interativo():
    print("=== Criar novo usuário no Supabase ===")

    email = input("Email: ").strip()
    senha = input("Senha: ").strip()
    nome = input("Nome completo: ").strip()
    cpf = input("CPF (apenas números): ").strip()
    whatsapp = input("Whatsapp: ").strip()
    empresa = input("Nome da empresa (ou deixe vazio se PF): ").strip()

    # 🔹 gera hash da senha
    senha_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # 🔹 cria IDs automáticos
    id_usuario = str(uuid.uuid4())
    id_empresa = str(uuid.uuid4()) if empresa else str(uuid.uuid4())  # sempre gera

    novo_usuario = {
        "id": id_usuario,
        "email": email,
        "senha_hash": senha_hash,
        "id_empresa": id_empresa,
        "nome": nome,
        "cpf": cpf,
        "whatsapp": whatsapp,
        "empresa": empresa if empresa else "Pessoa Física",
        "confirmado": True  # já entra confirmado
    }

    try:
        response = supabase.table("usuarios").insert(novo_usuario).execute()
        print("✅ Usuário criado com sucesso!")
        print("🔹 ID usuário:", id_usuario)
        print("🔹 ID empresa:", id_empresa)
    except Exception as e:
        print("⚠ Erro ao criar usuário:", e)


if __name__ == "__main__":
    criar_usuario_interativo()
