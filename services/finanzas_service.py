from services.supabase_client import supabase
import os
from PySide6.QtWidgets import QMessageBox
import logging
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
import calendar
from openpyxl import Workbook
from openpyxl.styles import Font

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def obtener_ventas_ffmm_anual(anio: int):
    inicio = f"{anio}-01-01"
    fin = f"{anio}-12-31"

    response = (
        supabase
        .table("venta")
        .select("fecha_venta, codigo_interno, monto_venta, abono_real")
        .eq("es_venta_proceso", False)
        .gte("fecha_venta", inicio)
        .lte("fecha_venta", fin)
        .execute()
    )

    return response.data or []


def obtener_arriendos_ffmm_anual(anio: int):
    inicio = f"{anio}-01-01"
    fin = f"{anio}-12-31"

    response = (
        supabase
        .table("arriendo")
        .select("codigo_interno, renta_mensual, fecha_inicio, fecha_termino, honorarios_porcentaje, cuenta_fm")
        .lte("fecha_inicio", fin)
        .or_(f"fecha_termino.is.null,fecha_termino.gte.{inicio}")
        .execute()
    )

    return response.data or []


def procesar_arriendos_anual(arriendos, anio):
    operaciones = []

    for a in arriendos:
        codigo = a["codigo_interno"]
        renta = Decimal(a["renta_mensual"])
        porcentaje_contrato = Decimal(a["honorarios_porcentaje"] or 0)
        cuenta_ffmm = a.get("cuenta_fm")

        fecha_inicio = date.fromisoformat(a["fecha_inicio"])
        fecha_termino = (
            date.fromisoformat(a["fecha_termino"])
            if a["fecha_termino"]
            else date(anio, 12, 31)
        )

        inicio = max(fecha_inicio, date(anio, 1, 1))
        fin = min(fecha_termino, date(anio, 12, 31))

        mes = inicio.month
        anio_iter = inicio.year

        while date(anio_iter, mes, 1) <= fin:

            es_primer_mes = (
                fecha_inicio.year == anio_iter
                and fecha_inicio.month == mes
            )

            if es_primer_mes:
                porcentaje = Decimal("50")
                tipo = "propietario"
            else:
                porcentaje = porcentaje_contrato
                tipo = "arrendatario"

            comision = renta * porcentaje / 100

            # IVA incluido → separar IVA real
            iva = comision * Decimal("19") / Decimal("119")
            honorarios_neto = comision - iva

            operaciones.append({
                "anio": anio_iter,
                "mes": mes,
                "codigo": codigo,
                "tipo": tipo,
                "base": renta,
                "porcentaje": porcentaje,
                "honorarios": honorarios_neto,
                "iva": iva,
                "total": comision,
                "cuenta_fm": cuenta_ffmm
            })

            # avanzar mes
            mes += 1
            if mes > 12:
                mes = 1
                anio_iter += 1

    return operaciones


def procesar_ventas_anual(ventas):
    operaciones = []

    for v in ventas:
        codigo = v["codigo_interno"]
        monto_venta = Decimal(v["monto_venta"])
        abono = Decimal(v["abono_real"] or 0)

        fecha = date.fromisoformat(v["fecha_venta"])
        anio = fecha.year
        mes = fecha.month

        # Comprador y vendedor
        for tipo in ("vendedor", "comprador"):
            porcentaje = Decimal("2")
            honorarios = monto_venta * porcentaje / 100
            iva = honorarios * Decimal("0.19")
            total = honorarios + iva

            operaciones.append({
                "anio": anio,
                "mes": mes,
                "codigo": codigo,
                "tipo": tipo,
                "base": monto_venta,
                "porcentaje": porcentaje,
                "honorarios": honorarios,
                "iva": iva,
                "total": total
            })

        # Abono
        if abono > 0:
            honorarios = abono
            iva = honorarios * Decimal("0.19")
            total = honorarios + iva

            operaciones.append({
                "anio": anio,
                "mes": mes,
                "codigo": codigo,
                "tipo": "abono",
                "base": abono,
                "porcentaje": None,
                "honorarios": honorarios,
                "iva": iva,
                "total": total
            })

    return operaciones



def generar_excel_ffmm_anual(anio, ruta_archivo):
   
    ventas = obtener_ventas_ffmm_anual(anio)
    arriendos = obtener_arriendos_ffmm_anual(anio)

    operaciones = []


    operaciones += procesar_arriendos_anual(arriendos, anio)

 
    operaciones += procesar_ventas_anual(ventas)

    for op in operaciones:
        if op.get("mes") is not None:
            op["mes_nombre"] = calendar.month_name[int(op["mes"])]
        else:
            op["mes_nombre"] = ""

    operaciones.sort(
        key=lambda x: (
            x["anio"],
            x["mes"] if x["mes"] is not None else 0,
            x["codigo"],
            x["tipo"]
        )
    )

    exportar_excel_ffmm(operaciones, ruta_archivo)


def exportar_excel_ffmm(operaciones, ruta_archivo):
    wb = Workbook()
    ws = wb.active
    ws.title = "FFMM"

    headers = [
        "Año",
        "Mes",
        "Mes Nombre",
        "Código Propiedad",
        "Tipo",
        "Cuenta FFMM",
        "Base Cálculo",
        "Porcentaje",
        "Honorarios",
        "IVA",
        "Total"
    ]

    ws.append(headers)

    # Datos
    for op in operaciones:
        ws.append([
            op["anio"],
            op["mes"],
            op["mes_nombre"],
            op["codigo"],
            op["tipo"],
            op.get("cuenta_fm", ""),
            float(op["base"]),
            float(op["porcentaje"]) if op["porcentaje"] is not None else "",
            float(op["honorarios"]),
            float(op["iva"]),
            float(op["total"])
        ])

    # Header en negrita
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Formatos contables
    # Formato moneda CLP
    FORMATO_CLP = '"$"#,##0'

    for row in ws.iter_rows(min_row=2):
        row[6].number_format = FORMATO_CLP
        row[8].number_format = FORMATO_CLP
        row[9].number_format = FORMATO_CLP
        row[10].number_format = FORMATO_CLP

    # Autoajustar ancho de columnas
    for col in ws.columns:
        max_length = max(
            len(str(cell.value)) if cell.value else 0
            for cell in col
        )
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    wb.save(ruta_archivo)