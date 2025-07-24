from services.supabase_client import supabase
import os
from PySide6.QtWidgets import QMessageBox
import logging
from typing import Optional, Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def obtener_ventas_resumen(filtro_estado=None):
    """
    Obtiene un resumen de todas las ventas, opcionalmente filtradas por estado
    """
    try:
        if filtro_estado and filtro_estado != "Todos los estados":
            # Mapear nombres de filtro a valores de base de datos
            estado_map = {
                "En proceso": "en_proceso",
                "Negociandose": "negociandose",
                "Cerrada verbalmente": "cerrada verbalmente",
                "Cerrada en notaria": "cerrada en notaria",
                "Inscrita": "inscrita"
            }
            estado = estado_map.get(filtro_estado, filtro_estado.lower())
            
            # Obtener solo las ventas con el estado especificado
            response = supabase.rpc("obtener_ventas_resumen").execute()
            filtered_data = [v for v in response.data if v.get('estado_venta', '').lower() == estado.lower()]
            return filtered_data or []
        else:
            # Obtener todas las ventas
            response = supabase.rpc("obtener_ventas_resumen").execute()
            return response.data or []
    except Exception as e:
        logger.error(f"Error al obtener ventas: {str(e)}")
        return []

def obtener_detalle_venta(venta_id):
    try:
        response = supabase.rpc("obtener_detalle_venta", {"venta_id": venta_id}).execute()

        data = response.data

        if data and isinstance(data, dict):
            return data  # el JSON con venta, comprador, vendedor, etc.

        logging.warning(f"No se encontró detalle para venta_id {venta_id}")
        return None

    except Exception as e:
        logging.error(f"Error crítico al obtener venta {venta_id}: {str(e)}", exc_info=True)
        return None


def actualizar_estado_venta(venta_id, nuevo_estado):
    try:
        print(f"Llamando RPC actualizar_estado_venta con venta_id={venta_id}, nuevo_estado={nuevo_estado}")
        response = supabase.rpc("actualizar_estado_venta", {
            "venta_id": venta_id,
            "nuevo_estado": nuevo_estado
        }).execute()
        print("Respuesta RPC:", response.data)

        if response.data is None:
            return False
        if isinstance(response.data, list):
            # Para respuesta en lista, devuelve el primer elemento
            return response.data[0]
        else:
            # Para respuesta directa (bool u otro tipo), devuelve tal cual
            return response.data
    except Exception as e:
        print(f"Error al actualizar estado de venta {venta_id}: {str(e)}")
        return False


    
def asignar_porcentajes_herencia(herederos):
    tipo_counts = {"conyugue": 0, "hijo": 0, "padre": 0, "fisco": 0}
    for heredero in herederos:
        tipo = heredero.get("tipo_heredero", "").lower()
        if tipo in tipo_counts:
            tipo_counts[tipo] += 1

    conyugue = tipo_counts["conyugue"]
    hijos = tipo_counts["hijo"]
    padres = tipo_counts["padre"]
    fisco = tipo_counts["fisco"]

    if hijos > 0 and conyugue > 0:
        # Escenario: conyugue + hijos
        if 2 <= hijos <= 7:
            # El cónyuge recibe el doble que cada hijo
            partes_hijos = hijos
            partes_conyugue = 2
            total_partes = partes_hijos + partes_conyugue
            porcentaje_hijo = 100 / total_partes
            porcentaje_conyugue = porcentaje_hijo * 2
            for heredero in herederos:
                if heredero["tipo_heredero"] == "hijo":
                    heredero["porcentaje"] = round(porcentaje_hijo, 2)
                elif heredero["tipo_heredero"] == "conyugue":
                    heredero["porcentaje"] = round(porcentaje_conyugue, 2)

        elif hijos >= 8:
            # El cónyuge recibe 25%, el resto se reparte entre los hijos
            porcentaje_conyugue = 25.0
            porcentaje_restante = 75.0 / hijos
            for heredero in herederos:
                if heredero["tipo_heredero"] == "hijo":
                    heredero["porcentaje"] = round(porcentaje_restante, 2)
                elif heredero["tipo_heredero"] == "conyugue":
                    heredero["porcentaje"] = porcentaje_conyugue

        else:
            # Caso general: 1 hijo o casos no cubiertos explícitamente
            total_partes = hijos + 1  # cónyuge = 1 parte
            porcentaje_base = 100 / total_partes
            for heredero in herederos:
                if heredero["tipo_heredero"] in ["hijo", "conyugue"]:
                    heredero["porcentaje"] = round(porcentaje_base, 2)

    elif hijos > 0 and conyugue == 0:
        # Solo hijos
        porcentaje_hijo = 100 / hijos
        for heredero in herederos:
            if heredero["tipo_heredero"] == "hijo":
                heredero["porcentaje"] = round(porcentaje_hijo, 2)

    elif conyugue > 0 and hijos == 0 and padres > 0:
        # Conyugue + padres
        porcentaje_conyugue = 50
        porcentaje_padre = 50 / padres
        for heredero in herederos:
            if heredero["tipo_heredero"] == "conyugue":
                heredero["porcentaje"] = porcentaje_conyugue
            elif heredero["tipo_heredero"] == "padre":
                heredero["porcentaje"] = round(porcentaje_padre, 2)

    elif conyugue > 0 and hijos == 0 and padres == 0:
        # Solo conyugue
        for heredero in herederos:
            if heredero["tipo_heredero"] == "conyugue":
                heredero["porcentaje"] = 100.0

    elif fisco > 0:
        # Sin herederos → herencia al fisco
        for heredero in herederos:
            if heredero["tipo_heredero"] == "fisco":
                heredero["porcentaje"] = 100.0



def asignar_porcentajes_herencia_testada(herederos, mejoras=None, libre_disposicion=None):
    """
    Asigna porcentajes de herencia para una posesión efectiva testada.
    
    mejoras: lista de ruts de herederos que recibirán la cuarta de mejoras.
    libre_disposicion: diccionario con rut como clave y porcentaje (del 25%) como valor.
    """
    total_porcentaje = 0

    mejoras = mejoras or []
    libre_disposicion = libre_disposicion or {}

    # Identificar herederos forzosos
    herederos_forzosos = [h for h in herederos if h.get("tipo_heredero") == "forzoso"]
    total_forzosos = len(herederos_forzosos)

    if total_forzosos == 0:
        raise ValueError("Debe haber al menos un heredero forzoso en posesión testada.")
    
    for h in herederos:
        h["porcentaje"] = 0
        
    # Asignar mitad legítima (50%)
    porcentaje_legitima = 50 / total_forzosos
    for heredero in herederos_forzosos:
        heredero["porcentaje"] = porcentaje_legitima

    # Asignar cuarta de mejoras (25%)
    if mejoras:
        porcentaje_mejora = 25 / len(mejoras)
        for heredero in herederos:
            if heredero["rut"] in mejoras:
                heredero["porcentaje"] += porcentaje_mejora

    # Asignar cuarta de libre disposición (25%)
    total_libre = sum(libre_disposicion.values())
    if round(total_libre, 2) != 25.0:
        raise ValueError(f"La suma de libre disposición debe ser 25%, pero es {total_libre}%")

    for heredero in herederos:
        rut = heredero["rut"]
        if rut in libre_disposicion:
            heredero["porcentaje"] = heredero.get("porcentaje", 0) + libre_disposicion[rut]

    # Redondeo final (opcional)
    for heredero in herederos:
        heredero["porcentaje"] = round(heredero["porcentaje"], 2)

    if round(total_porcentaje, 2) > 100:
        raise ValueError(f"La suma total de porcentajes de herencia supera el 100%: {total_porcentaje}%")



def guardar_venta(data_venta, data_posesion=None, herederos=None, mejoras=None, libre_disposicion=None, es_venta_cerrada=False):
    """
    Guarda una nueva venta (en proceso o cerrada)
    """
    try:
        # Validar datos mínimos

        if not data_venta.get('propiedad',{}).get('codigo'):
            raise ValueError("El código de la propiedad es obligatorio")
        
        if es_venta_cerrada:
            if not data_venta.get('comprador', {}).get('rut'):
                raise ValueError("El RUT del comprador es obligatorio para ventas cerradas")
            if not data_venta.get('vendedor', {}).get('rut'):
                raise ValueError("El RUT del vendedor es obligatorio para ventas cerradas")
            if not data_venta.get('venta', {}).get('tipo_venta'):
                raise ValueError("El tipo de venta es obligatorio para ventas cerradas")

        # Determinar estado de venta
        estado_venta = data_venta['venta'].get('estado_venta', 'en_proceso' if not es_venta_cerrada else 'negociandose')

        # 1. Guardar/actualizar comprador
        if data_venta.get('comprador',{}).get('rut'):
            comprador_data = {
                'rut': data_venta['comprador']['rut'],
                'nombre': data_venta['comprador'].get('nombre', ''),
                'direccion': data_venta['comprador'].get('direccion', ''),
                'telefono': data_venta['comprador'].get('telefono', ''),
                'correo_electronico': data_venta['comprador'].get('correo', ''),
                'banco': data_venta['comprador'].get('banco', ''),
                'tipo_cuenta': data_venta['comprador'].get('tipo_cuenta', ''),
                'nro_cuenta': data_venta['comprador'].get('nro_cuenta', ''),
                'poder_judicial': data_venta['comprador'].get('poder_judicial', 'No')
            }
            supabase.table("comprador").upsert(comprador_data).execute()

        # 2. Guardar/actualizar vendedor
        if data_venta.get('vendedor',{}).get('rut'):
            vendedor_data = {
                'rut': data_venta['vendedor']['rut'],
                'nombre': data_venta['vendedor'].get('nombre', ''),
                'direccion': data_venta['vendedor'].get('direccion', ''),
                'telefono': data_venta['vendedor'].get('telefono', ''),
                'correo_electronico': data_venta['vendedor'].get('correo', ''),
                'banco': data_venta['vendedor'].get('banco', ''),
                'tipo_cuenta': data_venta['vendedor'].get('tipo_cuenta', ''),
                'nro_cuenta': data_venta['vendedor'].get('nro_cuenta', ''),
                'poder_judicial': data_venta['vendedor'].get('poder_judicial', 'No'),
                'posesion_efectiva': 'Si' if data_venta['venta']['tipo_venta'] == 'Posesion Efectiva' else 'No'
            }
            supabase.table("vendedor").upsert(vendedor_data).execute()

        # 3. Guardar/actualizar propiedad
        propiedad_data = {
            'codigo_interno': data_venta['propiedad']['codigo'],
            'direccion': data_venta['propiedad'].get('direccion', ''),
            'rol': data_venta['propiedad'].get('rol', 0),
            'comuna': data_venta['propiedad'].get('comuna', ''),
            'estudio_titulos': data_venta['propiedad'].get('estudio_titulos', 'No Posee Documento'),
            'inscripcion': data_venta['propiedad'].get('inscripcion', 'No Posee Documento'),
            'dominio_vigente': data_venta['propiedad'].get('dominio_vigente', 'No Posee Documento'),
            'hipoteca': data_venta['propiedad'].get('hipoteca', 'No Posee Documento'),
            'gravamen': data_venta['propiedad'].get('gravamen', 'No Posee Documento'),
            'certificado_numero': data_venta['propiedad'].get('certificado_numero', 'No Posee Documento'),
            'aseo': data_venta['propiedad'].get('aseo', 'No Posee Documento'),
            'no_expropiacion': data_venta['propiedad'].get('no_expropiacion', 'No Posee Documento')
        }
        supabase.table("propiedad").upsert(propiedad_data).execute()

        # 4. Guardar estado documental si hay datos
        if any([data_venta['venta'].get('limitaciones'), data_venta['venta'].get('viabilidad')]):
            estado_doc_data = {
                'codigo_interno': data_venta['propiedad']['codigo'],
                'limitaciones_dominio': data_venta['venta'].get('limitaciones', 'No'),
                'viabilidad_vendedor': data_venta['venta'].get('viabilidad', '')
            }
            supabase.table("estado_documental").upsert(estado_doc_data).execute()

        # 5. Guardar recepción definitiva si hay datos
        if any([data_venta['propiedad'].get('superficie'), data_venta['propiedad'].get('edificada'), data_venta['propiedad'].get('recepcion')]):
            recepcion_data = {
                'codigo_interno': data_venta['propiedad']['codigo'],
                'superficie': data_venta['propiedad'].get('superficie', 'No Posee Documento'),
                'edificada': data_venta['propiedad'].get('edificada', 'No Posee Documento'),
                'recepcion': data_venta['propiedad'].get('recepcion', 'No Posee Documento')
            }
            supabase.table("recepcion_definitiva").upsert(recepcion_data).execute()

        # 6. Crear o actualizar tubo
        tubo_data = {
            'tipo_venta': data_venta['venta']['tipo_venta'],
            'estado_venta': estado_venta,
            'codigo_interno': data_venta['propiedad']['codigo'],
            'propiedad_ofrecida': data_venta['venta'].get('propiedad_ofrecida', 'No'),
            'en_venta': 'Si',
            'regularizaciones_ampliaciones': data_venta['venta'].get('regularizaciones', 'No')
        }
        
        tubo_response = supabase.table("tubo").select("id").eq("codigo_interno", data_venta['propiedad']['codigo']).execute()
        
        if tubo_response.data:
            tubo_id = tubo_response.data[0]['id']
            supabase.table("tubo").update(tubo_data).eq("id", tubo_id).execute()
        else:
            tubo_response = supabase.table("tubo").insert(tubo_data).execute()
            tubo_id = tubo_response.data[0]['id']

        # 7. Crear venta
        venta_data = {
            'comprador_rut': data_venta['comprador']['rut'],
            'vendedor_rut': data_venta['vendedor']['rut'],
            'codigo_interno': data_venta['propiedad']['codigo'],
            'tubo_id': tubo_id,
            'fecha_venta': data_venta['venta'].get('fecha_venta'),
            'monto_venta': float(data_venta['venta'].get('monto_venta', 0)) if data_venta['venta'].get('monto_venta') else None,
            'observaciones': data_venta['venta'].get('observaciones', ''),
            'es_venta_proceso': not es_venta_cerrada 
        }

        if es_venta_cerrada and data_posesion and data_venta['venta']['tipo_venta'] == 'Posesion Efectiva':
            if herederos:
                if not data_posesion or 'tipo' not in data_posesion:
                    raise ValueError("Para herederos, debe especificar el tipo de posesión (Intestada/Testada)")
                
                if data_posesion['tipo'].lower() == 'intestada':
                    asignar_porcentajes_herencia(herederos)
                elif data_posesion['tipo'].lower() == 'testada':
                    asignar_porcentajes_herencia_testada(herederos,
                                                        mejoras=mejoras if mejoras else [],
                                                        libre_disposicion=libre_disposicion if libre_disposicion else {})
                    total_porcentaje = sum([h.get("porcentaje", 0) for h in herederos])
                    if round(total_porcentaje, 2) > 100:
                        raise ValueError(f"La suma total de porcentajes de herencia supera el 100%: {total_porcentaje}%")
                else:
                    raise ValueError(f"Tipo de posesión no válido: {data_posesion['tipo']}")

        
        venta_response = supabase.table("venta").upsert(venta_data).execute()
        venta_id = venta_response.data[0]['id']

   
        if es_venta_cerrada and data_posesion and data_venta['venta']['tipo_venta'] == 'Posesion Efectiva':
            posesion_data = {
                'codigo_interno': data_venta['propiedad']['codigo'],
                'tipo_posesion': data_posesion.get('tipo', 'intestada'),
                'canal': data_posesion.get('canal', 'registro civil'),
                'estado_proceso': data_posesion.get('estado_proceso', 'solicitud')
            }
            supabase.table("posesion_efectiva").upsert(posesion_data).execute()
            
            if herederos:
                herederos_data = []
                for heredero in herederos:
                    if not heredero.get('nombre') or not heredero.get('rut'):
                        raise ValueError("Todos los herederos deben tener nombre y RUT")
                        
                    heredero_data = {
                        'venta_id': venta_id,
                        'codigo_interno': data_venta['propiedad']['codigo'],
                        'nombre': heredero.get('nombre', '').strip(),
                        'rut': heredero.get('rut', '').strip(),
                        'tipo_heredero': heredero.get('tipo_heredero', 'otro').lower(),
                        'porcentaje': float(heredero.get('porcentaje', 0))
                    }
                    herederos_data.append(heredero_data)
                
                supabase.table("herederos").insert(herederos_data).execute()

        # Retornar id de la venta
        return venta_id

    except Exception as e:
        print(f"Error detallado al guardar venta: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def obtener_o_crear_tubo(data_venta, estado_venta='en_proceso'):
    try:
        # Validar datos mínimos requeridos
        required_fields = ['tipo_venta', 'codigo_interno']
        for field in required_fields:
            if field not in data_venta['venta'] or not data_venta['venta'][field]:
                raise ValueError(f"Campo requerido faltante: {field}")

        # Preparar datos del tubo con valores por defecto
        tubo_data = {
            'tipo_venta': data_venta['venta']['tipo_venta'],
            'estado_venta': estado_venta,
            'codigo_interno': data_venta['propiedad']['codigo'],
            'propiedad_ofrecida': data_venta['venta'].get('propiedad_ofrecida', 'No'),
            'en_venta': 'Si',  # Campo requerido que faltaba
            'regularizaciones_ampliaciones': data_venta['venta'].get('regularizaciones', 'No')
        }

        # Buscar tubo existente (con manejo de errores)
        try:
            tubo_response = supabase.table("tubo")\
                                   .select("id")\
                                   .eq("codigo_interno", data_venta['propiedad']['codigo'])\
                                   .execute()
            
            if tubo_response.data:  # Actualizar existente
                tubo_id = tubo_response.data[0]['id']
                update_response = supabase.table("tubo")\
                                         .update(tubo_data)\
                                         .eq("id", tubo_id)\
                                         .execute()
                if not update_response.data:
                    raise ValueError("No se pudo actualizar el tubo existente")
            else:  # Crear nuevo
                insert_response = supabase.table("tubo")\
                                         .insert(tubo_data)\
                                         .execute()
                if not insert_response.data:
                    raise ValueError("No se pudo crear el nuevo tubo")
                tubo_id = insert_response.data[0]['id']
                
            return tubo_id
            
        except Exception as db_error:
            logger.error(f"Error en operación de tubo: {str(db_error)}")
            raise ValueError("Error al acceder a la base de datos")

    except ValueError as ve:
        logger.error(f"Error de validación: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise ValueError("Error al procesar el tubo")
    


def obtener_ventas_por_estado(estado):
    """
    Obtiene ventas filtradas por estado
    """
    try:
        # Mapear nombres de UI a valores de DB
        estado_map = {
            "En proceso": "en_proceso",
            "Negociandose": "negociandose",
            "Cerrada verbalmente": "cerrada verbalmente",
            "Cerrada en notaria": "cerrada en notaria",
            "Inscrita": "inscrita"
        }
        
        estado_db = estado_map.get(estado, estado.lower())
        
        # Obtener tubos con el estado solicitado
        tubos_response = supabase.table("tubo").select("id").eq("estado_venta", estado_db).execute()
        tubo_ids = [t["id"] for t in tubos_response.data] if tubos_response.data else []
        
        if not tubo_ids:
            return []
            
        # Obtener ventas asociadas a esos tubos
        ventas_response = supabase.table("venta").select("*").in_("tubo_id", tubo_ids).execute()
        return ventas_response.data or []
    except Exception as e:
        logger.error(f"Error al obtener ventas por estado {estado}: {str(e)}")
        return []

def obtener_ventas_recientes(dias=7):
    """
    Obtiene ventas recientes (últimos N días)
    """
    try:
        from datetime import datetime, timedelta
        fecha_limite = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
        
        response = supabase.table("venta").select("*").gte("fecha_venta", fecha_limite).execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error al obtener ventas recientes: {str(e)}")
        return []