from PySide6.QtWidgets import QFileDialog, QMainWindow,QHBoxLayout,QTextEdit,QTabWidget,QDoubleSpinBox,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from services.propiedades_service import obtener_detalle_propiedad, obtener_ventas_resumen
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QIntValidator, QColor, QDoubleValidator
from services.supabase_client import supabase


class DetallePropiedadWindow(QWidget):
    def __init__(self, codigo_interno, dashboard=None):
        super().__init__()
        self.codigo_interno = codigo_interno
        self.dashboard = dashboard
        self.setWindowTitle(f"Detalle de Propiedad #{codigo_interno}")
        self.resize(900, 700)
        
        # Layout principal con scroll
        layout_principal = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        scroll.setWidget(contenido)
        layout_principal.addWidget(scroll)
        
        # Layout del contenido
        layout_contenido = QVBoxLayout(contenido)
        
        # Obtener datos de la venta
        self.detalle_propiedad = obtener_detalle_propiedad(codigo_interno)

        
        if not self.detalle_propiedad:
            layout_contenido.addWidget(QLabel("No se encontraron detalles para esta propiedad"))
            return
        
        # Mostrar información en pestañas
        self.tabs = QTabWidget()
        layout_contenido.addWidget(self.tabs)


        # Pestaña de propiedad
        self.setup_tab_propiedad()


        # Botón para cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout_contenido.addWidget(btn_cerrar)


    def setup_tab_propiedad(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Propiedad")
        layout = QVBoxLayout(tab)
        
        propiedad = self.detalle_propiedad.get('propiedad', {})
        
        # Información básica
        form_total = QFormLayout()

        # Campos básicos
        campos_basicos = [
            ("Código interno", propiedad.get('codigo_interno')),
            ("Dirección", propiedad.get('direccion')),
            ("ROL", propiedad.get('rol')),
            ("Comuna", propiedad.get('comuna'))
        ]

        for label, value in campos_basicos:
            if value:
                form_total.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))

        # Encabezado documentación
        form_total.addRow(QLabel("<b>Documentación:</b>"), QLabel(""))

        # Campos documentación
        campos_doc = [
            ("Estudio de títulos", propiedad.get('estudio_titulos')),
            ("Dominio vigente", propiedad.get('dominio_vigente')) 
        ]


        for label, value in campos_doc:
            if value:
                form_total.addRow(QLabel(f"{label}:"), QLabel(str(value)))

        layout.addLayout(form_total)



class DashboardPropiedades(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        layout = QVBoxLayout(self)
        self.resize(1200, 800)
        self.cargando_tabla = False
        
        # Barra de filtros
        filter_layout = QHBoxLayout()
        
        # Filtro de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por propiedad...")
        self.search_input.textChanged.connect(self.filtrar_ventas)

        filter_layout.addWidget(QLabel("Filtros:"))
        filter_layout.addWidget(self.search_input)

        layout.addLayout(filter_layout)


        # Tabla de propiedades
        self.tabla_propiedades = QTableWidget()
        self.tabla_propiedades.setColumnCount(2)
        self.tabla_propiedades.setHorizontalHeaderLabels([
            "Propiedad", "Código Interno"
        ])
        self.tabla_propiedades.setSortingEnabled(True)
        self.tabla_propiedades.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_propiedades.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_propiedades.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla_propiedades.verticalHeader().setVisible(False)
        self.tabla_propiedades.itemDoubleClicked.connect(self.mostrar_detalle_propiedad)

        layout.addWidget(self.tabla_propiedades)
        self.cargar_propiedades()
        

    def cargar_propiedades(self):
        try:
            self.cargando_tabla = True
            


            self.tabla_propiedades.setRowCount(0)
            

            
            propiedades = obtener_ventas_resumen()
            

            if propiedades:
                self.tabla_propiedades.setRowCount(len(propiedades))
                self.propiedades = propiedades or []

                self.tabla_propiedades.setUpdatesEnabled(False)
                try:
                    for row, propiedad in enumerate(propiedades):
                        # Ejemplo: "asdjhjasd (prop-124)"
                        texto = propiedad.get("propiedad", "")
                        if "(" in texto and ")" in texto:
                            nombre = texto.split("(")[0].strip()
                            codigo = texto.split("(")[-1].split(")")[0].strip()
                        else:
                            nombre = texto
                            codigo = ""

                        self.tabla_propiedades.setItem(row, 0, QTableWidgetItem(nombre))
                        self.tabla_propiedades.setItem(row, 1, QTableWidgetItem(codigo))
                finally:
                    self.tabla_propiedades.setUpdatesEnabled(True)   # 🔸 Reactiva el renderizado
                    self.tabla_propiedades.resizeColumnsToContents()
                    # self.tabla_propiedades.setColumnHidden(0, True)
            

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las propiedades: {str(e)}")

        finally:
            self.cargando_tabla = False




    def filtrar_ventas(self):
        texto = self.search_input.text().lower()
    
        for row in range(self.tabla_ventas.rowCount()):
            mostrar_fila = True
            
            # Filtrar por texto
            if texto:
                mostrar_fila = any(
                    texto in self.tabla_propiedades.item(row, col).text().lower()
                    for col in range(self.tabla_propiedades.columnCount())
                )
            
            self.tabla_ventas.setRowHidden(row, not mostrar_fila)
    
    def mostrar_detalle_propiedad(self, item):
        codigo_interno = self.tabla_propiedades.item(item.row(), 1).text()
        self.ventana_detalle = DetallePropiedadWindow(codigo_interno, dashboard=self)
        self.ventana_detalle.show()
    