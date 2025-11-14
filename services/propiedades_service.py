from services.supabase_client import supabase
import os
from PySide6.QtWidgets import QMessageBox
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def obtener_ventas_resumen():
    """
    Obtiene un resumen de todas las ventas, opcionalmente filtradas por estado
    """
    try:
        # Obtener todas las ventas
        response = supabase.rpc("obtener_ventas_resumen").execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error al obtener ventas: {str(e)}")
        return []




def obtener_detalle_propiedad(codigo_interno):
    try:
        response = supabase.rpc("obtener_detalle_propiedad", {"p_codigo_interno": codigo_interno}).execute()
        
        data = response.data

        if data and isinstance(data, dict):
            return data

        logging.warning(f"No se encontró detalle para codigo_interno {codigo_interno}")
        return None

    except Exception as e:
        logging.error(f"Error crítico al obtener propiedad {codigo_interno} : {str(e)}", exc_info=True)