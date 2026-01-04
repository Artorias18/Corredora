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
    

def guardar_arriendo(data_arriendo):

    try:
        
        if not data_arriendo.get('propiedad',{}).get('codigo'):
            raise ValueError("El código de la propiedad es obligatorio")
        if not data_arriendo.get('arrendador', {}).get('rut'):
                raise ValueError("El RUT del arrendador es obligatorio para ventas cerradas")
        if not data_arriendo.get('arrendatario', {}).get('rut'):
                raise ValueError("El RUT del arrendatario es obligatorio para ventas cerradas")
        
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
             'rut': data_arriendo['arrendador']['rut'],
             'nombre': data_arriendo['arrendador']['nombre'],
             'direccion': data_arriendo['arrendador']['direccion'],
             'telefono': data_arriendo['arrendador']['telefono'],
             'correo_electronico': data_arriendo['arrendador']['correo_electronico']
        }

        supabase.table("arrendador").upsert(arrendador_data,
                                            ).execute()
        
        arrendatario_data = {
                 'rut': data_arriendo['arrendatario']['rut'] ,
                 'nombre': data_arriendo['arrendatario']['nombre'] ,
                 'telefono': data_arriendo['arrendatario']['telefono'] ,
                 'email': data_arriendo['arrendatario']['email'] ,
                 'direccion': data_arriendo['arrendatario']['direccion'],
                 'tipo_trabajador': data_arriendo['arrendatario']['tipo_trabajador'],
                 'antiguedad_laboral': data_arriendo['arrendatario']['antiguedad_laboral'],
                 'dicom': data_arriendo['arrendatario']['dicom'],
                 'comentarios': data_arriendo['arrendatario']['comentarios'],
                 'renta': float(data_arriendo['arrendatario']['renta'] or 0)

        }
    
        supabase.table("arrendatario").upsert(arrendatario_data, 
                                              ).execute()
        
        if tipo_trabajador == "Dependiente":
            evaluacion_arrendatario_data = {
                'rut_arrendatario': data_arriendo['arrendatario']['rut'],
                'fecha_evaluacion': data_arriendo['evaluacion_arrendatario']['fecha_evaluacion'],
                'sueldo_base': data_arriendo['evaluacion_arrendatario']['sueldo_base'],
                'gratificacion': data_arriendo['evaluacion_arrendatario']['gratificacion'],
                'total_imponible': data_arriendo['evaluacion_arrendatario']['total_imponible'],
                'total_no_imponible': data_arriendo['evaluacion_arrendatario']['total_no_imponible'],
                'descuentos_legales': data_arriendo['evaluacion_arrendatario']['descuentos_legales'],
                'liquido_pago':data_arriendo['evaluacion_arrendatario']['liquido_pago'],
                'anticipo': data_arriendo['evaluacion_arrendatario']['anticipo'],
                'desc_varios': data_arriendo['evaluacion_arrendatario']['desc_varios'],
                'locomocion': data_arriendo['evaluacion_arrendatario']['locomocion']
                
            }

            supabase.table("evaluacion_arrendatario").upsert(evaluacion_arrendatario_data,
                                                        ).execute()


        arriendo_data = {
             'codigo_interno': data_arriendo['propiedad']['codigo'],
             'rut_arrendador': data_arriendo['arrendador']['rut'],
             'rut_arrendatario': data_arriendo['arrendatario']['rut'],
             'fecha_inicio':data_arriendo['arriendo']['fecha_inicio'] or None,
             'fecha_termino':data_arriendo['arriendo']['fecha_termino'] or None,
             'renta_mensual':data_arriendo['arriendo']['renta_mensual'],
             'cuenta_fm': data_arriendo['arriendo']['cuenta_fm'],
             'garantia':data_arriendo['arriendo']['garantia'],
             'gastos_comunes_incluidos':data_arriendo['arriendo']['gastos_comunes_incluidos'],
             'estado':data_arriendo['arriendo']['estado'],
             'tipo_contrato':data_arriendo['arriendo']['tipo_contrato'],
             'forma_pago':data_arriendo['arriendo']['forma_pago'],
             'periodo_pago':data_arriendo['arriendo']['periodo_pago'],
             'nro_cuenta': data_arriendo['arriendo']['nro_cuenta'],
             'banco_destino': data_arriendo['arriendo']['banco_destino'],
             'aseo_municipal': data_arriendo['arriendo']['aseo_municipal'],
             'reajuste': data_arriendo['arriendo']['reajuste'],
             'ggcc': data_arriendo['arriendo']['ggcc'],

               
             'honorarios_porcentaje': data_arriendo['arriendo']['honorarios_porcentaje'],
             'titular_deposito': data_arriendo['arriendo']['titular_deposito'],
             'quien_deposita': data_arriendo['arriendo']['quien_deposita'],
             'correo_deposito': data_arriendo['arriendo']['correo_deposito'],
             'dia_pago': data_arriendo['arriendo']['dia_pago'],
             'honorarios_monto': data_arriendo['arriendo']['honorarios_monto'],
             'tipo_cuenta': data_arriendo['arriendo']['tipo_cuenta'],
             'rut_para_deposito': data_arriendo['arriendo']['rut_para_deposito'],
             'cuenta_ggcc': data_arriendo['arriendo']['cuenta_ggcc'],
             'ultimo_mes_pago': data_arriendo['arriendo']['ultimo_mes_pago'],
             'direccion_consulta': data_arriendo['arriendo']['direccion_consulta'],
             'periodo_anterior': data_arriendo['arriendo']['periodo_anterior'],
             'monto_anterior': data_arriendo['arriendo']['monto_anterior'],
             'naturaleza_bien_raiz': data_arriendo['arriendo']['naturaleza_bien_raiz'],

                
             'dfl2': data_arriendo['arriendo']['dfl2'],
             'destino': data_arriendo['arriendo']['destino'],
             'amoblado': data_arriendo['arriendo']['amoblado'],
             'observaciones':data_arriendo['arriendo']['observaciones']
                
        }
        arriendo_response = supabase.table("arriendo").upsert(arriendo_data).execute()

        arriendo_id = arriendo_response.data[0]['id']


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
