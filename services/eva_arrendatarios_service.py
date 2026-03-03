from services.supabase_client import supabase
from datetime import date, datetime



def obtener_arrendatarios():
    """
    Devuelve lista de trabajadores (para combos, tablas, etc.).
    """
    try:
        resp = (
            supabase.table("arrendatario")
            .select("*")
            .order("nombre")  # ascendente por defecto
            .execute()
        )
        return resp.data or []
    except Exception as e:
        print("Error obtener_arrendatarios:", e)
        return []


def obtener_arrendatario(rut: str):
    """
    Devuelve un trabajador específico por RUT.
    """
    try:
        resp = (
            supabase.table("arrendatario")
            .select("*")
            .eq("rut", rut)
            .execute()
        )
        data = resp.data or []
        return data[0] if data else None
    except Exception as e:
        print("Error obtener_trabajador:", e)
        return None


def crear_arrendatario(data: dict):
    """
    Crea un arrendatario nuevo.
    Espera keys: rut, nombre, fecha_ingreso (YYYY-MM-DD), tipo_contrato,
    cargo, afp_id, sistema_salud_id, porcentaje_salud, cargas_familiares,
    sueldo_base, activo.
    """
    try:
        # Asegurar campos mínimos
        if not data.get("rut") or not data.get("nombre"):
            raise ValueError("El RUT y el nombre son obligatorios.")

        # La BD se encarga de created_at, defaults, etc.
        resp = supabase.table("arrendatario").insert(data).execute()
        return resp.data
    except Exception as e:
        print("Error crear_arrendatario:", e)
        return None


def actualizar_arrendatario(rut: str, data: dict):
    """
    Actualiza un trabajador existente por RUT.
    """
    try:
        resp = (
            supabase.table("arrendatario")
            .update(data)
            .eq("rut", rut)
            .execute()
        )
        return resp.data
    except Exception as e:
        print("Error actualizar_arrendatario:", e)
        return None


def eliminar_arrendatario(rut: str):
    """
    Elimina un trabajador y TODAS sus liquidaciones (ON DELETE CASCADE).
    """
    try:
        (
            supabase.table("arrendatario")
            .delete()
            .eq("rut", rut)
            .execute()
        )
        return True
    except Exception as e:
        print("Error eliminar_arrendatario:", e)
        return False


def safe_numeric(value):
    if value in (None, "", " "):
        return 0
    try:
        return float(value)
    except:
        return 0



def cargar_detalle(eval_id):
    resp = supabase.rpc(
        "obtener_eval_independiente_detalle",
        {"p_eval_id": eval_id}
    ).execute()

    return resp.data


def obtener_evaluaciones_arrendatario():

    resp = supabase.rpc(
        "obtener_evaluaciones_arrendatario"
    ).execute()

    return resp.data or []


