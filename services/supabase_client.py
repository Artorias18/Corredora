import os
from dotenv import load_dotenv
from supabase import create_client, Client

#.env
load_dotenv()

#Credenciales desde .env
url = os.getenv("SUPABASE_URL")
public_key = os.getenv("SUPABASE_KEY")


supabase: Client = create_client(url, public_key)
