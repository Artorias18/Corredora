from PySide6.QtWidgets import QHeaderView,QSplitter, QGroupBox, QDialogButtonBox, QSizePolicy, QFileDialog, QMainWindow, QHBoxLayout, QTextEdit, QTabWidget, QDoubleSpinBox, QHeaderView, QFrame, QWidget, QLabel, QVBoxLayout, QAbstractItemView, QTableWidget, QTableWidgetItem, QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton, QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem, QSpinBox, QDialog
from PySide6.QtCore import Qt, QDate, Signal, QTimer

from PySide6.QtGui import QIntValidator, QColor, QDoubleValidator, QFont
from gui.usuario_actual import UsuarioActual
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from services.supabase_client import supabase
from services.eva_arrendatarios_service import actualizar_arrendatario,regla_3x_renta,eliminar_evaluacion,obtener_evaluacion_completa,editar_evaluacion,guardar_evaluacion,CASTIGO_DEFAULT, IVA_FACTOR,calcular_evaluacion_independiente,obtener_detalle_evaluacion,cargar_detalle_dependiente,safe_numeric,obtener_evaluaciones_arrendatario, cargar_detalle, obtener_arrendatarios, obtener_arrendatario, crear_arrendatario, eliminar_arrendatario
import json
import calendar
import re
from datetime import date
from calendar import monthrange
import pandas as pd


class DashboardEvaluaciones(QWidget):
    def __init__(self, arriendo_id=None, parent=None):
        super().__init__(parent)
        self.arriendo_id = arriendo_id
        self.rentas_tributables = []
        self.detalle_arriendo = {}
        self.evaluacion_meses = {}

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(TabArrendatarios(), " Arrendatarios")
        self.tabs.addTab(TabEvaluaciones(), " Evaluaciones")
        layout.addWidget(self.tabs)
        self.setLayout(layout)


class DoubleClickButton(QPushButton):
    doubleClicked = Signal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()


class TabArrendatarios(QWidget):
    def __init__(self, parent=None):
            super().__init__(parent)
            layout = QVBoxLayout(self)

            # -----------------------------
            # 1. FILTROS (ARRIBA)
            # -----------------------------
            filtros_layout = QHBoxLayout()

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Buscar por RUT o Nombre...")
            self.search_input.textChanged.connect(self.aplicar_filtros)

            filtros_layout.addWidget(QLabel("Filtros:"))
            filtros_layout.addWidget(self.search_input)

            layout.addLayout(filtros_layout)

            # -----------------------------
            # 2. TABLA (CENTRO)
            # -----------------------------
            self.tabla = QTableWidget()
            self.tabla.setColumnCount(3)
            self.tabla.setHorizontalHeaderLabels(["RUT", "Nombre", "Tipo Trabajador"])
            self.tabla.verticalHeader().setVisible(False)
            self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
            self.tabla.setSelectionMode(QTableWidget.SingleSelection)

            # Permitir que el texto se ajuste a varias líneas
            self.tabla.setWordWrap(True)

            # Ajustar columnas al contenido (no estira la última)
            
            self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            # Ajustar altura de filas según contenido
            self.tabla.resizeRowsToContents()

            layout.addWidget(self.tabla)

            self.tabla.setStyleSheet("""
                QTableWidget::item:selected {
                    background-color: #D5D8DC;
                    color: black;
                }
            """)

            # -----------------------------
            # 3. BOTONES (ABAJO)
            # -----------------------------
            boton_layout = QHBoxLayout()
            self.btn_agregar = DoubleClickButton("Agregar")
            self.btn_editar = DoubleClickButton("Editar")
            self.btn_actualizar_tabla = DoubleClickButton("Actualizar")
            self.btn_eliminar = DoubleClickButton("Eliminar")

            boton_layout.addWidget(self.btn_agregar)
            boton_layout.addWidget(self.btn_editar)
            boton_layout.addWidget(self.btn_eliminar)
            boton_layout.addWidget(self.btn_actualizar_tabla)

            layout.addLayout(boton_layout)

            # Conexiones
            self.btn_agregar.doubleClicked.connect(self.agregar_arrendatario)
            self.btn_editar.doubleClicked.connect(self.editar_arrendatario)
            self.btn_eliminar.doubleClicked.connect(self.eliminar_arrendatario)
            self.btn_actualizar_tabla.clicked.connect(self.cargar_arrendatarios)

            # Cargar datos
            self.todo_arrendatarios = []
            self.cargar_arrendatarios()

    def cargar_arrendatarios(self):
            self.todo_arrendatarios = obtener_arrendatarios()
            self.aplicar_filtros()

        # ----------------------------------------
        # FILTROS
        # ----------------------------------------
    def aplicar_filtros(self):
            texto = self.search_input.text().lower()

            datos = []

            for t in self.todo_arrendatarios:
                rut = t.get("rut", "").lower()
                nombre = t.get("nombre", "").lower()

                if texto and texto not in rut and texto not in nombre:
                    continue

                datos.append(t)

            self._poblar_tabla(datos)

    def _poblar_tabla(self, data):
            self.tabla.setRowCount(0)
            for row, t in enumerate(data):
                self.tabla.insertRow(row)
                self.tabla.setItem(row, 0, QTableWidgetItem(t.get("rut", "")))
                self.tabla.setItem(
                    row, 1, QTableWidgetItem(t.get("nombre", "")))
                self.tabla.setItem(row, 2, QTableWidgetItem(
                    t.get("tipo_trabajador", "")))

    def _obtener_arrendatario_fila(self, fila: int) -> dict | None:
            if fila < 0:
                return None
            rut = self.tabla.item(fila, 0).text()
            return obtener_arrendatario(rut)

    def agregar_arrendatario(self):
            dlg = FormularioArrendatario(parent=self)
            if dlg.exec():
                data = dlg.datos
                if data:
                    crear_arrendatario(data)
                    self.cargar_arrendatarios()

    def editar_arrendatario(self):
            fila = self.tabla.currentRow()
            if fila < 0:
                QMessageBox.warning(
                    self, "Atención", "Seleccione un arrendatario para editar.")
                return
            arrendatario = self._obtener_arrendatario_fila(fila)
            if not arrendatario:
                QMessageBox.warning(
                    self, "Error", "No se pudo cargar el arrendatario seleccionado.")
                return

            dlg = FormularioArrendatario(arrendatario, parent=self)
            if dlg.exec():
                data = dlg.datos
                if data:
                    actualizar_arrendatario(arrendatario["rut"], data)
                    self.cargar_arrendatarios()


    def eliminar_arrendatario(self):
            fila = self.tabla.currentRow()
            if fila < 0:
                QMessageBox.warning(
                    self, "Atención", "Seleccione un trabajador para eliminar.")
                return
            rut = self.tabla.item(fila, 0).text()
            if QMessageBox.question(
                self,
                "Confirmar",
                f"¿Eliminar trabajador {rut}?"
            ) == QMessageBox.Yes:
                eliminar_arrendatario(rut)
                self.cargar_arrendatarios()


class TabEvaluaciones(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.evaluaciones = []   # cache maestro

        self._eval_ids = []
        self._eval_tipos = []   # 👈 NUEVO

        layout = QVBoxLayout(self)

        # =============================
        # 1. FILTROS
        # =============================
        filtros_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Buscar por nombre o RUT..."
        )
        self.search_input.textChanged.connect(self.aplicar_filtros)


        filtros_layout.addWidget(QLabel("Filtros:"))
        filtros_layout.addWidget(self.search_input)


        layout.addLayout(filtros_layout)

        # =============================
        # 2. TABLA EVALUACIONES
        # =============================
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "RUT",
            "Nombre",
            "Tipo",
            "Fecha",
            "Resultado",
            "Renta"
        ])

        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)

        # Permitir que el texto se ajuste en varias líneas
        self.tabla.setWordWrap(True)

        # Ajustar columnas al contenido
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Ajustar altura de filas según contenido
        self.tabla.resizeRowsToContents()

        

        self.tabla.itemSelectionChanged.connect(
            self._evaluacion_seleccionada
        )

        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.tabla.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #D5D8DC;
                color: black;
            }
        """)

        
        # =============================
        # 3. TABLA DETALLE IVA
        # =============================
        self.tabla_detalle = QTableWidget()
        self.tabla_detalle.setColumnCount(5)
        self.tabla_detalle.setHorizontalHeaderLabels([
            "Periodo",
            "IVA Débito",
            "IVA Crédito",
            "Ventas Netas",
            "Compras Netas"
        ])

        self.tabla_detalle.verticalHeader().setVisible(False)
        self.tabla_detalle.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_detalle.setSelectionMode(QTableWidget.SingleSelection)

        # Ajuste de texto y altura de filas
        self.tabla_detalle.setWordWrap(True)
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabla_detalle.resizeRowsToContents()
        

        splitter = QSplitter(Qt.Horizontal)

        splitter.addWidget(self.tabla)
        splitter.addWidget(self.tabla_detalle)

        # Tamaños iniciales (60% - 40%)
        splitter.setSizes([800, 400])

        layout.addWidget(splitter)

        # =============================
        # 4. BOTONES
        # =============================
        botones = QHBoxLayout()

        self.btn_nueva = DoubleClickButton("Nueva Evaluación")
        self.btn_ver = DoubleClickButton("Ver / Editar")
        self.btn_actualizar = QPushButton("Actualizar tabla")
        self.btn_eliminar = DoubleClickButton("Eliminar")

        botones.addWidget(self.btn_nueva)
        botones.addWidget(self.btn_ver)
        botones.addWidget(self.btn_actualizar)
        botones.addWidget(self.btn_eliminar)

        

        layout.addLayout(botones)

        self.btn_actualizar.clicked.connect(self.cargar_evaluaciones)

        # =============================
        # LOAD INICIAL
        # =============================

        self.btn_nueva.doubleClicked.connect(self.crear_evaluacion)
        self.btn_ver.doubleClicked.connect(self.ver_editar_evaluacion)
        self.btn_eliminar.doubleClicked.connect(self.eliminar_evaluacion)

        self.todo_evaluaciones = []
        self.cargar_evaluaciones()


    def cargar_evaluaciones(self):

        data = obtener_evaluaciones_arrendatario()

        self.todo_evaluaciones = data[:]   # ✅ lista completa base
        self.evaluaciones = data[:]   

        self.render_tabla()


    def render_tabla(self, evaluaciones=None):
        if evaluaciones is None:
            evaluaciones = self.evaluaciones  

        self.tabla.setRowCount(0)
        self._eval_ids = []
        self._eval_tipos = []

        for fila, ev in enumerate(evaluaciones):
            self.tabla.insertRow(fila)

            self.tabla.setItem(fila, 0, QTableWidgetItem(ev.get("rut", "")))
            self.tabla.setItem(fila, 1, QTableWidgetItem(ev.get("nombre", "")))
            self.tabla.setItem(fila, 2, QTableWidgetItem(ev.get("tipo", "")))
            self.tabla.setItem(fila, 3, QTableWidgetItem(str(ev.get("fecha") or "")))
            self.tabla.setItem(fila, 4, QTableWidgetItem(ev.get("resultado") or ""))
            self.tabla.setItem(fila, 5, QTableWidgetItem(str(ev.get("renta") or "0")))

            self._eval_ids.append(ev["id"])
            self._eval_tipos.append(ev["tipo"])

    def render_detalle(self, data):

        self.tabla_detalle.setDisabled(False)
        self.tabla_detalle.setRowCount(0)

        if not data:
            return

        keys = list(data[0].keys())

        self.tabla_detalle.setColumnCount(len(keys))
        self.tabla_detalle.setHorizontalHeaderLabels(keys)

        for fila, item in enumerate(data):

            self.tabla_detalle.insertRow(fila)

            for col, key in enumerate(keys):
                self.tabla_detalle.setItem(
                    fila,
                    col,
                    QTableWidgetItem(str(item.get(key, "")))
                )
        
    def _evaluacion_seleccionada(self):

        eval_id = self._eval_id_seleccionado()
        tipo = self._eval_tipo_seleccionado()

        if not eval_id:
            return

        detalle = obtener_detalle_evaluacion(tipo, eval_id)

        self.render_detalle(detalle)

    def mostrar_detalle(self, data):

        self.tabla_detalle.setRowCount(len(data))

        for fila, item in enumerate(data):

            self.tabla_detalle.setItem(
                fila, 0, QTableWidgetItem(str(item["periodo"]))
            )
            self.tabla_detalle.setItem(
                fila, 1, QTableWidgetItem(str(item["iva_debito"]))
            )
            self.tabla_detalle.setItem(
                fila, 2, QTableWidgetItem(str(item["iva_credito"]))
            )
            self.tabla_detalle.setItem(
                fila, 3, QTableWidgetItem(str(item["ventas"]))
            )
            self.tabla_detalle.setItem(
                fila, 4, QTableWidgetItem(str(item["compras"]))
            )



    def _eval_id_seleccionado(self):

        fila = self.tabla.currentRow()

        if fila < 0 or fila >= len(self._eval_ids):
            return None

        return self._eval_ids[fila]
    
    def _eval_tipo_seleccionado(self):

        fila = self.tabla.currentRow()

        if fila < 0 or fila >= len(self._eval_tipos):
            return None

        return self._eval_tipos[fila]

    def aplicar_filtros(self):
        texto = self.search_input.text().lower().strip()

        if not texto:
            self.evaluaciones = self.todo_evaluaciones[:]   # ✅ reset
            self.render_tabla()
            return

        datos = []
        for t in self.todo_evaluaciones:
            rut = (t.get("rut") or "").lower()
            nombre = (t.get("nombre") or "").lower()

            if texto in rut or texto in nombre:
                datos.append(t)

        self.evaluaciones = datos[:]       # ✅ mantiene estado
        self.render_tabla(datos)           # o self.render_tabla() 




    def _id_seleccionado(self) -> int | None:
        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self._eval_ids):
            return None
        return self._eval_ids[fila]


    def crear_evaluacion(self):
        dlg = FormularioEvaluacion(parent=self)

        if dlg.exec():
            self.cargar_evaluaciones()

    def ver_editar_evaluacion(self):

        eval_id = self._eval_id_seleccionado()

        if not eval_id:
            QMessageBox.warning(self, "Atención", "Seleccione una evaluación.")
            return

        dlg = FormularioEvaluacion(
            evaluacion_id=eval_id,
            parent=self
        )

        dlg.evaluacion_guardada.connect(self.cargar_evaluaciones)

        if dlg.exec():
            self.cargar_evaluaciones()

    def eliminar_evaluacion(self):
        ev_id = self._id_seleccionado()
        if not ev_id:
            QMessageBox.warning(self, "Atención", "Seleccione una evaluación.")
            return
        if QMessageBox.question(self, "Confirmar", "¿Eliminar la evaluación seleccionada?") == QMessageBox.Yes:
            eliminar_evaluacion(ev_id)   # 👈 ahora sí es el ID entero
            self.cargar_evaluaciones()




class FormularioArrendatario(QDialog):
    arrendatario_guardado = Signal()

    def __init__(self,arrendatario=None, parent=None):
        super().__init__(parent)
        self.arrendatario = arrendatario
        self.rentas_tributables = []

        self.setWindowTitle("Editar Arrendatario" if arrendatario else "Nuevo Arrendatario")
        self.resize(900, 700)
        self.detalle_arriendo = {}
        self.evaluacion_meses = {}

        # Layout principal con scroll
        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        scroll.setWidget(contenido)
        layout_principal.addWidget(scroll)
        
        # Layout del formulario
        layout_form = QVBoxLayout(contenido)
        
        # Pestañas para organizar el formulario
        self.tabs = QTabWidget()
        layout_form.addWidget(self.tabs)

        btn_guardar = DoubleClickButton("Guardar Arrendatario")
        btn_guardar.doubleClicked.connect(self.guardar_arrendatario)
        layout_form.addWidget(btn_guardar)

        tab_arrendatario = QWidget()
        self.tabs.addTab(tab_arrendatario , "Arrendatario")
        self.setup_tab_arrendatario(tab_arrendatario )


        if self.arrendatario:
            self.cargar_datos_arrendatario(self.arrendatario)


    def money(self, value):
            return f"{int(safe_numeric(value)):,}".replace(",", ".")

    def percent(self, value):
            return f"{safe_numeric(value) * 100:.1f}%"

    def safe_text(self, value):
            return "" if value in (None, "") else str(value)

            

    def setup_tab_arrendatario(self, tab):
        layout = QFormLayout(tab)
        
        # Campos del arrendatario
        self.txt_arrendatario_nombre = QLineEdit()
        self.txt_arrendatario_rut = QLineEdit()
        self.txt_arrendatario_direccion = QLineEdit()
        self.txt_arrendatario_telefono = QLineEdit()
        self.txt_arrendatario_email = QLineEdit()
        self.cmb_tipo_trabajador = QComboBox()
        self.cmb_tipo_trabajador.addItems(["Dependiente", "Independiente", "Otro"])
        self.txt_antiguedad_laboral = QLineEdit()
        self.cmb_dicom = QComboBox()
        self.cmb_dicom.addItems(["Sí","No"])
        self.txt_comentarios = QTextEdit()
        self.cmb_evaluacion_estado = QComboBox()
        self.cmb_evaluacion_estado.addItems(["Pendiente","Aprobado","Rechazado"])

        self.fecha_evaluacion = QDateEdit(QDate.currentDate())
        self.fecha_evaluacion.setCalendarPopup(True)

        self.txt_renta = QLineEdit()

     
        
        # Agregar campos

        layout.addRow(self.crear_label("Nombre:", True), self.txt_arrendatario_nombre)
        layout.addRow(self.crear_label("RUT:", True), self.txt_arrendatario_rut)
        layout.addRow(self.crear_label("Dirección:"), self.txt_arrendatario_direccion)
        layout.addRow(self.crear_label("Teléfono:"), self.txt_arrendatario_telefono)
        layout.addRow(self.crear_label("Email:"), self.txt_arrendatario_email)
        
        layout.addRow(self.crear_label("Tipo de Trabajador:"), self.cmb_tipo_trabajador)
        layout.addRow(self.crear_label("Antigüedad Laboral(Meses):"), self.txt_antiguedad_laboral)

        # --- Evaluación ---
        layout.addRow(self.crear_label("¿Tiene DICOM?"), self.cmb_dicom)
        layout.addRow(self.crear_label("Comentarios:"), self.txt_comentarios)
        layout.addRow(self.crear_label("Estado de Evaluación:"), self.cmb_evaluacion_estado)
        layout.addRow(self.crear_label("Renta Mensual:"), self.txt_renta)

    def cargar_datos_arrendatario(self, arrendatario):
        try:

            def set_text(widget, value):
                widget.setText(self.safe_text(value))

            def set_money(widget, value):
                widget.setText(self.money(value))

            def set_date(widget, value):
                if value:
                    widget.setDate(QDate.fromString(value, "yyyy-MM-dd"))
                else:
                    widget.setDate(QDate.currentDate())

            # ===============================
            # ARRENDATARIO
            # ===============================
            if isinstance(arrendatario, dict):
                set_text(self.txt_arrendatario_rut, arrendatario.get("rut"))
                set_text(self.txt_arrendatario_nombre, arrendatario.get("nombre"))
                set_text(self.txt_arrendatario_telefono, arrendatario.get("telefono"))
                set_text(self.txt_arrendatario_email, arrendatario.get("email"))
                set_text(self.txt_arrendatario_direccion, arrendatario.get("direccion"))

                self.cmb_tipo_trabajador.setCurrentText(
                    arrendatario.get("tipo_trabajador", "Dependiente")
                )

                set_text(self.txt_antiguedad_laboral, arrendatario.get("antiguedad_laboral"))
                self.cmb_dicom.setCurrentText(arrendatario.get("dicom", "Sí"))
                set_text(self.txt_comentarios, arrendatario.get("comentarios"))
                self.cmb_evaluacion_estado.setCurrentText(
                    arrendatario.get("evaluacion_estado", "Pendiente")
                )
                set_money(self.txt_renta, arrendatario.get("renta"))

                self.datos = None



        except Exception as e:
            print(f"Error al cargar el arriendo: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudieron cargar los datos del arrendatario:\n{e}"
            )




    
    def crear_label(self, texto, obligatorio=False):
        label = QLabel(texto)
        if obligatorio:
            label.setProperty("obligatorio", "true")
        return label
    
    def get_int(self, value):
        if not value:  # None o cadena vacía
            return 0
        # eliminar puntos y comas si hay separadores de miles
        value = value.replace(".", "").replace(",", "")
        try:
            return int(value)
        except ValueError:
            return 0

        
    def guardar_arrendatario(self):
        try:
            rut = self.txt_arrendatario_rut.text().strip()

            if not rut or not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", rut):
                QMessageBox.warning(self, "Error", "Ingrese un RUT válido (formato 12.345.678-9).")
                return
            self.datos = {
                'rut': self.txt_arrendatario_rut.text(),
                'nombre': self.txt_arrendatario_nombre.text(),
                'telefono': self.txt_arrendatario_telefono.text(),
                'email': self.txt_arrendatario_email.text(),
                'direccion': self.txt_arrendatario_direccion.text(),
                'tipo_trabajador': self.cmb_tipo_trabajador.currentText(),
                'dicom': self.cmb_dicom.currentText(),
                'comentarios': self.txt_comentarios.toPlainText(),
                'evaluacion_estado': self.cmb_evaluacion_estado.currentText(),
                'antiguedad_laboral': self.get_int(self.txt_antiguedad_laboral.text()),
                'renta': self.get_int(self.txt_renta.text())
            }



            if rut:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"El arrendatario se ha guardado correctamente.\n\nID: {rut}"
                )
                self.arrendatario_guardado.emit()
                self.accept()
               

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el arriendo: {str(e)}")


class FormularioEvaluacion(QDialog):
    evaluacion_guardada = Signal()
    def __init__(self,evaluacion_id=None, parent=None):
        super().__init__(parent)


        self.rentas_tributables = []
        self.evaluacion_meses = {}
        self.evaluacion_id = evaluacion_id

        # Layout principal con scroll
        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.resize(900, 700)
        contenido = QWidget()
        scroll.setWidget(contenido)
        layout_principal.addWidget(scroll)
        
        # Layout del formulario
        layout_form = QVBoxLayout(contenido)

        
        self.combo_arrendatario = QComboBox()
        layout_form.addWidget(self.combo_arrendatario)

        self.combo_arrendatario.currentIndexChanged.connect(
            self.arrendatario_seleccionado
        )
        
        # Pestañas para organizar el formulario
        self.tabs = QTabWidget()
        layout_form.addWidget(self.tabs)

        tab_evaluacion = QWidget()
        self.tabs.addTab(tab_evaluacion, "Evaluación")
        self.setup_tab_evaluacion(tab_evaluacion)
        self.setup_tab_evaluacion_index = self.tabs.indexOf(tab_evaluacion)

        tab_evaluacion_independiente = QWidget()
        self.tabs.addTab(tab_evaluacion_independiente, "Evaluación")
        self.setup_tab_evaluacion_independiente(tab_evaluacion_independiente)
        self.setup_tab_evaluacion_independiente_index = self.tabs.indexOf(tab_evaluacion_independiente )

        self.combo_arrendatario.currentIndexChanged.connect(
            self.arrendatario_seleccionado
        )

        self.txt_monto_arriendo = QLineEdit()
        self.txt_monto_arriendo.setPlaceholderText("Monto arriendo objetivo (ej: 400000)")

        self.txt_veces_renta = QLineEdit()
        self.txt_veces_renta.setReadOnly(True)

        self.txt_renta_minima = QLineEdit()
        self.txt_renta_minima.setReadOnly(True)

        self.lbl_regla = QLabel("")
        self.lbl_regla.setStyleSheet("font-weight: bold;")

        frm = QFormLayout()
        frm.addRow("Monto arriendo objetivo:", self.txt_monto_arriendo)
        frm.addRow("Veces renta:", self.txt_veces_renta)
        frm.addRow("Renta mínima (arriendo x3):", self.txt_renta_minima)
        frm.addRow("Estado regla 3x:", self.lbl_regla)
        layout_form.addLayout(frm)

        # Recalcular al escribir
        self.txt_monto_arriendo.textChanged.connect(self.recalcular_regla_3x)

        btn_guardar = DoubleClickButton("Guardar Evaluación")
        btn_guardar.doubleClicked.connect(self.guardar_evaluacion)
        layout_form.addWidget(btn_guardar)

        self.cargar_arrendatarios()

        if self.evaluacion_id:
            self.cargar_evaluacion()

    def _obtener_renta_calculada_actual(self) -> float:
        arr = self.combo_arrendatario.currentData()
        if not arr:
            return 0.0

        tipo = arr.get("tipo_trabajador")

        if tipo == "Dependiente":
            valores = self.obtener_diccionario_evaluacion()
            # líquida a pago de la evaluación dependiente
            return float(self.get_int(valores.get("liquido_pago", 0)))

        if tipo == "Independiente":
            ev = self.obtener_diccionario_evaluacion_independiente()
            return float(self.get_int(ev["resumen"].get("renta_mensual_estimada", 0)))

        return 0.0

    def recalcular_regla_3x(self):
        renta = self.parse_num(self._obtener_renta_calculada_actual())
        arriendo = self.parse_num(self.txt_monto_arriendo.text())

        # si arriendo inválido, corta antes (evita división por 0)
        if arriendo <= 0:
            self.txt_veces_renta.setText("")
            self.txt_renta_minima.setText("")
            self.lbl_regla.setText("⚠️ Ingrese un monto de arriendo válido (>0).")
            self.lbl_regla.setStyleSheet("font-weight:bold; color:#B02A37;")
            return

        res = regla_3x_renta(renta, arriendo, minimo=3.0)

        self.txt_veces_renta.setText(f"{res['veces_renta']:.2f}")
        self.txt_renta_minima.setText(f"{res['renta_minima']:,.0f}")

        if res["califica"]:
            self.lbl_regla.setText("✅ Califica (>= 3x renta).")
            self.lbl_regla.setStyleSheet("font-weight:bold; color:#1E7E34;")
        else:
            self.lbl_regla.setText("❌ No califica (< 3x renta).")
            self.lbl_regla.setStyleSheet("font-weight:bold; color:#B02A37;")


    def arrendatario_seleccionado(self):

        arr = self.combo_arrendatario.currentData()

        if not arr:
            return

        tipo = arr["tipo_trabajador"]
        renta = arr["renta"]
        dicom = arr["dicom"]

        # 🔥 activar tab correcto
        self.toggle_evaluacion_tab(tipo)
        self.toggle_evaluacion_independiente_tab(tipo)
        self.recalcular_regla_3x()

    def cargar_arrendatarios(self):
        arrendatarios = obtener_arrendatarios()

        self.combo_arrendatario.clear()

        for arr in arrendatarios:
            self.combo_arrendatario.addItem(
                f"{arr['nombre']} - {arr['rut']}",
                arr  # 👈 guardamos TODO el diccionario
            )

    def crear_label(self, texto, obligatorio=False):
        label = QLabel(texto)
        if obligatorio:
            label.setProperty("obligatorio", "true")
        return label
    
    def setup_tab_evaluacion(self, tab):
        layout = QFormLayout(tab)

        # Contenedor para centrar la tabla
        contenedor = QWidget()
        contenedor_layout = QVBoxLayout(contenedor)
        contenedor_layout.setAlignment(Qt.AlignCenter)

        # Crear tabla

        self.fecha_evaluacion_arrendatario = QDateEdit(QDate.currentDate())
        self.fecha_evaluacion_arrendatario.setCalendarPopup(True)

        layout.addRow(self.crear_label("Fecha Evaluación:"), self.fecha_evaluacion_arrendatario)

        self.txt_impuesto_renta = QLineEdit()
        layout.addRow(self.crear_label("Impuesto Renta"), self.txt_impuesto_renta)

        self.btn_calcular_impuesto = DoubleClickButton("Calcular Impuesto Renta")
        self.btn_calcular_impuesto.doubleClicked.connect(self.abrir_dialogo_impuesto)
        layout.addRow(self.btn_calcular_impuesto)

        self.tbl_evaluacion = QTableWidget()
        self.tbl_evaluacion.setRowCount(10)
        self.tbl_evaluacion.setColumnCount(5)

        # Tamaño mínimo más grande
        self.tbl_evaluacion.setMinimumWidth(700)
        self.tbl_evaluacion.setMinimumHeight(300)
        self.tbl_evaluacion.resizeColumnsToContents()

        # Encabezados
        self.tbl_evaluacion.setHorizontalHeaderLabels([
            "Concepto", "Mes 1", "Mes 2", "Mes 3", "Resultado"
        ])

        # Centrar texto de encabezados
        header = self.tbl_evaluacion.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)

        conceptos = [
            "Sueldo Base (SB)",
            "Gratificación (GT)",
            "TH Imponibles (THIMP)",
            "Locomoción / Movilización (LOCMOV)",
            "TH No Imponibles (THNI)",
            "Total Haberes",
            "Descuentos Legales",
            "Descuentos Varios",
            "Anticipos",
            "Líquido a Pago"
        ]

        # Llenar columna de conceptos
        for i, concepto in enumerate(conceptos):
            item = QTableWidgetItem(concepto)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.tbl_evaluacion.setItem(i, 0, item)

        # Ajustar automáticamente tamaños de columnas
        self.tbl_evaluacion.resizeColumnsToContents()
        header = self.tbl_evaluacion.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        

        # Añadir tabla al contenedor centrado
        contenedor_layout.addWidget(self.tbl_evaluacion)

        botones_layout = QHBoxLayout()
        botones_layout.setAlignment(Qt.AlignCenter)

        self.btn_mes1 = DoubleClickButton("Ingresar Mes 1")
        self.btn_mes2 = DoubleClickButton("Ingresar Mes 2")
        self.btn_mes3 = DoubleClickButton("Ingresar Mes 3")

        self.btn_mes1.doubleClicked.connect(lambda: self.abrir_formulario_mes(1))
        self.btn_mes2.doubleClicked.connect(lambda: self.abrir_formulario_mes(2))
        self.btn_mes3.doubleClicked.connect(lambda: self.abrir_formulario_mes(3))

        botones_layout.addWidget(self.btn_mes1)
        botones_layout.addWidget(self.btn_mes2)
        botones_layout.addWidget(self.btn_mes3)

        contenedor_layout.addLayout(botones_layout)

        # Agregar contenedor al layout final
        layout.addRow(contenedor)


    

    def setup_tab_evaluacion_independiente(self, tab):
        layout = QVBoxLayout(tab)

        # --- Tabla mensual ---
        self.tbl_independiente = QTableWidget()
        self.tbl_independiente.setRowCount(12)
        self.tbl_independiente.setColumnCount(6)

        headers = [
            "Mes",
            "IVA Débito (538)",
            "IVA Crédito (537)",
            "Ventas Netas Est.",
            "Compras Netas Est.",
            "Excedente Mes"
        ]
        self.tbl_independiente.setHorizontalHeaderLabels(headers)

        # 🔹 Headers centrados y en negrita
        header = self.tbl_independiente.horizontalHeader()
        font = QFont()
        font.setBold(True)
        header.setFont(font)

        for i in range(self.tbl_independiente.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        header.setDefaultAlignment(Qt.AlignCenter)

        # 🔹 Estética general
        self.tbl_independiente.verticalHeader().setVisible(False)
        self.tbl_independiente.setAlternatingRowColors(True)
        self.tbl_independiente.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)

        self.tbl_independiente.setSelectionBehavior(QTableWidget.SelectRows)

        # 🔹 Centrar TODAS las celdas
        for row in range(12):
            for col in range(6):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)
                self.tbl_independiente.setItem(row, col, item)

        layout.addWidget(self.tbl_independiente)

                # --- Acciones ---
        acciones_frame = QFrame()
        acciones_frame.setFrameShape(QFrame.StyledPanel)
     
        acciones_layout = QHBoxLayout(acciones_frame)
        acciones_layout.setAlignment(Qt.AlignRight)

        btn_excel = DoubleClickButton("📄 Generar Excel")
        btn_excel.setFixedHeight(36)
        btn_excel.setCursor(Qt.PointingHandCursor)

        btn_excel.doubleClicked.connect(self.obtener_ruta_excel)

        acciones_layout.addWidget(btn_excel)
        layout.addWidget(acciones_frame)



        # --- Resumen ---
        resumen_layout = QHBoxLayout()

        self.lbl_ventas = QLabel("Ventas Anuales: $0")
        self.lbl_compras = QLabel("Compras Anuales: $0")
        self.lbl_excedente = QLabel("Excedente Anual: $0")
        self.lbl_renta = QLabel("Renta Mensual Estimada: $0")

        for lbl in (
            self.lbl_ventas,
            self.lbl_compras,
            self.lbl_excedente,
            self.lbl_renta
        ):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-weight: bold;")
            resumen_layout.addWidget(lbl)

        layout.addLayout(resumen_layout)

        self.configurar_edicion_tabla_independiente()

        self.tbl_independiente.itemChanged.connect(
                self.recalcular_evaluacion_independiente
            )
        
        self.cargar_meses_independiente()


    
    def configurar_edicion_tabla_independiente(self):
        for row in range(12):
            for col in range(6):
                item = self.tbl_independiente.item(row, col)
                flags = item.flags()

                if col in (1, 2):  # IVA Débito y Crédito
                    item.setFlags(flags | Qt.ItemIsEditable)
                else:
                    item.setFlags(flags & ~Qt.ItemIsEditable)


    def toggle_evaluacion_tab(self, tipo_trabajador):
        if not hasattr(self,'setup_tab_evaluacion_index'):
            return
        mostrar = tipo_trabajador == "Dependiente"
        self.tabs.setTabVisible(self.setup_tab_evaluacion_index, mostrar)

    def toggle_evaluacion_independiente_tab(self, tipo_trabajador):
        if not hasattr(self, 'setup_tab_evaluacion_independiente_index'):
            return
        mostrar = tipo_trabajador == "Independiente"
        self.tabs.setTabVisible(self.setup_tab_evaluacion_independiente_index, mostrar)
                


    def parse_num(self, texto) -> float:
        if texto is None:
            return 0.0
        if isinstance(texto, (int, float)):
            return float(texto)

        s = str(texto).strip()
        if not s:
            return 0.0

        s = s.replace("$", "").replace(" ", "")
        s = re.sub(r"[^\d\.,\-]", "", s)

        if not s:
            return 0.0

        # ambos separadores => decidir decimal por el último
        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                # 30.000,50
                s = s.replace(".", "").replace(",", ".")
            else:
                # 30,000.50
                s = s.replace(",", "")
        else:
            # solo coma
            if "," in s:
                parts = s.split(",")
                if len(parts[-1]) == 3:  # 30,000 miles
                    s = s.replace(",", "")
                else:  # 30,5 decimal
                    s = s.replace(",", ".")
            # solo punto
            elif "." in s:
                parts = s.split(".")
                if len(parts[-1]) == 3:  # 30.000 miles
                    s = s.replace(".", "")

        try:
            return float(s)
        except ValueError:
            return 0.0


    def recalcular_evaluacion_independiente(self, item):
        if item.column() not in (1, 2):
            return

        meses = []

        for row in range(12):
            txt_deb = self.tbl_independiente.item(row, 1).text() if self.tbl_independiente.item(row, 1) else ""
            txt_cre = self.tbl_independiente.item(row, 2).text() if self.tbl_independiente.item(row, 2) else ""

            iva_debito = self.parse_num(txt_deb)
            iva_credito = self.parse_num(txt_cre)

            meses.append({
                "iva_debito": iva_debito,
                "iva_credito": iva_credito
            })

        resultado = calcular_evaluacion_independiente(meses)

        self.actualizar_tabla_independiente(resultado)
        self.actualizar_resumen_independiente(resultado)
        self.recalcular_regla_3x()

    def actualizar_tabla_independiente(self, resultado):
        self.tbl_independiente.blockSignals(True)

        for row, detalle in enumerate(resultado["detalle"]):
            self.tbl_independiente.item(row, 3).setText(
                f"{detalle['ventas']:,.0f}"
            )
            self.tbl_independiente.item(row, 4).setText(
                f"{detalle['compras']:,.0f}"
            )
            self.tbl_independiente.item(row, 5).setText(
                f"{detalle['excedente']:,.0f}"
            )

        self.tbl_independiente.blockSignals(False)



    def cargar_meses_independiente(self):
        # Mes actual
        hoy = QDate.currentDate()

        primer_dia_mes_actual = QDate(hoy.year(), hoy.month(), 1)
        primer_dia_mes_anterior = primer_dia_mes_actual.addMonths(-1)
        inicio = primer_dia_mes_anterior.addMonths(-11)

        self.tbl_independiente.blockSignals(True)
        try:
            for row in range(12):
                periodo = inicio.addMonths(row)  # QDate

                # Texto visible (puedes cambiar el formato)
                texto = periodo.toString("MMM yyyy")  # ej: "Mar 2026" (depende locale)
                # Alternativa más clara:
                # texto = periodo.toString("yyyy-MM")

                item_mes = QTableWidgetItem(texto)
                item_mes.setFlags(item_mes.flags() & ~Qt.ItemIsEditable)
                item_mes.setTextAlignment(Qt.AlignCenter)

                # ✅ Guardamos el periodo real para usarlo después (clave del arreglo)
                item_mes.setData(Qt.UserRole, periodo.toString("yyyy-MM-dd"))

                self.tbl_independiente.setItem(row, 0, item_mes)

        finally:
            self.tbl_independiente.blockSignals(False)


    def actualizar_resumen_independiente(self, resultado):
        self.lbl_ventas.setText(
            f"Ventas Anuales: ${resultado['ventas_anuales']:,.0f}"
        )
        self.lbl_compras.setText(
            f"Compras Anuales: ${resultado['compras_anuales']:,.0f}"
        )
        self.lbl_excedente.setText(
            f"Excedente Anual: ${resultado['excedente_anual']:,.0f}"
        )
        self.lbl_renta.setText(
            f"Renta Mensual Estimada: ${resultado['renta_mensual']:,.0f}"
        )


    def abrir_formulario_mes(self, mes):
        arr = self.combo_arrendatario.currentData()

        dlg = FormularioMes(mes, self, rut_arrendatario=arr["rut"] )

        if dlg.exec():
            resultado = dlg.resultado_final   # ← ya trae todo

            datos = resultado["datos"]
            calculos = resultado["calculos"]

            # Guardas lo que quieras
            self.evaluacion_meses[mes] = datos

            # Rellenas la tabla usando los cálculos
            resultados_completos = {**datos, **calculos}

            self.actualizar_tabla_evaluacion(mes, resultados_completos)

    def calcular_resultados_evaluacion(self):
        """
        Recorre la tabla de evaluación y calcula la columna Resultado.
        Si los valores de Mes1, Mes2 y Mes3 son iguales → usa ese valor.
        Si hay cambios → calcula el promedio.
        """
        COL_M1 = 1
        COL_M2 = 2
        COL_M3 = 3
        COL_RES = 4

        for fila in range(self.tbl_evaluacion.rowCount()):

            valores = []

            # Obtener los valores de cada mes
            for col in (COL_M1, COL_M2, COL_M3):
                item = self.tbl_evaluacion.item(fila, col)

                if item and item.text().strip():
                    texto = item.text().replace(".", "").replace(",", "")
                    try:
                        valor = float(texto)
                    except:
                        valor = 0
                else:
                    valor = 0

                valores.append(valor)

            v1, v2, v3 = valores

            # --- LÓGICA DE PROMEDIO O IGUALDAD ---
            if v1 == v2 == v3:
                resultado = v1
            else:
                resultado = sum(valores) / 3

            # Crear item resultado
            item_res = QTableWidgetItem(f"{resultado:,.0f}")
            item_res.setTextAlignment(Qt.AlignCenter)
            item_res.setFlags(item_res.flags() ^ Qt.ItemIsEditable)

            self.tbl_evaluacion.setItem(fila, COL_RES, item_res)
            self.recalcular_regla_3x()


    def actualizar_tabla_evaluacion(self, mes, resultados):
        col = mes  

        # print("CALCULOS MES:", resultados)

        mapping = [
            ("sueldo_base", 0),
            ("gratificacion", 1),
            ("th_imponibles", 2),
            ("locomocion", 3),
            ("th_no_imponibles", 4),
            ("total_haberes",5),
            ("descuentos_legales", 6),
            ("descuentos_varios", 7),
            ("anticipo", 8),
            ("liquido", 9)
        ]

        for clave, fila in mapping:
            valor = resultados.get(clave, 0)
            item = QTableWidgetItem(f"{valor:,.0f}")
            item.setTextAlignment(Qt.AlignCenter)
            self.tbl_evaluacion.setItem(fila, col, item)

        self.calcular_resultados_evaluacion()

    
    def obtener_diccionario_evaluacion(self):
        col = 4  # columna Resultado

        mapping = [
            "sueldo_base",
            "gratificacion",
            "total_imponible",
            "locomocion",
            "total_no_imponible",
            "total_haberes",
            "descuentos_legales",
            "desc_varios",
            "anticipo",
            "liquido_pago",
        ]

        datos = {}

        for fila, clave in enumerate(mapping):
            item = self.tbl_evaluacion.item(fila, col)

            if item and item.text().strip():
                texto = item.text().replace(".", "").replace(",", "").strip()
                valor = float(texto) if texto else 0.0
            else:
                valor = 0.0

            datos[clave] = valor

        return datos
    

    def abrir_dialogo_impuesto(self):
        datos_eval = self.obtener_diccionario_evaluacion()
        renta_tributable = datos_eval.get("total_imponible", 0.0)


        dialog = ImpuestoRentaDialog(renta_tributable, self)

        if dialog.exec():
            self.txt_impuesto_renta.setText(str(dialog.resultado))


    def _calcular_resultado_evaluacion(self) -> tuple[str, dict]:
        """
        Retorna: (resultado, res_regla)
        - resultado: 'Aprobado' | 'Rechazado' | 'Pendiente'
        - res_regla: dict con veces_renta, renta_minima, califica
        """
        arriendo = self.get_int(self.txt_monto_arriendo.text())
        renta = self._obtener_renta_calculada_actual()

        # si no hay datos suficientes, queda pendiente
        if arriendo <= 0 or renta <= 0:
            return "Pendiente", {"veces_renta": 0.0, "renta_minima": 0.0, "califica": False}

        res = regla_3x_renta(renta, arriendo, minimo=3.0)
        resultado = "Aprobado" if res["califica"] else "Rechazado"
        return resultado, res

    def cargar_resultado_final_evaluacion(self, eva):
        """
        evaluacion: dict que viene desde la BD
        Solo setea la columna Resultado (4).
        """

        mapping = {
            0: eva.get("sueldo_base"),
            1: eva.get("gratificacion"),
            2: eva.get("total_imponible"),
            3: eva.get("locomocion"),
            4: eva.get("total_no_imponible"),
            5: eva.get("total_haberes"),
            6: eva.get("descuentos_legales"),
            7: eva.get("desc_varios"),
            8: eva.get("anticipo"),
            9: eva.get("liquido_pago"),
        }

        for fila, valor in mapping.items():
            if valor is None:
                continue

            item = QTableWidgetItem(f"{valor:,.0f}")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsEnabled)  # solo lectura
            self.tbl_evaluacion.setItem(fila, 4, item)

    def get_int(self, value):
        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        texto = str(value).strip()
        if not texto:
            return 0.0

        # eliminar símbolos
        texto = texto.replace("$", "").replace("%", "")

        # normalizar separadores
        # miles: .  → eliminar
        # decimales: , → .
        texto = texto.replace(".", "").replace(",", ".")

        try:
            return float(texto)
        except ValueError:
            return 0.0

    def obtener_diccionario_evaluacion_independiente(self):
        detalle = []
        total_ventas = 0.0
        total_compras = 0.0

        for row in range(12):
            # ✅ obtener periodo desde la col 0
            item_periodo = self.tbl_independiente.item(row, 0)
            periodo = None
            if item_periodo:
                periodo = item_periodo.data(Qt.UserRole)  # "yyyy-MM-dd"

            if not periodo:
                # fallback por si no estuviera seteado (no debería)
                # usa el texto visible si está en yyyy-MM
                periodo = f"{QDate.currentDate().year()}-{row+1:02d}-01"

            try:
                iva_debito = float((self.tbl_independiente.item(row, 1).text() or "0").replace(".", "").replace(",", "."))
                iva_credito = float((self.tbl_independiente.item(row, 2).text() or "0").replace(".", "").replace(",", "."))
            except (ValueError, AttributeError):
                iva_debito = 0.0
                iva_credito = 0.0

            ventas = iva_debito / IVA_FACTOR
            compras = iva_credito / IVA_FACTOR

            detalle.append({
                'periodo': periodo,
                'iva_debito': iva_debito,
                'iva_credito': iva_credito,
                'ventas_netas_estimadas': ventas,
                'compras_netas_estimadas': compras
            })

            total_ventas += ventas
            total_compras += compras

        excedente = total_ventas - total_compras
        renta_anual = excedente * CASTIGO_DEFAULT
        renta_mensual = renta_anual / 12

        # periodo_desde: primer periodo visible
        periodo_desde = detalle[0]['periodo'] if detalle else QDate.currentDate().toString("yyyy-MM-dd")

        return {
            'periodo_desde': periodo_desde,
            'resumen': {
                'ventas_anuales': total_ventas,
                'compras_anuales': total_compras,
                'excedente_anual': excedente,
                'renta_anual_estimada': renta_anual,
                'renta_mensual_estimada': renta_mensual
            },
            'detalle': detalle
        }
    
    
    from PySide6.QtWidgets import QFileDialog

    def obtener_ruta_excel(self):

        rut_arrendatario = self.combo_arrendatario.currentData()

        rut = rut_arrendatario.strip().replace(".", "").replace("-", "")
        nombre_archivo = f"evaluacion_independiente_{rut}.xlsx"

        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar evaluación",
            nombre_archivo,
            "Excel (*.xlsx)"
        )

        if not ruta_archivo:
            return  # usuario canceló

        if not ruta_archivo.lower().endswith(".xlsx"):
            ruta_archivo += ".xlsx"

        # 👉 generar el excel
        self.generar_excel_evaluacion_independiente(ruta_archivo)


    def generar_excel_evaluacion_independiente(self, ruta_archivo):
        datos = self.obtener_diccionario_evaluacion_independiente()

        wb = Workbook()
        ws = wb.active
        ws.title = "Evaluación Independiente"

        # -----------------------------
        # ESTILOS
        # -----------------------------
        bold = Font(bold=True)

        thin = Side(style="thin")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        formato_contable = '"$"#,##0;("$"#,##0)'

        # -----------------------------
        # TITULO
        # -----------------------------
        ws["A1"] = "EVALUACIÓN TRABAJADOR INDEPENDIENTE"
        ws["A1"].font = bold
        ws.append([])

        # -----------------------------
        # TABLA MENSUAL
        # -----------------------------
        headers = [
            "Mes",
            "IVA Débito",
            "IVA Crédito",
            "Ventas Netas Estimadas",
            "Compras Netas Estimadas",
            "Excedente"
        ]

        ws.append(headers)
        header_row = ws.max_row

        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=header_row, column=col)
            cell.font = bold
            cell.border = border

        inicio_tabla = header_row + 1

        for detalle in datos["detalle"]:
            excedente = (
                detalle["ventas_netas_estimadas"]
                - detalle["compras_netas_estimadas"]
            )

            ws.append([
                detalle["periodo"][:7],
                detalle["iva_debito"],
                detalle["iva_credito"],
                detalle["ventas_netas_estimadas"],
                detalle["compras_netas_estimadas"],
                excedente
            ])

        fin_tabla = ws.max_row

        # Aplicar bordes y formato contable
        for row in range(inicio_tabla, fin_tabla + 1):
            for col in range(1, 7):
                cell = ws.cell(row=row, column=col)
                cell.border = border

                if col >= 2:  # columnas monetarias
                    cell.number_format = formato_contable

        # -----------------------------
        # RESUMEN ANUAL
        # -----------------------------
        ws.append([])
        ws.append(["RESUMEN ANUAL"])
        ws["A" + str(ws.max_row)].font = bold

        resumen = datos["resumen"]

        resumen_filas = [
            ("Ventas Anuales", resumen["ventas_anuales"]),
            ("Compras Anuales", resumen["compras_anuales"]),
            ("Excedente Anual", resumen["excedente_anual"]),
            ("Factor Castigo", f"{CASTIGO_DEFAULT * 100:.0f}%"),
            ("Renta Anual Estimada", resumen["renta_anual_estimada"]),
            ("Renta Mensual Estimada", resumen["renta_mensual_estimada"]),
        ]

        for etiqueta, valor in resumen_filas:
            ws.append([etiqueta, valor])
            fila = ws.max_row
            ws.cell(row=fila, column=1).font = bold

            if isinstance(valor, (int, float)):
                ws.cell(row=fila, column=2).number_format = formato_contable

        # -----------------------------
        # METODOLOGÍA
        # -----------------------------
        ws.append([])
        ws.append(["METODOLOGÍA DE CÁLCULO"])
        ws["A" + str(ws.max_row)].font = bold

        metodologia = [
            "IVA Débito: IVA declarado por ventas del período.",
            "IVA Crédito: IVA declarado por compras o gastos del período.",
            "Ventas Netas Estimadas = IVA Débito / 0,19.",
            "Compras Netas Estimadas = IVA Crédito / 0,19.",
            "Excedente Mensual = Ventas Netas - Compras Netas.",
            f"Renta Anual Estimada = Excedente Anual x Factor Castigo ({CASTIGO_DEFAULT}).",
            "Renta Mensual Estimada = Renta Anual / 12.",
            f"Fecha de evaluación: {date.today().isoformat()}",
        ]

        for linea in metodologia:
            ws.append([linea])

        # -----------------------------
        # AJUSTE DE ANCHO
        # -----------------------------
        ws.column_dimensions["A"].width = 22
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 18
        ws.column_dimensions["D"].width = 24
        ws.column_dimensions["E"].width = 26
        ws.column_dimensions["F"].width = 18

        wb.save(ruta_archivo)

    def get_porcentaje(self, value):
        if not value or value.strip() == "":
            return 0.0
        try:
            limpio = value.replace('%', '').replace(',', '.').strip()
            return float(limpio) / 100
        except:
            return 0.0
        

    def cargar_evaluacion(self):

        data = obtener_evaluacion_completa(self.evaluacion_id)

        if not data:
            QMessageBox.warning(self, "Error", "No se pudo cargar la evaluación.")
            self.close()
            return

        arr_rut = data["arrendatario"]["rut"]
        tipo = data["arrendatario"]["tipo_trabajador"]

        # 🔹 Seleccionar arrendatario en combo
        
        for i in range(self.combo_arrendatario.count()):
            arr = self.combo_arrendatario.itemData(i)
            if arr["rut"] == arr_rut:
                self.combo_arrendatario.setCurrentIndex(i)
                break

        # 🔹 Bloquear cambio
        self.combo_arrendatario.setDisabled(True)

        # 🔹 Activar tab correcto
        self.toggle_evaluacion_tab(tipo)
        self.toggle_evaluacion_independiente_tab(tipo)


        eva_madre = data.get("evaluacion", data)  # por si vienen en root

        monto = eva_madre.get("monto_arriendo_objetivo", 0) or 0
        veces = eva_madre.get("veces_renta", 0) or 0
        renta_min = eva_madre.get("renta_minima", 0) or 0

        # si son QLineEdit:
        self.txt_monto_arriendo.setText(f"{monto:,.0f}")

        # si son QLabel (o QLineEdit igual sirve):
        self.txt_veces_renta.setText(f"{veces:,.2f}")
        self.txt_renta_minima.setText(f"{renta_min:,.0f}")

        # =========================
        # DEPENDIENTE
        # =========================
        if tipo == "Dependiente":

            eva = data["evaluacion_arrendatario"]

            self.fecha_evaluacion_arrendatario.setDate(
                QDate.fromString(eva["fecha_evaluacion"], "yyyy-MM-dd")
            )

            self.txt_impuesto_renta.setText(
                f"{eva.get('im_renta', 0):,.0f}"
            )

            self.cargar_resultado_final_evaluacion(eva)

        # =========================
        # INDEPENDIENTE
        # =========================
        if tipo == "Independiente":

            detalle = data["evaluacion_independiente_detalle"]

            self.tbl_independiente.blockSignals(True)

            for row, mes in enumerate(detalle):

                self.tbl_independiente.item(row, 1).setText(
                    f"{mes['iva_debito']:,.0f}"
                )

                self.tbl_independiente.item(row, 2).setText(
                    f"{mes['iva_credito']:,.0f}"
                )

            self.tbl_independiente.blockSignals(False)

            # recalcular para actualizar resumen
            self.recalcular_evaluacion_independiente(
                self.tbl_independiente.item(0, 1)
            )

        self.recalcular_regla_3x()

    
    def guardar_evaluacion(self):
        try:
            valores_tabla = {}

            # 1) Validar arrendatario seleccionado
            arr = self.combo_arrendatario.currentData()
            if not arr:
                QMessageBox.warning(self, "Error", "Debe seleccionar un arrendatario.")
                return

            tipo = arr["tipo_trabajador"]
            rut = arr["rut"]

            # 2) Construir dict base (UNA SOLA VEZ)
            data_evaluacion = {
                "arrendatario": {
                    "rut": rut,
                    "tipo_trabajador": tipo
                }
            }

            # 3) Calcular renta + regla 3x (ahora sí, con data_evaluacion ya creado)
            arriendo = self.get_int(self.txt_monto_arriendo.text())
            renta = self._obtener_renta_calculada_actual()
            res = regla_3x_renta(renta, arriendo, minimo=3.0)
            resultado, res = self._calcular_resultado_evaluacion()

            # Guardar extras en el dict principal
            data_evaluacion["resultado"] = resultado
            data_evaluacion["monto_arriendo_objetivo"] = arriendo
            data_evaluacion["veces_renta"] = res["veces_renta"]
            data_evaluacion["renta_minima"] = res["renta_minima"]
            data_evaluacion["resultado"] = "Aprobado" if res["califica"] else "Rechazado"

            # 4) Construir payload según tipo
            if tipo == "Dependiente":
                valores_tabla = self.obtener_diccionario_evaluacion()

                data_evaluacion["evaluacion_arrendatario"] = {
                    "fecha_evaluacion": self.fecha_evaluacion_arrendatario.date().toString("yyyy-MM-dd"),
                    "sueldo_base": self.get_int(valores_tabla.get("sueldo_base", 0)),
                    "gratificacion": self.get_int(valores_tabla.get("gratificacion", 0)),
                    "total_imponible": self.get_int(valores_tabla.get("total_imponible", 0)),
                    "total_no_imponible": self.get_int(valores_tabla.get("total_no_imponible", 0)),
                    "descuentos_legales": self.get_int(valores_tabla.get("descuentos_legales", 0)),
                    "liquido_pago": self.get_int(valores_tabla.get("liquido_pago", 0)),
                    "anticipo": self.get_int(valores_tabla.get("anticipo", 0)),
                    "total_haberes": self.get_int(valores_tabla.get("total_haberes", 0)),
                    "desc_varios": self.get_int(valores_tabla.get("desc_varios", 0)),
                    "locomocion": self.get_int(valores_tabla.get("locomocion", 0)),
                    "im_renta": self.get_int(self.txt_impuesto_renta.text()),
                }

            elif tipo == "Independiente":
                evaluacion = self.obtener_diccionario_evaluacion_independiente()

                data_evaluacion["evaluacion_independiente"] = {
                    "periodo_desde": date.today().isoformat(),
                    "factor_castigo": CASTIGO_DEFAULT,
                    **evaluacion["resumen"],  # NO cambia tus claves
                }

                data_evaluacion["evaluacion_independiente_detalle"] = evaluacion["detalle"]

            else:
                QMessageBox.warning(self, "Error", "Tipo de trabajador no válido.")
                return

            # 5) Guardar / Editar
            if self.evaluacion_id:
                ok = editar_evaluacion(self.evaluacion_id, data_evaluacion)
                if ok:
                    QMessageBox.information(self, "Actualizado", "La evaluación se actualizó correctamente.")
                    self.evaluacion_guardada.emit()
                    self.accept()
            else:
                eval_id = guardar_evaluacion(data_evaluacion)
                if eval_id:
                    QMessageBox.information(self, "Éxito", f"Evaluación creada correctamente.\n\nID: {eval_id}")
                    self.evaluacion_guardada.emit()
                    self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la evaluación: {str(e)}")

        

        

class FormularioMes(QDialog):
    def __init__(self, numero_mes, parent=None, rut_arrendatario=None):
        super().__init__(parent)
        self.setWindowTitle(f"Evaluación - Mes {numero_mes}")
        self.resize(650, 600)

        # --- LAYOUT PRINCIPAL ---
        layout_principal = QVBoxLayout(self)

        # --- SCROLL AREA ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout_principal.addWidget(scroll)

        self.rut_arrendatario = rut_arrendatario

        # --- CONTENEDOR INTERNO (donde va todo tu contenido) ---
        contenedor = QWidget()
        scroll.setWidget(contenedor)

        layout = QVBoxLayout(contenedor)

        form = QFormLayout()

        # ---- CAMPOS ----
        self.sueldo_base = QLineEdit()
        self.horas_extras = QLineEdit()
        self.afp = QLineEdit()
        self.salud = QLineEdit()
        self.cesantia = QLineEdit()
        self.bono1 = QLineEdit()
        self.bono2 = QLineEdit()
        self.bono3 = QLineEdit()
        self.colacion = QLineEdit()
        self.locomocion = QLineEdit()
        self.cargas_familiares = QLineEdit()
        self.viaticos = QLineEdit()
        self.herramientas = QLineEdit()
        self.anticipo = QLineEdit()
        self.otros = QLineEdit()
        self.sueldo_minimo = QLineEdit()

        form.addRow("Sueldo Base:", self.sueldo_base)
        form.addRow("Horas Extras:", self.horas_extras)
        form.addRow("AFP:", self.afp)
        form.addRow("Salud:", self.salud)
        form.addRow("Cesantía:", self.cesantia)
        form.addRow("Bono 1:", self.bono1)
        form.addRow("Bono 2:", self.bono2)
        form.addRow("Bono 3:", self.bono3)
        form.addRow("Colación:", self.colacion)
        form.addRow("Locomoción:", self.locomocion)
        form.addRow("Cargas Familiares:", self.cargas_familiares)
        form.addRow("Anticipo:", self.anticipo)
        form.addRow("Viáticos:", self.viaticos)
        form.addRow("Herramientas:", self.herramientas)
        form.addRow("Sueldo Mínimo:", self.sueldo_minimo)

        layout.addLayout(form)

        # ---- TABLA DE OTROS DESCUENTOS ----
        layout.addWidget(QLabel("Otros Descuentos:"))

        self.tbl_descuentos = QTableWidget()
        self.tbl_descuentos.setColumnCount(2)
        self.tbl_descuentos.setHorizontalHeaderLabels(["Concepto", "Monto"])
        self.tbl_descuentos.horizontalHeader().setStretchLastSection(True)

        self.tbl_descuentos.setMinimumHeight(120)
        
        layout.addWidget(self.tbl_descuentos)

        # Botones descuentos
        btns = QHBoxLayout()
        btn_add = DoubleClickButton("Agregar descuento")
        btn_del = DoubleClickButton("Eliminar seleccionado")

        btn_add.doubleClicked.connect(self.agregar_descuento)
        btn_del.doubleClicked.connect(self.eliminar_descuento)

        btns.addWidget(btn_add)
        btns.addWidget(btn_del)
        layout.addLayout(btns)

        # Botones OK/Cancel
        botones = QHBoxLayout()
        btn_ok = DoubleClickButton("Aceptar")
        btn_cancel = DoubleClickButton("Cancelar")
        btn_excel = DoubleClickButton("Exportar a Excel")

        btn_ok.doubleClicked.connect(self.aceptar)
        btn_cancel.doubleClicked.connect(self.reject)
        btn_excel.doubleClicked.connect(self.exportar_evaluacion_excel)

        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancel)
        botones.addWidget(btn_excel)
        layout.addLayout(botones)



    # ---------- Obtener datos para procesarlos ----------
    def obtener_datos(self):
        descuentos = []
        for i in range(self.tbl_descuentos.rowCount()):
            item_concepto = self.tbl_descuentos.item(i, 0)
            item_monto = self.tbl_descuentos.item(i, 1)

            if item_concepto is None or item_monto is None:
                continue

            concepto = item_concepto.text().strip()
            if not concepto:
                continue

            try:
                monto = float(item_monto.text() or 0)
            except:
                monto = 0

            descuentos.append({"nombre": concepto, "monto": monto})

        return {
            "sueldo_base": float(self.sueldo_base.text() or 0),
            "horas_extras": float(self.horas_extras.text() or 0),
            "afp": float(self.afp.text() or 0),
            "salud": float(self.salud.text() or 0),
            "cesantia": float(self.cesantia.text() or 0),
            "bono1": float(self.bono1.text() or 0),
            "bono2": float(self.bono2.text() or 0),
            "bono3": float(self.bono3.text() or 0),
            "colacion": float(self.colacion.text() or 0),
            "locomocion": float(self.locomocion.text() or 0),
            "viaticos": float(self.viaticos.text() or 0),
            "herramientas": float(self.herramientas.text() or 0),
            "otros": float(self.otros.text() or 0) if hasattr(self, "otros") else 0,
            "anticipo": float(self.anticipo.text() or 0) if hasattr(self, "anticipo") else 0,
            "cargas_familiares": float(self.cargas_familiares.text() or 0),

            # ⚠ IMPORTANTE: debes tener un input para sueldo mínimo
            "sueldo_minimo": float(self.sueldo_minimo.text() or 0),

            # Descuentos varios
            "descuentos_varios": descuentos
        }

    
    def agregar_descuento(self):
        row = self.tbl_descuentos.rowCount()
        self.tbl_descuentos.insertRow(row)
        self.tbl_descuentos.setItem(row, 0, QTableWidgetItem(""))
        self.tbl_descuentos.setItem(row, 1, QTableWidgetItem("0"))

    # ---------- Función para eliminar un descuento ----------
    def eliminar_descuento(self):
        row = self.tbl_descuentos.currentRow()
        if row >= 0:
            self.tbl_descuentos.removeRow(row)

    # ---------- Obtener datos para procesarlos ----------
    def calcular_totales_mes(self, datos):

        # 1) Tope legal gratificación
        tope_grat = datos["sueldo_minimo"] * 4.75 / 12

        # 2) Gratificación (25% SB topado)
        gratificacion = min(datos["sueldo_base"] * 0.25, tope_grat)

        # 3) Total imponible
        th_imponibles = (
            datos["sueldo_base"]
            + gratificacion
            + datos["bono1"]
            + datos["bono2"]
            + datos["bono3"]
            + datos["horas_extras"]
        )

        # 4) Total no imponible
        th_no_imponibles = (
            datos["colacion"]
            + datos["locomocion"]
            + datos["viaticos"]
            + datos["herramientas"]
            + datos['cargas_familiares']
            + datos["otros"]
        )

        # 5) Total haberes
        total_haberes = th_imponibles + th_no_imponibles

        # 6) Descuentos legales
        descuentos_legales = datos["afp"] + datos["salud"] + datos["cesantia"]

        # 7) Descuentos varios
        descuentos_varios_total = sum(d["monto"] for d in datos.get("descuentos_varios", []))

        # 8) Anticipo
        anticipo = datos.get("anticipo", 0)

        # 9) Líquido a pago
        liquido = total_haberes - descuentos_legales - descuentos_varios_total - anticipo


        return {
            "tope_gratificacion": tope_grat,
            "gratificacion": gratificacion,
            "th_imponibles": th_imponibles,
            "th_no_imponibles": th_no_imponibles,
            "total_haberes": total_haberes,
            "descuentos_legales": descuentos_legales,
            "descuentos_varios": descuentos_varios_total,
            "anticipo": anticipo,
            "liquido": liquido
        }
    

    def aceptar(self):
        datos = self.obtener_datos()
        resultados = self.calcular_totales_mes(datos)

        # Guardamos ambos: datos originales + cálculos
        self.resultado_final = {
            "datos": datos,
            "calculos": resultados
        }
        
        

        self.accept()

    def exportar_evaluacion_excel(self):
        datos = self.obtener_datos()
        calculos = self.calcular_totales_mes(datos)

        self.resultado_final = {
            "datos": datos,
            "calculos": calculos
        }


        rut = self.rut_arrendatario.strip().replace(".", "").replace("-", "")
        nombre_archivo = f"evaluacion_arrendatario_{rut}.xlsx"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar evaluación",
            nombre_archivo,
            "Excel (*.xlsx)"
        )

        if not ruta:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Evaluación"

        bold = Font(bold=True)

        fila = 1

        # =========================
        # DATOS DE ENTRADA
        # =========================
        ws[f"A{fila}"] = "DATOS DE ENTRADA"
        ws[f"A{fila}"].font = bold
        fila += 2

        for clave, valor in datos.items():
            if clave == "descuentos_varios":
                continue
            ws[f"A{fila}"] = clave.replace("_", " ").title()
            ws[f"B{fila}"] = valor
            fila += 1

        # Descuentos varios
        fila += 1
        ws[f"A{fila}"] = "Descuentos Varios"
        ws[f"A{fila}"].font = bold
        fila += 1

        for d in datos.get("descuentos_varios", []):
            ws[f"A{fila}"] = d["nombre"]
            ws[f"B{fila}"] = d["monto"]
            fila += 1

        # Margen grande
        fila += 3

        # =========================
        # CÁLCULOS
        # =========================
        ws[f"A{fila}"] = "CÁLCULOS"
        ws[f"A{fila}"].font = bold
        fila += 2

        for clave, valor in calculos.items():
            ws[f"A{fila}"] = clave.replace("_", " ").title()
            ws[f"B{fila}"] = valor
            fila += 1

        fila += 3

        # =========================
        # EXPLICACIÓN DE CÁLCULOS
        # =========================
        ws[f"A{fila}"] = "EXPLICACIÓN DE LOS CÁLCULOS"
        ws[f"A{fila}"].font = bold
        fila += 2

        explicaciones = [
            "1) Tope de gratificación: sueldo mínimo × 4.75 / 12.",
            "2) Gratificación: 25% del sueldo base, con tope legal.",
            "3) Total imponible: sueldo base + gratificación + bonos + horas extras.",
            "4) Total no imponible: colación, locomoción, viáticos, herramientas, cargas familiares y otros.",
            "5) Total haberes: imponibles + no imponibles.",
            "6) Descuentos legales: AFP + salud + cesantía.",
            "7) Descuentos varios: suma de descuentos adicionales ingresados.",
            "8) Anticipo: monto adelantado al trabajador.",
            "9) Líquido a pago: total haberes − descuentos − anticipo."
        ]

        for texto in explicaciones:
            ws[f"A{fila}"] = texto
            fila += 1

        # =========================
        # AJUSTES VISUALES
        # =========================
        ws.column_dimensions["A"].width = 45
        ws.column_dimensions["B"].width = 20

        try:
            wb.save(ruta)
            QMessageBox.information(self, "Éxito", f"Archivo exportado correctamente:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{e}")

    
class ImpuestoRentaDialog(QDialog):
    def __init__(self, renta_tributable, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calcular Impuesto a la Renta")

        self.renta_tributable = renta_tributable
        self.resultado = None  # ← aquí guardaremos el cálculo final

        layout = QFormLayout()

        # Campo RT (solo lectura)
        self.txt_rt = QLineEdit(str(renta_tributable))
        self.txt_rt.setReadOnly(True)
        layout.addRow("Renta Tributable:", self.txt_rt)

        # Campos editables
        self.txt_multiplicador = QLineEdit()
        layout.addRow("Tasa:", self.txt_multiplicador)

        self.txt_resta = QLineEdit()
        layout.addRow("Rebaja:", self.txt_resta)

        # Botones
        btn_calcular = DoubleClickButton("Calcular")
        btn_cancelar = DoubleClickButton("Cancelar")

        btn_calcular.doubleClicked.connect(self.calcular)
        btn_cancelar.doubleClicked.connect(self.reject)

        hbox = QHBoxLayout()
        hbox.addWidget(btn_calcular)
        hbox.addWidget(btn_cancelar)

        layout.addRow(hbox)
        self.setLayout(layout)

    def calcular(self):
        try:
            rt = float(self.renta_tributable)
            multiplicador = float(self.txt_multiplicador.text())
            resta = float(self.txt_resta.text())

            self.resultado = (rt * multiplicador) - resta
            self.accept()

        except ValueError:
            pass  # puedes mostrar un QMessageBox si quieres



