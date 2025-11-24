from PySide6.QtWidgets import QHeaderView, QFileDialog, QMainWindow,QHBoxLayout,QTextEdit,QTabWidget,QDoubleSpinBox,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from services.finanzas_service import obtener_arriendos_finanzas
from PySide6.QtGui import QIntValidator, QColor, QDoubleValidator
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from gui.usuario_actual import UsuarioActual
from services.supabase_client import supabase
import pandas as pd
import os

class DashboardFinanzas(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tabla de arriendos
        self.tabla_arriendos = QTableWidget()
        self.tabla_arriendos.setColumnCount(7)
        self.tabla_arriendos.setHorizontalHeaderLabels([
            "ROL",
            "Destino",
            "DFL2",
            "Naturaleza bien raiz",
            "Comuna",
            "Rut dueño",
            "Rut arrendatario"
        ])
        self.tabla_arriendos.setSortingEnabled(True)
        self.tabla_arriendos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_arriendos.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tabla_arriendos.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla_arriendos.verticalHeader().setVisible(False)

        layout.addWidget(self.tabla_arriendos)

        # Botón exportar
        button_layout = QHBoxLayout()
        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.clicked.connect(self.exportar_excel)
        button_layout.addWidget(self.btn_exportar)
        layout.addLayout(button_layout)


    #### ---------------- FUNCIONES DE EXCEL ---------------- ####

    def generar_excel_finanzas(self, df, ruta):
        """
        Genera el Excel con formato bonito.
        """
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Arriendos"

        # Título
        ws.merge_cells("A1:R1")
        titulo = ws["A1"]
        titulo.value = "CONSOLIDADO DE ARRIENDOS"
        titulo.font = Font(size=16, bold=True)
        titulo.alignment = Alignment(horizontal="center")

        # Insertar DataFrame
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 3):
            for c_idx, value in enumerate(row, 1):
                ws.cell(row=r_idx, column=c_idx, value=value)

        # Estilo cabeceras
        header_fill = PatternFill("solid", fgColor="D9D9D9")
        for cell in ws[3]:
            cell.font = Font(bold=True)
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin")
            )

        # Ajuste seguro de anchos (sin errores por merged cells)
        for col_idx, column_cells in enumerate(ws.columns, 1):
            max_length = 0
            for cell in column_cells:
                if cell.value:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = max_length + 3

        wb.save(ruta)


    #### ---------------- EXPORTADOR ---------------- ####

    def exportar_excel(self):
        """
        Exporta Excel directamente desde Supabase, 
        incluyendo toda la información de arriendos.
        """

        datos = obtener_arriendos_finanzas()

        if not datos:
            QMessageBox.warning(self, "Sin datos", "No se encontraron arriendos para exportar.")
            return

        columnas = [
            "ROL", "COMUNA", "DIRECCION", "NRO DEPARTAMENTO",
            "NOMBRE ARRENDATARIO", "RUT ARRENDATARIO",
            "MONTO RENTA", "ESTADO",
            "FECHA INICIO", "FECHA TERMINO",
            "NOMBRE PROPIETARIO", "RUT PROPIETARIO",
            "CORREO ARRENDATARIO", "TELEFONO",
            "TIPO PAGO", "GASTO COMUN", "GARANTIA"
        ]

        df = pd.DataFrame(datos)

        # 🔹 Convertir booleano a texto legible
        if "gastos_comunes_incluidos" in df.columns:
            df["gastos_comunes"] = df["gastos_comunes_incluidos"].apply(
                lambda x: "Incluido" if x else "No incluido"
            )
        else:
            df["gastos_comunes"] = ""

        # Renombrar columnas
        df_final = df.rename(columns={
            "rol": "ROL",
            "comuna": "COMUNA",
            "direccion": "DIRECCION",
            "nombre_arrendatario": "NOMBRE ARRENDATARIO",
            "rut_arrendatario": "RUT ARRENDATARIO",
            "renta_mensual": "MONTO RENTA",
            "estado": "ESTADO",
            "fecha_inicio": "FECHA INICIO",
            "fecha_termino": "FECHA TERMINO",
            "nombre_propietario": "NOMBRE PROPIETARIO",
            "rut_propietario": "RUT PROPIETARIO",
            "correo_arrendatario": "CORREO ARRENDATARIO",
            "telefono_arrendatario": "TELEFONO",
            "forma_pago": "TIPO PAGO",
            "gastos_comunes": "GASTO COMUN",
            "garantia": "GARANTIA"
        })

        df_final = df_final.reindex(columns=columnas)

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Excel",
            "conglomerado_arriendos",
            "Archivos Excel (*.xlsx)"
        )

        if not ruta:
            return

        if not ruta.endswith(".xlsx"):
            ruta += ".xlsx"

        try:
            self.generar_excel_finanzas(df_final, ruta)
            QMessageBox.information(self, "Éxito", f"Excel generado correctamente:\n{ruta}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar Excel:\n{e}")

