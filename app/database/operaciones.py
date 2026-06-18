import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("❌ No se encontraron las credenciales en el archivo .env")

supabase: Client = create_client(URL, KEY)

def insertar_fila_trabajo(titulo: str, compañia: str, ubicacion: bool):
    try:
        print(f"🚀 Insertando fila a tabla trabajos: '{titulo}'...")
        response = supabase.table("trabajos").insert([
            {"titulo": titulo}
        ]).execute()
        
        print(f"✅ Fila guardada con éxito.")
        return response.data
    except Exception as e:
        print(f"❌ Error al insertar fila: {e}")
        return None

if __name__ == "__main__":
    # Si ejecutas este archivo directamente, correrá con este valor por defecto
    insertar_fila_trabajo("Full stack en copec")