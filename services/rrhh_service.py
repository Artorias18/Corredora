# services/rrhh_service.py

from services.supabase_client import supabase
from datetime import date

# =========================================================================================
#   UTILIDADES INTERNAS
# =========================================================================================

def _get_single(data):
    """Convierte la respuesta Supabase en un dict manejable."""
    if not data or not isinstance(data, list):
        return None
    return data[0] if data else None


# =========================================================================================
#   OBTENER DATOS MAESTROS (AFP, SALUD, TRABAJADORES)
# =========================================================================================

def obtener_afps():
    """Devuelve la lista completa de AFPs."""
    try:
        res = supabase.table("afp").select("id, nombre").order("nombre").execute()
        return res.data or []
    except Exception as e:
        print("Error obtener_afps:", e)
        return []


def obtener_sistemas_salud():
    """Lista Fonasa / Isapres."""
    try:
        res = supabase.table("sistema_salud").select("id, nombre, tipo").order("nombre").execute()
        return res.data or []
    except Exception as e:
        print("Error obtener_sistemas_salud:", e)
        return []


def obtener_trabajadores():
    """Lista todos los trabajadores."""
    try:
        res = supabase.table("trabajador").select("*").order("nombre").execute()
        return res.data or []
    except Exception as e:
        print("Error obtener_trabajadores:", e)
        return []


def crear_trabajador(data):
    """Crea un trabajador."""
    try:
        res = supabase.table("trabajador").insert(data).execute()
        return res.data
    except Exception as e:
        print("Error crear_trabajador:", e)
        return None


def actualizar_trabajador(rut, data):
    """Actualiza los datos de un trabajador."""
    try:
        res = supabase.table("trabajador").update(data).eq("rut", rut).execute()
        return res.data
    except Exception as e:
        print("Error actualizar_trabajador:", e)
        return None


def eliminar_trabajador(rut):
    """Elimina trabajador y liquidaciones asociadas por CASCADE."""
    try:
        supabase.table("trabajador").delete().eq("rut", rut).execute()
        return True
    except Exception as e:
        print("Error eliminar_trabajador:", e)
        return False


# =========================================================================================
#   CONSULTAS A LA BD PARA CÁLCULOS
# =========================================================================================

def obtener_tasa_afp(afp_id, fecha=date.today()):
    """
    Llama a la función RPC que devuelve:
       - tasa_cotizacion
       - tasa_sis
    """
    try:
        res = supabase.rpc(
            "obtener_tasa_afp",
            {"p_afp_id": afp_id, "p_fecha": fecha.isoformat()}
        ).execute()
        return _get_single(res.data)
    except Exception as e:
        print("Error obtener_tasa_afp:", e)
        return None


def obtener_tasa_salud(salud_id, fecha=date.today()):
    """
    Llama a obtener_tasa_salud y retorna:
       - porcentaje_base
       - plan_fijo (si corresponde)
    """
    try:
        res = supabase.rpc(
            "obtener_tasa_salud",
            {"p_salud_id": salud_id, "p_fecha": fecha.isoformat()}
        ).execute()
        return _get_single(res.data)
    except Exception as e:
        print("Error obtener_tasa_salud:", e)
        return None


def calcular_asignacion_familiar(imponible, cargas):
    """Invoca la función RPC de asignación familiar."""
    try:
        res = supabase.rpc(
            "calcular_asignacion_familiar",
            {"p_imponible": imponible, "p_cargas": cargas}
        ).execute()
        return res.data if res.data is not None else 0
    except Exception as e:
        print("Error calcular_asignacion_familiar:", e)
        return 0


# =========================================================================================
#   CÁLCULO DE LIQUIDACIÓN
# =========================================================================================

def calcular_liquidacion(datos, trabajador):
    """
    Calcula imponibles, no imponibles, descuentos y líquido a pagar.
    Usa AFP, salud y asignación familiar desde BD.
    """

    imponibles = sum([
        datos.get("sueldo_base", 0),
        datos.get("gratificacion", 0),
        datos.get("horas_extras", 0),
        datos.get("bonos", 0),
    ])

    no_imponibles = sum([
        datos.get("colacion", 0),
        datos.get("movilizacion", 0),
    ])

    # === Monto AFP ===
    afp_data = obtener_tasa_afp(trabajador["afp_id"])
    afp_monto = imponibles * afp_data["tasa"] if afp_data else 0

    # === Monto Salud ===
    salud_data = obtener_tasa_salud(trabajador["salud_id"])
    salud_monto = imponibles * salud_data["porcentaje"] if salud_data else 0

    # === Asignación familiar ===
    asig_familiar = calcular_asignacion_familiar(
        imponibles,
        trabajador.get("cargas_familiares", 0)
    )
    no_imponibles += asig_familiar  # se suma al total no imponible

    descuentos = afp_monto + salud_monto + datos.get("otros_descuentos", 0)

    liquido = imponibles + no_imponibles - descuentos

    return {
        "imponibles": imponibles,
        "no_imponibles": no_imponibles,
        "afp_monto": afp_monto,
        "salud_monto": salud_monto,
        "asignacion_familiar": asig_familiar,
        "otros_descuentos": datos.get("otros_descuentos", 0),
        "total_descuentos": descuentos,
        "liquido_pagar": liquido,
    }


# =========================================================================================
#   CRUD LIQUIDACIONES
# =========================================================================================

def obtener_liquidaciones():
    """Devuelve las liquidaciones existentes."""
    try:
        res = supabase.table("liquidacion_rrhh")\
            .select("*")\
            .order("fecha_emision", desc=True)\
            .execute()
        return res.data or []
    except Exception as e:
        print("Error obtener_liquidaciones:", e)
        return []


def obtener_detalle_liquidacion(liquidacion_id):
    """Devuelve los ítems de una liquidación."""
    try:
        res = supabase.table("liquidacion_detalle_rrhh")\
            .select("*")\
            .eq("liquidacion_id", liquidacion_id)\
            .execute()
        return res.data or []
    except Exception as e:
        print("Error obtener_detalle_liquidacion:", e)
        return []


def crear_liquidacion(cabecera, detalles):
    """Inserta la liquidación completa usando CASCADE."""
    try:
        cabecera.setdefault("fecha_emision", date.today().isoformat())

        # Insertar cabecera
        res = supabase.table("liquidacion_rrhh").insert(cabecera).execute()
        if not res.data:
            print("Error creando cabecera")
            return None

        liquidacion_id = res.data[0]["id"]

        # Insertar detalles
        for d in detalles:
            d["liquidacion_id"] = liquidacion_id
        supabase.table("liquidacion_detalle_rrhh").insert(detalles).execute()

        return liquidacion_id

    except Exception as e:
        print("Error crear_liquidacion:", e)
        return None


def eliminar_liquidacion(liquidacion_id):
    """Elimina una liquidación específica."""
    try:
        supabase.table("liquidacion_rrhh").delete().eq("id", liquidacion_id).execute()
        return True
    except Exception as e:
        print("Error eliminar_liquidacion:", e)
        return False


def actualizar_liquidacion(liquidacion_id, cabecera, detalles):
    """Actualiza la cabecera y reemplaza los detalles."""
    try:
        supabase.table("liquidacion_rrhh").update(cabecera).eq("id", liquidacion_id).execute()
        supabase.table("liquidacion_detalle_rrhh").delete().eq("liquidacion_id", liquidacion_id).execute()

        for d in detalles:
            d["liquidacion_id"] = liquidacion_id
        supabase.table("liquidacion_detalle_rrhh").insert(detalles).execute()

        return True

    except Exception as e:
        print("Error actualizar_liquidacion:", e)
        return False
