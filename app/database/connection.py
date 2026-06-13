import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

# --- BLOQUE DE VERIFICACIÓN ---
print(f"🔍 ¿Detecta URL?: {'SÍ' if URL else 'NO'}")
print(f"🔍 ¿Detecta KEY?: {'SÍ' if KEY else 'NO'}")
if KEY:
    print(f"🔍 Longitud de la KEY: {len(KEY)} caracteres")
# ------------------------------

if not URL or not KEY:
    raise ValueError("❌ Error: No se encontraron las credenciales...")


supabase: Client = create_client(URL, KEY)


def verificar_conexion():
    try:
        print("⚡ Intentando insertar un dato de prueba en Supabase...")

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