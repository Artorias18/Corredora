from services.supabase_client import supabase
import os
from PySide6.QtWidgets import QMessageBox

def obtener_ventas_resumen():
    try:
        response = supabase.rpc("obtener_ventas_resumen").execute()
        return response.data or []
    except Exception as e:
        print("Error al obtener ventas:", e)
        return []

def obtener_detalle_venta(venta_id):
    try:
        response = supabase.rpc("obtener_detalle_venta", {"venta_id": venta_id}).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print("Error al obtener detalle:", e)
        return None
    
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
    mejoras = mejoras or []
    libre_disposicion = libre_disposicion or {}

    # Identificar herederos forzosos
    herederos_forzosos = [h for h in herederos if h.get("tipo_heredero") == "forzoso"]
    total_forzosos = len(herederos_forzosos)

    if total_forzosos == 0:
        raise ValueError("Debe haber al menos un heredero forzoso en posesión testada.")

    # Asignar mitad legítima (50%)
    porcentaje_legitima = 50 / total_forzosos
    for heredero in herederos_forzosos:
        heredero["porcentaje"] = porcentaje_legitima

    # Asignar cuarta de mejoras (25%)
    if mejoras:
        porcentaje_mejora = 25 / len(mejoras)
        for heredero in herederos:
            if heredero["rut"] in mejoras:
                heredero["porcentaje"] = heredero.get("porcentaje", 0) + porcentaje_mejora

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



def guardar_venta(data_venta, data_posesion=None, herederos=None, mejoras=None, libre_disposicion=None):
    try:
        # Insertar comprador
        supabase.table("comprador").insert({
            'rut': data_venta['comprador']['rut'],
            'nombre': data_venta['comprador']['nombre'],
            'direccion': data_venta['comprador']['direccion'],
            'telefono': data_venta['comprador']['telefono'],
            'correo_electronico': data_venta['comprador']['correo'],
            'banco': data_venta['comprador'].get('banco', ''), 
            'tipo_cuenta': data_venta['comprador']['tipo_cuenta'],
            'nro_cuenta': data_venta['comprador']['nro_cuenta'],
            'poder_judicial': data_venta['comprador']['poder_judicial']
        }).execute()

        # Insertar vendedor
        supabase.table("vendedor").insert({
            'rut': data_venta['vendedor']['rut'],
            'nombre': data_venta['vendedor']['nombre'],
            'direccion': data_venta['vendedor']['direccion'],
            'telefono': data_venta['vendedor']['telefono'],
            'correo_electronico': data_venta['vendedor']['correo'],
            'banco': data_venta['vendedor'].get('banco', ''),
            'tipo_cuenta': data_venta['vendedor']['tipo_cuenta'],
            'nro_cuenta': data_venta['vendedor']['nro_cuenta'] 
        }).execute()

        # Insertar propiedad si no existe
        supabase.table("propiedad").upsert({
            'codigo_interno': data_venta['propiedad']['codigo'],
            'direccion': data_venta['propiedad']['direccion'],
            'rol': data_venta['propiedad']['rol'],
            'comuna': data_venta['propiedad']['comuna'],
            'estudio_titulos': data_venta['propiedad']['estudio_titulos'],
            'inscripcion': data_venta['propiedad']['inscripcion'],
            'dominio_vigente': data_venta['propiedad']['dominio_vigente'],
            'hipoteca': data_venta['propiedad']['hipoteca'],
            'gravamen': data_venta['propiedad']['gravamen'],
            'certificado_numero': data_venta['propiedad']['certificado_numero'],
            'aseo': data_venta['propiedad']['aseo'],
            'no_expropiacion': data_venta['propiedad']['no_expropiacion']
        }).execute()

        supabase.table("estado_documental").upsert({
            'codigo_interno': data_venta['propiedad']['codigo'],
            'limitaciones_dominio': data_venta['venta']['limitaciones'],
            'viabilidad_vendedor': data_venta['venta']['viabilidad']
        }).execute()

        # supabase.table("recepcion_definitiva").upsert({
        #     'codigo_interno': data_venta['propiedad']['codigo'],
        #     'superficie': data_venta['venta']['superficie'],
        #     'edificada': data_venta['venta']['edificada'],
        #     'recepcion':data_venta['venta']['recepcion']
        # }).execute()




        # Obtener tubo_id
        tubo_id = obtener_o_crear_tubo(
            tipo_venta=data_venta['venta']['tipo_venta'],
            estado_venta=data_venta['venta']['estado_venta'],
            codigo_interno=data_venta['propiedad']['codigo'],
            propiedad_ofrecida=data_venta['venta'].get('propiedad_ofrecida'),  # None si no existe
            regularizaciones_ampliaciones=data_venta['venta'].get('regularizaciones')  # None si no existe
        )

        if tubo_id is None:
            raise ValueError("No se pudo obtener o crear el tubo.")

        # Insertar venta
        venta_insertada = supabase.table("venta").insert({
            'comprador_rut': data_venta['comprador']['rut'],
            'vendedor_rut': data_venta['vendedor']['rut'],
            'codigo_interno': data_venta['propiedad']['codigo'],
            'fecha_venta': data_venta['venta']['fecha_venta'],
            'monto_venta': float(data_venta['venta']['monto_venta']),
            'observaciones': data_venta['venta']['observaciones'],
            'tubo_id': tubo_id
        }).execute()

        if not venta_insertada or venta_insertada.data is None or not venta_insertada.data:
            raise ValueError(f"La venta no se insertó correctamente. Resultado: {venta_insertada}")

        venta_id = venta_insertada.data[0]['id']

        # Insertar herederos si corresponde
        if data_posesion is not None and isinstance(data_posesion, dict) and data_venta['venta']['tipo_venta'] == 'Posesión Efectiva':
            # Asegurar que herederos sea una lista válida
            herederos = herederos if herederos is not None else []
            
            if not isinstance(herederos, list):
                raise ValueError("'herederos' debe ser una lista o None")

            # Verificar que data_posesion tenga 'tipo'
            if 'tipo' not in data_posesion:
                raise ValueError("data_posesion debe tener clave 'tipo'")

            # Procesar herederos solo si hay datos válidos
            if herederos:  # Solo si la lista no está vacía
                if data_posesion['tipo'] == 'Intestada':
                    asignar_porcentajes_herencia(herederos)
                elif data_posesion['tipo'] == 'Testada':
                    asignar_porcentajes_herencia_testada(
                        herederos, 
                        mejoras=mejoras or [], 
                        libre_disposicion=libre_disposicion or {}
                    )

                # Insertar en Supabase
                for heredero in herederos:
                    heredero['venta_id'] = venta_id
                supabase.table("herederos").insert(herederos).execute()

        return venta_id

    except Exception as e:
        print(f"Error detallado al guardar venta: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def obtener_o_crear_tubo(tipo_venta, estado_venta, codigo_interno, propiedad_ofrecida=None, regularizaciones_ampliaciones=None):
    try:
        # Normalizar valores para coincidir con la tabla
        tipo_venta_normalizado = {
            'Posesión Efectiva': 'Posesion Efectiva',
            'Efectivo': 'Efectivo',
            'Subsidio': 'Subsidio',
            'Credito H.': 'Credito H.',
            'Credito H. + Subsidio': 'Credito H. + Subsidio'
        }.get(tipo_venta, tipo_venta)

        # Valores por defecto para campos NOT NULL
        propiedad_ofrecida = 'No' if propiedad_ofrecida is None else ('Si' if propiedad_ofrecida else 'No')
        en_venta = 'No'  # Valor por defecto según tu estructura
        regularizaciones = 'No' if regularizaciones_ampliaciones is None else ('Si' if regularizaciones_ampliaciones else 'No')

        # 1. Buscar tubo existente
        response = supabase.table("tubo").select("id").match({
            "tipo_venta": tipo_venta_normalizado,
            "codigo_interno": codigo_interno
        }).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        
        # 2. Crear nuevo tubo
        insert_data = {
            "tipo_venta": tipo_venta_normalizado,
            "estado_venta": estado_venta,
            "codigo_interno": codigo_interno,
            "propiedad_ofrecida": propiedad_ofrecida,
            "en_venta": en_venta,
            "regularizaciones_ampliaciones": regularizaciones
        }

        insert_response = supabase.table("tubo").insert(insert_data).execute()

        if insert_response.data and len(insert_response.data) > 0:
            return insert_response.data[0]["id"]
        else:
            print("Error al crear tubo. Respuesta:", insert_response)
            raise ValueError("No se pudo crear el tubo. Verifica los datos y restricciones.")

    except Exception as e:
        print(f"Error detallado en obtener_o_crear_tubo: {str(e)}")
        import traceback
        traceback.print_exc()
        return None