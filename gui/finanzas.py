from PySide6.QtWidgets import QHeaderView, QFileDialog, QMainWindow,QHBoxLayout,QTextEdit,QTabWidget,QDoubleSpinBox,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QIntValidator, QColor, QDoubleValidator
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
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

    def ajustar_columnas(self, ws):
        """Ajusta automáticamente el ancho de las columnas."""
        for col in ws.columns:
            max_length = 0
            col_letter = get_column_letter(col[0].column)

            for cell in col:
                try:
                    value_length = len(str(cell.value)) if cell.value else 0
                    max_length = max(max_length, value_length)
                except:
                    pass

            ws.column_dimensions[col_letter].width = max_length + 2


    def generar_excel_finanzas(self, df, ruta_salida):
        """Genera el archivo Excel usando openpyxl."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Finanzas"

        # Escribir encabezados
        ws.append(list(df.columns))

        # Escribir filas
        for _, row in df.iterrows():
            ws.append(list(row))

        # Ajustar columnas
        self.ajustar_columnas(ws)

        # Guardar archivo
        wb.save(ruta_salida)


    #### ---------------- EXPORTADOR ---------------- ####

    def exportar_excel(self):
        """
        Exporta a Excel tomando los datos desde la tabla de PySide,
        creará un DataFrame con TODAS las columnas que indicaste,
        completando con vacío lo que no exista en la tabla.
        """

        # Columnas definidas por ti
        columnas = [
            "ROL", "COMUNA", "DIRECCION", "NRO DEPARTAMENTO",
            "NOMBRE ARRENDATARIO", "RUT ARRENDATARIO", "MES ARRIENDO",
            "MONTO RENTA", "FECHA PAGO", "ESTADO", "NRO CONTRATO",
            "FECHA INICIO", "FECHA TERMINO", "DESCUENTO", "FORMATO",
            "CATEGORIA", "CUENTA CONTABLE", "NOMBRE PROPIETARIO",
            "RUT PROPIETARIO", "CORREO ARRENDATARIO", "TELEFONO",
            "FECHA CONVENIO", "CODIGO", "COMISION", "RESPONSABLE",
            "OBSERVACIONES", "TIPO PAGO", "GASTO COMUN", "GARANTIA",
            "OTROS CARGOS", "NETO A PAGAR"
        ]

        # --- Crear DataFrame vacío con todas las columnas ---
        df = pd.DataFrame(columns=columnas)

        # --- Obtener datos desde tu tabla actual ---
        filas = self.tabla_arriendos.rowCount()
        columnas_tabla = self.tabla_arriendos.columnCount()

        for row in range(filas):
            fila_dict = {}

            # SOLO se llenan las columnas reales que existan en tu tabla actual
            for col in range(columnas_tabla):
                header = self.tabla_arriendos.horizontalHeaderItem(col).text()
                item = self.tabla_arriendos.item(row, col)
                value = item.text() if item else ""
                fila_dict[header] = value

            # Agregar fila al DataFrame (las demás columnas quedan vacías)
            df = pd.concat([df, pd.DataFrame([fila_dict])], ignore_index=True)

        # --- Elegir ruta de guardado ---
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Excel",
            "",
            "Archivos Excel (*.xlsx)"
        )

        if not ruta:
            return
        
        if not ruta.endswith(".xlsx"):
            ruta += ".xlsx"

        try:
            self.generar_excel_finanzas(df, ruta)
            QMessageBox.information(self, "Éxito", f"Excel generado correctamente:\n{ruta}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar Excel:\n{e}")
