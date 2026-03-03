from services.supabase_client import supabase
import os
from PySide6.QtWidgets import QMessageBox
import logging
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def obtener_arriendos_resumen(filtro_estado = None):
    try:
        if filtro_estado and filtro_estado != "Todos los arriendos":
              
              response = supabase.rpc("obtener_arriendos_resumen").execute()
              filtered_data = [a for a in response.data if a.get('estado', '')==filtro_estado]
              return filtered_data or []
        else:
             response = supabase.rpc("obtener_arriendos_resumen").execute()
             return response.data or []
             
    
         
    except Exception as e:
        logger.error(f"Error al obtener arriendos: {str(e)}")
        return []
    

def safe_numeric(value):
    if value in (None, "", " "):
        return 0
    try:
        return float(value)
    except:
        return 0

    

def guardar_arriendo(data_arriendo):

    try:
        
        if not data_arriendo.get('propiedad',{}).get('codigo'):
            raise ValueError("El código de la propiedad es obligatorio")
        
        tipo_trabajador = data_arriendo['arrendatario'].get('tipo_trabajador','')
        

        propiedad_data = {
            'codigo_interno': data_arriendo['propiedad']['codigo'],
            'direccion': data_arriendo['propiedad'].get('direccion', ''),
            'rol': data_arriendo['propiedad'].get('rol', 0),
            'comuna': data_arriendo['propiedad'].get('comuna', ''),
            'dominio_vigente': data_arriendo['propiedad'].get('dominio_vigente', 'No Posee Documento'),
            'estudio_titulos': data_arriendo['propiedad'].get('estudio_titulos', 'No Posee Documento')
        }
        supabase.table("propiedad").upsert(propiedad_data,
                                           on_conflict= "codigo_interno").execute()
        

        arrendador_data = {
             'rut': data_arriendo['arrendador'].get('rut',''),
             'nombre': data_arriendo['arrendador'].get('nombre',''),
             'direccion': data_arriendo['arrendador'].get('direccion',''),
             'telefono': data_arriendo['arrendador'].get('telefono',''),
             'correo_electronico': data_arriendo['arrendador'].get('correo_electronico','')
        }

        supabase.table("arrendador").upsert(arrendador_data,
                                            on_conflict="rut").execute()
        
        arrendatario_data = {
                 'rut': data_arriendo['arrendatario'].get('rut',''),
                 'nombre': data_arriendo['arrendatario'].get('nombre','') ,
                 'telefono': data_arriendo['arrendatario'].get('telefono','') ,
                 'email': data_arriendo['arrendatario'].get('email','') ,
                 'direccion': data_arriendo['arrendatario'].get('direccion',''),
                 'tipo_trabajador': data_arriendo['arrendatario'].get('tipo_trabajador','Dependiente'),
                 'antiguedad_laboral': int(data_arriendo['arrendatario'].get('antiguedad_laboral') or 0),
                 'dicom': data_arriendo['arrendatario'].get('dicom','Sí'),
                 'comentarios': data_arriendo['arrendatario'].get('comentarios',''),
                 'renta': safe_numeric(data_arriendo['arrendatario'].get('renta'))


        }
    
        supabase.table("arrendatario").upsert(arrendatario_data, 
                                              on_conflict="rut").execute()
        
        if tipo_trabajador == "Dependiente":
            evaluacion_arrendatario_data = {
                'rut_arrendatario': data_arriendo['arrendatario'].get('rut',''),
                'fecha_evaluacion': data_arriendo['evaluacion_arrendatario'].get('fecha_evaluacion'),
                'sueldo_base': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('sueldo_base')),
                'gratificacion': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('gratificacion')),
                'total_imponible': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('total_imponible')),
                'total_no_imponible': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('total_no_imponible')),
                'descuentos_legales': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('descuentos_legales')),
                'liquido_pago': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('liquido_pago')),
                'anticipo': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('anticipo')),
                'desc_varios': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('desc_varios')),
                'locomocion': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('locomocion')),
                'im_renta': safe_numeric(data_arriendo['evaluacion_arrendatario'].get('im_renta')),
                
            }

            supabase.table("evaluacion_arrendatario").upsert(evaluacion_arrendatario_data).execute()
        
        if tipo_trabajador == "Independiente":

            eval_data = data_arriendo['evaluacion_independiente']

            evaluacion_independiente_data = {
                'rut_arrendatario': eval_data['rut_arrendatario'],
                'periodo_desde': eval_data['periodo_desde'],
                'factor_castigo': safe_numeric(eval_data.get('factor_castigo')),
                'ventas_anuales': safe_numeric(eval_data.get('ventas_anuales')),
                'compras_anuales': safe_numeric(eval_data.get('compras_anuales')),
                'excedente_anual': safe_numeric(eval_data.get('excedente_anual')),
                'renta_anual_estimada': safe_numeric(eval_data.get('renta_anual_estimada')),
                'renta_mensual_estimada': safe_numeric(eval_data.get('renta_mensual_estimada')),
            }

            eval_resp = (
                supabase
                .table("evaluacion_independiente")
                .insert(evaluacion_independiente_data)
                .execute()
            )

            evaluacion_id = eval_resp.data[0]['id']

            detalle = data_arriendo['evaluacion_independiente_detalle']

            for mes in detalle:
                supabase.table("evaluacion_independiente_detalle").insert({
                    'evaluacion_id': evaluacion_id,
                    'periodo': mes['periodo'],
                    'iva_debito': safe_numeric(mes.get('iva_debito')),
                    'iva_credito': safe_numeric(mes.get('iva_credito')),
                    'ventas_netas_estimadas': safe_numeric(mes.get('ventas_netas_estimadas')),
                    'compras_netas_estimadas': safe_numeric(mes.get('compras_netas_estimadas'))
                }).execute()





        arriendo_data = {
             'codigo_interno': data_arriendo['propiedad']['codigo'],
             'rut_arrendador': data_arriendo['arrendador'].get('rut',''),
             'rut_arrendatario': data_arriendo['arrendatario'].get('rut', ''),
             'fecha_inicio':data_arriendo['arriendo']['fecha_inicio'] or None,
             'fecha_termino':data_arriendo['arriendo']['fecha_termino'] or None,
             'tipo_documento': data_arriendo['arriendo'].get('tipo_documento', 'Boleta'),
             'renta_mensual':safe_numeric(data_arriendo['arriendo'].get('renta_mensual')),
             'cuenta_fm': data_arriendo['arriendo'].get('cuenta_fm', '2'),
             'garantia':safe_numeric(data_arriendo['arriendo'].get('garantia')),
             'gastos_comunes_incluidos':data_arriendo['arriendo'].get('gastos_comunes_incluidos'),
             'estado':data_arriendo['arriendo'].get('estado', 'Vigente'),
             'tipo_contrato':data_arriendo['arriendo'].get('tipo_contrato','Plazo Indefinido'),
             'forma_pago':data_arriendo['arriendo'].get('forma_pago', ''),
             'periodo_pago':data_arriendo['arriendo'].get('periodo_pago'),
             'nro_cuenta': data_arriendo['arriendo'].get('nro_cuenta', ''),
             'banco_destino': data_arriendo['arriendo'].get('banco_destino', ''),
             'aseo_municipal': data_arriendo['arriendo'].get('aseo_municipal',''),
             'reajuste': data_arriendo['arriendo'].get('reajuste',''),
             'ggcc': data_arriendo['arriendo'].get('ggcc', ''),

               
             'honorarios_porcentaje': safe_numeric(data_arriendo['arriendo'].get('honorarios_porcentaje')),
             'titular_deposito': data_arriendo['arriendo'].get('titular_deposito', ''),
             'quien_deposita': data_arriendo['arriendo'].get('quien_deposita',''),
             'correo_deposito': data_arriendo['arriendo'].get('correo_deposito',''),
             'dia_pago': data_arriendo['arriendo'].get('dia_pago', ''),
             'honorarios_monto': safe_numeric(data_arriendo['arriendo'].get('honorarios_monto')),
             'tipo_cuenta': data_arriendo['arriendo'].get('tipo_cuenta',''),
             'rut_para_deposito': data_arriendo['arriendo'].get('rut_para_deposito',''),
             'cuenta_ggcc': data_arriendo['arriendo'].get('cuenta_ggcc', ''),
             'ultimo_mes_pago': data_arriendo['arriendo'].get('ultimo_mes_pago', ''),
             'direccion_consulta': data_arriendo['arriendo'].get('direccion_consulta', ''),
             'periodo_anterior': data_arriendo['arriendo'].get('periodo_anterior', ''),
             'monto_anterior': safe_numeric(data_arriendo['arriendo'].get('monto_anterior')),
             'naturaleza_bien_raiz': data_arriendo['arriendo'].get('naturaleza_bien_raiz',''),
             'dfl2': data_arriendo['arriendo'].get('dfl12', 'Si'),
             'destino': data_arriendo['arriendo'].get('destino', ''),
             'amoblado': data_arriendo['arriendo'].get('amoblado', ''),
             'observaciones':data_arriendo['arriendo'].get('observaciones')
                
        }
        arriendo_response = supabase.table("arriendo").upsert(
            arriendo_data,
            on_conflict="codigo_interno"
        ).execute()

        if not arriendo_response.data:
            raise Exception("No se pudo guardar el arriendo")

        arriendo_id = arriendo_response.data[0]["id"]
        return arriendo_id


                
    except Exception as e:
        print(f"Error detallado al guardar arriendo: {str(e)}")
        import traceback
        traceback.print_exc()
        return None



def obtener_detalle_arriendo(arriendo_id):
    try:
        response = supabase.rpc("obtener_detalle_arriendo", {"a_arriendo_id":arriendo_id}).execute()
        data = response.data

        if data and isinstance(data, dict):
              return data
         
        logging.warning(f"No se encontró detalle para arriendo_id{arriendo_id}")
        return None

    except Exception as e:
        logging.error(f"Error crítico al obtener arriendo{arriendo_id}: {str(e)}", exc_info=True)
        return None





def obtener_arriendos_por_estado(estado):
    try:
        if not estado or estado == "Todos los arriendos":
            # Si no se pide un estado específico, devolvemos todo
            response = supabase.table("arriendo").select("*").execute()
            return response.data or []

        # Obtener arriendos por estado exacto
        response = supabase.table("arriendo").select("*").eq("estado", estado).execute()
        return response.data or []

    except Exception as e:
        logger.error(f"Error al obtener arriendos por estado {estado}: {str(e)}")
        return []


def obtener_arriendos_finanzas():
    """
    Llama a la función SQL obtener_arriendos_finanzas()
    y retorna la lista de arriendos con todos los datos.
    """
    try:
        response = supabase.rpc("obtener_arriendos_finanzas").execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error al obtener arriendos finanzas: {e}")
        return []

def eliminar_arriendo(codigo_interno):

    try:
        response = supabase.rpc("eliminar_arriendo", {"p_codigo_interno" : codigo_interno}).execute()
        
        if response.data:
            print(response.data)
            return response.data
        else:
            print("Error:", response.error)
            return None
        
    except Exception as e:
        print("Excepción al eliminar:", e)
        return None





def guardar_abonos_arriendo(arriendo_id: int, abonos: list[dict]):
    if not arriendo_id:
        raise ValueError("arriendo_id inválido")

    registros = []

    for a in abonos:
        monto = float(a.get("monto", 0))

        if monto <= 0:
            continue

        registros.append({
            "arriendo_id": arriendo_id,
            "fecha": a.get("fecha", date.today().isoformat()),
            "monto": monto,
            "descripcion": a.get("descripcion", "")
        })

    if not registros:
        raise ValueError("No hay abonos válidos para guardar")

    supabase.table("abonos_arriendo").insert(registros).execute()

def guardar_gastos_arriendo(arriendo_id : int, gastos : list[dict]):
    if not arriendo_id:
        raise ValueError("arriendo_id inválido")
    
    registros = []

    for g in gastos:
        monto = float(g.get("monto", 0))
        if monto <= 0:
            continue
        registros.append({
            "arriendo_id": arriendo_id,
            "fecha": g.get("fecha", date.today().isoformat()),
            "monto": monto,
            "descripcion": g.get("descripcion", "")
        })

    if not registros:
        raise ValueError("No hay gastos validos para guardar")
    
    supabase.table("gastos_arriendo").insert(registros).execute()



def obtener_ultima_evaluacion_arrendatario(rut_arrendatario):
    try:
        response = (
            supabase
            .table("evaluacion_arrendatario")
            .select("*")
            .eq("rut_arrendatario", rut_arrendatario)
            .order("fecha_evaluacion", desc=True)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]  # evaluación más reciente

        return None

    except Exception as e:
        print(f"Error al obtener evaluación del arrendatario: {e}")
        return None




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


