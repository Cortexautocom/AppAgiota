from supabase import create_client

SUPABASE_URL = "https://zqvbgfqzdcejgxthdmht.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpxdmJnZnF6ZGNlamd4dGhkbWh0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUxMTI5ODAsImV4cCI6MjA3MDY4ODk4MH0.e4NhuarlGNnXrXUWKdLmGoa1DGejn2jmgpbRR_Ztyqw"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔎 Testando conexão...")

try:
    data = supabase.table("Clientes").select("*").limit(10).execute()
    print("✅ Conectado! Primeiros registros:")
    print(data.data)
except Exception as e:
    print("⚠ Erro na conexão:", e)
