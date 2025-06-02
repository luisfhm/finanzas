from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Conectar a Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def registrar_usuario(email, password):
    return supabase.auth.sign_up({
        "email": email,
        "password": password
    })

def login_usuario(email, password):
    return supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
