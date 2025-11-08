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
            "Todas las ventas",
            "En proceso",
            "Negociandose", 
            "Cerradas verbalmente",
            "Cerradas en notaría",
            "Inscritas"
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


         # Tabla de ventas
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
        self.formulario_arriendo.venta_guardada.connect(self.cargar_arriendos)
        self.formulario_arriendo.show()

        
    def crear_label(self, texto, obligatorio=False):
        label = QLabel(texto)
        if obligatorio:
            label.setProperty("obligatorio", "true")
        return label
    

class FormularioArriendo(QWidget):
    arriendo_guardado = Signal()

    def __init__(self,arriendo_id=None, parent=None):
        super().__init__(parent)
        self.arriendo_id = arriendo_id