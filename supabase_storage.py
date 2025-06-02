from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def subir_portafolio(usuario_id, path_local):
    nombre_archivo = f"portafolios/portafolio_{usuario_id}.csv"
    with open(path_local, "rb") as f:
        supabase.storage.from_('portafolios').upload(nombre_archivo, f, {"upsert": True})

def descargar_portafolio(usuario_id):
    nombre_archivo = f"portafolios/portafolio_{usuario_id}.csv"
    url = supabase.storage.from_('portafolios').get_public_url(nombre_archivo)
    return url
