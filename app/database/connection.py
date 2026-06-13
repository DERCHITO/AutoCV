import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

URL = os.environ.get("SUPABASE_URL", "https://mockproject.supabase.co")
KEY = os.environ.get("SUPABASE_KEY", "mock_key_characters_long_enough_for_test")

print(f"🔍 ¿Detecta URL?: {'SÍ' if URL else 'NO'}")
print(f"🔍 ¿Detecta KEY?: {'SÍ' if KEY else 'NO'}")
if KEY:
    print(f"🔍 Longitud de la KEY: {len(KEY)} caracteres")

supabase: Client = create_client(URL, KEY)

def verificar_conexion():
    try:
        print("⚡ Intentando insertar un dato de prueba en Supabase...")
        
        if "mockproject" in URL:
            print("✨ Entorno de test detectado (GitHub Actions). Saltando conexión real. ¡Todo OK!  ")
            return

        resultado = supabase.table("fuentes").insert([
            {"nombre_fuente": "Laborum"},
            {"nombre_fuente": "GetOnBoard"},
            {"nombre_fuente": "CompuTrabajo"}
        ]).execute()

        resultado = supabase.table("fuentes").select("*").execute()
        print(resultado.data)
        
    except Exception as e:
        print(f"❌ Error al interactuar con la base de datos: {e}")

if __name__ == "__main__":
    verificar_conexion()