from PySide6.QtWidgets import QHeaderView, QFileDialog, QMainWindow,QHBoxLayout,QTextEdit,QTabWidget,QDoubleSpinBox,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from services.arriendos_service import obtener_arriendos_resumen, obtener_detalle_arriendo,obtener_arriendos_por_estado, guardar_arriendo
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
            "Estado",
            "Tipo de contrato"
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

            if estado_filtro == "Todos los arriendos":
                arriendos = obtener_arriendos_resumen()
            else:
                arriendos = obtener_arriendos_por_estado(estado_filtro)
 

            
            if arriendos:
                self.tabla_arriendos.setRowCount(len(arriendos))
                self.arriendos = arriendos or []
            

                self.tabla_arriendos.setUpdatesEnabled(False)  # 🔸 Pausa el renderizado de la tabla
            try:
                for row, arriendo in enumerate(arriendos):
                    self.tabla_arriendos.setItem(row, 0, QTableWidgetItem(str(arriendo.get("id", ""))))
                    self.tabla_arriendos.setItem(row, 1, QTableWidgetItem(arriendo.get("arrendador", "")))
                    self.tabla_arriendos.setItem(row, 2, QTableWidgetItem(arriendo.get("arrendatario", "")))
                    self.tabla_arriendos.setItem(row, 3, QTableWidgetItem(arriendo.get("propiedad", "")))
                    self.tabla_arriendos.setItem(row, 4,QTableWidgetItem(str(arriendo.get("estado", ""))))
                    self.tabla_arriendos.setItem(row, 5, QTableWidgetItem(arriendo.get("tipo_contrato", "")))
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

        self.tbl_evaluacion = QTableWidget()
        self.tbl_evaluacion.setRowCount(9)
        self.tbl_evaluacion.setColumnCount(4)

        # Tamaño mínimo más grande
        self.tbl_evaluacion.setMinimumWidth(700)
        self.tbl_evaluacion.setMinimumHeight(300)

        # Encabezados
        self.tbl_evaluacion.setHorizontalHeaderLabels([
            "Concepto", "Mes 1", "Mes 2", "Mes 3"
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

        # Añadir tabla al contenedor centrado
        contenedor_layout.addWidget(self.tbl_evaluacion)

        botones_layout = QHBoxLayout()
        botones_layout.setAlignment(Qt.AlignCenter)

        self.btn_mes1 = QPushButton("Ingresar Mes 1")
        self.btn_mes2 = QPushButton("Ingresar Mes 2")
        self.btn_mes3 = QPushButton("Ingresar Mes 3")

        self.btn_mes1.clicked.connect(lambda: self.abrir_formulario_mes(1))
        self.btn_mes2.clicked.connect(lambda: self.abrir_formulario_mes(2))
        self.btn_mes3.clicked.connect(lambda: self.abrir_formulario_mes(3))

        botones_layout.addWidget(self.btn_mes1)
        botones_layout.addWidget(self.btn_mes2)
        botones_layout.addWidget(self.btn_mes3)

        contenedor_layout.addLayout(botones_layout)

        # Agregar contenedor al layout final
        layout.addRow(contenedor)


    def abrir_formulario_mes(self, mes):
        dlg = FormularioMes(mes, self)

        if dlg.exec():
            resultado = dlg.resultado_final   # ← ya trae todo

            datos = resultado["datos"]
            calculos = resultado["calculos"]

            # Guardas lo que quieras
            self.evaluacion_meses[mes] = datos

            # Rellenas la tabla usando los cálculos
            resultados_completos = {**datos, **calculos}

            self.actualizar_tabla_evaluacion(mes, resultados_completos)


    def actualizar_tabla_evaluacion(self, mes, resultados):
        col = mes  

        print("CALCULOS MES:", resultados)

        mapping = [
            ("sueldo_base", 0),
            ("gratificacion", 1),
            ("th_imponibles", 2),
            ("locomocion", 3),
            ("th_no_imponibles", 4),
            ("descuentos_legales", 5),
            ("descuentos_varios", 6),
            ("anticipo", 7),
            ("liquido", 8)
        ]

        for clave, fila in mapping:
            valor = resultados.get(clave, 0)
            item = QTableWidgetItem(f"{valor:,.0f}")
            item.setTextAlignment(Qt.AlignCenter)
            self.tbl_evaluacion.setItem(fila, col, item)

    
    def obtener_diccionario_evaluacion(self):
        col = self.tbl_evaluacion.columnCount() - 1

        mapping = [
            "sueldo_base",
            "gratificacion",
            "total_imponible",
            "locomocion",
            "total_no_imponible",
            "descuentos_legales",
            "desc_varios",
            "anticipo",
            "liquido_pago"
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

        self.cmb_cuenta_fm = QComboBox()
        self.cmb_cuenta_fm.addItems(["1","2","3","4"])

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
        layout.addRow(self.crear_label("Cuenta FM"), self.cmb_cuenta_fm)
        layout.addRow(self.crear_label("Observaciones"), self.txt_observaciones)

        



    

        





    def cargar_datos_arriendo(self, arriendo_id):
        pass


    def guardar_arriendo(self):
        try:
            valores_tabla = self.obtener_diccionario_evaluacion()

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
                    'tipo_trabajador': self.cmb_tipo_trabajador.currentText(),
                    'dicom': self.cmb_dicom.currentText(),
                    'comentarios': self.txt_comentarios.toPlainText(),
                    'evaluacion_estado': self.cmb_evaluacion_estado.currentText(),
                    'antiguedad_laboral': self.txt_antiguedad_laboral.text(),
                    'fecha_evaluacion': self.fecha_evaluacion.date().toString("yyyy-MM-dd"),
                    'renta': self.txt_renta.text()

                },

                'evaluacion_arrendatario':{
                    'fecha_evaluacion': self.fecha_evaluacion_arrendatario.date().toString("yyyy-MM-dd"),
                    'sueldo_base': valores_tabla.get('sueldo_base', 0),
                    'gratificacion': valores_tabla.get('gratificacion', 0),
                    'total_imponible': valores_tabla.get('total_imponible', 0),
                    'total_no_imponible': valores_tabla.get('total_no_imponible', 0),
                    'descuentos_legales': valores_tabla.get('descuentos_legales', 0),
                    'liquido_pago': valores_tabla.get('liquido_pago', 0),
                    'anticipo': valores_tabla.get('anticipo', 0),
                    'desc_varios': valores_tabla.get('desc_varios', 0),
                    'locomocion': valores_tabla.get('locomocion', 0)



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
    

class FormularioMes(QDialog):
    def __init__(self, numero_mes, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Evaluación - Mes {numero_mes}")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        # ---- CAMPOS FIJOS ----
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
        form.addRow("Sueldo minimo:", self.sueldo_minimo)

        layout.addLayout(form)

        # ---- TABLA DE OTROS DESCUENTOS ----
        layout.addWidget(QLabel("Otros Descuentos:"))

        self.tbl_descuentos = QTableWidget()
        self.tbl_descuentos.setColumnCount(2)
        self.tbl_descuentos.setHorizontalHeaderLabels(["Concepto", "Monto"])
        self.tbl_descuentos.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.tbl_descuentos)

        # Botones para manejar descuentos
        btns = QHBoxLayout()
        btn_add = QPushButton("Agregar descuento")
        btn_del = QPushButton("Eliminar seleccionado")

        btn_add.clicked.connect(self.agregar_descuento)
        btn_del.clicked.connect(self.eliminar_descuento)

        btns.addWidget(btn_add)
        btns.addWidget(btn_del)

        layout.addLayout(btns)

        # Botones OK / Cancel
        botones = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_cancel = QPushButton("Cancelar")

        btn_ok.clicked.connect(self.aceptar)
        btn_cancel.clicked.connect(self.reject)

        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancel)

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