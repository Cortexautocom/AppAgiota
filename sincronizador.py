from config import supabase

def sincronizar_clientes(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    for cliente in clientes:
        supabase.table("clientes").upsert({
            "id": cliente[0],
            "nome": cliente[1],
            "cpf": cliente[2],
            "telefone": cliente[3]
        }).execute()
