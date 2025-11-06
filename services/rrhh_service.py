# services/rrhh_service.py
from services.supabase_client import supabase
from datetime import date

# ====================================================
#  FUNCIONES CRUD - TABLA TRABAJADOR
# ====================================================

def obtener_trabajadores():
    """Obtiene todos los trabajadores registrados."""
    try:
        response = supabase.table("trabajador").select("*").order("nombre").execute()
        return response.data or []
    except Exception as e:
        print("Error al obtener trabajadores:", e)
        return []


def crear_trabajador(data):
    """Crea un nuevo trabajador en la base de datos."""
    try:
        if not data.get("rut") or not data.get("nombre"):
            raise ValueError("El RUT y el nombre son obligatorios.")

        data.setdefault("created_at", date.today().isoformat())
        response = supabase.table("trabajador").insert(data).execute()
        return response.data
    except Exception as e:
        print("Error al crear trabajador:", e)
        return None


def actualizar_trabajador(rut, data):
    """Actualiza un trabajador existente."""
    try:
        response = supabase.table("trabajador").update(data).eq("rut", rut).execute()
        return response.data
    except Exception as e:
        print("Error al actualizar trabajador:", e)
        return None


def eliminar_trabajador(rut):
    """Elimina un trabajador por su RUT."""
    try:
        supabase.table("trabajador").delete().eq("rut", rut).execute()
        return True
    except Exception as e:
        print("Error al eliminar trabajador:", e)
        return False
    

# ====================================================
#  CRUD - LIQUIDACIONES RRHH
# ====================================================

def obtener_liquidaciones():
    """Devuelve todas las liquidaciones con info del trabajador."""
    try:
        response = supabase.table("liquidacion_rrhh")\
            .select("id, periodo, trabajador_rut, total_haberes_imponibles, total_descuentos, liquido_pagar, fecha_emision")\
            .order("fecha_emision", desc=True)\
            .execute()
        return response.data or []
    except Exception as e:
        print("Error al obtener liquidaciones:", e)
        return []

def obtener_detalle_liquidacion(liquidacion_id):
    """Devuelve los detalles de una liquidación específica."""
    try:
        response = supabase.table("liquidacion_detalle_rrhh")\
            .select("*")\
            .eq("liquidacion_id", liquidacion_id)\
            .execute()
        return response.data or []
    except Exception as e:
        print("Error al obtener detalle de liquidación:", e)
        return []
def crear_liquidacion(data, detalles):
    """Crea una liquidación y sus ítems asociados."""
    try:
        data.setdefault("fecha_emision", date.today().isoformat())

        # ✅ Filtrar solo columnas válidas para liquidacion_rrhh
        columnas_validas = {
            "trabajador_rut",
            "periodo",
            "dias_trabajados",
            "sueldo_base",
            "total_haberes_imponibles",
            "total_haberes_no_imponibles",
            "total_descuentos",
            "liquido_pagar",
            "fecha_emision",
        }

        data_filtrada = {k: v for k, v in data.items() if k in columnas_validas}

        # Insertar la cabecera
        response = supabase.table("liquidacion_rrhh").insert(data_filtrada).execute()
        if not response.data:
            print("Error: no se insertó la cabecera de liquidación.")
            return None

        liquidacion_id = response.data[0]["id"]

        # Insertar detalles asociados
        for d in detalles:
            d["liquidacion_id"] = liquidacion_id

        if detalles:
            supabase.table("liquidacion_detalle_rrhh").insert(detalles).execute()

        # Recalcular totales en la BD
        supabase.rpc("calcular_totales_liquidacion", {"liquidacion_uuid": liquidacion_id}).execute()

        print(" Liquidación creada correctamente:", liquidacion_id)
        return liquidacion_id

    except Exception as e:
        print("Error al crear liquidación:", e)
        return None




# ====================================================
#  Función de cálculo (
# ====================================================

def calcular_liquidacion(datos):
    """
    Calcula totales de la liquidación, como en la planilla Excel.
    """
    try:
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

        descuentos = sum([
            datos.get("afp", 0),
            datos.get("salud", 0),
            datos.get("otros_descuentos", 0),
        ])

        liquido = imponibles + no_imponibles - descuentos

        datos.update({
            "total_haberes_imponibles": imponibles,
            "total_haberes_no_imponibles": no_imponibles,
            "total_descuentos": descuentos,
            "liquido_pagar": liquido,
        })

        return datos
    except Exception as e:
        print("Error al calcular liquidación:", e)
        return datos


def actualizar_liquidacion(liquidacion_id, data, detalles):
    """Actualiza una liquidación existente y recalcula los totales."""
    try:
        # Actualiza la cabecera
        supabase.table("liquidacion_rrhh").update(data).eq("id", liquidacion_id).execute()

        # Elimina los detalles antiguos
        supabase.table("liquidacion_detalle_rrhh").delete().eq("liquidacion_id", liquidacion_id).execute()

        # Inserta los nuevos detalles
        for d in detalles:
            d["liquidacion_id"] = liquidacion_id
        supabase.table("liquidacion_detalle_rrhh").insert(detalles).execute()

        # Recalcula totales con la función SQL
        supabase.rpc("calcular_totales_liquidacion", {"liquidacion_uuid": liquidacion_id}).execute()

        print(f"✅ Liquidación actualizada correctamente: {liquidacion_id}")
        return True
    except Exception as e:
        print("Error al actualizar liquidación:", e)
        return False



