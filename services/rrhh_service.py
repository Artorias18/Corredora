# ===============================
#        RRHH SERVICE
# ===============================

from services.supabase_client import supabase
from datetime import date
import traceback


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _exec(query):
    """Ejecuta una consulta Supabase y maneja errores."""
    try:
        response = query.execute()
        return response.data
    except Exception as e:
        print("❌ Supabase Error:", e)
        traceback.print_exc()
        return None


# =========================================================
#  TRABAJADORES
# =========================================================

def obtener_trabajadores():
    """Lista todos los trabajadores."""
    try:
        return _exec(
            supabase.table("trabajador")
            .select("*")
            .order("nombre", desc=False)
        ) or []
    except Exception as e:
        print("Error obtener_trabajadores:", e)
        return []


def crear_trabajador(data):
    """Inserta un trabajador nuevo."""
    try:
        data.setdefault("created_at", date.today().isoformat())
        return _exec(
            supabase.table("trabajador")
            .insert(data)
        )
    except Exception as e:
        print("Error crear_trabajador:", e)
        return None


def actualizar_trabajador(rut, data):
    """Actualiza datos de un trabajador."""
    try:
        return _exec(
            supabase.table("trabajador")
            .update(data)
            .eq("rut", rut)
        )
    except Exception as e:
        print("Error actualizar_trabajador:", e)
        return None


def eliminar_trabajador(rut):
    """Elimina trabajador completo."""
    try:
        _exec(
            supabase.table("trabajador")
            .delete()
            .eq("rut", rut)
        )
        return True
    except Exception as e:
        print("Error eliminar_trabajador:", e)
        return False


# =========================================================
#  AFP / SALUD
# =========================================================

def obtener_afps():
    """Lista AFP disponibles."""
    try:
        return _exec(
            supabase.table("afp")
            .select("id,nombre")
            .order("nombre", desc=False)
        ) or []
    except:
        print("Error obtener_afps")
        return []


def obtener_sistemas_salud():
    """Lista sistemas de salud disponibles."""
    try:
        return _exec(
            supabase.table("sistema_salud")
            .select("id,nombre,tipo")
            .order("nombre", desc=False)
        ) or []
    except:
        print("Error obtener_sistemas_salud")
        return []


def obtener_tasa_afp(afp_id, fecha=None):
    fecha = fecha or date.today().isoformat()
    data = _exec(
        supabase.rpc("obtener_tasa_afp", {"p_afp_id": afp_id, "p_fecha": fecha})
    )
    return data[0] if data else {"tasa": 0, "seguro_invalidez": 0}


def obtener_tasa_salud(salud_id, fecha=None):
    fecha = fecha or date.today().isoformat()
    data = _exec(
        supabase.rpc("obtener_tasa_salud", {"p_salud_id": salud_id, "p_fecha": fecha})
    )
    return data[0] if data else {"porcentaje": 0, "plan_fijo": 0}


def calcular_asignacion_familiar(monto_imponible, cargas):
    data = _exec(
        supabase.rpc(
            "calcular_asignacion_familiar",
            {"p_imponible": monto_imponible, "p_cargas": cargas}
        )
    )
    return data if data else 0


# =========================================================
#  CONCEPTOS
# =========================================================

def obtener_conceptos():
    """Retorna todos los conceptos, ordenados para mostrarse en el GUI."""
    return _exec(
        supabase.table("concepto")
        .select("*")
        .order("grupo", desc=False)
        .order("orden", desc=False)
    ) or []


def obtener_conceptos_agrupados():
    """Retorna diccionario: grupo → lista de conceptos."""
    conceptos = obtener_conceptos()
    agrupado = {"haber_imponible": [], "haber_no_imponible": [],
                "descuento_previsional": [], "descuento_otro": []}

    for c in conceptos:
        agrupado[c["grupo"]].append(c)

    return agrupado


# =========================================================
#  LIQUIDACIONES
# =========================================================

def obtener_liquidaciones_resumen():
    """Llama al RPC que devuelve resumen."""
    try:
        return _exec(
            supabase.rpc("obtener_liquidaciones_resumen")
        ) or []
    except:
        print("Error obtener_liquidaciones_resumen")
        return []


def obtener_liquidacion(liquidacion_id):
    """Obtiene datos completos de una liquidación."""
    try:
        data = _exec(
            supabase.table("liquidacion")
            .select("*")
            .eq("id", liquidacion_id)
        )
        return data[0] if data else None
    except:
        print("Error obtener_liquidacion")
        return None


def obtener_detalle_liquidacion(liquidacion_id):
    """Lista detalle por concepto."""
    try:
        return _exec(
            supabase.table("liquidacion_detalle")
            .select("*, concepto(nombre,grupo)")
            .eq("liquidacion_id", liquidacion_id)
            .order("id", desc=False)
        ) or []
    except:
        print("Error obtener_detalle_liquidacion")
        return []


# =========================================================
#  CREAR LIQUIDACIÓN COMPLETA
# =========================================================

def crear_liquidacion(cabecera, detalles):
    """
    Crea la liquidación:
      1) snapshot AFP / Salud
      2) inserta cabecera
      3) inserta detalle
      4) recalcula totales vía RPC
    """
    try:
        rut = cabecera["trabajador_rut"]
        trabajador = obtener_trabajador_por_rut(rut)

        if not trabajador:
            print("❌ Trabajador no encontrado")
            return None

        # 1. SNAPSHOT AFP
        afp_info = obtener_tasa_afp(trabajador["afp_id"])
        cabecera["afp_id"] = trabajador["afp_id"]
        cabecera["afp_nombre"] = trabajador["afp_id"] and _buscar_afp_nombre(trabajador["afp_id"])
        cabecera["afp_tasa"] = afp_info.get("tasa", 0)

        # 2. SNAPSHOT SALUD
        salud_info = obtener_tasa_salud(trabajador["sistema_salud_id"])
        cabecera["sistema_salud_id"] = trabajador["sistema_salud_id"]
        cabecera["sistema_salud_nombre"] = trabajador["sistema_salud_id"] and _buscar_salud_nombre(trabajador["sistema_salud_id"])
        cabecera["porcentaje_salud"] = salud_info.get("porcentaje", 0)

        cabecera.setdefault("fecha_emision", date.today().isoformat())

        # 3. Insertamos cabecera
        resp = _exec(
            supabase.table("liquidacion").insert(cabecera)
        )

        if not resp:
            return None

        liquidacion_id = resp[0]["id"]

        # 4. Insertamos detalle
        for d in detalles:
            d["liquidacion_id"] = liquidacion_id

        _exec(
            supabase.table("liquidacion_detalle").insert(detalles)
        )

        # 5. Recalcular totales
        _exec(
            supabase.rpc("calcular_totales_liquidacion",
                         {"p_liquidacion_id": liquidacion_id})
        )

        return liquidacion_id

    except Exception as e:
        print("Error crear_liquidacion:", e)
        traceback.print_exc()
        return None


# =========================================================
#  ACTUALIZAR LIQUIDACIÓN
# =========================================================

def actualizar_liquidacion(liquidacion_id, cabecera, detalles):
    try:
        # actualizar cabecera
        _exec(
            supabase.table("liquidacion")
            .update(cabecera)
            .eq("id", liquidacion_id)
        )

        # borrar detalle viejo
        _exec(
            supabase.table("liquidacion_detalle")
            .delete()
            .eq("liquidacion_id", liquidacion_id)
        )

        # insertar detalle nuevo
        for d in detalles:
            d["liquidacion_id"] = liquidacion_id

        _exec(
            supabase.table("liquidacion_detalle")
            .insert(detalles)
        )

        # recalcular totales
        _exec(
            supabase.rpc("calcular_totales_liquidacion",
                         {"p_liquidacion_id": liquidacion_id})
        )
        return True

    except Exception as e:
        print("Error actualizar_liquidacion:", e)
        return False


# =========================================================
#  ELIMINAR LIQUIDACIÓN
# =========================================================

def eliminar_liquidacion(liquidacion_id):
    try:
        _exec(
            supabase.table("liquidacion")
            .delete()
            .eq("id", liquidacion_id)
        )
        return True
    except:
        return False


# =========================================================
#  HELPERS SECUNDARIOS
# =========================================================

def obtener_trabajador_por_rut(rut):
    data = _exec(
        supabase.table("trabajador")
        .select("*")
        .eq("rut", rut)
    )
    return data[0] if data else None


def _buscar_afp_nombre(afp_id):
    data = _exec(
        supabase.table("afp")
        .select("nombre")
        .eq("id", afp_id)
    )
    return data[0]["nombre"] if data else None


def _buscar_salud_nombre(salud_id):
    data = _exec(
        supabase.table("sistema_salud")
        .select("nombre")
        .eq("id", salud_id)
    )
    return data[0]["nombre"] if data else None





# =============================================
# COMPATIBILIDAD TEMPORAL CON EL GUI ANTIGUO
# =============================================

def obtener_trabajador(rut):
    """Compatibilidad con el GUI antiguo."""
    return obtener_trabajador_por_rut(rut)


def obtener_liquidaciones():
    """El GUI antiguo llamaba esta función."""
    return obtener_liquidaciones_resumen()
