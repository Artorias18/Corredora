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


def _obtener_tasa_afp(afp_id, fecha: date):
    """
    Llama a la función SQL obtener_tasa_afp.
    Devuelve dict con keys: tasa, seguro_invalidez (o None).
    """
    if not afp_id:
        return None
    try:
        resp = supabase.rpc(
            "obtener_tasa_afp",
            {"p_afp_id": afp_id, "p_fecha": fecha.isoformat()},
        ).execute()
        data = resp.data or []
        return data[0] if data else None
    except Exception as e:
        print("Error _obtener_tasa_afp:", e)
        return None


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

def _recalcular_montos_automaticos(trabajador: dict, periodo: str, montos_por_concepto: dict):
    """
    Recibe:
      trabajador: fila completa de 'trabajador'
      periodo: string 'YYYY-MM'
      montos_por_concepto: { concepto_id: monto (float) } (viene del GUI)

    Devuelve un nuevo dict { concepto_id: monto_final } aplicando:
      - GRATIFICACION = 25% SUELDO BASE (si está en 0)
      - ASIGNACION_FAMILIAR = función SQL según base imponible y cargas
      - FONDO_PENSIONES = tasa_afp * base_imponible
      - 7% Previsión = porcentaje_salud * base_imponible
    """
    if not trabajador:
        return montos_por_concepto

    periodo_date = _parse_periodo_to_date(periodo)
    por_id, por_codigo = _obtener_catalogo_conceptos()

    # Copiamos montos originales para no mutar el dict que viene del GUI
    final_montos = {cid: float(m or 0) for cid, m in montos_por_concepto.items()}

    # ---- Obtener IDs de conceptos especiales por código
    c_sueldo = por_codigo.get("SUELDO_BASE")
    c_grat = por_codigo.get("GRATIFICACION")
    c_asig_fam = por_codigo.get("ASIGNACION_FAMILIAR")
    c_fondo_pen = por_codigo.get("FONDO_PENSIONES")
    c_prev_7 = por_codigo.get("PREVISION_7")

    # ---- SUELDO BASE desde los montos
    sueldo_base = 0.0
    if c_sueldo and c_sueldo["id"] in final_montos:
        sueldo_base = final_montos[c_sueldo["id"]]

    # ---- GRATIFICACION (auto si está en 0)
    if c_grat and c_grat["id"] in final_montos and c_grat.get("es_automatico"):
        if final_montos[c_grat["id"]] == 0 and sueldo_base > 0:
            final_montos[c_grat["id"]] = round(sueldo_base * 0.25)

    # ---- Base imponible provisional (para asignación familiar, AFP, etc.)
    base_imponible = 0.0
    for cid, monto in final_montos.items():
        info = por_id.get(cid)
        if info and info.get("grupo") == "haber_imponible":
            base_imponible += float(monto or 0)

    # ---- ASIGNACION FAMILIAR (auto si está en 0)
    cargas = int(trabajador.get("cargas_familiares") or 0)
    if c_asig_fam and c_asig_fam["id"] in final_montos and c_asig_fam.get("es_automatico"):
        if final_montos[c_asig_fam["id"]] == 0 and base_imponible > 0 and cargas > 0:
            final_montos[c_asig_fam["id"]] = round(
                _calcular_asignacion_familiar(base_imponible, cargas)
            )

    # ---- AFP y salud
    afp_id = trabajador.get("afp_id")
    salud_id = trabajador.get("sistema_salud_id")

    tasa_afp = 0.0
    datos_afp = _obtener_tasa_afp(afp_id, periodo_date) if afp_id else None
    if datos_afp and datos_afp.get("tasa") is not None:
        try:
            tasa_afp = float(datos_afp["tasa"])  # ej: 0.1144
        except Exception:
            tasa_afp = 0.0

    # Porcentaje salud: priorizamos porcentaje de trabajador (7.0 -> 0.07)
    porc_salud_trab = trabajador.get("porcentaje_salud")
    if porc_salud_trab is not None:
        try:
            tasa_salud = float(porc_salud_trab) / 100.0
        except Exception:
            tasa_salud = 0.07
    else:
        # fallback a tasa en sistema_salud_tasa
        datos_salud = _obtener_tasa_salud(salud_id, periodo_date) if salud_id else None
        if datos_salud and datos_salud.get("porcentaje") is not None:
            try:
                tasa_salud = float(datos_salud["porcentaje"])
            except Exception:
                tasa_salud = 0.07
        else:
            tasa_salud = 0.07  # default 7%

    # ---- FONDO DE PENSIONES (auto si está en 0)
    if c_fondo_pen and c_fondo_pen["id"] in final_montos and c_fondo_pen.get("es_automatico"):
        if final_montos[c_fondo_pen["id"]] == 0 and base_imponible > 0 and tasa_afp > 0:
            final_montos[c_fondo_pen["id"]] = round(base_imponible * tasa_afp)

    # ---- 7% Previsión (auto si está en 0)
    if c_prev_7 and c_prev_7["id"] in final_montos and c_prev_7.get("es_automatico"):
        if final_montos[c_prev_7["id"]] == 0 and base_imponible > 0 and tasa_salud > 0:
            final_montos[c_prev_7["id"]] = round(base_imponible * tasa_salud)

    return final_montos


# ====================================================
#  LIQUIDACIONES - CREAR / ACTUALIZAR
# ====================================================

def crear_liquidacion(
    trabajador_rut: str,
    periodo: str,
    datos_cabecera: dict,
    montos_por_concepto: dict,
):
    """
    Crea una liquidación completa:
      - Inserta cabecera en 'liquidacion'
      - Inserta detalles en 'liquidacion_detalle'
      - Llama a calcular_totales_liquidacion en la BD

    montos_por_concepto: { concepto_id: monto_float } (viene del GUI)
    """
    try:
        trabajador = obtener_trabajador(trabajador_rut)
        if not trabajador:
            raise ValueError(f"Trabajador {trabajador_rut} no encontrado.")

        periodo_date = _parse_periodo_to_date(periodo)

        # AFP / Salud snapshot
        afp_id = trabajador.get("afp_id")
        salud_id = trabajador.get("sistema_salud_id")

        # Nombre AFP
        afp_nombre = None
        if afp_id:
            resp_afp = (
                supabase.table("afp")
                .select("nombre")
                .eq("id", afp_id)
                .execute()
            )
            if resp_afp.data:
                afp_nombre = resp_afp.data[0].get("nombre")

        # Nombre sistema salud
        salud_nombre = None
        if salud_id:
            resp_salud = (
                supabase.table("sistema_salud")
                .select("nombre")
                .eq("id", salud_id)
                .execute()
            )
            if resp_salud.data:
                salud_nombre = resp_salud.data[0].get("nombre")

        # Tasa AFP
        datos_afp = _obtener_tasa_afp(afp_id, periodo_date) if afp_id else None
        tasa_afp = None
        if datos_afp and datos_afp.get("tasa") is not None:
            try:
                tasa_afp = float(datos_afp["tasa"])
            except Exception:
                tasa_afp = None

        # Porcentaje salud decimal en liquidación
        porc_salud_trab = trabajador.get("porcentaje_salud")
        if porc_salud_trab is not None:
            try:
                porcentaje_salud_liq = float(porc_salud_trab) / 100.0
            except Exception:
                porcentaje_salud_liq = 0.07
        else:
            datos_salud = _obtener_tasa_salud(salud_id, periodo_date) if salud_id else None
            if datos_salud and datos_salud.get("porcentaje") is not None:
                try:
                    porcentaje_salud_liq = float(datos_salud["porcentaje"])
                except Exception:
                    porcentaje_salud_liq = 0.07
            else:
                porcentaje_salud_liq = 0.07

        # Recalcular automáticos
        montos_finales = _recalcular_montos_automaticos(
            trabajador, periodo, montos_por_concepto
        )

        # Base imponible (solo haberes imponibles)
        por_id, _ = _obtener_catalogo_conceptos()
        base_imponible = 0.0
        for cid, monto in montos_finales.items():
            info = por_id.get(cid)
            if info and info.get("grupo") == "haber_imponible":
                base_imponible += float(monto or 0)

        # Cabecera a insertar
        liq_data = {
            "trabajador_rut": trabajador_rut,
            "periodo": periodo,
            "fecha_emision": date.today().isoformat(),
            "dias_trabajados": int(datos_cabecera.get("dias_trabajados", 30)),
            "numero_horas_extras": int(datos_cabecera.get("numero_horas_extras", 0)),
            "base_imponible": base_imponible,
            "base_tributable": base_imponible,
            "afp_id": afp_id,
            "afp_nombre": afp_nombre,
            "afp_tasa": tasa_afp,
            "sistema_salud_id": salud_id,
            "sistema_salud_nombre": salud_nombre,
            "porcentaje_salud": porcentaje_salud_liq,
            "retro_antiguo": datos_cabecera.get("retro_antiguo"),
            "retro_actual": datos_cabecera.get("retro_actual"),
            "retro_diferencia": datos_cabecera.get("retro_diferencia"),
            "observaciones": datos_cabecera.get("observaciones"),
        }

        # Insertar cabecera
        resp_liq = supabase.table("liquidacion").insert(liq_data).execute()
        if not resp_liq.data:
            print("Error: no se insertó cabecera de liquidación.")
            return None

        liq_id = resp_liq.data[0]["id"]

        # Detalles
        detalles = []
        for cid, monto in montos_finales.items():
            monto = float(monto or 0)
            if abs(monto) < 0.5:
                continue  # evitamos insertar ceros
            detalles.append(
                {
                    "liquidacion_id": liq_id,
                    "concepto_id": cid,
                    "monto": monto,
                }
            )

        if detalles:
            supabase.table("liquidacion_detalle").insert(detalles).execute()

        # Recalcular totales en la BD
        supabase.rpc(
            "calcular_totales_liquidacion",
            {"p_liquidacion_id": liq_id},
        ).execute()

        print("Liquidación creada:", liq_id)
        return liq_id

    except Exception as e:
        print("Error crear_liquidacion:", e)
        return None


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
        montos_finales = _recalcular_montos_automaticos(
            trabajador, periodo, montos_por_concepto
        )

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
