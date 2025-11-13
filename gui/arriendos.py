from PySide6.QtWidgets import QFileDialog, QMainWindow,QHBoxLayout,QTextEdit,QTabWidget,QDoubleSpinBox,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from services.arriendos_service import obtener_arriendos_resumen, obtener_detalle_arriendo, obtener_arriendos_por_estado
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QIntValidator, QColor, QDoubleValidator
from gui.usuario_actual import UsuarioActual
from services.supabase_client import supabase
import json
import pandas as pd

class DashboardArriendos(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.cargando_tabla = False

        filter_layout = QHBoxLayout()
        
        # Filtro de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por arrendador, arrendatario o propiedad...")
        self.search_input.textChanged.connect(self.filtrar_arriendos)


         # Filtro de estado
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems([
            "Todas los arriendos",
            "Vigentes",
            "Terminados"
            
        ])
        self.filtro_estado.currentIndexChanged.connect(self.filtrar_arriendos)
        
        # Filtro de fecha
        self.filtro_fecha = QComboBox()
        self.filtro_fecha.addItems([
            "Todas los arriendos",
            "Últimos 7 días",
            "Últimos 30 días",
            "Este mes",
            "Este año"
        ])
        self.filtro_fecha.currentIndexChanged.connect(self.filtrar_arriendos)

        # Agregar filtros al layout
        filter_layout.addWidget(QLabel("Filtros:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Estado:"))
        filter_layout.addWidget(self.filtro_estado)
        filter_layout.addWidget(QLabel("Fecha:"))
        filter_layout.addWidget(self.filtro_fecha)

        layout.addLayout(filter_layout)


         # Tabla de arriendos
        self.tabla_arriendos = QTableWidget()
        self.tabla_arriendos.setColumnCount(6)
        self.tabla_arriendos.setHorizontalHeaderLabels([
            "ID", 
            "Arrendador", 
            "Arrendatario", 
            "Propiedad", 
            "Fecha",
            "Tipo"
        ])
        self.tabla_arriendos.setSortingEnabled(True)
        self.tabla_arriendos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_arriendos.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tabla_arriendos.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla_arriendos.verticalHeader().setVisible(False)
        self.tabla_arriendos.itemDoubleClicked.connect(self.mostrar_detalle_arriendo)
        
        layout.addWidget(self.tabla_arriendos)

        button_layout = QHBoxLayout()

        
        self.btn_agregar_arriendo = QPushButton("Agregar Arriendo")
        self.btn_agregar_arriendo.clicked.connect(self.abrir_formulario_arriendo)
        
        self.btn_actualizar = QPushButton("Actualizar Lista")
        self.btn_actualizar.clicked.connect(self.cargar_arriendos)
        
        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.clicked.connect(self.exportar_a_excel)
        
 
        
       
        button_layout.addWidget(self.btn_agregar_arriendo)
        button_layout.addWidget(self.btn_actualizar)
        button_layout.addWidget(self.btn_exportar)
        
        layout.addLayout(button_layout)
        
        # Cargar datos iniciales
        self.cargar_arriendos()

    def cargar_arriendos(self):
        try:
            self.cargando_tabla = True
            

            self.tabla_arriendos.setRowCount(0)
            estado_filtro = self.filtro_estado.currentText()

            if estado_filtro == "Todas los arriendos":
                arriendos = obtener_arriendos_resumen()
            else:
                arriendos = obtener_arriendos_por_estado(estado_filtro)

            if arriendos:
                self.tabla_ventas.setRowCount(len(arriendos))
                self.arriendos = arriendos or []
            

                self.tabla_ventas.setUpdatesEnabled(False)  # 🔸 Pausa el renderizado de la tabla
            try:
                for row, arriendo in enumerate(arriendos):
                    self.tabla_arriendos.setItem(row, 0, QTableWidgetItem(str(arriendo.get("id", ""))))
                    self.tabla_arriendos.setItem(row, 1, QTableWidgetItem(arriendo.get("arrendador", "")))
                    self.tabla_arriendos.setItem(row, 2, QTableWidgetItem(arriendo.get("arrendatario", "")))
                    self.tabla_arriendos.setItem(row, 3, QTableWidgetItem(arriendo.get("propiedad", "")))
                    self.tabla_arriendos.setItem(row, 4, QTableWidgetItem(str(arriendo.get("fecha_arriendo", ""))))
                    self.tabla_ventas.setItem(row, 5, QTableWidgetItem(arriendo.get("tipo_arriendo", "")))
            finally:
                self.tabla_arriendos.setUpdatesEnabled(True)   # 🔸 Reactiva el renderizado
                self.tabla_arriendos.resizeColumnsToContents()
                self.tabla_arriendos.setColumnHidden(0, True)
            

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los arriendos: {str(e)}")

        finally:
            self.cargando_tabla = False

    


    def filtrar_arriendos(self):
        pass
        
    def mostrar_detalle_arriendo(self):
        pass

    def exportar_a_excel(self):
        pass


    def abrir_formulario_arriendo(self, en_proceso=False):
        self.formulario_arriendo = FormularioArriendo()
        self.formulario_arriendo.arriendo_guardado.connect(self.cargar_arriendos)
        self.formulario_arriendo.show()

        
    

class FormularioArriendo(QWidget):
    arriendo_guardado = Signal()

    def __init__(self,arriendo_id=None, parent=None):
        super().__init__(parent)
        self.arriendo_id = arriendo_id

        self.setWindowTitle("Editar Arriendo" if arriendo_id else "Nuevo Arriendo")
        self.resize(900, 700)
        self.detalle_arriendo = {}

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


        tab_arrendador = QWidget()
        self.tabs.addTab(tab_arrendador, "Arrendador")
        self.setup_tab_arrendador(tab_arrendador)

        tab_arrendatario = QWidget()
        self.tabs.addTab(tab_arrendatario , "Arrendatario")
        self.setup_tab_arrendatario(tab_arrendatario )


        btn_guardar = QPushButton("Guardar Arriendo")
        btn_guardar.clicked.connect(self.guardar_arriendo)
        layout_form.addWidget(btn_guardar)
        
        # Estilo para campos obligatorios
        self.setStyleSheet("""
            QLabel[obligatorio="true"] {
                font-weight: bold;
                color: #FF0000;
            }
        """)

        if self.arriendo_id:
            self.detalle_arriendo = obtener_detalle_arriendo(self.arriendo_id)
            if not self.detalle_arriendo:
                layout_principal.addWidget(QLabel("No se encontraron detalles para este arriendo"))
            else:
                self.cargar_datos_arriendo(self.arriendo_id)

    


    def setup_tab_arrendador(self, tab):
        layout = QFormLayout(tab)
        
        # Campos del comprador
        self.txt_arren_nombre = QLineEdit()
        self.txt_arren_rut = QLineEdit()
        self.txt_arren_direccion = QLineEdit()
        self.txt_arren_telefono = QLineEdit()
        self.txt_arren_email = QLineEdit()
     
        
        # Agregar campos

        layout.addRow(self.crear_label("Nombre:", True), self.txt_arren_nombre)
        layout.addRow(self.crear_label("RUT:", True), self.txt_arren_rut)
        layout.addRow(self.crear_label("Dirección:"), self.txt_arren_direccion)
        layout.addRow(self.crear_label("Teléfono:"), self.txt_arren_telefono)
        layout.addRow(self.crear_label("Email:"), self.txt_arren_email)

    def setup_tab_arrendatario(self, tab):
        layout = QFormLayout(tab)
        
        # Campos del comprador
        self.txt_arrendatario_nombre = QLineEdit()
        self.txt_arrendatario_rut = QLineEdit()
        self.txt_arrendatario_direccion = QLineEdit()
        self.txt_arrendatario_telefono = QLineEdit()
        self.txt_arrendatario_email = QLineEdit()
        self.txt_sueldo_base = QLineEdit()
        self.txt_horas_extras = QLineEdit()
        self.txt_afp = QLineEdit()
        self.txt_salud = QLineEdit()
        self.txt_cesantia = QLineEdit()
        self.cmb_tipo_trabajador = QComboBox()
        self.cmb_tipo_trabajador.addItems(["Dependiente", "Independiente", "Otro"])
        self.txt_bono_1 = QLineEdit()
        self.txt_bono_2 = QLineEdit()
        self.txt_bono_3 = QLineEdit()
        self.txt_colacion = QLineEdit()
        self.txt_locomocion = QLineEdit()
        self.txt_cargas_familiares = QLineEdit()
        self.txt_viaticos = QLineEdit()
        self.txt_herramientas = QLineEdit()
        self.txt_otros = QLineEdit()
        self.txt_antiguedad_laboral = QLineEdit()
        self.cmb_dicom = QComboBox()
        self.cmb_dicom.addItems(["Si","No"])
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
        layout.addRow(self.crear_label("Sueldo Base:"), self.txt_sueldo_base)
        layout.addRow(self.crear_label("Horas Extras:"), self.txt_horas_extras)
        layout.addRow(self.crear_label("AFP:"), self.txt_afp)
        layout.addRow(self.crear_label("Salud:"), self.txt_salud)
        layout.addRow(self.crear_label("Cesantía:"), self.txt_cesantia)
        layout.addRow(self.crear_label("Bono 1:"), self.txt_bono_1)
        layout.addRow(self.crear_label("Bono 2:"), self.txt_bono_2)
        layout.addRow(self.crear_label("Bono 3:"), self.txt_bono_3)
        layout.addRow(self.crear_label("Colación:"), self.txt_colacion)
        layout.addRow(self.crear_label("Locomoción:"), self.txt_locomocion)
        layout.addRow(self.crear_label("Cargas Familiares:"), self.txt_cargas_familiares)
        layout.addRow(self.crear_label("Viáticos:"), self.txt_viaticos)
        layout.addRow(self.crear_label("Herramientas:"), self.txt_herramientas)
        layout.addRow(self.crear_label("Otros:"), self.txt_otros)
        layout.addRow(self.crear_label("Antigüedad Laboral (meses):"), self.txt_antiguedad_laboral)

        # --- Evaluación ---
        layout.addRow(self.crear_label("¿Tiene DICOM?"), self.cmb_dicom)
        layout.addRow(self.crear_label("Comentarios:"), self.txt_comentarios)
        layout.addRow(self.crear_label("Estado de Evaluación:"), self.cmb_evaluacion_estado)
        layout.addRow(self.crear_label("Fecha Evaluación:"), self.fecha_evaluacion)
        layout.addRow(self.crear_label("Renta Mensual:"), self.txt_renta)
                







    def cargar_datos_arriendo(self, arriendo_id):
        pass


    def guardar_arriendo(self):
        pass


    def crear_label(self, texto, obligatorio=False):
        label = QLabel(texto)
        if obligatorio:
            label.setProperty("obligatorio", "true")
        return label