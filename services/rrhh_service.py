# services/rrhh_service.py

from services.supabase_client import supabase
from datetime import date, datetime

# ====================================================
#  HELPERS
# ====================================================

def _parse_periodo_to_date(periodo: str) -> date:
    """
    Convierte 'YYYY-MM' a date (primer día del mes).
    Si falla, devuelve hoy().
    """
    try:
        return datetime.strptime(periodo + "-01", "%Y-%m-%d").date()
    except Exception:
        return date.today()


# ====================================================
#  TRABAJADORES
# ====================================================

def obtener_trabajadores():
    """
    Devuelve lista de trabajadores (para combos, tablas, etc.).
    """
    try:
        resp = (
            supabase.table("trabajador")
            .select("*")
            .order("nombre")  # ascendente por defecto
            .execute()
        )
        return resp.data or []
    except Exception as e:
        print("Error obtener_trabajadores:", e)
        return []


def obtener_trabajador(rut: str):
    """
    Devuelve un trabajador específico por RUT.
    """
    try:
        resp = (
            supabase.table("trabajador")
            .select("*")
            .eq("rut", rut)
            .execute()
        )
        data = resp.data or []
        return data[0] if data else None
    except Exception as e:
        print("Error obtener_trabajador:", e)
        return None


def crear_trabajador(data: dict):
    """
    Crea un trabajador nuevo.
    Espera keys: rut, nombre, fecha_ingreso (YYYY-MM-DD), tipo_contrato,
    cargo, afp_id, sistema_salud_id, porcentaje_salud, cargas_familiares,
    sueldo_base, activo.
    """
    try:
        # Asegurar campos mínimos
        if not data.get("rut") or not data.get("nombre"):
            raise ValueError("El RUT y el nombre son obligatorios.")

        # La BD se encarga de created_at, defaults, etc.
        resp = supabase.table("trabajador").insert(data).execute()
        return resp.data
    except Exception as e:
        print("Error crear_trabajador:", e)
        return None


def actualizar_trabajador(rut: str, data: dict):
    """
    Actualiza un trabajador existente por RUT.
    """
    try:
        resp = (
            supabase.table("trabajador")
            .update(data)
            .eq("rut", rut)
            .execute()
        )
        return resp.data
    except Exception as e:
        print("Error actualizar_trabajador:", e)
        return None


def eliminar_trabajador(rut: str):
    """
    Elimina un trabajador y TODAS sus liquidaciones (ON DELETE CASCADE).
    """
    try:
        (
            supabase.table("trabajador")
            .delete()
            .eq("rut", rut)
            .execute()
        )
        return True
    except Exception as e:
        print("Error eliminar_trabajador:", e)
        return False


# ====================================================
#  AFP / SISTEMA DE SALUD
# ====================================================

def obtener_afps():
    """
    Devuelve lista de AFP (id, nombre).
    """
    try:
        resp = (
            supabase.table("afp")
            .select("id,nombre")
            .order("nombre")
            .execute()
        )
        return resp.data or []
    except Exception as e:
        print("Error obtener_afps:", e)
        return []


def actualizar_tasa_afp_supabase(
    afp_id: str,
    fecha,
    tasa_cotizacion: float,
    tasa_sis: float,
):
    response = supabase.rpc(
        "actualizar_tasa_afp",
        {
            "p_afp_id": afp_id,
            "p_fecha": fecha.isoformat(),
            "p_tasa_cotizacion": tasa_cotizacion,
            "p_tasa_sis": tasa_sis,
        }
    ).execute()

        # CORRECCIÓN: verificar existencia de error
    if getattr(response, "error", None):
        raise Exception(response.error.message)





def obtener_tasa_afp_vigente(afp_id: str, fecha: date) -> dict | None:
    response = (
        supabase
        .table("afp_tasa")
        .select("tasa_cotizacion, tasa_sis")
        .eq("afp_id", afp_id)
        .lte("vigente_desde", fecha)
        .or_(f"vigente_hasta.is.null, vigente_hasta.gte.{fecha.isoformat()}")
        .order("vigente_desde", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]

    return None



from datetime import date

def obtener_afp_trabajador(trabajador: dict | str, fecha: date) -> dict:
    # Permitir pasar rut o ficha completa
    if isinstance(trabajador, dict):
        afp_id = trabajador.get("afp_id")
    else:
        ficha = obtener_trabajador(trabajador)
        afp_id = ficha.get("afp_id") if ficha else None

    if not afp_id:
        return {
            "afp_tasa": 0.0,
            "tasa_txt": "0%",
            "afp_nombre": "-",
            "sis_tasa": 0.0,
            "sis_txt": "0%",
            "tasa_total": 0.0,
            "tasa_total_txt": "0%"
        }

    # -----------------------------
    # 1) Nombre AFP
    # -----------------------------
    afp_resp = (
        supabase.table("afp")
        .select("nombre")
        .eq("id", afp_id)
        .execute()
    )
    afp_data = afp_resp.data or []
    afp_nombre = afp_data[0]["nombre"] if afp_data else "-"

    # -----------------------------
    # 2) Tasa AFP vigente
    # -----------------------------
    tasa_resp = (
        supabase.table("afp_tasa")
        .select("tasa_cotizacion,tasa_sis")
        .eq("afp_id", afp_id)
        .lte("vigente_desde", fecha)
        .or_(f"vigente_hasta.is.null,vigente_hasta.gte.{fecha}")
        .order("vigente_desde", desc=True)
        .limit(1)
        .execute()
    )

    tasa_data = tasa_resp.data or []
    if tasa_data:
        tasa_afp = float(tasa_data[0]["tasa_cotizacion"])
        tasa_sis = float(tasa_data[0]["tasa_sis"])
    else:
        tasa_afp = 0.0
        tasa_sis = 0.0

    tasa_total = tasa_afp + tasa_sis

    return {
        "afp_tasa": tasa_afp,
        "tasa_txt": f"{tasa_afp * 100:.2f}%",
        "afp_nombre": afp_nombre,
        "sis_tasa": tasa_sis,
        "sis_txt": f"{tasa_sis * 100:.2f}%",
        "tasa_total": tasa_total,
        "tasa_total_txt": f"{tasa_total * 100:.2f}%"
    }


def obtener_sistemas_salud():
    """
    Devuelve sistemas de salud (id, nombre, tipo).
    """
    try:
        resp = (
            supabase.table("sistema_salud")
            .select("id,nombre,tipo")
            .order("nombre")
            .execute()
        )
        return resp.data or []
    except Exception as e:
        print("Error obtener_sistemas_salud:", e)
        return []


def obtener_salud_trabajador(trabajador: dict, fecha: date) -> dict:
    salud_id = trabajador.get("salud_id")
    if not salud_id:
        return {
            "salud_nombre": "-",
            "salud_tipo": None,
            "salud_tasa": 0.0,
            "salud_plan": None,
            "tasa_txt": "0%"
        }

    try:
        # 1️⃣ Obtener sistema de salud (nombre + tipo)
        resp = (
            supabase.table("sistema_salud")
            .select("id,nombre,tipo")
            .eq("id", salud_id)
            .single()
            .execute()
        )
        sistema = resp.data or {}
    except Exception as e:
        print("Error sistema_salud:", e)
        sistema = {}

    nombre = sistema.get("nombre", "-")
    tipo = sistema.get("tipo")

    try:
        # 2️⃣ Obtener tasa vigente
        resp = (
            supabase.table("sistema_salud_tasa")
            .select("porcentaje_base,plan_fijo_monto")
            .eq("sistema_salud_id", salud_id)
            .lte("vigente_desde", fecha.isoformat())
            .or_(f"vigente_hasta.is.null,vigente_hasta.gte.{fecha.isoformat()}")
            .order("vigente_desde", desc=True)
            .limit(1)
            .execute()
        )
        data = resp.data or []
        tasa = data[0] if data else {}
    except Exception as e:
        print("Error sistema_salud_tasa:", e)
        tasa = {}

    porcentaje = float(tasa.get("porcentaje_base") or 0.0)
    plan = tasa.get("plan_fijo_monto")

    return {
        "salud_nombre": nombre,
        "salud_tipo": tipo,
        "salud_tasa": porcentaje,
        "salud_plan": float(plan) if plan is not None else None,
        "tasa_txt": f"{porcentaje * 100:.2f}%"
    }


def _obtener_tasa_salud(salud_id, fecha: date):
    """
    Llama a la función SQL obtener_tasa_salud.
    Devuelve dict con keys: porcentaje, plan_fijo (o None).
    """
    if not salud_id:
        return None
    try:
        resp = supabase.rpc(
            "obtener_tasa_salud",
            {"p_salud_id": salud_id, "p_fecha": fecha.isoformat()},
        ).execute()
        data = resp.data or []
        return data[0] if data else None
    except Exception as e:
        print("Error _obtener_tasa_salud:", e)
        return None


def _calcular_asignacion_familiar(imponible: float, cargas: int) -> float:
    """
    Usa la función SQL calcular_asignacion_familiar.
    """
    if cargas <= 0 or imponible <= 0:
        return 0.0
    try:
        resp = supabase.rpc(
            "calcular_asignacion_familiar",
            {
                "p_imponible": float(imponible),
                "p_cargas": int(cargas),
            },
        ).execute()
        # Supabase RPC scalars vienen en resp.data
        valor = resp.data
        if isinstance(valor, (int, float)):
            return float(valor)
        if isinstance(valor, str):
            try:
                return float(valor)
            except Exception:
                return 0.0
        return 0.0
    except Exception as e:
        print("Error _calcular_asignacion_familiar:", e)
        return 0.0


# ====================================================
#  CONCEPTOS
# ====================================================

def obtener_conceptos_agrupados():
    """
    Devuelve { grupo: [conceptos...] } ordenados por 'orden',
    para que el GUI genere dinámicamente los campos en el mismo
    orden que el Excel.
    """
    try:
        resp = (
            supabase.table("concepto")
            .select("*")
            .order("orden")
            .execute()
        )
        conceptos = resp.data or []
        agrupado = {
            "haber_imponible": [],
            "haber_no_imponible": [],
            "descuento_previsional": [],
            "descuento_otro": [],
        }
        for c in conceptos:
            grupo = c.get("grupo")
            if grupo in agrupado:
                agrupado[grupo].append(c)
        return agrupado
    except Exception as e:
        print("Error obtener_conceptos_agrupados:", e)
        return {
            "haber_imponible": [],
            "haber_no_imponible": [],
            "descuento_previsional": [],
            "descuento_otro": [],
        }



# --- Normalización y consolidación de conceptos ---
def _normalizar_y_consolidar_montos(montos_input: dict[str, float], por_codigo: dict[str, dict]) -> dict[str, float]:
    """
    Recibe montos_input con claves que pueden ser labels ('GRATIFICACION') o códigos del catálogo,
    normaliza a códigos existentes del catálogo (por_codigo) y consolida duplicados por grupo.
    """
    SINONIMOS_A_CODIGO = {
        "GRATIFICACION":    "GRAT_LEGAL",   # ← AJUSTA al código real del catálogo
        "FONDO_PENSIONES":  "DESC_AFP",     # ← AJUSTA: p.ej., 'AFP' o 'DESC_AFP'
        "SALUD":            "DESC_SALUD",   # ← AJUSTA
        "ADICIONAL_ISAPRE": "ADICIONAL_ISAPRE",
        "RETROACTIVO":      "RETROACTIVO",
    }

    GRUPO_EXCLUYENTE = "GRATIFICACION"  # ← AJUSTA al nombre del grupo exacto en tu tabla 'concepto'

    normalizados: dict[str, float] = {}

    for clave, monto in (montos_input or {}).items():
        try:
            valor = round(float(monto), 0)
        except (TypeError, ValueError):
            print(f"[WARN] Monto inválido para {clave}: {monto}")
            continue

        if abs(valor) < 0.5:
            continue

        code = SINONIMOS_A_CODIGO.get(clave, clave)
        concepto = por_codigo.get(code)
        if not concepto:
            print(f"[WARN] Código de concepto no encontrado en catálogo: {clave} → {code}")
            continue

        grupo = concepto.get("grupo")

        # Consolidación: si el grupo es excluyente (gratificación), deja una sola (prioriza la legal)
        if grupo == GRUPO_EXCLUYENTE:
            codigos_existentes = [c for c in normalizados.keys() if por_codigo[c].get("grupo") == GRUPO_EXCLUYENTE]
            if codigos_existentes and code != "GRAT_LEGAL":
                print(f"[INFO] Ignorando {code} porque ya existe otro del grupo {GRUPO_EXCLUYENTE}")
                continue
            # Si llega 'GRAT_LEGAL' y ya hay otra, reemplazar
            if code == "GRAT_LEGAL":
                for cprev in codigos_existentes:
                    normalizados.pop(cprev, None)

        normalizados[code] = round(float(normalizados.get(code, 0)) + float(valor), 0)

    return normalizados


def _obtener_catalogo_conceptos():
    """
    Devuelve dos diccionarios:
      - por_id: { concepto_id: {id,codigo,grupo,es_automatico,...} }
      - por_codigo: { codigo: {id,codigo,grupo,es_automatico,...} }
    """
    try:
        resp = (
            supabase.table("concepto")
            .select("id,codigo,grupo,es_automatico")
            .execute()
        )
        conceptos = resp.data or []
        por_id = {}
        por_codigo = {}
        for c in conceptos:
            cid = c["id"]
            code = c["codigo"]
            por_id[cid] = c
            por_codigo[code] = c
        return por_id, por_codigo
    except Exception as e:
        print("Error _obtener_catalogo_conceptos:", e)
        return {}, {}


# ====================================================
#  LIQUIDACIONES - RESUMEN / LECTURA
# ====================================================

def obtener_liquidaciones_resumen():
    """
    Usa la función SQL obtener_liquidaciones_resumen().
    Devuelve cada fila con:
      id, periodo, trabajador_rut, trabajador_nombre,
      total_haberes, total_descuentos_general, liquido_pagar, fecha_emision
    """
    try:
        resp = supabase.rpc("obtener_liquidaciones_resumen", {}).execute()
        return resp.data or []
    except Exception as e:
        print("Error obtener_liquidaciones_resumen:", e)
        return []


def obtener_liquidacion_completa(liq_id: str):
    """
    Devuelve:
    {
      "cabecera": {... columnas de liquidacion ...},
      "detalles": [... filas de liquidacion_detalle ...]
    }
    para poder editar/ver en el diálogo.
    """
    try:
        # Cabecera
        cab_resp = (
            supabase.table("liquidacion")
            .select("*")
            .eq("id", liq_id)
            .execute()
        )
        cab_data = (cab_resp.data or [])
        if not cab_data:
            return None
        cabecera = cab_data[0]

        # Detalles
        det_resp = (
            supabase.table("liquidacion_detalle")
            .select("*")
            .eq("liquidacion_id", liq_id)
            .execute()
        )
        detalles = det_resp.data or []

        return {
            "cabecera": cabecera,
            "detalles": detalles,
        }
    except Exception as e:
        print("Error obtener_liquidacion_completa:", e)
        return None


def eliminar_liquidacion(liq_id: str):
    """
    Elimina una liquidación (detalles se borran por ON DELETE CASCADE).
    """
    try:
        (
            supabase.table("liquidacion")
            .delete()
            .eq("id", liq_id)
            .execute()
        )
        return True
    except Exception as e:
        print("Error eliminar_liquidacion:", e)
        return False


# ====================================================
#  LIQUIDACIONES - LÓGICA AUTOMÁTICA
# ====================================================

# def _recalcular_montos_automaticos(trabajador: dict, periodo: str, montos_por_concepto: dict):
#     """
#     Recibe:
#       trabajador: fila completa de 'trabajador'
#       periodo: string 'YYYY-MM'
#       montos_por_concepto: { concepto_id: monto (float) } (viene del GUI)

#     Devuelve un nuevo dict { concepto_id: monto_final } aplicando:
#       - GRATIFICACION = 25% SUELDO BASE (si está en 0)
#       - ASIGNACION_FAMILIAR = función SQL según base imponible y cargas
#       - FONDO_PENSIONES = tasa_afp * base_imponible
#       - 7% Previsión = porcentaje_salud * base_imponible
#     """
#     if not trabajador:
#         return montos_por_concepto

#     periodo_date = _parse_periodo_to_date(periodo)
#     por_id, por_codigo = _obtener_catalogo_conceptos()

#     # Copiamos montos originales para no mutar el dict que viene del GUI
#     final_montos = {cid: float(m or 0) for cid, m in montos_por_concepto.items()}

#     # ---- Obtener IDs de conceptos especiales por código
#     c_sueldo = por_codigo.get("SUELDO_BASE")
#     c_grat = por_codigo.get("GRATIFICACION")
#     c_asig_fam = por_codigo.get("ASIGNACION_FAMILIAR")
#     c_fondo_pen = por_codigo.get("FONDO_PENSIONES")
#     c_prev_7 = por_codigo.get("PREVISION_7")

#     # ---- SUELDO BASE desde los montos
#     sueldo_base = 0.0
#     if c_sueldo and c_sueldo["id"] in final_montos:
#         sueldo_base = final_montos[c_sueldo["id"]]

#     # ---- GRATIFICACION (auto si está en 0)
#     if c_grat and c_grat["id"] in final_montos and c_grat.get("es_automatico"):
#         if final_montos[c_grat["id"]] == 0 and sueldo_base > 0:
#             final_montos[c_grat["id"]] = round(sueldo_base * 0.25)

#     # ---- Base imponible provisional (para asignación familiar, AFP, etc.)
#     base_imponible = 0.0
#     for cid, monto in final_montos.items():
#         info = por_id.get(cid)
#         if info and info.get("grupo") == "haber_imponible":
#             base_imponible += float(monto or 0)

#     # ---- ASIGNACION FAMILIAR (auto si está en 0)
#     cargas = int(trabajador.get("cargas_familiares") or 0)
#     if c_asig_fam and c_asig_fam["id"] in final_montos and c_asig_fam.get("es_automatico"):
#         if final_montos[c_asig_fam["id"]] == 0 and base_imponible > 0 and cargas > 0:
#             final_montos[c_asig_fam["id"]] = round(
#                 _calcular_asignacion_familiar(base_imponible, cargas)
#             )

#     # ---- AFP y salud
#     salud_id = trabajador.get("sistema_salud_id")

#     # Porcentaje salud: priorizamos porcentaje de trabajador (7.0 -> 0.07)
#     porc_salud_trab = trabajador.get("porcentaje_salud")
#     if porc_salud_trab is not None:
#         try:
#             tasa_salud = float(porc_salud_trab) / 100.0
#         except Exception:
#             tasa_salud = 0.07
#     else:
#         # fallback a tasa en sistema_salud_tasa
#         datos_salud = _obtener_tasa_salud(salud_id, periodo_date) if salud_id else None
#         if datos_salud and datos_salud.get("porcentaje") is not None:
#             try:
#                 tasa_salud = float(datos_salud["porcentaje"])
#             except Exception:
#                 tasa_salud = 0.07
#         else:
#             tasa_salud = 0.07  # default 7%

#     # ---- FONDO DE PENSIONES (auto si está en 0)
#     if c_fondo_pen and c_fondo_pen["id"] in final_montos and c_fondo_pen.get("es_automatico"):
#         if final_montos[c_fondo_pen["id"]] == 0 and base_imponible > 0 and tasa_afp > 0:
#             final_montos[c_fondo_pen["id"]] = round(base_imponible * tasa_afp)

#     # ---- 7% Previsión (auto si está en 0)
#     if c_prev_7 and c_prev_7["id"] in final_montos and c_prev_7.get("es_automatico"):
#         if final_montos[c_prev_7["id"]] == 0 and base_imponible > 0 and tasa_salud > 0:
#             final_montos[c_prev_7["id"]] = round(base_imponible * tasa_salud)

#     return final_montos


# ====================================================
#  LIQUIDACIONES - CREAR / ACTUALIZAR
# ====================================================







from datetime import date
from typing import Dict, Optional, List, Any

def crear_liquidacion(
    trabajador_rut: str,
    periodo: str,
    datos_cabecera: Dict,
    montos_por_concepto: List[Dict[str, Any]],
    *,
    ejecutar_rpc: bool = True,
) -> Optional[str]:

    try:
        trabajador = obtener_trabajador(trabajador_rut)
        if not trabajador:
            raise ValueError("Trabajador no encontrado")

        cab = dict(datos_cabecera or {})

        liq_data = {
            "trabajador_rut": trabajador_rut,
            "periodo": periodo,
            "fecha_emision": date.today().isoformat(),
            **cab,
        }

        # 2) INSERT cabecera
        resp = supabase.table("liquidacion").insert(liq_data).execute()
        if not resp.data:
            return None
        liq_id = resp.data[0]["id"]

        # 3) INSERT detalle (ya viene en lista con concepto_id)
        if montos_por_concepto:
            detalles = []
            for d in montos_por_concepto:
                detalles.append({
                    "liquidacion_id": liq_id,
                    "concepto_id": d["concepto_id"],
                    "monto": round(float(d["monto"]), 2),
                })

            supabase.table("liquidacion_detalle").insert(detalles).execute()

        # 4) RPC
        if ejecutar_rpc:
            supabase.rpc("calcular_totales_liquidacion", {"p_liquidacion_id": liq_id}).execute()

        return liq_id

    except Exception as e:
        print("Error crear_liquidacion:", e)
        return None


def obtener_nombre_salud(salud_id):
    if not salud_id:
        return "-"
    resp = (
        supabase.table("sistema_salud")
        .select("nombre")
        .eq("id", salud_id)
        .single()
        .execute()
    )
    return resp.data["nombre"] if resp.data else "-"




def actualizar_liquidacion(
    liq_id: str,
    datos_cabecera: dict,
    montos_por_concepto: dict,
):
    """
    Actualiza una liquidación:
      - Recalcula automáticos igual que crear_liquidacion
      - Actualiza cabecera (días, horas, retro, obs)
      - Reemplaza completamente los detalles
      - Llama a calcular_totales_liquidacion
    """
    try:

        if isinstance(montos_por_concepto, list):
            montos_por_concepto = {
                d["concepto_id"]: d["monto"]
                for d in montos_por_concepto
                if "concepto_id" in d
            }
        # Obtener cabecera actual para saber trabajador y periodo
        liq_resp = (
            supabase.table("liquidacion")
            .select("*")
            .eq("id", liq_id)
            .execute()
        )
        liq_data_list = liq_resp.data or []
        if not liq_data_list:
            raise ValueError("Liquidación no encontrada.")

        liq_actual = liq_data_list[0]
        trabajador_rut = liq_actual.get("trabajador_rut")
        periodo = liq_actual.get("periodo")

        trabajador = obtener_trabajador(trabajador_rut)
        if not trabajador:
            raise ValueError(f"Trabajador {trabajador_rut} no encontrado.")

        # Recalcular automáticos
        montos_finales = montos_por_concepto
        # Base imponible
        por_id, _ = _obtener_catalogo_conceptos()
        base_imponible = 0.0
        for cid, monto in montos_finales.items():
            info = por_id.get(cid)
            if info and info.get("grupo") == "haber_imponible":
                base_imponible += float(monto or 0)

        # Actualizar cabecera
        update_data = {
            "dias_trabajados": int(datos_cabecera.get("dias_trabajados", liq_actual.get("dias_trabajados", 30))),
            "numero_horas_extras": int(datos_cabecera.get("numero_horas_extras", liq_actual.get("numero_horas_extras", 0))),
            "retro_antiguo": datos_cabecera.get("retro_antiguo"),
            "retro_actual": datos_cabecera.get("retro_actual"),
            "retro_diferencia": datos_cabecera.get("retro_diferencia"),
            "observaciones": datos_cabecera.get("observaciones", liq_actual.get("observaciones")),
            "base_imponible": base_imponible,
            "base_tributable": base_imponible,
        }

        (
            supabase.table("liquidacion")
            .update(update_data)
            .eq("id", liq_id)
            .execute()
        )

        # Reemplazar detalles
        supabase.table("liquidacion_detalle").delete().eq("liquidacion_id", liq_id).execute()

        detalles = []
        for cid, monto in montos_finales.items():
            monto = float(monto or 0)
            if abs(monto) < 0.5:
                continue
            detalles.append(
                {
                    "liquidacion_id": liq_id,
                    "concepto_id": cid,
                    "monto": monto,
                }
            )

        if detalles:
            supabase.table("liquidacion_detalle").insert(detalles).execute()

        # Recalcular totales
        supabase.rpc(
            "calcular_totales_liquidacion",
            {"p_liquidacion_id": liq_id},
        ).execute()

        print("Liquidación actualizada:", liq_id)
        return True

    except Exception as e:
        print("Error actualizar_liquidacion:", e)
        return False



