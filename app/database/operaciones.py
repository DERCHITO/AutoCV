import os
import requests
from dotenv import load_dotenv
from supabase import Client, create_client
from typing import List, Dict, Any

load_dotenv()

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("❌ No se encontraron las credenciales en el archivo .env")

supabase: Client = create_client(URL, KEY)


def insertar_fila_trabajo(
    titulo: str,
    compania: str,
    ubicacion: str,
    rango_salarial: str,
    descripcion: str,
    url: str,
    estado: int,
    fecha_creacion: str,
    id_fuente: int,
    preguntas: List[Dict[str, Any]]  # <-- Definimos que es una lista de objetos/diccionarios
):
    URL = os.environ.get("URL_N8N_INSERCION_TRABAJO_SUPABASE")

    if not URL:
        print("\n[AVISO]: No se configuró la variable 'URL_N8N_INSERCION_TRABAJO_SUPABASE' en el archivo .env.")
        print("Se omitirá la insercion del trabajo en supabase.")
        return

    # Construimos el payload incluyendo la lista de preguntas
    payload = {
        "titulo": titulo,
        "compania": compania,
        "ubicacion": ubicacion,
        "rango_salarial": rango_salarial,
        "descripcion": descripcion,
        "url": url,
        "estado": estado,
        "fecha_creacion": fecha_creacion,
        "id_fuente": id_fuente,
        "preguntas": preguntas  # <-- Se envía como un array JSON nativo
    }

    try:
        print(f"🚀 Insertando fila a tabla trabajos: '{titulo}'...")
        # Al usar json=payload, 'requests' convierte automáticamente la lista de Python a un array JSON
        respuesta = requests.post(URL, json=payload, timeout=15)
        respuesta.raise_for_status()
        print("¡Flujo de n8n invocado exitosamente!")
    except requests.exceptions.RequestException as e:
        print(f"Error al invocar el servicio de N8N: {e}")


def insertar_fila_pregunta(
    id_trabajo: int,
    pregunta: str,
    tipo_pregunta: int,
    respuesta_generada_ia: str,
):
    try:
        print(f"🚀 Insertando fila a tabla preguntas: '{pregunta[:30]}...'")
        # Antes apuntaba a "trabajos"; ahora inserta en "preguntas".
        response = supabase.table("preguntas").insert([
            {
                "id_trabajo": id_trabajo,
                "pregunta": pregunta,
                "tipo_pregunta": tipo_pregunta,
                "respuesta_generada_ia": respuesta_generada_ia
            }
        ]).execute()

        print("✅ Pregunta guardada con éxito.")
        return response.data
    except Exception as e:
        print(f"❌ Error al insertar pregunta: {e}")
        return None


if __name__ == "__main__":
    print("--- Iniciando proceso de inserción ---")


    lista_de_preguntas = [
        {"texto_pregunta": "¿Cuántos años de experiencia tienes en Python?", "tipo": "texto"},
        {"texto_pregunta": "¿Cuál es tu pretensión salarial?", "tipo": "numero"},
        {"texto_pregunta": "¿Cuál es tu pretensión salarial?", "tipo": "numero"},
        {"texto_pregunta": "¿Disponibilidad inmediata?", "tipo": "booleano"}
    ]
    # 1. Insertamos el trabajo con datos de prueba (ya que no tienen valores por defecto)
    nuevo_trabajo = insertar_fila_trabajo(
        titulo="PRUEBA N8N",
        compania="Copec",
        ubicacion="Santiago, Chile",
        rango_salarial="2.500.000 - 3.000.000 CLP",
        descripcion="ESTA ES UNA PRUEBA DE CONEXION CON N8N DESDE EL SCRIPT",
        url="https://empleos.copec.cl/123",
        estado=1,
        fecha_creacion="2026-06-24",
        id_fuente=1,
        preguntas=lista_de_preguntas
    )

    # # 2. Si el trabajo se insertó correctamente, extraemos su ID para la pregunta
    # if nuevo_trabajo and len(nuevo_trabajo) > 0:
    #     # Supabase devuelve una lista, tomamos el id del primer elemento devuelto
    #     trabajo_id = nuevo_trabajo[0]["id"]
    #     print(f"🔗 ID generado para el trabajo: {trabajo_id}")

    #     # 3. Insertamos la pregunta asociada a ese trabajo
    #     insertar_fila_pregunta(
    #         id_trabajo=trabajo_id,
    #         pregunta="¿Cuántos años de experiencia tienes con React?",
    #         tipo_pregunta=1,
    #         respuesta_generada_ia="El candidato ideal debe contar con al menos 3 años..."
    #     )
    # else:
    #     print("⚠️ No se pudo obtener el ID del trabajo, se cancela la inserción de la pregunta.")
