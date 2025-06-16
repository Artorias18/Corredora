from PySide6.QtWidgets import QMainWindow,QHBoxLayout,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from services.database import obtener_ventas_resumen, obtener_detalle_venta, asignar_porcentajes_herencia, guardar_venta, asignar_porcentajes_herencia_testada
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIntValidator
from gui.usuarlo_actual import UsuarioActual
from services.supabase_client import supabase



class DetalleVentaWindow(QWidget):
    def __init__(self, venta_id, rol):
        super().__init__()
        self.rol = rol 
        self.setWindowTitle("Detalle de Venta")
        self.setMinimumSize(800, 600)
        
        # Crear scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Widget contenido
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Obtener datos
        detalle = obtener_detalle_venta(venta_id)
        
        # Mapeo de nombres amigables
        names = {
            "id": "ID",
            "comprador_nombre": "Nombre Comprador",
            "comprador_rut": "RUT Comprador",
            "comprador_direccion": "Dirección Comprador",
            "comprador_telefono": "Teléfono Comprador",
            "comprador_correo_electronico": "Correo Electrónico Comprador",
            "comprador_banco": "Banco Comprador",
            "comprador_tipo_cuenta": "Tipo Cuenta Comprador",
            "comprador_nro_cuenta": "Número Cuenta Comprador",
            "comprador_poder_judicial": "Poder Judicial Comprador",
            "vendedor_nombre": "Nombre Vendedor",
            "vendedor_rut": "RUT Vendedor",
            "vendedor_direccion": "Dirección Vendedor",
            "vendedor_telefono": "Teléfono Vendedor",
            "vendedor_correo_electronico": "Correo Electrónico Vendedor",
            "vendedor_banco": "Banco Vendedor",
            "vendedor_tipo_cuenta": "Tipo Cuenta Vendedor",
            "vendedor_nro_cuenta": "Número Cuenta Vendedor",
            "vendedor_poder_judicial": "Poder Judicial Vendedor",
            "vendedor_posesion_efectiva": "Posesión Efectiva Vendedor",
            "propiedad_direccion": "Dirección Propiedad",
            "propiedad_rol": "ROL Propiedad",
            "propiedad_comuna": "Comuna Propiedad",
            "propiedad_estudio_titulos": "Estudio de Títulos",
            "propiedad_inscripcion": "Inscripción",
            "propiedad_dominio_vigente": "Dominio Vigente",
            "propiedad_hipoteca": "Hipoteca",
            "propiedad_gravamen": "Gravamen",
            "propiedad_certificado_numero": "Certificado Número",
            "propiedad_aseo": "Aseo",
            "propiedad_no_expropiacion": "No Expropiación",
            "fecha_venta": "Fecha de Venta",
            "monto_venta": "Monto Venta",
            "observaciones": "Observaciones",
            "estado_venta": "Estado Venta",
            "tipo_venta": "Tipo Venta",
            "limitaciones_dominio": "Limitaciones Dominio",
            "viabilidad_vendedor": "Viabilidad Vendedor",
            "superficie": "Superficie",
            "edificada": "Edificada",
            "recepcion": "Recepción"
        }
        
        if detalle:
            # Agrupar campos por secciones
            sections = {
                "Información General": [
                    "id", "fecha_venta", "monto_venta", "observaciones",
                    "estado_venta", "tipo_venta"
                ],
                "Comprador": [
                    "comprador_nombre", "comprador_rut", "comprador_direccion",
                    "comprador_telefono", "comprador_correo_electronico",
                    "comprador_banco", "comprador_tipo_cuenta", "comprador_nro_cuenta",
                    "comprador_poder_judicial"
                ],
                "Vendedor": [
                    "vendedor_nombre", "vendedor_rut", "vendedor_direccion",
                    "vendedor_telefono", "vendedor_correo_electronico",
                    "vendedor_banco", "vendedor_tipo_cuenta", "vendedor_nro_cuenta",
                    "vendedor_poder_judicial", "vendedor_posesion_efectiva"
                ],
                "Propiedad": [
                    "propiedad_direccion", "propiedad_rol", "propiedad_comuna",
                    "propiedad_estudio_titulos", "propiedad_inscripcion",
                    "propiedad_dominio_vigente", "propiedad_hipoteca",
                    "propiedad_gravamen", "propiedad_certificado_numero",
                    "propiedad_aseo", "propiedad_no_expropiacion"
                ],
                "Documentación": [
                    "limitaciones_dominio", "viabilidad_vendedor",
                    "superficie", "edificada", "recepcion"
                ]
            }
            
            for section, fields in sections.items():
                # Añadir título de sección
                section_label = QLabel(f"<h3>{section}</h3>")
                layout.addWidget(section_label)
                
                # Añadir campos de la sección
                for field in fields:
                    if field in detalle and (self.rol.lower() in ("superusuario", "admin") or field != "monto_venta"):
                        show_name = names.get(field, field)
                        value = detalle[field]
                        
                        # Formatear valores booleanos
                        if isinstance(value, bool):
                            value = "Sí" if value else "No"
                        elif value is None:
                            value = "No especificado"
                            
                        field_layout = QHBoxLayout()
                        field_layout.addWidget(QLabel(f"{show_name}:"), stretch=1)
                        field_layout.addWidget(QLabel(str(value)), stretch=2)
                        layout.addLayout(field_layout)
                
                # Añadir separador
                layout.addWidget(QFrame(frameShape=QFrame.HLine))
        
        scroll.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

class DashboardVentas(QMainWindow):
    def __init__(self, rol, parent=None):
        super().__init__(parent)
        self.rol = rol
        self.setWindowTitle("Ventas")
        self.resize(1200, 800)
        
        # Widget central y layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Barra de búsqueda y filtros
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar...")
        self.search_input.textChanged.connect(self.filtrar_ventas)
        
        # Filtro por fecha
        self.date_filter = QComboBox()
        self.date_filter.addItems(["Todas las fechas", "Últimos 7 días", "Últimos 30 días", "Este año"])
        self.date_filter.currentIndexChanged.connect(self.filtrar_ventas)
        
        filter_layout.addWidget(QLabel("Filtros:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.date_filter)
        main_layout.addLayout(filter_layout)
        
        # Configurar la tabla
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Comprador", "Vendedor", "Propiedad", "Fecha"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.itemDoubleClicked.connect(self.mostrar_detalle_venta)
        
        # Botones
        button_layout = QHBoxLayout()
        self.boton_agregar = QPushButton("Agregar Venta")
        self.boton_agregar.clicked.connect(self.abrir_ventana_agregar_venta)
        
        self.boton_exportar = QPushButton("Exportar a Excel")
        self.boton_exportar.clicked.connect(self.exportar_a_excel)
        
        if self.rol.lower() in ("superusuario", "admin"):
            self.boton_eliminar = QPushButton("Eliminar Venta")
            self.boton_eliminar.clicked.connect(self.eliminar_venta)
            button_layout.addWidget(self.boton_eliminar)
        
        button_layout.addWidget(self.boton_agregar)
        button_layout.addWidget(self.boton_exportar)
        
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)
        
        self.cargar_ventas()
    
    def abrir_ventana_agregar_venta(self):
        self.ventana_agregar = VentanaAgregarVenta()
        self.ventana_agregar.venta_guardada.connect(self.cargar_ventas)  # recargar al cerrar
        self.ventana_agregar.show()

    def get_user_role(self,user_id):

        response = supabase.table('usuarios').select('rol').eq('id',user_id).execute()

        if response.data:
            rol = response.data[0]['rol']
            UsuarioActual.id = user_id
            UsuarioActual.rol = rol
            self.message_label.setText(f"Rol: {rol}")
            self.redirect_to_dashboard(rol)
        else:
            self.message_label.setText("Usuario no encontrado en la base de datos")

    def cargar_ventas(self):
        self.table.setRowCount(0)
        ventas = obtener_ventas_resumen()
        
        if ventas:
            self.table.setRowCount(len(ventas))
            for row, venta in enumerate(ventas):
                self.table.setItem(row, 0, QTableWidgetItem(str(venta["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(venta["comprador"]))
                self.table.setItem(row, 2, QTableWidgetItem(venta["vendedor"]))
                self.table.setItem(row, 3, QTableWidgetItem(venta["propiedad"]))
                self.table.setItem(row, 4, QTableWidgetItem(str(venta["fecha_venta"])))
        
        # Ajustar columnas
        self.table.resizeColumnsToContents()
    def mostrar_detalle_venta(self, item):
        row = item.row()
        venta_id = int(self.table.item(row, 0).text())
        self.detalle_window = DetalleVentaWindow(venta_id, self.rol)
        self.detalle_window.show()


        
    def filtrar_ventas(self):
        text = self.search_input.text().lower()
        date_filter = self.date_filter.currentText()
        
        for row in range(self.table.rowCount()):
            match_text = False
            match_date = True
            
            # Filtrar por texto
            if text:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and text in item.text().lower():
                        match_text = True
                        break
            else:
                match_text = True
            
            # Filtrar por fecha
            if date_filter != "Todas las fechas":
                date_item = self.table.item(row, 5)  # Columna de fecha
                if date_item:
                    venta_date = QDate.fromString(date_item.text(), "yyyy-MM-dd")
                    today = QDate.currentDate()
                    
                    if date_filter == "Últimos 7 días" and venta_date.daysTo(today) > 7:
                        match_date = False
                    elif date_filter == "Últimos 30 días" and venta_date.daysTo(today) > 30:
                        match_date = False
                    elif date_filter == "Este año" and venta_date.year() != today.year():
                        match_date = False
            
            self.table.setRowHidden(row, not (match_text and match_date))
    
    def exportar_a_excel(self):
        # Implementar exportación a Excel
        pass
    
    def eliminar_venta(self):
        # Implementar eliminación segura
        pass
    
    


class VentanaAgregarVenta(QWidget):
    venta_guardada = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agregar Venta")
        self.resize(800, 600)

        layout_principal = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout_principal.addWidget(scroll_area)

        contenido = QWidget()
        scroll_area.setWidget(contenido)
        layout_contenido = QVBoxLayout(contenido)

        self.formulario = QFormLayout()
        layout_contenido.addLayout(self.formulario)

        # === Comprador ===
        self.comprador_nombre = QLineEdit()
        self.comprador_rut = QLineEdit()
        self.comprador_direccion = QLineEdit()
        self.comprador_telefono = QLineEdit()
        self.comprador_correo = QLineEdit()
        self.comprador_banco = QLineEdit()
        self.comprador_tipo_cuenta = QLineEdit()
        self.comprador_nro_cuenta = QLineEdit()
        self.comprador_nro_cuenta.setValidator(QIntValidator())
        self.comprador_poder_judicial = QComboBox()
        self.comprador_poder_judicial.addItems(["Si", "No"])

        self.formulario.addRow("Nombre Comprador:", self.comprador_nombre)
        self.formulario.addRow("RUT Comprador:", self.comprador_rut)
        self.formulario.addRow("Dirección Comprador:", self.comprador_direccion)
        self.formulario.addRow("Teléfono Comprador:", self.comprador_telefono)
        self.formulario.addRow("Correo Comprador:", self.comprador_correo)
        self.formulario.addRow("Poder Judicial:", self.comprador_poder_judicial)
        self.formulario.addRow("Banco:", self.comprador_banco)
        self.formulario.addRow("Tipo de Cuenta:", self.comprador_tipo_cuenta)
        self.formulario.addRow("Numero de Cuenta:", self.comprador_nro_cuenta)

        # === Vendedor ===
        self.vendedor_nombre = QLineEdit()
        self.vendedor_rut = QLineEdit()
        self.vendedor_direccion = QLineEdit()
        self.vendedor_telefono = QLineEdit()
        self.vendedor_correo = QLineEdit()
        self.vendedor_banco = QLineEdit()
        self.vendedor_tipo_cuenta = QLineEdit()
        self.vendedor_nro_cuenta = QLineEdit()
        self.vendedor_nro_cuenta.setValidator(QIntValidator())

        self.formulario.addRow("Nombre Vendedor:", self.vendedor_nombre)
        self.formulario.addRow("RUT Vendedor:", self.vendedor_rut)
        self.formulario.addRow("Dirección Vendedor:", self.vendedor_direccion)
        self.formulario.addRow("Teléfono Vendedor:", self.vendedor_telefono)
        self.formulario.addRow("Correo Vendedor:", self.vendedor_correo)
        self.formulario.addRow("Banco:", self.vendedor_banco)
        self.formulario.addRow("Tipo de Cuenta:", self.vendedor_tipo_cuenta)
        self.formulario.addRow("Numero de Cuenta:", self.vendedor_nro_cuenta)

        # === Propiedad ===
        self.propiedad_codigo = QLineEdit()
        self.propiedad_direccion = QLineEdit()
        self.propiedad_rol = QLineEdit()
        self.propiedad_comuna = QLineEdit()

        # Campos documentales de propiedad con combobox
        self.estudio_titulos = QComboBox()
        self.estudio_titulos.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.inscripcion = QComboBox()
        self.inscripcion.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.dominio_vigente = QComboBox()
        self.dominio_vigente.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.hipoteca = QComboBox()
        self.hipoteca.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.gravamen = QComboBox()
        self.gravamen.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.certificado_numero = QComboBox()
        self.certificado_numero.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.aseo = QComboBox()
        self.aseo.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.no_expropiacion = QComboBox()
        self.no_expropiacion.addItems(["Si Posee Documento", "No Posee Documento"])

        self.superficie = QComboBox()
        self.superficie.addItems(["Si Posee Documento", "No Posee Documento"])

        self.edificada = QComboBox()
        self.edificada.addItems(["Si Posee Documento", "No Posee Documento"])

        self.recepcion = QComboBox()
        self.recepcion.addItems(["Si Posee Documento", "No Posee Documento"])

        self.formulario.addRow("Código Propiedad:", self.propiedad_codigo)
        self.formulario.addRow("Dirección Propiedad:", self.propiedad_direccion)
        self.formulario.addRow("Rol Propiedad:", self.propiedad_rol)
        self.formulario.addRow("Comuna Propiedad:", self.propiedad_comuna)
        
        # Agregar campos documentales al formulario
        self.formulario.addRow("Estudio de Títulos:", self.estudio_titulos)
        self.formulario.addRow("Inscripción:", self.inscripcion)
        self.formulario.addRow("Dominio Vigente:", self.dominio_vigente)
        self.formulario.addRow("Hipoteca:", self.hipoteca)
        self.formulario.addRow("Gravamen:", self.gravamen)
        self.formulario.addRow("Certificado Número:", self.certificado_numero)
        self.formulario.addRow("Aseo:", self.aseo)
        self.formulario.addRow("No Expropiación:", self.no_expropiacion)
        self.formulario.addRow("Prop Superficie:", self.superficie)
        self.formulario.addRow("Prop Edificada:", self.edificada)
        self.formulario.addRow("Prop Recepcion:", self.recepcion)

        # === Venta ===
        self.fecha_venta = QDateEdit(QDate.currentDate())
        self.fecha_venta.setCalendarPopup(True)
        self.monto_venta = QLineEdit()
        self.observaciones = QLineEdit()

        self.tipo_venta = QComboBox()
        self.tipo_venta.addItems(["Efectivo", "Posesión Efectiva", "Subsidio", "Credito H.", "Credito H. + Subsidio"])
        self.tipo_venta.currentTextChanged.connect(self.verificar_posesion)

        self.estado_venta = QComboBox()
        self.estado_venta.addItems(["Negociandose", "Cerrada Verbalmente", "Cerrada en Notaria", "Inscrita"])
        
        self.propiedad_ofrecida = QComboBox()
        self.propiedad_ofrecida.addItems(["Si", "No"])
        
        self.regularizaciones = QComboBox()
        self.regularizaciones.addItems(["Si", "No"])
        
        self.limitaciones = QComboBox()
        self.limitaciones.addItems(["Si", "No"])
        
        self.viabilidad = QLineEdit()

        self.formulario.addRow("Fecha Venta:", self.fecha_venta)
        self.formulario.addRow("Monto Venta:", self.monto_venta)
        self.formulario.addRow("Observaciones:", self.observaciones)
        self.formulario.addRow("Tipo Venta:", self.tipo_venta)
        self.formulario.addRow("Estado Venta:", self.estado_venta)
        self.formulario.addRow("Propiedad Ofrecida:", self.propiedad_ofrecida)
        self.formulario.addRow("Regularizaciones:", self.regularizaciones)
        self.formulario.addRow("Limitaciones Dominio:", self.limitaciones)
        self.formulario.addRow("Viabilidad Vendedor:", self.viabilidad)

        # === Sección Posesión Efectiva ===

        self.seccion_posesion = QWidget()
        self.seccion_posesion.setVisible(False)
        self.posesion_layout = QFormLayout(self.seccion_posesion)

        self.tipo_posesion = QComboBox()
        self.tipo_posesion.addItems(["Testada", "Intestada"])
        self.tipo_posesion.currentTextChanged.connect(self.actualizar_herederos)

        self.estado_proceso = QLineEdit()
        self.canal = QLineEdit()
        self.obs_posesion = QLineEdit()

        self.posesion_layout.addRow("Tipo Posesión:", self.tipo_posesion)
        self.posesion_layout.addRow("Estado Proceso:", self.estado_proceso)
        self.posesion_layout.addRow("Canal:", self.canal)
        self.posesion_layout.addRow("Observaciones Posesión:", self.obs_posesion)
        layout_contenido.addWidget(self.seccion_posesion)

        # === Herederos ===
        self.tabla_herederos = QTableWidget(0, 3)
        self.tabla_herederos.setHorizontalHeaderLabels(["Nombre", "RUT", "Tipo Heredero"])
        self.tabla_herederos.setVisible(False)
        layout_contenido.addWidget(self.tabla_herederos)

        self.boton_agregar_heredero = QPushButton("Agregar Heredero")
        self.boton_agregar_heredero.clicked.connect(self.agregar_heredero)
        self.boton_agregar_heredero.setVisible(False)
        layout_contenido.addWidget(self.boton_agregar_heredero)

        # === Botón Guardar ===
        self.boton_guardar = QPushButton("Guardar Venta")
        self.boton_guardar.clicked.connect(self.guardar_venta)
        layout_contenido.addWidget(self.boton_guardar)

    def verificar_posesion(self, texto):
        self.seccion_posesion.setVisible(texto == "Posesión Efectiva")
        self.actualizar_herederos()

    def actualizar_herederos(self):
        mostrar = self.tipo_venta.currentText() == "Posesión Efectiva"
        self.tabla_herederos.setVisible(mostrar)
        self.boton_agregar_heredero.setVisible(mostrar)

        if mostrar:
            # Cambiar los encabezados si es testada
            if self.tipo_posesion.currentText() == "Testada":
                self.tabla_herederos.setColumnCount(5)
                self.tabla_herederos.setHorizontalHeaderLabels(["Nombre", "RUT", "Tipo Heredero","¿Recibe Mejora?", "% Libre Disposición"])
            else:
                self.tabla_herederos.setColumnCount(3)
                self.tabla_herederos.setHorizontalHeaderLabels(["Nombre", "RUT", "Tipo Herdero"])

    def agregar_heredero(self):
        fila = self.tabla_herederos.rowCount()
        self.tabla_herederos.insertRow(fila)
        for col in range(2):
            self.tabla_herederos.setItem(fila, col, QTableWidgetItem(""))

        combo = QComboBox()
        if self.tipo_posesion.currentText() == "Testada":
                # Columna 3: ¿Recibe Mejora?
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            self.tabla_herederos.setItem(fila, 3, checkbox_item)

            # Columna 4: % Libre Disposición
            self.tabla_herederos.setItem(fila, 4, QTableWidgetItem("0"))
            combo.addItems(["forzoso", "conyugue", "hijo", "padre"])
        else:
            combo.addItems(["conyugue", "hijo", "padre","fisco","otro"])

        self.tabla_herederos.setCellWidget(fila, 2, combo)

    def guardar_venta(self):
        comprador = {
            'nombre': self.comprador_nombre.text(),
            'rut': self.comprador_rut.text(),
            'direccion': self.comprador_direccion.text(),
            'telefono': self.comprador_telefono.text(),
            'correo': self.comprador_correo.text(),
            'banco':self.comprador_banco.text(),
            'tipo_cuenta':self.comprador_tipo_cuenta.text(),
            'nro_cuenta':self.comprador_nro_cuenta.text(),
            'poder_judicial': self.comprador_poder_judicial.currentText()
        }
        
        vendedor = {
            'nombre': self.vendedor_nombre.text(),
            'rut': self.vendedor_rut.text(),
            'direccion': self.vendedor_direccion.text(),
            'telefono': self.vendedor_telefono.text(),
            'correo': self.vendedor_correo.text(),
            'banco':self.vendedor_banco.text(),
            'tipo_cuenta':self.vendedor_tipo_cuenta.text(),
            'nro_cuenta':self.vendedor_nro_cuenta.text(),

        }
        
        propiedad = {
            'codigo': self.propiedad_codigo.text(),
            'direccion': self.propiedad_direccion.text(),
            'rol': self.propiedad_rol.text(),
            'comuna': self.propiedad_comuna.text(),
            'estudio_titulos': self.estudio_titulos.currentText(),
            'inscripcion': self.inscripcion.currentText(),
            'dominio_vigente': self.dominio_vigente.currentText(),
            'hipoteca': self.hipoteca.currentText(),
            'gravamen': self.gravamen.currentText(),
            'certificado_numero': self.certificado_numero.currentText(),
            'aseo': self.aseo.currentText(),
            'no_expropiacion': self.no_expropiacion.currentText()
        }

        # recepcion_definitiva = {
        #     'codigo_interno': self.propiedad_ofrecida.currentText(),
        #     'superficie': self.superficie.currentText(),
        #     'edificada': self.edificada.currentText(),
        #     'recepcion': self.recepcion.currentText()
        # }
        
        venta = {
            'fecha_venta': self.fecha_venta.date().toString("yyyy-MM-dd"),
            'monto_venta': self.monto_venta.text(),
            'observaciones': self.observaciones.text(),
            'tipo_venta': self.tipo_venta.currentText(),
            'estado_venta': self.estado_venta.currentText().lower(),
            'propiedad_ofrecida': self.propiedad_ofrecida.currentText(),
            'regularizaciones': self.regularizaciones.currentText(),
            'limitaciones': self.limitaciones.currentText(),
            'viabilidad': self.viabilidad.text()
        }

        data_venta = {
            'comprador': comprador,
            'vendedor': vendedor,
            'propiedad': propiedad,
            # 'recepcion_definitiva':recepcion_definitiva,
            'venta': venta
        }
        posesion_efectiva = None
        herederos = []
        
        mejoras = []
        libre_disposicion = {}

        if self.tipo_venta.currentText() == "Posesión Efectiva":
            posesion_efectiva = {
                'tipo': self.tipo_posesion.currentText(),
                'estado_proceso': self.estado_proceso.text(),
                'canal': self.canal.text(),
                'observaciones': self.obs_posesion.text()
            }

            for row in range(self.tabla_herederos.rowCount()):
                heredero = {
                    'nombre': self.tabla_herederos.item(row, 0).text(),
                    'rut': self.tabla_herederos.item(row, 1).text(),
                    'tipo_heredero': self.tabla_herederos.cellWidget(row, 2).currentText() if self.tabla_herederos.cellWidget(row, 2) else "",
                }

                if self.tipo_posesion.currentText() == "Testada":
                    mejora_item = self.tabla_herederos.item(row, 3)
                    libre_item = self.tabla_herederos.item(row, 4)

                    if mejora_item is not None and mejora_item.checkState() == Qt.Checked:
                        mejoras.append(heredero["rut"])

                    if libre_item is not None:
                        try:
                            porcentaje_libre = float(libre_item.text())
                        except ValueError:
                            porcentaje_libre = 0
                        libre_disposicion[heredero["rut"]] = porcentaje_libre



                herederos.append(heredero)

        if not comprador['nombre'] or not vendedor['nombre'] or not propiedad['codigo']:
            QMessageBox.warning(self, "Error", "Faltan datos obligatorios.")
            return

        try:
            print("Mejoras:", mejoras)
            print("Libre disposición:", libre_disposicion, "Total:",
            sum(libre_disposicion.values()))
            venta_id = guardar_venta(data_venta, posesion_efectiva, herederos, mejoras, libre_disposicion)
            if venta_id:
                if self.tipo_venta.currentText() == "Posesión Efectiva":
                    if self.tipo_posesion.currentText() == "Intestada":
                        asignar_porcentajes_herencia(herederos)
                    elif self.tipo_posesion.currentText() == "Testada":
                        asignar_porcentajes_herencia_testada(herederos, mejoras, libre_disposicion)

                QMessageBox.information(self, "Éxito", "Venta guardada con éxito.")
                self.venta_guardada.emit()
                self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error: {str(e)}")
