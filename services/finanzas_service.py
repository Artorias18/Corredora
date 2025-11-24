from services.supabase_client import supabase
import os
from PySide6.QtWidgets import QMessageBox
import logging
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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