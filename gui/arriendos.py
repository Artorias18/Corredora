from PySide6.QtWidgets import QFileDialog, QMainWindow,QHBoxLayout,QTextEdit,QTabWidget,QDoubleSpinBox,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from services.arriendos_service import obtener_arriendos_resumen, obtener_detalle_arriendo, obtener_arriendos_por_estado, guardar_arriendo
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
            "Todos los arriendos",
            "Vigentes",
            "Terminados"
            
        ])
        self.filtro_estado.currentIndexChanged.connect(self.filtrar_arriendos)
        
        # Filtro de fecha
        self.filtro_fecha = QComboBox()
        self.filtro_fecha.addItems([
            "Todas las fechas",
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
        # button_layout.addWidget(self.btn_actualizar)
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


    def abrir_formulario_arriendo(self):
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

        tab_propiedad = QWidget()
        self.tabs.addTab(tab_propiedad, "Propiedad")
        self.setup_tab_propiedad(tab_propiedad)

        tab_evaluacion = QWidget()
        self.tabs.addTab(tab_evaluacion, "Evaluación")
        self.setup_tab_evaluacion(tab_evaluacion)

        tab_arriendo = QWidget()
        self.tabs.addTab(tab_arriendo, "Contrato Arriendo")
        self.setup_tab_arriendo(tab_arriendo)


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
                

    def setup_tab_propiedad(self, tab):
        layout = QFormLayout(tab)
        
        # Campos de propiedad
        self.txt_prop_codigo = QLineEdit()
        self.txt_prop_direccion = QLineEdit()
        self.txt_prop_rol = QLineEdit()
        self.txt_prop_comuna = QLineEdit()
        
        # Documentación
        
        self.cmb_dominio_vigente = QComboBox()
        self.cmb_dominio_vigente.addItems(["Si Posee Documento", "No Posee Documento"])


        # Agregar campos
        layout.addRow(self.crear_label("Código interno:", True), self.txt_prop_codigo)
        layout.addRow(self.crear_label("Dirección:", True), self.txt_prop_direccion)
        layout.addRow(self.crear_label("ROL:", True), self.txt_prop_rol)
        layout.addRow(self.crear_label("Comuna:", True), self.txt_prop_comuna)
        
        # Documentación
        layout.addRow(QLabel("<b>Documentación:</b>"))
        layout.addRow(self.crear_label("Dominio vigente:"), self.cmb_dominio_vigente)


    def setup_tab_evaluacion(self,tab):
        layout= QFormLayout(tab)


        self.tbl_evaluacion = QTableWidget()
        self.tbl_evaluacion.setRowCount(8)
        self.tbl_evaluacion.setColumnCount(4)

        # Encabezados
        self.tbl_evaluacion.setHorizontalHeaderLabels([
            "Concepto", "Mes 1", "Mes 2", "Mes 3"
        ])

        conceptos = [
            "Sueldo Base (SB)",
            "Gratificación (GT)",
            "TH Imponibles (THIMP)",
            "Loc/Móvil (LOCMOV)",
            "TH No Imponibles (THNI)",
            "Descuentos Legales",
            "Descuentos Varios",
            "Líquido a Pago"
        ]

        # Llenar columna de conceptos
        for i, concepto in enumerate(conceptos):
            item = QTableWidgetItem(concepto)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # Hacerlo no editable
            self.tbl_evaluacion.setItem(i, 0, item)

        layout.addRow(self.tbl_evaluacion)
        
            

        

    def setup_tab_arriendo(self,tab):

        layout = QFormLayout(tab)

        self.fecha_inicio = QDateEdit(QDate.currentDate())
        self.fecha_inicio.setCalendarPopup(True)

        self.fecha_termino = QDateEdit(QDate.currentDate())
        self.fecha_termino.setCalendarPopup(True)

        self.txt_renta_mensual = QLineEdit()

        self.txt_garantia = QLineEdit()

        self.chk_gastos_comunes = QCheckBox("¿Gastos comunes incluidos?")
        self.chk_gastos_comunes.setChecked(False)

        self.cmb_estado_arriendo = QComboBox()
        self.cmb_estado_arriendo.addItems(["Vigente", "Finalizado", "Rescindido"])

        self.cmb_tipo_contrato = QComboBox()
        self.cmb_tipo_contrato.addItems(["Plazo Fijo", "Plazo Indefinido"])

        self.txt_forma_pago = QLineEdit()

        self.cmb_periodo_pago = QComboBox()
        self.cmb_periodo_pago.addItems(["Mensual", "Trimestral", "Anual"])

        self.txt_observaciones = QTextEdit()

        layout.addRow(self.crear_label("Fecha Inicio:", True), self.fecha_inicio)
        layout.addRow(self.crear_label("Fecha de Termino:"), self.fecha_termino)
        layout.addRow(self.crear_label("Renta Mensual:"), self.txt_renta_mensual)
        layout.addRow(self.crear_label("Garantía:"), self.txt_garantia)
        layout.addWidget(self.chk_gastos_comunes)
        layout.addRow(self.crear_label("Estado del arriendo:"), self.cmb_estado_arriendo)
        layout.addRow(self.crear_label("Tipo de contrato:"), self.cmb_tipo_contrato)
        layout.addRow(self.crear_label("Forma de pago:"), self.txt_forma_pago)
        layout.addRow(self.crear_label("Periodo de pago"), self.cmb_periodo_pago)
        layout.addRow(self.crear_label("Observaciones"), self.txt_observaciones)

        



    def obtener_datos_evaluacion(self):
        datos = []

        conceptos = [
            "sueldo_base",
            "gratificacion",
            "th_imponibles",
            "locacion",
            "th_no_imponibles",
            "descuentos_legales",
            "descuentos_varios",
            "liquido"
        ]

        for fila, concepto in enumerate(conceptos):
            fila_data = {
                "concepto": concepto,
                "mes1": self.tbl_evaluacion.item(fila, 1).text() if self.tbl_evaluacion.item(fila, 1) else "",
                "mes2": self.tbl_evaluacion.item(fila, 2).text() if self.tbl_evaluacion.item(fila, 2) else "",
                "mes3": self.tbl_evaluacion.item(fila, 3).text() if self.tbl_evaluacion.item(fila, 3) else "",
            }
            datos.append(fila_data)

        return datos

        





    def cargar_datos_arriendo(self, arriendo_id):
        pass


    def guardar_arriendo(self):
        try:
            data_arriendo = {
                
                'propiedad':{
                    'codigo': self.txt_prop_codigo.text(),
                    'direccion': self.txt_prop_direccion.text(),
                    'rol': self.txt_prop_rol.text(),
                    'comuna': self.txt_prop_comuna.text(),
                    'dominio_vigente': self.cmb_dominio_vigente.currentText()
                },

                'arrendador':{
                    'rut': self.txt_arren_rut.text(),
                    'nombre': self.txt_arren_nombre.text(),
                    'direccion': self.txt_arren_direccion.text(),
                    'telefono': self.txt_arren_telefono.text(),
                    'correo_electronico': self.txt_arren_email.text()
                },

                'arrendatario':{
                    'rut': self.txt_arrendatario_rut.text(),
                    'nombre': self.txt_arrendatario_nombre.text(),
                    'telefono': self.txt_arrendatario_telefono.text(),
                    'email': self.txt_arrendatario_email.text(),
                    'direccion': self.txt_arrendatario_direccion.text(),
                    'sueldo_base': self.txt_sueldo_base.text(),
                    'horas_extras': self.txt_horas_extras.text(),
                    'afp': self.txt_afp.text(),
                    'salud': self.txt_salud.text(),
                    'cesantia': self.txt_cesantia.text(),
                    'tipo_trabajador': self.cmb_tipo_trabajador.currentText(),
                    'bono1': self.txt_bono_1.text(),
                    'bono2': self.txt_bono_2.text(),
                    'bono3': self.txt_bono_3.text(),
                    'colacion': self.txt_colacion.text(),
                    'locomocion': self.txt_locomocion.text(),
                    'cargas_familiares': self.txt_cargas_familiares.text(),
                    'viaticos': self.txt_viaticos.text(),
                    'herramientas': self.txt_herramientas.text(),
                    'otros': self.txt_otros.text(),
                    'antiguedad_laboral': self.txt_antiguedad_laboral.text(),
                    'dicom': self.cmb_dicom.currentText(),
                    'comentarios': self.txt_comentarios.toPlainText(),
                    'evaluacion_estado': self.cmb_evaluacion_estado.currentText(),
                    'fecha_evaluacion': self.fecha_evaluacion.date().toString("yyyy-MM-dd"),
                    'renta': self.txt_renta

                },

                'evaluacion_arrendatario':{

                },
                
                'arriendo':{
                    'fecha_inicio': self.fecha_inicio.date().toString("yyyy-MM-dd"),
                    'fecha_termino': self.fecha_termino.date().toString("yyyy-MM-dd"),
                    'renta_mensual': self.txt_renta_mensual.text(),
                    'garantia': self.txt_garantia.text(),
                    'gastos_comunes_incluidos': self.chk_gastos_comunes.isChecked(),
                    'estado': self.cmb_estado_arriendo.currentText(),
                    'tipo_contrato': self.cmb_tipo_contrato.currentText(),
                    'forma_pago': self.txt_forma_pago.text(),
                    'periodo_pago': self.cmb_periodo_pago.currentText(),
                    'observaciones': self.txt_observaciones.toPlainText()
                }
            }


            arriendo_id = guardar_arriendo(
                data_arriendo
            )

            if arriendo_id:
                print(f"Arriendo guardado con ID {arriendo_id}, mostrando mensaje")
                QMessageBox.information(
                    self,
                    "Éxito",
                    "El arriendo se ha guardado correctamente.\n\n"
                    f"ID de arriendo: {arriendo_id}"
                )

                self.arriendo_guardado.emit()
                self.close()

            else:
                print("guardar_arriendo retornó ID falso o None")


        except Exception as e:
            print(f"Error en guardar_arriendo: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar el arriendo: {str(e)}")
            

            


    def crear_label(self, texto, obligatorio=False):
        label = QLabel(texto)
        if obligatorio:
            label.setProperty("obligatorio", "true")
        return label
    

    def validar_rut(self, rut):
        # Implementación básica de validación de RUT chileno
        rut = rut.replace(".", "").replace("-", "").upper()
        if not rut[:-1].isdigit():
            return False
        
        cuerpo = rut[:-1]
        dv = rut[-1]
        
        suma = 0
        multiplicador = 2
        
        for c in reversed(cuerpo):
            suma += int(c) * multiplicador
            multiplicador += 1
            if multiplicador > 7:
                multiplicador = 2
        
        resto = suma % 11

        dv_calculado = 11-resto

        if dv_calculado == 11:
            dv_calculado = "0"
        elif dv_calculado == 10:
            dv_calculado = "K"
        else:
            dv_calculado = str(dv_calculado)
        
        return dv == dv_calculado
    

    def validar_campos_obligatorios(self):
        # Validar campos obligatorios básicos
        campos_obligatorios = [
            (self.txt_prop_codigo.text(), "Código de propiedad"),
            (self.txt_prop_direccion.text(), "Dirección de propiedad"),
            (self.txt_prop_rol.text(), "ROL de propiedad"),
            (self.txt_prop_comuna.text(), "Comuna de propiedad")
        ]
        
        

        campos_obligatorios += [
                (self.txt_arren_nombre.text(), "Nombre del arrendador"),
                (self.txt_arren_rut.text(), "RUT del arrendador"),
                (self.txt_arrendatario_nombre.text(), "Nombre del arrendatario"),
                (self.txt_arrendatario_rut.text(), "RUT del arrendatario"),
        ]


        for valor, nombre in campos_obligatorios:
            if not valor.strip():
                QMessageBox.warning(self, "Campo obligatorio", f"El campo {nombre} es obligatorio")
                return False
        
        # Validar RUTs
        
        if not self.validar_rut(self.txt_arren_rut.text()):
            QMessageBox.warning(self, "RUT inválido", "El RUT del arrendador no es válido")
            return False
            
        if not self.validar_rut(self.txt_arrendatario_rut.text()):
            QMessageBox.warning(self, "RUT inválido", "El RUT del arrendatario no es válido")
            return False
    