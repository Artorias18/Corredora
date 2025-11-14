from services.supabase_client import supabase
import os
from PySide6.QtWidgets import QMessageBox
import logging
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP

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
                raise ValueError("El RUT del comprador es obligatorio para ventas cerradas")
        if not data_arriendo.get('arrendatario', {}).get('rut'):
                raise ValueError("El RUT del vendedor es obligatorio para ventas cerradas")
        

        propiedad_data = {
            'codigo_interno': data_arriendo['propiedad']['codigo'],
            'direccion': data_arriendo['propiedad'].get('direccion', ''),
            'rol': data_arriendo['propiedad'].get('rol', 0),
            'comuna': data_arriendo['propiedad'].get('comuna', ''),
            'dominio_vigente': data_arriendo['propiedad'].get('dominio_vigente', 'No Posee Documento')
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
                                            on_conflict= "rut").execute()
        
        arrendatario_data = {
                 'rut': data_arriendo['arrendatario']['rut'] ,
                 'nombre': data_arriendo['arrendatario']['nombre'] ,
                 'telefono': data_arriendo['arrendatario']['telefono'] ,
                 'email': data_arriendo['arrendatario']['email'] ,
                 'direccion': data_arriendo['arrendatario']['direccion'],
                 'sueldo_base': data_arriendo['arrendatario']['sueldo_base'],
                 'horas_extras': data_arriendo['arrendatario']['horas_extras'],
                 'afp': data_arriendo['arrendatario']['afp'],
                 'salud': data_arriendo['arrendatario']['salud'],
                 'cesantia': data_arriendo['arrendatario']['cesantia'],
                 'tipo_trabajador': data_arriendo['arrendatario']['tipo_trabajador'],
                 'bono1': data_arriendo['arrendatario']['bono1'],
                 'bono2': data_arriendo['arrendatario']['bono2'],
                 'bono3': data_arriendo['arrendatario']['bono3'],
                 'colacion': data_arriendo['arrendatario']['colacion'],
                 'locomocion': data_arriendo['arrendatario']['locomocion'],
                 'cargas_familiares': data_arriendo['arrendatario']['cargas_familiares'],
                 'viaticos': data_arriendo['arrendatario']['viaticos'],
                 'herramientas': data_arriendo['arrendatario']['herramientas'],
                 'otros': data_arriendo['arrendatario']['otros'],
                 'antiguedad_laboral': data_arriendo['arrendatario']['antiguedad_laboral'],
                 'dicom': data_arriendo['arrendatario']['dicom'],
                 'comentarios': data_arriendo['arrendatario']['comentarios'],
                 'evaluacion_estado': data_arriendo['arrendatario']['evaluacion_estado'],
                 'fecha_evaluacion': data_arriendo['arrendatario']['fecha_evaluacion'],
                 'renta': data_arriendo['arrendatario']['renta']

        }
    
        supabase.table("arrendatario").upsert(arrendatario_data, 
                                              on_conflict= "rut").execute()
        
        evaluacion_arriendo_data = {
             'rut': data_arriendo['arrendatario']['rut']
             
        }

        supabase.table("evaluacion_arriendo").upsert(evaluacion_arriendo_data,
                                                     )


        arriendo_data = {
             'codigo_interno': data_arriendo['propiedad']['codigo'],
             'rut': data_arriendo['arrendador']['rut'],
             'rut': data_arriendo['arrendatario']['rut'],
             'fecha_inicio':data_arriendo['arriendo']['fecha_inicio'] or None,
             'fecha_termino':data_arriendo['arriendo']['fecha_termino'] or None,
             'renta_mensual':data_arriendo['arriendo']['renta_mensual'],
             'garantia':data_arriendo['arriendo']['garantia'],
             'gastos_comunes_incluidos':data_arriendo['arriendo']['gastos_comunes_incluidos'],
             'estado':data_arriendo['arriendo']['estado'],
             'tipo_contrato':data_arriendo['arriendo']['tipo_contrato'],
             'forma_pago':data_arriendo['arriendo']['forma_pago'],
             'periodo_pago':data_arriendo['arriendo']['periodo_pago'],
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



def obtener_detalle_arriendo():
    pass

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

