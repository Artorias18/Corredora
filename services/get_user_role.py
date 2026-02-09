from services.supabase_client import supabase

def get_user_role(user_id):
    response = (
        supabase
        .table("usuarios")
        .select("rol")
        .eq("id", user_id)
        .execute()
    )

    if response.data:
        return response.data[0]["rol"]

    return "usuario"
