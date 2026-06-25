import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("❌ No se encontraron las credenciales en el archivo .env")

supabase: Client = create_client(URL, KEY)

def insertar_fila_trabajo(titulo: str, compania: str, ubicacion: str, rango_salarial: str, descripcion: str, url: str, estado: int, fecha_creacion: str, id_fuente: int):
    try:
        print(f"🚀 Insertando fila a tabla trabajos: '{titulo}'...")
        response = supabase.table("trabajos").insert([
            {
                "titulo": titulo,
                "compania": compania,
                "ubicacion": ubicacion,
                "rango_salarial": rango_salarial,
                "descripcion": descripcion,
                "url": url,
                "estado": estado,
                "fecha_creacion": fecha_creacion,
                "id_fuente": id_fuente
            }
        ]).execute()
        
        print(f"✅ Trabajo guardado con éxito.")
        return response.data # Supabase devuelve una lista con las filas insertadas
    except Exception as e:
        print(f"❌ Error al insertar trabajo: {e}")
        return None


def insertar_fila_pregunta(id_trabajo: int, pregunta: str, tipo_pregunta: int, respuesta_generada_ia: str):
    try:
        print(f"🚀 Insertando fila a tabla preguntas: '{pregunta[:30]}...'")
        # Corregido: apuntaba a "trabajos", ahora apunta a "preguntas" (cambia el nombre si tu tabla se llama distinto)
        response = supabase.table("preguntas").insert([
            {
                "id_trabajo": id_trabajo,
                "pregunta": pregunta,
                "tipo_pregunta": tipo_pregunta,
                "respuesta_generada_ia": respuesta_generada_ia
            }
        ]).execute()
        
        print(f"✅ Pregunta guardada con éxito.")
        return response.data
    except Exception as e:
        print(f"❌ Error al insertar pregunta: {e}")
        return None


if __name__ == "__main__":
    print("--- Iniciando proceso de inserción ---")
    
    # 1. Insertamos el trabajo con datos de prueba (ya que no tienen valores por defecto)
    nuevo_trabajo = insertar_fila_trabajo(
        titulo="Full stack en Copec",
        compania="Copec",
        ubicacion="Santiago, Chile",
        rango_salarial="2.500.000 - 3.000.000 CLP",
        descripcion="Buscamos desarrollador Full Stack con experiencia en Python y React.",
        url="https://empleos.copec.cl/123",
        estado=1,
        fecha_creacion="2026-06-24",
        id_fuente=1
    )
    
    # 2. Si el trabajo se insertó correctamente, extraemos su ID para la pregunta
    if nuevo_trabajo and len(nuevo_trabajo) > 0:
        # Supabase devuelve una lista, tomamos el id del primer elemento devuelto
        trabajo_id = nuevo_trabajo[0]["id"] 
        print(f"🔗 ID generado para el trabajo: {trabajo_id}")
        
        # 3. Insertamos la pregunta asociada a ese trabajo
        insertar_fila_pregunta(
            id_trabajo=trabajo_id,
            pregunta="¿Cuántos años de experiencia tienes con React?",
            tipo_pregunta=1,
            respuesta_generada_ia="El candidato ideal debe contar con al menos 3 años..."
        )
    else:
        print("⚠️ No se pudo obtener el ID del trabajo, se cancela la inserción de la pregunta.")