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


def cargar_detalle_dependiente(eval_id):
    resp = supabase.rpc(
        "obtener_eval_dependiente_detalle",
        {"p_eval_id": eval_id}
    ).execute()

    return resp.data


def obtener_detalle_evaluacion(tipo, eval_id):

    if tipo == "Independiente":
        return cargar_detalle(eval_id)

    if tipo == "Dependiente":
        return cargar_detalle_dependiente(eval_id)

    return []


IVA_FACTOR = 0.19
CASTIGO_DEFAULT = 0.6


def calcular_evaluacion_independiente(meses, factor=CASTIGO_DEFAULT):
        ventas_anuales = 0
        compras_anuales = 0
        detalle = []

        for mes in meses:
            ventas = mes["iva_debito"] / IVA_FACTOR
            compras = mes["iva_credito"] / IVA_FACTOR
            excedente = ventas - compras

            ventas_anuales += ventas
            compras_anuales += compras

            detalle.append({
                "ventas": ventas,
                "compras": compras,
                "excedente": excedente
            })

        excedente_anual = max(ventas_anuales - compras_anuales, 0)
        renta_anual = excedente_anual * factor
        renta_mensual = renta_anual / 12

        return {
            "ventas_anuales": ventas_anuales,
            "compras_anuales": compras_anuales,
            "excedente_anual": excedente_anual,
            "renta_mensual": renta_mensual,
            "detalle": detalle
        }

def guardar_evaluacion(data_evaluacion):
    try:
        arr = data_evaluacion.get("arrendatario") or {}
        tipo_trabajador = arr.get("tipo_trabajador", "")
        rut = arr.get("rut")

        if not rut:
            raise Exception("Falta arrendatario.rut")

        if tipo_trabajador not in ("Dependiente", "Independiente"):
            raise Exception("Tipo trabajador inválido")

        # 1) Crear evaluacion (tabla madre)
        evaluacion_data = {
            "rut_arrendatario": rut,
            "tipo": tipo_trabajador,
            "resultado": data_evaluacion.get("resultado", "Pendiente"),
            "monto_arriendo_objetivo": safe_numeric(data_evaluacion.get("monto_arriendo_objetivo")),
            "veces_renta": safe_numeric(data_evaluacion.get("veces_renta")),
            "renta_minima": safe_numeric(data_evaluacion.get("renta_minima")),
        }

        resp_eval = supabase.table("evaluacion").insert(evaluacion_data).execute()
        if not resp_eval.data:
            raise Exception("No se pudo guardar la evaluación (tabla madre)")

        eval_id = resp_eval.data[0]["id"]

        # 2) DEPENDIENTE
        if tipo_trabajador == "Dependiente":
            eva = data_evaluacion.get("evaluacion_arrendatario") or {}

            evaluacion_arrendatario_data = {
                "evaluacion_id": eval_id,
                "fecha_evaluacion": eva.get("fecha_evaluacion"),
                "sueldo_base": safe_numeric(eva.get("sueldo_base")),
                "gratificacion": safe_numeric(eva.get("gratificacion")),
                "total_imponible": safe_numeric(eva.get("total_imponible")),
                "total_no_imponible": safe_numeric(eva.get("total_no_imponible")),
                "descuentos_legales": safe_numeric(eva.get("descuentos_legales")),
                "liquido_pago": safe_numeric(eva.get("liquido_pago")),
                "total_haberes": safe_numeric(eva.get("total_haberes")),
                "anticipo": safe_numeric(eva.get("anticipo")),
                "desc_varios": safe_numeric(eva.get("desc_varios")),
                "locomocion": safe_numeric(eva.get("locomocion")),
                "im_renta": safe_numeric(eva.get("im_renta")),
            }

            # Recomendado: UNIQUE(evaluacion_id) en evaluacion_arrendatario
            supabase.table("evaluacion_arrendatario").upsert(evaluacion_arrendatario_data).execute()
            return eval_id

        # 3) INDEPENDIENTE
        eval_data = data_evaluacion.get("evaluacion_independiente") or {}

        evaluacion_independiente_data = {
            "evaluacion_id": eval_id,  # FK hacia evaluacion(id)
            "periodo_desde": eval_data.get("periodo_desde"),
            "periodo_hasta": eval_data.get("periodo_hasta"),
            "factor_castigo": safe_numeric(eval_data.get("factor_castigo")),
            "ventas_anuales": safe_numeric(eval_data.get("ventas_anuales")),
            "compras_anuales": safe_numeric(eval_data.get("compras_anuales")),
            "excedente_anual": safe_numeric(eval_data.get("excedente_anual")),
            "renta_anual_estimada": safe_numeric(eval_data.get("renta_anual_estimada")),
            "renta_mensual_estimada": safe_numeric(eval_data.get("renta_mensual_estimada")),
        }

        resp_ind = supabase.table("evaluacion_independiente").insert(evaluacion_independiente_data).execute()
        if not resp_ind.data:
            raise Exception("No se pudo guardar evaluacion_independiente")


        detalle = data_evaluacion.get("evaluacion_independiente_detalle") or []
        for mes in detalle:
            supabase.table("evaluacion_independiente_detalle").upsert({
                "evaluacion_id": eval_id,  # ✅ FK -> evaluacion_independiente(id)
                "periodo": mes.get("periodo"),
                "iva_debito": safe_numeric(mes.get("iva_debito")),
                "iva_credito": safe_numeric(mes.get("iva_credito")),
                "ventas_netas_estimadas": safe_numeric(mes.get("ventas_netas_estimadas")),
                "compras_netas_estimadas": safe_numeric(mes.get("compras_netas_estimadas")),
            }).execute()

        return eval_id

    except Exception as e:
        print(f"Error detallado al guardar la evaluación: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def editar_evaluacion(eval_id, data_evaluacion):
    try:
        # 1️⃣ Verificar estado y tipo
        resp = (
            supabase
            .table("evaluacion")
            .select("estado, tipo")
            .eq("id", eval_id)
            .single()
            .execute()
        )

        if not resp.data:
            raise Exception("Evaluación no encontrada")

        if resp.data["estado"] != "Borrador":
            raise Exception("No se puede editar una evaluación finalizada")

        tipo = resp.data["tipo"]

        # =========================
        # DEPENDIENTE
        # =========================
        if tipo == "Dependiente":

            datos = data_evaluacion["evaluacion_arrendatario"]

            supabase.table("evaluacion_arrendatario") \
                .update({
                    'fecha_evaluacion': datos.get('fecha_evaluacion'),
                    'sueldo_base': safe_numeric(datos.get('sueldo_base')),
                    'gratificacion': safe_numeric(datos.get('gratificacion')),
                    'total_imponible': safe_numeric(datos.get('total_imponible')),
                    'total_no_imponible': safe_numeric(datos.get('total_no_imponible')),
                    'descuentos_legales': safe_numeric(datos.get('descuentos_legales')),
                    'liquido_pago': safe_numeric(datos.get('liquido_pago')),
                    'anticipo': safe_numeric(datos.get('anticipo')),
                    'desc_varios': safe_numeric(datos.get('desc_varios')),
                    'total_haberes': safe_numeric(datos.get('total_haberes')),
                    'locomocion': safe_numeric(datos.get('locomocion')),
                    'im_renta': safe_numeric(datos.get('im_renta')),
                }) \
                .eq("evaluacion_id", eval_id) \
                .execute()

        # =========================
        # INDEPENDIENTE
        # =========================
        if tipo == "Independiente":

            resumen = data_evaluacion["evaluacion_independiente"]
            detalle = data_evaluacion["evaluacion_independiente_detalle"]

            # 1️⃣ Actualizar resumen
            # 1️⃣ Obtener ID real de evaluacion_independiente
            resp_ind = (
                supabase
                .table("evaluacion_independiente")
                .select("id")
                .eq("evaluacion_id", eval_id)
                .single()
                .execute()
            )

            independiente_id = resp_ind.data["id"]

            # 2️⃣ Borrar detalle usando independiente_id
            supabase.table("evaluacion_independiente_detalle") \
                .delete() \
                .eq("evaluacion_id", independiente_id) \
                .execute()

            # 3️⃣ Insertar detalle nuevo usando independiente_id
            for mes in detalle:
                supabase.table("evaluacion_independiente_detalle").insert({
                    'evaluacion_id': independiente_id,
                    'periodo': mes['periodo'],
                    'iva_debito': safe_numeric(mes.get('iva_debito')),
                    'iva_credito': safe_numeric(mes.get('iva_credito')),
                    'ventas_netas_estimadas': safe_numeric(mes.get('ventas_netas_estimadas')),
                    'compras_netas_estimadas': safe_numeric(mes.get('compras_netas_estimadas'))
                }).execute()

        return True

    except Exception as e:
        print("Error al editar evaluación:", str(e))
        return False
    

def eliminar_evaluacion(eval_id: int) -> bool:
    try:
        existe = (
            supabase.table("evaluacion")
            .select("id")
            .eq("id", eval_id)
            .single()
            .execute()
        )

        if not existe.data:
            return False

        supabase.table("evaluacion").delete().eq("id", eval_id).execute()
        return True

    except Exception as e:
        print("Error al eliminar evaluación:", e)
        return False


def obtener_evaluacion_completa(eval_id: int):

    try:
        # =====================================
        # 1️⃣ TRAER TABLA PRINCIPAL evaluacion
        # =====================================
        resp_eval = (
            supabase
            .table("evaluacion")
            .select("*")
            .eq("id", eval_id)
            .single()
            .execute()
        )

        if not resp_eval.data:
            return None

        evaluacion = resp_eval.data
        tipo = evaluacion["tipo"]

        resultado = {
            "evaluacion": evaluacion,
            "arrendatario": {
                "rut": evaluacion["rut_arrendatario"],
                "tipo_trabajador": tipo
            }
        }

        # =====================================
        # 2️⃣ SI ES DEPENDIENTE
        # =====================================
        if tipo == "Dependiente":

            resp_dep = (
                supabase
                .table("evaluacion_arrendatario")
                .select("*")
                .eq("evaluacion_id", eval_id)
                .single()
                .execute()
            )

            resultado["evaluacion_arrendatario"] = resp_dep.data or {}

        # =====================================
        # 3️⃣ SI ES INDEPENDIENTE
        # =====================================
        if tipo == "Independiente":

            # 3.1 Traer resumen
            resp_ind = (
                supabase
                .table("evaluacion_independiente")
                .select("*")
                .eq("evaluacion_id", eval_id)
                .single()
                .execute()
            )

            independiente = resp_ind.data

            if not independiente:
                resultado["evaluacion_independiente"] = {}
                resultado["evaluacion_independiente_detalle"] = []
                return resultado

            resultado["evaluacion_independiente"] = independiente

            independiente_id = independiente["id"]

            # 3.2 Traer detalle (ojo: referencia a evaluacion_independiente.id)
            resp_det = (
                supabase
                .table("evaluacion_independiente_detalle")
                .select("*")
                .eq("evaluacion_id", eval_id)  # 👈 FK real de la tabla
                .order("periodo")
                .execute()
            )

            resultado["evaluacion_independiente_detalle"] = resp_det.data or []

        return resultado

    except Exception as e:
        print("Error obteniendo evaluación completa:", str(e))
        return None


def regla_3x_renta(renta_calculada: float, monto_arriendo: float, minimo: float = 3.0) -> dict:
    renta = float(renta_calculada or 0)
    arriendo = float(monto_arriendo or 0)

    if arriendo <= 0:
        return {"veces_renta": 0.0, "renta_minima": 0.0, "califica": False}

    veces = renta / arriendo
    return {
        "veces_renta": round(veces, 2),
        "renta_minima": arriendo * minimo,
        "califica": veces >= minimo
    }