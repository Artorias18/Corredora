from services.supabase_client import supabase
import os
from PySide6.QtWidgets import QMessageBox
import logging
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP

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
        response = supabase.rpc("obtener_detalle_venta", {"p_venta_id": venta_id}).execute()

        data = response.data

        if data and isinstance(data, dict):
            return data  # el JSON con venta, comprador, vendedor, etc.

        logging.warning(f"No se encontró detalle para venta_id {venta_id}")
        return None

    except Exception as e:
        logging.error(f"Error crítico al obtener venta {venta_id}: {str(e)}", exc_info=True)
        return None

def eliminar_venta(codigo_interno):

    try:
        response = supabase.rpc("eliminar_venta", {"p_codigo_interno" : codigo_interno}).execute()
        
        if response.data:
            print(response.data)
            return response.data
        else:
            print("Error:", response.error)
            return None
        
    except Exception as e:
        print("Excepción al eliminar:", e)
        return None


# def actualizar_estado_venta(venta_id, nuevo_estado):
#     try:
#         print(f"Llamando RPC actualizar_estado_venta con venta_id={venta_id}, nuevo_estado={nuevo_estado}")
#         response = supabase.rpc("actualizar_estado_venta", {
#             "venta_id": venta_id,
#             "nuevo_estado": nuevo_estado
#         }).execute()
#         print("Respuesta RPC:", response.data)

#         if response.data is None:
#             return False
#         if isinstance(response.data, list):
#             # Para respuesta en lista, devuelve el primer elemento
#             return response.data[0]
#         else:
#             # Para respuesta directa (bool u otro tipo), devuelve tal cual
#             return response.data
#     except Exception as e:
#         print(f"Error al actualizar estado de venta {venta_id}: {str(e)}")
#         return False


    
def asignar_porcentajes_herencia(herederos):
    """
    Asigna porcentajes de herencia para una posesión efectiva intestada.
    """
    # Contar tipos
    tipo_counts = {"conyugue": 0, "hijo": 0, "padre": 0, "fisco": 0}
    for h in herederos:
        tipo = h.get("tipo_heredero", "").lower()
        if tipo in tipo_counts:
            tipo_counts[tipo] += 1

    conyugue = tipo_counts["conyugue"]
    hijos = tipo_counts["hijo"]
    padres = tipo_counts["padre"]
    fisco = tipo_counts["fisco"]

    # Inicializar porcentajes
    for h in herederos:
        h["porcentaje"] = 0

    # Distribución según escenario
    if hijos > 0 and conyugue > 0:
        if 2 <= hijos <= 7:
            # Cónyuge doble que cada hijo
            total_partes = 2 + hijos
            porcentaje_hijo = 100 / total_partes
            porcentaje_conyugue = porcentaje_hijo * 2
            for h in herederos:
                if h["tipo_heredero"] == "hijo":
                    h["porcentaje"] = round(porcentaje_hijo, 2)
                elif h["tipo_heredero"] == "conyugue":
                    h["porcentaje"] = round(porcentaje_conyugue, 2)
        elif hijos >= 8:
            # Cónyuge 25%, resto hijos
            porcentaje_conyugue = 25.0
            porcentaje_restante = 75.0 / hijos
            for h in herederos:
                if h["tipo_heredero"] == "hijo":
                    h["porcentaje"] = round(porcentaje_restante, 2)
                elif h["tipo_heredero"] == "conyugue":
                    h["porcentaje"] = porcentaje_conyugue
        else:
            # 1 hijo o escenario no cubierto
            total_partes = hijos + 1
            porcentaje_base = 100 / total_partes
            for h in herederos:
                if h["tipo_heredero"] in ["hijo", "conyugue"]:
                    h["porcentaje"] = round(porcentaje_base, 2)

    elif hijos > 0 and conyugue == 0:
        # Solo hijos
        porcentaje_hijo = 100 / hijos
        for h in herederos:
            if h["tipo_heredero"] == "hijo":
                h["porcentaje"] = round(porcentaje_hijo, 2)

    elif conyugue > 0 and hijos == 0 and padres > 0:
        # Cónyuge + padres
        porcentaje_conyugue = 50
        porcentaje_padre = 50 / padres
        for h in herederos:
            if h["tipo_heredero"] == "conyugue":
                h["porcentaje"] = porcentaje_conyugue
            elif h["tipo_heredero"] == "padre":
                h["porcentaje"] = round(porcentaje_padre, 2)

    elif hijos > 0 and padres > 0 and conyugue == 0:
        # Hijos + padres
        porcentaje_hijo = 50 / hijos
        porcentaje_padre = 50 / padres
        for h in herederos:
            if h["tipo_heredero"] == "hijo":
                h["porcentaje"] = round(porcentaje_hijo, 2)
            elif h["tipo_heredero"] == "padre":
                h["porcentaje"] = round(porcentaje_padre, 2)

    elif conyugue > 0 and hijos == 0 and padres == 0:
        # Solo cónyuge
        for h in herederos:
            if h["tipo_heredero"] == "conyugue":
                h["porcentaje"] = 100.0

    elif fisco > 0 or len(herederos) == 0:
        # Herencia al fisco si no hay otros herederos
        for h in herederos:
            if h["tipo_heredero"] == "fisco":
                h["porcentaje"] = 100.0

    # Ajuste final para que la suma sea 100%
    total = round(sum(h["porcentaje"] for h in herederos), 2)
    diff = round(100 - total, 2)
    if abs(diff) > 0.01 and herederos:
        herederos[-1]["porcentaje"] = round(herederos[-1]["porcentaje"] + diff, 2)

    return herederos




def asignar_porcentajes_herencia_testada(herederos, mejoras=None, libre_disposicion=None):
    """
    Asigna porcentajes de herencia para una posesión efectiva testada.
    
    mejoras: lista de ruts de herederos que recibirán la cuarta de mejoras.
    libre_disposicion: diccionario con rut como clave y porcentaje (del 25%) como valor.
    """
    mejoras = mejoras or []
    libre_disposicion = libre_disposicion or {}

    # Identificar herederos forzosos
    herederos_forzosos = [h for h in herederos if h.get("tipo_heredero") == "forzoso"]
    if not herederos_forzosos:
        raise ValueError("Debe haber al menos un heredero forzoso en posesión testada.")

    # Inicializar porcentajes
    for h in herederos:
        h["porcentaje"] = 0

    # Asignar mitad legítima (50%) entre forzosos
    porcentaje_legitima = 50 / len(herederos_forzosos)
    for h in herederos_forzosos:
        h["porcentaje"] += porcentaje_legitima

    # Asignar cuarta de mejoras (25%)
    if mejoras:
        porcentaje_mejora = 25 / len(mejoras)
        for h in herederos:
            if h["rut"] in mejoras:
                h["porcentaje"] += porcentaje_mejora

    # Asignar cuarta de libre disposición (25%)
    if libre_disposicion:
        total_libre = sum(libre_disposicion.values())
        if total_libre != 25:
            # Normalizar proporcionalmente
            factor = 25 / total_libre
        else:
            factor = 1

        for h in herederos:
            rut = h["rut"]
            if rut in libre_disposicion:
                h["porcentaje"] += libre_disposicion[rut] * factor

    # Redondeo final
    for h in herederos:
        h["porcentaje"] = round(h["porcentaje"], 2)

    # Validar suma total
    total_porcentaje = round(sum(h["porcentaje"] for h in herederos), 2)
    if total_porcentaje > 100:
        raise ValueError(f"La suma total de porcentajes de herencia supera el 100%: {total_porcentaje}%")




def guardar_venta(data_venta, data_posesion=None, herederos=None, mejoras=None, libre_disposicion=None, es_venta_cerrada=False):
    """
    Guarda una nueva venta (en proceso o cerrada)
    """
    try:
        # Validar datos mínimos

        if not data_venta.get('propiedad',{}).get('codigo'):
            raise ValueError("El código de la propiedad es obligatorio")
        
        # if es_venta_cerrada:
        #     if not data_venta.get('comprador', {}).get('rut'):
        #         raise ValueError("El RUT del comprador es obligatorio para ventas cerradas")
        #     if not data_venta.get('vendedor', {}).get('rut'):
        #         raise ValueError("El RUT del vendedor es obligatorio para ventas cerradas")
        #     if not data_venta.get('venta', {}).get('tipo_venta'):
        #         raise ValueError("El tipo de venta es obligatorio para ventas cerradas")

        # Determinar estado de venta
        estado_venta = data_venta['venta'].get('estado_venta', 'en_proceso' if not es_venta_cerrada else 'negociandose')
        
        # Determinar tipo de venta
        tipo_venta = data_venta['venta'].get('tipo_venta', '')

        # Guardar/actualizar propiedad
        propiedad_data = {
            'codigo_interno': data_venta['propiedad']['codigo'],
            'direccion': data_venta['propiedad'].get('direccion', ''),
            'rol': data_venta['propiedad'].get('rol', 0),
            'comuna': data_venta['propiedad'].get('comuna', ''),
            'estudio_titulos': data_venta['propiedad'].get('estudio_titulos', 'No Posee Documento'),
            'dominio_vigente': data_venta['propiedad'].get('dominio_vigente', 'No Posee Documento')
        }
        supabase.table("propiedad").upsert(propiedad_data,
                                           on_conflict= "codigo_interno").execute()
        


        # 1. Guardar/actualizar comprador si hay datos
        if any ([data_venta['comprador'].get('rut')]):
            comprador_data = {
                'rut': data_venta['comprador']['rut'],
                'codigo_interno': data_venta['propiedad']['codigo'],
                'nombre': data_venta['comprador'].get('nombre', ''),
                'direccion': data_venta['comprador'].get('direccion', ''),
                'telefono': data_venta['comprador'].get('telefono', ''),
                'correo_electronico': data_venta['comprador'].get('correo', ''),
                'banco': data_venta['comprador'].get('banco', ''),
                'tipo_cuenta': data_venta['comprador'].get('tipo_cuenta', ''),
                'nro_cuenta': data_venta['comprador'].get('nro_cuenta', ''),
                'poder_judicial': data_venta['comprador'].get('poder_judicial', 'No')
            }
            supabase.table("comprador").upsert(comprador_data, 
                                               on_conflict="rut").execute()

        # 2. Guardar/actualizar vendedor si hay datos
        if any([data_venta['vendedor'].get('rut')]):
            vendedor_data = {
                'rut': data_venta['vendedor']['rut'],
                'codigo_interno': data_venta['propiedad']['codigo'],
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
            supabase.table("vendedor").upsert(vendedor_data,
                                              on_conflict="rut").execute()


        
        if any([data_venta['venta'].get('limitaciones'), data_venta['venta'].get('viabilidad')]):
            estado_doc_data = {
                'codigo_interno': data_venta['propiedad']['codigo'],
                'limitaciones_dominio': data_venta['venta'].get('limitaciones', 'No'),
                'viabilidad_vendedor': data_venta['venta'].get('viabilidad', '')
            }
            supabase.table("estado_documental").upsert(estado_doc_data,
                                                       on_conflict= "codigo_interno").execute()

        if es_venta_cerrada and tipo_venta in ["Credito H.", "Credito H. + Subsidio"]:

            monto_texto = data_venta['pre_aprobacion_credito']['monto_financiamiento']  # ejemplo: "40.000.000"

            
            try:
                monto_limpio = float(monto_texto.replace(".", "").replace(",", ""))  # opcional eliminar comas si vienen
            except ValueError:
                monto_limpio = 0  # o manejar error de forma adecuada

            pre_aprobacion_data = {
                'codigo_interno': data_venta['propiedad']['codigo'],
                'porcentaje_financiamiento': data_venta['pre_aprobacion_credito']['porcentaje_financiamiento'],
                'monto_financiamiento': monto_limpio,
                'diferencias': data_venta['pre_aprobacion_credito'].get('diferencias',''),
                'banco_credito': data_venta['pre_aprobacion_credito']['banco_credito'].strip(),
                'estado_preaprobacion':data_venta['pre_aprobacion_credito']['estado_preaprobacion']
            }

            porcentaje_str = pre_aprobacion_data.get('porcentaje_financiamiento', '0')  # siempre un string
            try:
                # Convierte a Decimal, divide entre 100 y fija 4 decimales exactos
                porcentaje = (Decimal(porcentaje_str) / Decimal(100)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            except Exception:
                porcentaje = Decimal("0.0000")

            pre_aprobacion_data['porcentaje_financiamiento'] = float(porcentaje)

            supabase.table("pre_aprobacion_credito").upsert(pre_aprobacion_data,
                                                            on_conflict= "codigo_interno").execute()

        if es_venta_cerrada and tipo_venta in ["Subsidio", "Credito H. + Subsidio"]:

            monto_subsidio_texto = data_venta['subsidio_aprobado']['monto_subsidio']

            try:
                monto_subsdio_limpio = float(monto_subsidio_texto.replace(".","").replace(",",""))

            except ValueError:

                monto_subsdio_limpio = 0

            subsidio_aprobado_data = {
                'codigo_interno': data_venta['propiedad']['codigo'],
                'monto_subsidio': monto_subsdio_limpio ,
                'porcentaje_subsidio': data_venta['subsidio_aprobado']['porcentaje_subsidio'],
                'resolucion_subsidio': data_venta['subsidio_aprobado'].get('resolucion_subsidio', ''),
                'estado_subsidio': data_venta['subsidio_aprobado']['estado_subsidio']
            }

            porcentaje_sub_str = subsidio_aprobado_data.get('porcentaje_subsidio', '0')
            try:
                # Convierte a Decimal, divide entre 100 y fija 4 decimales exactos
                porcentaje_sub = (Decimal(porcentaje_sub_str) / Decimal(100)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            except Exception:
                porcentaje_sub = Decimal("0.0000")
            
            subsidio_aprobado_data['porcentaje_subsidio'] = float(porcentaje_sub)

            supabase.table("subsidio_aprobado").upsert(subsidio_aprobado_data,
                                                       on_conflict= "codigo_interno").execute()


            


        
        if es_venta_cerrada and  tipo_venta in ["Subsidio", "Credito H.", "Credito H. + Subsidio"]:
            if any([data_venta['tasador'].get('rut')]):
                tasador_data = {
                    'rut': data_venta['tasador']['rut'],
                    'nombre': data_venta['tasador'].get('nombre', ''),
                    'telefono': data_venta['tasador'].get('telefono', ''),
                    'codigo_interno': data_venta['propiedad']['codigo'],
                    'correo_electronico': data_venta['tasador'].get('correo', ''),
                }
                supabase.table("tasador").upsert(tasador_data,
                                                 on_conflict="rut").execute()


            if any([data_venta['recepcion_definitiva'].get('superficie'), 
                    data_venta['recepcion_definitiva'].get('edificada'),
                    data_venta['recepcion_definitiva'].get('recepcion')]):
                recepcion_data = {
                    'codigo_interno': data_venta['propiedad']['codigo'],
                    'superficie': data_venta['recepcion_definitiva'].get('superficie', 'No Posee Documento'),
                    'edificada': data_venta['recepcion_definitiva'].get('edificada', 'No Posee Documento'),
                    'recepcion': data_venta['recepcion_definitiva'].get('recepcion', 'No Posee Documento')
                } 
                
                supabase.table("recepcion_definitiva").upsert(recepcion_data,
                                                              on_conflict= "codigo_interno").execute()
            
            if any([
                data_venta['documentos_tasacion'].get('doc_propiedad'),
                data_venta['documentos_tasacion'].get('copia_subsidio'),
                data_venta['documentos_tasacion'].get('informe_tasacion'),
                data_venta['documentos_tasacion'].get('certif_habitabilidad')]):


                tasacion_data = {
                    'codigo_interno': data_venta['propiedad']['codigo'],
                    'doc_propiedad' : data_venta['documentos_tasacion']['doc_propiedad'],
                    'copia_subsidio': data_venta['documentos_tasacion']['copia_subsidio'],
                    'informe_tasacion':data_venta['documentos_tasacion']['informe_tasacion'],
                    'certif_habitabilidad': data_venta['documentos_tasacion']['certif_habitabilidad']

                }
                supabase.table("documentos_tasacion").upsert(tasacion_data,
                                                             on_conflict= "codigo_interno").execute()

            confeccion_data = {
                'codigo_interno': data_venta['propiedad']['codigo'],
                'doc_propiedad': data_venta['documentos_escritura'].get('doc_propiedad', 'No Posee Documento'),
                'doc_tasacion': data_venta['documentos_escritura'].get('doc_tasacion', 'No Posee Documento'),
                'dj_no_parent_comp_vend': data_venta['documentos_escritura'].get('dj_no_parent_comp_vend', 'No Posee Documento'),
                'subsidio_original': data_venta['documentos_escritura'].get('subsidio_original', 'No Posee Documento'),
                'dj_vend_no_habitual': data_venta['documentos_escritura'].get('dj_vend_no_habitual', 'No Posee Documento'),
                'dj_comp_no_parientes_cargos_publicos': data_venta['documentos_escritura'].get('dj_comp_no_parientes_cargos_publicos', 'No Posee Documento')
            }
            supabase.table("documentos_escritura").upsert(confeccion_data,
                                                          on_conflict= "codigo_interno").execute()



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

        monto_venta = data_venta['venta'].get('monto_venta', "")

        try:
            monto_venta_limpio = float(monto_venta.replace(".","").replace(",","")) if monto_venta else 0

        except ValueError:
            monto_venta_limpio = 0

        venta_data = {
            'codigo_interno': data_venta['propiedad']['codigo'],
            'tubo_id': tubo_id,
            'fecha_venta': data_venta['venta'].get('fecha_venta'),
            'monto_venta': monto_venta_limpio,
            'observaciones': data_venta['venta'].get('observaciones', ''),
            'es_venta_proceso': not es_venta_cerrada,
            'inscripcion': data_venta['venta'].get('inscripcion', 'No Posee Documento'),
            'hipoteca': data_venta['venta'].get('hipoteca', 'No Posee Documento'),
            'gravamen': data_venta['venta'].get('gravamen', 'No Posee Documento'),
            'certificado_numero': data_venta['venta'].get('certificado_numero', 'No Posee Documento'),
            'aseo': data_venta['venta'].get('aseo', 'No Posee Documento'),
            'no_expropiacion': data_venta['venta'].get('no_expropiacion', 'No Posee Documento'),
            'comprador_pago':data_venta['venta'].get('comprador_pago', 'No'),
            'vendedor_pago':data_venta['venta'].get('vendedor_pago', 'No'),
            'comprador_cuando_paga':data_venta['venta'].get('comprador_cuando_paga', 'Promesa'),
            'vendedor_cuando_paga':data_venta['venta'].get('vendedor_cuando_paga', 'Promesa'),
            'tipo_documento': data_venta['venta'].get('tipo_documento', 'Boleta')

        }

        if es_venta_cerrada and tipo_venta in ["Subsidio", "Credito H. + Subsidio"]:

            abono_prev_texto = data_venta['venta'].get('abono_previsto', '0')
            abono_real_texto = data_venta['venta'].get('abono_real', '0')

            try:
                abono_previo = float(abono_prev_texto.replace(".", "").replace(",", "."))
            except (ValueError, AttributeError):
                abono_previo = 0.0

            try:
                abono_real = float(abono_real_texto.replace(".", "").replace(",", "."))
            except (ValueError, AttributeError):
                abono_real = 0.0

            # Siempre insertar ambos valores, incluso si son 0
            venta_data['abono_previsto'] = abono_previo
            venta_data['abono_real'] = abono_real

            

            documentos_pas_data = {
                'codigo_interno': data_venta['propiedad']['codigo'],
                'fecha_ingreso_docs': data_venta['documentos_pas']['fecha_ingreso_docs'],
                'supe_platas': data_venta['documentos_pas'].get('supe_platas'),
                'reparos' : data_venta['documentos_pas'].get('reparos','')
            }
            
            supabase.table("documentos_pas").upsert(documentos_pas_data,
                                                    on_conflict= "codigo_interno").execute()





        comprador_rut = data_venta['comprador'].get('rut','').strip()
        if comprador_rut:
            venta_data['comprador_rut'] = comprador_rut
        
        vendedor_rut = data_venta['vendedor'].get('rut','').strip()
        if vendedor_rut:
            venta_data['vendedor_rut'] = vendedor_rut


        venta_existente_resp = supabase.table("venta").select("id").eq("tubo_id", tubo_id).execute()
        if venta_existente_resp.data:
            venta_id = venta_existente_resp.data[0]['id']
            venta_data["id"] = venta_id  # 👉 Esto hace que el upsert actualice


        

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
                'canal': data_posesion.get('canal', 'Registro Civil'),
                'estado_proceso': data_posesion.get('estado_proceso', 'solicitud'),
                'observaciones': data_posesion.get('observaciones', '')
            }
            supabase.table("posesion_efectiva").upsert(posesion_data,
                                                       on_conflict= "codigo_interno").execute()
            
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
                
                supabase.table("herederos").upsert(herederos_data, on_conflict=["heredero_key"]).execute()

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