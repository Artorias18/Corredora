import os
from dotenv import load_dotenv
from supabase import create_client, Client

from utils.file_utils import resource_path

# 🔹 Cargar .env desde la ruta correcta (script / exe / setup)
env_path = resource_path(".env")
load_dotenv(env_path)

# 🔹 Credenciales desde .env
url = os.getenv("SUPABASE_URL")
public_key = os.getenv("SUPABASE_KEY")
service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# 🔒 Validación clara (evita errores silenciosos)
if not url or not public_key:
    raise RuntimeError("SUPABASE_URL o SUPABASE_KEY no cargadas desde .env")

if not service_role_key:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY no cargada desde .env")

# 🔹 Cliente público
supabase: Client = create_client(url, public_key)

# 🔹 Cliente ADMIN (Auth Admin API)
supabase_admin: Client = create_client(
    url,
    service_role_key
)
