from PySide6.QtWidgets import QHeaderView, QGroupBox, QDialogButtonBox, QSizePolicy, QFileDialog, QMainWindow, QHBoxLayout, QTextEdit, QTabWidget, QDoubleSpinBox, QHeaderView, QFrame, QWidget, QLabel, QVBoxLayout, QAbstractItemView, QTableWidget, QTableWidgetItem, QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton, QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem, QSpinBox, QDialog
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QIntValidator, QColor, QDoubleValidator, QFont
from gui.usuario_actual import UsuarioActual
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from services.supabase_client import supabase
from services.arriendos_service import obtener_detalle_arriendo
from services.eva_arrendatarios_service import actualizar_arrendatario,safe_numeric,obtener_evaluaciones_arrendatario, cargar_detalle, obtener_arrendatarios, obtener_arrendatario, crear_arrendatario, eliminar_arrendatario
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
            self.tabla.setHorizontalHeaderLabels([
                "RUT", "Nombre", "Tipo Trabajador"
            ])
            layout.addWidget(self.tabla)

            self.tabla.verticalHeader().setVisible(False)
            self.tabla.resizeColumnsToContents()
            self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
            self.tabla.setSelectionMode(QTableWidget.SingleSelection)

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
                    self.cargar_arrendatario()


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

        self.filtro_periodo = QComboBox()
        self.filtro_periodo.addItems([
            "Todos los periodos",
            "Últimos 6 meses",
            "Último año"
        ])
        self.filtro_periodo.currentIndexChanged.connect(
            self.aplicar_filtros
        )

        filtros_layout.addWidget(QLabel("Filtros:"))
        filtros_layout.addWidget(self.search_input)
        filtros_layout.addWidget(QLabel("Periodo:"))
        filtros_layout.addWidget(self.filtro_periodo)

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

        layout.addWidget(self.tabla)

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

        layout.addWidget(self.tabla_detalle)

        # =============================
        # 4. BOTONES
        # =============================
        botones = QHBoxLayout()

        self.btn_nueva = DoubleClickButton("Nueva Liquidación")
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
        self.todo_evaluaciones = []
        self.cargar_evaluaciones()


    def cargar_evaluaciones(self):

        data = obtener_evaluaciones_arrendatario()

        self.evaluaciones = data or []

        self.render_tabla()


    def render_tabla(self):

        self.tabla.setRowCount(0)

        # 🔥 estado interno
        self._eval_ids = []
        self._eval_tipos = []

        for fila, ev in enumerate(self.evaluaciones):

            self.tabla.insertRow(fila)

            self.tabla.setItem(
                fila, 0,
                QTableWidgetItem(ev["nombre"])
            )

            self.tabla.setItem(
                fila, 1,
                QTableWidgetItem(ev["tipo"])
            )

            self.tabla.setItem(
                fila, 2,
                QTableWidgetItem(str(ev["fecha"] or ""))
            )

            self.tabla.setItem(
                fila, 3,
                QTableWidgetItem(ev["resultado"] or "")
            )

            # ✅ guardar metadata invisible
            self._eval_ids.append(ev["id"])
            self._eval_tipos.append(ev["tipo"])

       
    def _evaluacion_seleccionada(self):
        eval_id = self._eval_id_seleccionado()
        tipo = self._eval_tipo_seleccionado()

        if not eval_id:
            return

        # 🔴 dependientes NO tienen detalle
        if tipo == "Dependiente":
            self.tabla_detalle.setRowCount(0)
            self.tabla_detalle.setDisabled(True)
            return

        # 🟢 independientes → cargar detalle
        self.tabla_detalle.setDisabled(False)

        detalle = cargar_detalle(eval_id)

        self.mostrar_detalle(detalle)

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
                fila, 3, QTableWidgetItem(str(item["ventas_netas_estimadas"]))
            )
            self.tabla_detalle.setItem(
                fila, 4, QTableWidgetItem(str(item["compras_netas_estimadas"]))
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
            texto = self.search_input.text().lower()
            filtro = self.filtro_periodo.currentText()

            filtrado = []

            for l in self.todo_liquidaciones:
                nom = l.get("trabajador_nombre", "").lower()
                rut = l.get("trabajador_rut", "").lower()

                if texto and texto not in nom and texto not in rut:
                    continue

                periodo = QDate.fromString(l.get("periodo", "") + "-01", "yyyy-MM-dd")
                hoy = QDate.currentDate()

                if filtro == "Últimos 6 meses" and periodo < hoy.addMonths(-6):
                    continue
                if filtro == "Último año" and periodo < hoy.addYears(-1):
                    continue

                filtrado.append(l)

            self._poblar_tabla(filtrado)

    def _poblar_tabla(self, liqs):
            self.tabla.setRowCount(0)
            self._ids = []

            for row, l in enumerate(liqs):
                self.tabla.insertRow(row)
                self._ids.append(l.get("id"))
                self.tabla.setItem(row, 0, QTableWidgetItem(l.get("periodo", "")))
                self.tabla.setItem(row, 1, QTableWidgetItem(l.get("trabajador_rut", "")))
                self.tabla.setItem(row, 2, QTableWidgetItem(l.get("trabajador_nombre", "")))
                self.tabla.setItem(row, 3, QTableWidgetItem(str(int(l.get("total_haberes") or 0))))
                self.tabla.setItem(row, 4, QTableWidgetItem(str(int(l.get("total_descuentos_general") or 0))))
                self.tabla.setItem(row, 5, QTableWidgetItem(str(int(l.get("liquido_pagar") or 0))))


    def _id_seleccionado(self) -> str | None:
            fila = self.tabla.currentRow()
            if fila < 0 or fila >= len(getattr(self, "_ids", [])):
                return None
            return self._ids[fila]

    def crear_liquidacion(self):
            dlg = DialogoLiquidacion(parent=self)
            dlg.liquidacion_guardada.connect(self.cargar_liquidaciones)
            if dlg.exec():
                self.cargar_liquidaciones()

    def ver_editar_liquidacion(self):
            liq_id = self._id_seleccionado()
            # if not liq_id:
            #     QMessageBox.warning(self, "Atención", "Seleccione una liquidación.")
            #     return
            # data = rrhh_service.obtener_liquidacion_completa(liq_id)
            # if not data:
            #     QMessageBox.warning(self, "Error", "No se pudo cargar la liquidación.")
            #     return
            # dlg = DialogoLiquidacion(liquidacion_existente=data, parent=self)
            # if dlg.exec():
            #     self.cargar_liquidaciones()

    def eliminar_liquidacion(self):
            liq_id = self._id_seleccionado()
            # if not liq_id:
            #     QMessageBox.warning(self, "Atención", "Seleccione una liquidación.")
            #     return
            # if QMessageBox.question(self, "Confirmar", "¿Eliminar la liquidación seleccionada?") == QMessageBox.Yes:
            #     rrhh_service.eliminar_liquidacion(liq_id)
            #     self.cargar_liquidaciones()




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
        if value is None:
            return 0.0

    
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
     def __init__(self,parent=None):
        super().__init__(parent)


        self.rentas_tributables = []
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

        tab_evaluacion = QWidget()
        self.tabs.addTab(tab_evaluacion, "Evaluación")
        self.setup_tab_evaluacion(tab_evaluacion)
        self.setup_tab_evaluacion_index = self.tabs.indexOf(tab_evaluacion)

        tab_evaluacion_independiente = QWidget()
        self.tabs.addTab(tab_evaluacion_independiente, "Evaluación")
        self.setup_tab_evaluacion_independiente(tab_evaluacion_independiente)
        self.setup_tab_evaluacion_independiente_index = self.tabs.indexOf(tab_evaluacion_independiente )


        

        

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





