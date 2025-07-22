from PySide6.QtWidgets import QMainWindow,QHBoxLayout,QTextEdit,QTabWidget,QDoubleSpinBox,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from services.database import obtener_ventas_resumen, obtener_detalle_venta, asignar_porcentajes_herencia, guardar_venta, asignar_porcentajes_herencia_testada, actualizar_estado_venta, obtener_ventas_por_estado
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIntValidator, QColor, QDoubleValidator
from gui.usuarlo_actual import UsuarioActual
from services.supabase_client import supabase



class DetalleVentaWindow(QWidget):
    def __init__(self, venta_id, rol):
        super().__init__()
        self.venta_id = venta_id
        self.rol = rol
        self.setWindowTitle(f"Detalle de Venta #{venta_id}")
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
        self.detalle_venta = obtener_detalle_venta(venta_id)
        
        if not self.detalle_venta:
            layout_contenido.addWidget(QLabel("No se encontraron detalles para esta venta"))
            return
        
        # Mostrar información en pestañas
        self.tabs = QTabWidget()
        layout_contenido.addWidget(self.tabs)
        
        # Pestaña de información general
        self.setup_tab_info_general()
        
        # Pestaña de comprador
        self.setup_tab_comprador()
        
        # Pestaña de vendedor
        self.setup_tab_vendedor()
        
        # Pestaña de propiedad
        self.setup_tab_propiedad()
        
        # Pestaña de posesión efectiva (si aplica)
        if self.detalle_venta.get('venta', {}).get('tipo_venta') == 'Posesion Efectiva':
            self.setup_tab_pos_efectiva()
        
        # Botón para cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout_contenido.addWidget(btn_cerrar)
    
    def setup_tab_info_general(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Información General")
        layout = QFormLayout(tab)
        
        venta = self.detalle_venta.get('venta', {})
        
        # Campos de información general
        campos = [
            ("ID Venta", venta.get('id')),
            ("Fecha", venta.get('fecha_venta')),
            ("Monto", f"${venta.get('monto_venta', 0):,.0f}" if venta.get('monto_venta') else "No especificado"),
            ("Tipo de venta", venta.get('tipo_venta')),
            ("Estado", venta.get('estado_venta', '').capitalize()),
            ("Propiedad ofrecida", venta.get('propiedad_ofrecida')),
            ("Regularizaciones", venta.get('regularizaciones')),
            ("Observaciones", venta.get('observaciones'))
        ]
        
        for label, value in campos:
            if value:
                layout.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))
    
    def setup_tab_comprador(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Comprador")
        layout = QFormLayout(tab)
        
        comprador = self.detalle_venta.get('comprador', {})
        
        # Campos del comprador
        campos = [
            ("Nombre", comprador.get('nombre')),
            ("RUT", comprador.get('rut')),
            ("Dirección", comprador.get('direccion')),
            ("Teléfono", comprador.get('telefono')),
            ("Email", comprador.get('correo_electronico')),
            ("Banco", comprador.get('banco')),
            ("Tipo de cuenta", comprador.get('tipo_cuenta')),
            ("Número de cuenta", comprador.get('nro_cuenta')),
            ("Poder judicial", comprador.get('poder_judicial'))
        ]
        
        for label, value in campos:
            if value:
                layout.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))
    
    def setup_tab_vendedor(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Vendedor")
        layout = QFormLayout(tab)
        
        vendedor = self.detalle_venta.get('vendedor', {})
        
        # Campos del vendedor
        campos = [
            ("Nombre", vendedor.get('nombre')),
            ("RUT", vendedor.get('rut')),
            ("Dirección", vendedor.get('direccion')),
            ("Teléfono", vendedor.get('telefono')),
            ("Email", vendedor.get('correo_electronico')),
            ("Banco", vendedor.get('banco')),
            ("Tipo de cuenta", vendedor.get('tipo_cuenta')),
            ("Número de cuenta", vendedor.get('nro_cuenta')),
            ("Poder judicial", vendedor.get('poder_judicial')),
            ("Posesión efectiva", vendedor.get('posesion_efectiva'))
        ]
        
        for label, value in campos:
            if value:
                layout.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))
    
    def setup_tab_propiedad(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Propiedad")
        layout = QVBoxLayout(tab)
        
        propiedad = self.detalle_venta.get('propiedad', {})
        documentacion = self.detalle_venta.get('documentacion', {})
        
        # Información básica
        form_basica = QFormLayout()
        campos_basicos = [
            ("Código interno", propiedad.get('codigo_interno')),
            ("Dirección", propiedad.get('direccion')),
            ("ROL", propiedad.get('rol')),
            ("Comuna", propiedad.get('comuna'))
        ]
        
        for label, value in campos_basicos:
            if value:
                form_basica.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))
        
        layout.addLayout(form_basica)
        
        # Documentación
        layout.addWidget(QLabel("<b>Documentación:</b>"))
        
        form_doc = QFormLayout()
        campos_doc = [
            ("Estudio de títulos", propiedad.get('estudio_titulos')),
            ("Inscripción", propiedad.get('inscripcion')),
            ("Dominio vigente", propiedad.get('dominio_vigente')),
            ("Hipoteca", propiedad.get('hipoteca')),
            ("Gravamen", propiedad.get('gravamen')),
            ("Certificado número", propiedad.get('certificado_numero')),
            ("Aseo", propiedad.get('aseo')),
            ("No expropiación", propiedad.get('no_expropiacion')),
            ("Superficie", documentacion.get('superficie')),
            ("Edificada", documentacion.get('edificada')),
            ("Recepción", documentacion.get('recepcion'))
        ]
        
        for label, value in campos_doc:
            if value:
                form_doc.addRow(QLabel(f"{label}:"), QLabel(str(value)))
        
        layout.addLayout(form_doc)
    
    def setup_tab_pos_efectiva(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Posesión Efectiva")
        layout = QVBoxLayout(tab)
        
        # Obtener herederos de la venta
        herederos_response = supabase.table("herederos").select("*").eq("venta_id", self.venta_id).execute()
        herederos = herederos_response.data if herederos_response.data else []
        
        if not herederos:
            layout.addWidget(QLabel("No hay información de posesión efectiva disponible"))
            return
        
        # Información de posesión efectiva
        posesion_response = supabase.table("posesion_efectiva").select("*").eq("codigo_interno", self.detalle_venta['propiedad']['codigo_interno']).execute()
        posesion = posesion_response.data[0] if posesion_response.data else {}
        
        if posesion:
            form_pos = QFormLayout()
            campos_pos = [
                ("Tipo", posesion.get('tipo_posesion', '').capitalize()),
                ("Canal", posesion.get('canal', '').capitalize()),
                ("Estado del proceso", posesion.get('estado_proceso', '').capitalize())
            ]
            
            for label, value in campos_pos:
                form_pos.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))
            
            layout.addLayout(form_pos)
        
        # Tabla de herederos
        layout.addWidget(QLabel("<b>Herederos:</b>"))
        
        tabla = QTableWidget(len(herederos), 4)
        tabla.setHorizontalHeaderLabels(["Nombre", "RUT", "Tipo", "Porcentaje"])
        
        for row, heredero in enumerate(herederos):
            tabla.setItem(row, 0, QTableWidgetItem(heredero.get('nombre', '')))
            tabla.setItem(row, 1, QTableWidgetItem(heredero.get('rut', '')))
            tabla.setItem(row, 2, QTableWidgetItem(heredero.get('tipo_heredero', '').capitalize()))
            tabla.setItem(row, 3, QTableWidgetItem(f"{heredero.get('porcentaje', 0)}%"))
        
        tabla.resizeColumnsToContents()
        layout.addWidget(tabla)

class DashboardVentas(QMainWindow):
    def __init__(self, rol, parent=None):
        super().__init__(parent)
        self.rol = rol
        self.setWindowTitle("Gestión de Ventas")
        self.resize(1200, 800)
        self.cargando_tabla = False
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Barra de filtros
        filter_layout = QHBoxLayout()
        
        # Filtro de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por comprador, vendedor o propiedad...")
        self.search_input.textChanged.connect(self.filtrar_ventas)
        
        
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
        self.filtro_estado.currentIndexChanged.connect(self.filtrar_ventas)
        
        # Filtro de fecha
        self.filtro_fecha = QComboBox()
        self.filtro_fecha.addItems([
            "Todas las fechas",
            "Últimos 7 días",
            "Últimos 30 días",
            "Este mes",
            "Este año"
        ])
        self.filtro_fecha.currentIndexChanged.connect(self.filtrar_ventas)
        
        # Agregar filtros al layout
        filter_layout.addWidget(QLabel("Filtros:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Estado:"))
        filter_layout.addWidget(self.filtro_estado)
        filter_layout.addWidget(QLabel("Fecha:"))
        filter_layout.addWidget(self.filtro_fecha)
        
        main_layout.addLayout(filter_layout)
        
        # Tabla de ventas
        self.tabla_ventas = QTableWidget()
        self.tabla_ventas.setColumnCount(7)
        self.tabla_ventas.setHorizontalHeaderLabels([
            "ID", 
            "Comprador", 
            "Vendedor", 
            "Propiedad", 
            "Fecha", 
            "Estado",
            "Tipo"
        ])
        self.tabla_ventas.setSortingEnabled(True)
        self.tabla_ventas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_ventas.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tabla_ventas.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla_ventas.verticalHeader().setVisible(False)
        self.tabla_ventas.itemDoubleClicked.connect(self.mostrar_detalle_venta)
        self.tabla_ventas.itemChanged.connect(self.actualizar_estado_venta)
        
        main_layout.addWidget(self.tabla_ventas)
        
        # Barra de botones
        button_layout = QHBoxLayout()
        
        self.btn_agregar_proceso = QPushButton("Nueva Venta en Proceso")
        self.btn_agregar_proceso.clicked.connect(lambda: self.abrir_formulario_venta(en_proceso=True))
        
        self.btn_agregar_cerrada = QPushButton("Nueva Venta Cerrada")
        self.btn_agregar_cerrada.clicked.connect(lambda: self.abrir_formulario_venta(en_proceso=False))
        
        self.btn_actualizar = QPushButton("Actualizar Lista")
        self.btn_actualizar.clicked.connect(self.cargar_ventas)
        
        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.clicked.connect(self.exportar_a_excel)
        
        if self.rol.lower() in ("superusuario", "admin"):
            self.btn_editar_estado = QPushButton("Cambiar Estado")
            self.btn_editar_estado.clicked.connect(self.habilitar_edicion_estado)
            button_layout.addWidget(self.btn_editar_estado)
        
        button_layout.addWidget(self.btn_agregar_proceso)
        button_layout.addWidget(self.btn_agregar_cerrada)
        button_layout.addWidget(self.btn_actualizar)
        button_layout.addWidget(self.btn_exportar)
        
        main_layout.addLayout(button_layout)
        
        # Cargar datos iniciales
        self.cargar_ventas()
    
    def cargar_ventas(self):
        try:
            self.cargando_tabla = True
            # Desconectar signal para no disparar itemChanged mientras cargas
            try:
                self.tabla_ventas.itemChanged.disconnect(self.actualizar_estado_venta)
            except TypeError:
                pass  # Si no está conectado, ignora

            self.tabla_ventas.setRowCount(0)
            estado_filtro = self.filtro_estado.currentText()

            if estado_filtro == "Todas las ventas":
                ventas = obtener_ventas_resumen()
            else:
                ventas = obtener_ventas_por_estado(estado_filtro)

            if ventas:
                self.tabla_ventas.setRowCount(len(ventas))

                for row, venta in enumerate(ventas):
                    id_item = QTableWidgetItem(str(venta.get("id", "")))
                    comprador_item = QTableWidgetItem(venta.get("comprador", ""))
                    vendedor_item = QTableWidgetItem(venta.get("vendedor", ""))
                    propiedad_item = QTableWidgetItem(venta.get("propiedad", ""))
                    fecha_item = QTableWidgetItem(venta.get("fecha_venta", ""))
                    estado_item = QTableWidgetItem(venta.get("estado_venta", "").capitalize())
                    estado_item.setFlags(estado_item.flags() | Qt.ItemIsEditable)
                    tipo_item = QTableWidgetItem(venta.get("tipo_venta", ""))

                    self.tabla_ventas.setItem(row, 0, id_item)
                    self.tabla_ventas.setItem(row, 1, comprador_item)
                    self.tabla_ventas.setItem(row, 2, vendedor_item)
                    self.tabla_ventas.setItem(row, 3, propiedad_item)
                    self.tabla_ventas.setItem(row, 4, fecha_item)
                    self.tabla_ventas.setItem(row, 5, estado_item)
                    self.tabla_ventas.setItem(row, 6, tipo_item)

                self.tabla_ventas.resizeColumnsToContents()

            # Reconectar el signal cuando termines
            self.tabla_ventas.itemChanged.connect(self.actualizar_estado_venta)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las ventas: {str(e)}")

        finally:
            self.cargando_tabla = False

    

    
    def filtrar_ventas(self):
        texto = self.search_input.text().lower()
        estado = self.filtro_estado.currentText()
        fecha = self.filtro_fecha.currentText()
        
        for row in range(self.tabla_ventas.rowCount()):
            mostrar_fila = True
            
            # Filtrar por texto
            if texto:
                mostrar_fila = any(
                    texto in self.tabla_ventas.item(row, col).text().lower()
                    for col in range(self.tabla_ventas.columnCount())
                )
            
            # Filtrar por estado
            if mostrar_fila and estado != "Todas las ventas":
                estado_item = self.tabla_ventas.item(row, 5).text().lower()
                estado_filtro = estado.lower().replace(" ", "_")
                
                if estado == "En proceso":
                    mostrar_fila = estado_item == "en_proceso"
                elif estado == "Negociandose":
                    mostrar_fila = estado_item == "negociandose"
                elif estado == "Cerradas verbalmente":
                    mostrar_fila = estado_item == "cerrada verbalmente"
                elif estado == "Cerradas en notaría":
                    mostrar_fila = estado_item == "cerrada en notaria"
                elif estado == "Inscritas":
                    mostrar_fila = estado_item == "inscrita"
            
            # Filtrar por fecha
            if mostrar_fila and fecha != "Todas las fechas":
                fecha_item = self.tabla_ventas.item(row, 4).text()
                fecha_venta = QDate.fromString(fecha_item, "yyyy-MM-dd")
                hoy = QDate.currentDate()
                
                if fecha == "Últimos 7 días":
                    mostrar_fila = fecha_venta.daysTo(hoy) <= 7
                elif fecha == "Últimos 30 días":
                    mostrar_fila = fecha_venta.daysTo(hoy) <= 30
                elif fecha == "Este mes":
                    mostrar_fila = fecha_venta.month() == hoy.month() and fecha_venta.year() == hoy.year()
                elif fecha == "Este año":
                    mostrar_fila = fecha_venta.year() == hoy.year()
            
            self.tabla_ventas.setRowHidden(row, not mostrar_fila)
    
    def abrir_formulario_venta(self, en_proceso=False):
        self.formulario_venta = FormularioVenta(en_proceso=en_proceso)
        self.formulario_venta.venta_guardada.connect(self.cargar_ventas)
        self.formulario_venta.show()
    
    def mostrar_detalle_venta(self, item):
        if item.column()==5:
            return
        venta_id = int(self.tabla_ventas.item(item.row(), 0).text())
        self.ventana_detalle = DetalleVentaWindow(venta_id, self.rol)
        self.ventana_detalle.show()
    
    def habilitar_edicion_estado(self):
    # Habilitar edición solo en la columna de estado
        for row in range(self.tabla_ventas.rowCount()):
            item = self.tabla_ventas.item(row, 5)
            if item:
                item.setFlags(item.flags() | Qt.ItemIsEditable)
        
        # try:
        #     self.tabla_ventas.itemChanged.disconnect(self.actualizar_estado_venta)
        # except TypeError:
        #     pass  # No estaba conectada, no pasa nada

        # self.tabla_ventas.itemChanged.connect(self.actualizar_estado_venta)

        QMessageBox.information(self, "Edición", "Puede editar el estado directamente en la tabla")

    
    def actualizar_estado_venta(self, item):
        if self.cargando_tabla:
            return  # Ignorar cambios que ocurren mientras se carga la tabla

        if item.column() != 5:
            return  # Solo procesar cambios en la columna Estado

        venta_id = int(self.tabla_ventas.item(item.row(), 0).text())
        nuevo_estado = item.text().lower()
        print(f"Intentando actualizar venta_id={venta_id} con estado={nuevo_estado}")

        try:
            resultado = actualizar_estado_venta(venta_id, nuevo_estado)
            print(f"Resultado actualización: {resultado}")
            if resultado:
                item.setText(nuevo_estado.capitalize())
            else:
                print("No se pudo actualizar el estado en la base de datos.")
        except Exception as e:
            print(f"Error en actualizar_estado_venta: {str(e)}")
            QMessageBox.warning(self, "Error", f"No se pudo actualizar el estado: {str(e)}")
            self.cargar_ventas()  # Recargar para revertir cambios



    
    def exportar_a_excel(self):
        # Implementar exportación a Excel
        pass

    def eliminar_venta(self):
        # Implementar eliminación segura
        pass

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

    
    


class FormularioVenta(QWidget):
    venta_guardada = Signal()
    
    def __init__(self, en_proceso=False, parent=None):
        super().__init__(parent)
        self.en_proceso = en_proceso
        self.setWindowTitle("Nueva Venta en Proceso" if en_proceso else "Nueva Venta Cerrada")
        self.resize(900, 700)
        
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
        
        # Pestaña de información básica
        tab_basica = QWidget()
        self.tabs.addTab(tab_basica, "Información Básica")
        self.setup_tab_basica(tab_basica)
        
        # Pestaña de comprador
        tab_comprador = QWidget()
        self.tabs.addTab(tab_comprador, "Comprador")
        self.setup_tab_comprador(tab_comprador)
        
        # Pestaña de vendedor
        tab_vendedor = QWidget()
        self.tabs.addTab(tab_vendedor, "Vendedor")
        self.setup_tab_vendedor(tab_vendedor)
        
        # Pestaña de propiedad
        tab_propiedad = QWidget()
        self.tabs.addTab(tab_propiedad, "Propiedad")
        self.setup_tab_propiedad(tab_propiedad)
        
        # Pestaña de posesión efectiva (solo para ventas cerradas)
        if not en_proceso:
            tab_pos_efectiva = QWidget()
            self.tabs.addTab(tab_pos_efectiva, "Posesión Efectiva")
            self.setup_tab_pos_efectiva(tab_pos_efectiva)
            index = self.tabs.indexOf(tab_pos_efectiva)
            self.tabs.setTabVisible(index, False)
            self.tab_pos_efectiva_index = index  
        
        # Botón de guardar
        btn_guardar = QPushButton("Guardar Venta")
        btn_guardar.clicked.connect(self.guardar_venta)
        layout_form.addWidget(btn_guardar)
        
        # Estilo para campos obligatorios
        self.setStyleSheet("""
            QLabel[obligatorio="true"] {
                font-weight: bold;
                color: #FF0000;
            }
        """)
        
        # Tipo de venta
    def setup_tab_basica(self, tab):
        layout = QFormLayout(tab)
        
        # Tipo de venta
        self.cmb_tipo_venta = QComboBox()
        self.cmb_tipo_venta.addItems([
            "Efectivo", 
            "Posesion Efectiva", 
            "Subsidio", 
            "Credito H.", 
            "Credito H. + Subsidio"
        ])
        # Cambiar el nombre de la señal conectada para mayor claridad
        self.cmb_tipo_venta.currentTextChanged.connect(self.toggle_pos_efectiva_tab)
        self.toggle_pos_efectiva_tab(self.cmb_tipo_venta.currentText())
        
        # Estado (solo para ventas cerradas)
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems([
            "Negociandose",
            "Cerrada verbalmente",
            "Cerrada en notaria",
            "Inscrita"
        ])
        self.cmb_estado.setVisible(not self.en_proceso)
        
        # Fecha
        self.date_fecha = QDateEdit(QDate.currentDate())
        self.date_fecha.setCalendarPopup(True)
        
        # Monto
        self.txt_monto = QLineEdit()
        self.txt_monto.setValidator(QDoubleValidator())
        
        # Observaciones
        self.txt_observaciones = QTextEdit()
        
        # Propiedad ofrecida
        self.cmb_prop_ofrecida = QComboBox()
        self.cmb_prop_ofrecida.addItems(["Si", "No"])
        
        # Regularizaciones
        self.cmb_regularizaciones = QComboBox()
        self.cmb_regularizaciones.addItems(["Si", "No"])
        
        # Agregar campos al layout
        layout.addRow(self.crear_label("Tipo de venta:", True), self.cmb_tipo_venta)
        
        if not self.en_proceso:
            layout.addRow(self.crear_label("Estado:", True), self.cmb_estado)
        
        layout.addRow(self.crear_label("Fecha:", True), self.date_fecha)
        layout.addRow(self.crear_label("Monto:", not self.en_proceso), self.txt_monto)
        layout.addRow(self.crear_label("Observaciones:"), self.txt_observaciones)
        layout.addRow(self.crear_label("Propiedad ofrecida:", True), self.cmb_prop_ofrecida)
        layout.addRow(self.crear_label("Regularizaciones:"), self.cmb_regularizaciones)

    def toggle_pos_efectiva_tab(self, tipo_venta):
        if not hasattr(self, 'tab_pos_efectiva_index'):
            return  # protección por si aún no está
        mostrar = (not self.en_proceso) and (tipo_venta == "Posesion Efectiva")
        self.tabs.setTabVisible(self.tab_pos_efectiva_index, mostrar)
    
    def setup_tab_comprador(self, tab):
        layout = QFormLayout(tab)
        
        # Campos del comprador
        self.txt_comp_nombre = QLineEdit()
        self.txt_comp_rut = QLineEdit()
        self.txt_comp_direccion = QLineEdit()
        self.txt_comp_telefono = QLineEdit()
        self.txt_comp_email = QLineEdit()
        self.txt_comp_banco = QLineEdit()
        self.txt_comp_tipo_cuenta = QLineEdit()
        self.txt_comp_nro_cuenta = QLineEdit()
        self.cmb_comp_poder = QComboBox()
        self.cmb_comp_poder.addItems(["Si", "No"])
        
        # Agregar campos
        layout.addRow(self.crear_label("Nombre:", True), self.txt_comp_nombre)
        layout.addRow(self.crear_label("RUT:", True), self.txt_comp_rut)
        layout.addRow(self.crear_label("Dirección:"), self.txt_comp_direccion)
        layout.addRow(self.crear_label("Teléfono:"), self.txt_comp_telefono)
        layout.addRow(self.crear_label("Email:"), self.txt_comp_email)
        layout.addRow(self.crear_label("Banco:"), self.txt_comp_banco)
        layout.addRow(self.crear_label("Tipo de cuenta:"), self.txt_comp_tipo_cuenta)
        layout.addRow(self.crear_label("Número de cuenta:"), self.txt_comp_nro_cuenta)
        layout.addRow(self.crear_label("Poder judicial:", True), self.cmb_comp_poder)
    
    def setup_tab_vendedor(self, tab):
        layout = QFormLayout(tab)
        
        # Campos del vendedor
        self.txt_vend_nombre = QLineEdit()
        self.txt_vend_rut = QLineEdit()
        self.txt_vend_direccion = QLineEdit()
        self.txt_vend_telefono = QLineEdit()
        self.txt_vend_email = QLineEdit()
        self.txt_vend_banco = QLineEdit()
        self.txt_vend_tipo_cuenta = QLineEdit()
        self.txt_vend_nro_cuenta = QLineEdit()
        self.cmb_vend_poder = QComboBox()
        self.cmb_vend_poder.addItems(["Si", "No"])
        
        # Agregar campos
        layout.addRow(self.crear_label("Nombre:", True), self.txt_vend_nombre)
        layout.addRow(self.crear_label("RUT:", True), self.txt_vend_rut)
        layout.addRow(self.crear_label("Dirección:"), self.txt_vend_direccion)
        layout.addRow(self.crear_label("Teléfono:"), self.txt_vend_telefono)
        layout.addRow(self.crear_label("Email:"), self.txt_vend_email)
        layout.addRow(self.crear_label("Banco:"), self.txt_vend_banco)
        layout.addRow(self.crear_label("Tipo de cuenta:"), self.txt_vend_tipo_cuenta)
        layout.addRow(self.crear_label("Número de cuenta:"), self.txt_vend_nro_cuenta)
        layout.addRow(self.crear_label("Poder judicial:"), self.cmb_vend_poder)
    
    def setup_tab_propiedad(self, tab):
        layout = QFormLayout(tab)
        
        # Campos de propiedad
        self.txt_prop_codigo = QLineEdit()
        self.txt_prop_direccion = QLineEdit()
        self.txt_prop_rol = QLineEdit()
        self.txt_prop_comuna = QLineEdit()
        
        # Documentación
        self.cmb_estudio_titulos = QComboBox()
        self.cmb_estudio_titulos.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.cmb_inscripcion = QComboBox()
        self.cmb_inscripcion.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.cmb_dominio_vigente = QComboBox()
        self.cmb_dominio_vigente.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.cmb_hipoteca = QComboBox()
        self.cmb_hipoteca.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.cmb_gravamen = QComboBox()
        self.cmb_gravamen.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.cmb_certificado_numero = QComboBox()
        self.cmb_certificado_numero.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.cmb_aseo = QComboBox()
        self.cmb_aseo.addItems(["Si Posee Documento", "No Posee Documento"])
        
        self.cmb_no_expropiacion = QComboBox()
        self.cmb_no_expropiacion.addItems(["Si Posee Documento", "No Posee Documento"])
        
        # Agregar campos
        layout.addRow(self.crear_label("Código interno:", True), self.txt_prop_codigo)
        layout.addRow(self.crear_label("Dirección:", True), self.txt_prop_direccion)
        layout.addRow(self.crear_label("ROL:", True), self.txt_prop_rol)
        layout.addRow(self.crear_label("Comuna:", True), self.txt_prop_comuna)
        
        # Documentación
        layout.addRow(QLabel("<b>Documentación:</b>"))
        layout.addRow(self.crear_label("Estudio de títulos:"), self.cmb_estudio_titulos)
        layout.addRow(self.crear_label("Inscripción:"), self.cmb_inscripcion)
        layout.addRow(self.crear_label("Dominio vigente:"), self.cmb_dominio_vigente)
        layout.addRow(self.crear_label("Hipoteca:"), self.cmb_hipoteca)
        layout.addRow(self.crear_label("Gravamen:"), self.cmb_gravamen)
        layout.addRow(self.crear_label("Certificado número:"), self.cmb_certificado_numero)
        layout.addRow(self.crear_label("Aseo:"), self.cmb_aseo)
        layout.addRow(self.crear_label("No expropiación:"), self.cmb_no_expropiacion)
    
    def setup_tab_pos_efectiva(self, tab):
        layout = QVBoxLayout(tab)
        
        # Tipo de posesión
        self.cmb_tipo_pos = QComboBox()
        self.cmb_tipo_pos.addItems(["Testada", "Intestada"])
        self.cmb_tipo_pos.currentTextChanged.connect(self.actualizar_formulario_herederos)
        
        # Canal
        self.cmb_canal = QComboBox()
        self.cmb_canal.addItems(["Justicia", "Registro civil"])
        
        # Estado proceso
        self.cmb_estado_proceso = QComboBox()
        self.cmb_estado_proceso.addItems([
            "Solicitud",
            "Dictamen",
            "Inscrita",
            "Ingreso",
            "Resolución"
        ])
        
        # Observaciones
        self.txt_obs_pos = QTextEdit()
        
        # Formulario para tipo de posesión
        form_layout = QFormLayout()
        form_layout.addRow("Tipo de posesión:", self.cmb_tipo_pos)
        form_layout.addRow("Canal:", self.cmb_canal)
        form_layout.addRow("Estado del proceso:", self.cmb_estado_proceso)
        form_layout.addRow("Observaciones:", self.txt_obs_pos)
        
        layout.addLayout(form_layout)
        
        # Herederos
        self.tabla_herederos = QTableWidget(0, 5)
        self.tabla_herederos.setHorizontalHeaderLabels([
            "Nombre", 
            "RUT", 
            "Tipo Heredero",
            "Recibe mejoras",
            "% Libre disposición"
        ])
        
        # Configurar columnas
        self.tabla_herederos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_herederos.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Botones para herederos
        btn_layout = QHBoxLayout()
        self.btn_agregar_heredero = QPushButton("Agregar Heredero")
        self.btn_agregar_heredero.clicked.connect(self.agregar_heredero)
        
        self.btn_eliminar_heredero = QPushButton("Eliminar Heredero")
        self.btn_eliminar_heredero.clicked.connect(self.eliminar_heredero)
        
        btn_layout.addWidget(self.btn_agregar_heredero)
        btn_layout.addWidget(self.btn_eliminar_heredero)
        
        layout.addWidget(QLabel("<b>Herederos:</b>"))
        layout.addWidget(self.tabla_herederos)
        layout.addLayout(btn_layout)
        
        # Inicialmente oculto hasta que se seleccione Posesión Efectiva
        self.tab_pos_efectiva = tab
        
    
    def actualizar_campos_pos_efectiva(self, tipo_venta):
        # Mostrar pestaña de posesión efectiva solo si es venta cerrada y tipo es Posesión Efectiva
        mostrar = (not self.en_proceso) and (tipo_venta == "Posesion Efectiva")
        self.tab_pos_efectiva.setVisible(mostrar)
        
        # Actualizar índice si es necesario
        if mostrar:
            self.tabs.setCurrentIndex(4)
    
    def actualizar_formulario_herederos(self, tipo_pos):
        # Configurar tabla de herederos según tipo de posesión
        if tipo_pos == "Testada":
            self.tabla_herederos.setColumnCount(5)
            self.tabla_herederos.setHorizontalHeaderLabels([
                "Nombre", "RUT", "Tipo Heredero", "Recibe mejoras", "% Libre disposición"
            ])
        else:
            self.tabla_herederos.setColumnCount(3)
            self.tabla_herederos.setHorizontalHeaderLabels([
                "Nombre", "RUT", "Tipo Heredero"
            ])
    
    def agregar_heredero(self):
        row = self.tabla_herederos.rowCount()
        self.tabla_herederos.insertRow(row)
        
        # Nombre y RUT
        self.tabla_herederos.setItem(row, 0, QTableWidgetItem(""))
        self.tabla_herederos.setItem(row, 1, QTableWidgetItem(""))
        
        # Tipo heredero (combobox)
        cmb_tipo = QComboBox()
        if self.cmb_tipo_pos.currentText() == "Testada":
            cmb_tipo.addItems(["Forzoso", "Conyugue", "Hijo", "Padre"])
        else:
            cmb_tipo.addItems(["Conyugue", "Hijo", "Padre", "Fisco", "Otro"])
        
        self.tabla_herederos.setCellWidget(row, 2, cmb_tipo)
        
        # Para posesión testada
        if self.cmb_tipo_pos.currentText() == "Testada":
            # Checkbox para mejoras
            chk_mejoras = QTableWidgetItem()
            chk_mejoras.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_mejoras.setCheckState(Qt.Unchecked)
            self.tabla_herederos.setItem(row, 3, chk_mejoras)
            
            # Porcentaje libre disposición
            spin_porcentaje = QDoubleSpinBox()
            spin_porcentaje.setRange(0, 100)
            spin_porcentaje.setValue(0)
            self.tabla_herederos.setCellWidget(row, 4, spin_porcentaje)
    
    def eliminar_heredero(self):
        fila = self.tabla_herederos.currentRow()
        if fila >= 0:
            self.tabla_herederos.removeRow(fila)
    
    def crear_label(self, texto, obligatorio=False):
        label = QLabel(texto)
        if obligatorio:
            label.setProperty("obligatorio", "true")
        return label
    
    def guardar_venta(self):
        print("guardar_venta llamada")
        try:
            # Validar campos obligatorios
            if not self.validar_campos_obligatorios():
                print("Validación falló, no se guarda")
                return
            print("Validación correcta, preparando datos")
            
            # Preparar datos de la venta
            data_venta = {
                'comprador': {
                    'nombre': self.txt_comp_nombre.text(),
                    'rut': self.txt_comp_rut.text(),
                    'direccion': self.txt_comp_direccion.text(),
                    'telefono': self.txt_comp_telefono.text(),
                    'correo': self.txt_comp_email.text(),
                    'banco': self.txt_comp_banco.text(),
                    'tipo_cuenta': self.txt_comp_tipo_cuenta.text(),
                    'nro_cuenta': self.txt_comp_nro_cuenta.text(),
                    'poder_judicial': self.cmb_comp_poder.currentText()
                },
                'vendedor': {
                    'nombre': self.txt_vend_nombre.text(),
                    'rut': self.txt_vend_rut.text(),
                    'direccion': self.txt_vend_direccion.text(),
                    'telefono': self.txt_vend_telefono.text(),
                    'correo': self.txt_vend_email.text(),
                    'banco': self.txt_vend_banco.text(),
                    'tipo_cuenta': self.txt_vend_tipo_cuenta.text(),
                    'nro_cuenta': self.txt_vend_nro_cuenta.text(),
                    'poder_judicial': self.cmb_vend_poder.currentText()
                },
                'propiedad': {
                    'codigo': self.txt_prop_codigo.text(),
                    'direccion': self.txt_prop_direccion.text(),
                    'rol': self.txt_prop_rol.text(),
                    'comuna': self.txt_prop_comuna.text(),
                    'estudio_titulos': self.cmb_estudio_titulos.currentText(),
                    'inscripcion': self.cmb_inscripcion.currentText(),
                    'dominio_vigente': self.cmb_dominio_vigente.currentText(),
                    'hipoteca': self.cmb_hipoteca.currentText(),
                    'gravamen': self.cmb_gravamen.currentText(),
                    'certificado_numero': self.cmb_certificado_numero.currentText(),
                    'aseo': self.cmb_aseo.currentText(),
                    'no_expropiacion': self.cmb_no_expropiacion.currentText()
                },
                'venta': {
                    'fecha_venta': self.date_fecha.date().toString("yyyy-MM-dd"),
                    'monto_venta': self.txt_monto.text() if self.txt_monto.text() else None,
                    'observaciones': self.txt_observaciones.toPlainText(),
                    'tipo_venta': self.cmb_tipo_venta.currentText(),
                    'estado_venta': 'en_proceso' if self.en_proceso else self.cmb_estado.currentText().lower(),
                    'propiedad_ofrecida': self.cmb_prop_ofrecida.currentText(),
                    'regularizaciones': self.cmb_regularizaciones.currentText(),
                    'limitaciones': 'No',  # Valor por defecto
                    'viabilidad': ''  # Valor por defecto
                }
            }
            
            # Preparar datos de posesión efectiva si es venta cerrada y tipo es Posesión Efectiva
            posesion_efectiva = None
            herederos = []
            mejoras = []
            libre_disposicion = {}
            
            if not self.en_proceso and self.cmb_tipo_venta.currentText() == "Posesion Efectiva":
                posesion_efectiva = {
                    'tipo': self.cmb_tipo_pos.currentText().lower(),
                    'canal': self.cmb_canal.currentText().lower(),
                    'estado_proceso': self.cmb_estado_proceso.currentText().lower(),
                    'observaciones': self.txt_obs_pos.toPlainText()
                }
                
                # Procesar herederos
                for row in range(self.tabla_herederos.rowCount()):
                    heredero = {
                        'nombre': self.tabla_herederos.item(row, 0).text(),
                        'rut': self.tabla_herederos.item(row, 1).text(),
                        'tipo_heredero': self.tabla_herederos.cellWidget(row, 2).currentText().lower()
                    }
                    
                    # Para posesión testada
                    if self.cmb_tipo_pos.currentText() == "Testada":
                        # Mejoras
                        if self.tabla_herederos.item(row, 3).checkState() == Qt.Checked:
                            mejoras.append(heredero['rut'])
                        
                        # Libre disposición
                        porcentaje = self.tabla_herederos.cellWidget(row, 4).value()
                        libre_disposicion[heredero['rut']] = porcentaje
                    
                    herederos.append(heredero)
            
            # Guardar venta
            venta_id = guardar_venta(
                data_venta,
                posesion_efectiva,
                herederos,
                mejoras,
                libre_disposicion,
                es_venta_cerrada=not self.en_proceso
            )
            
            if venta_id:
                print(f"Venta guardada con ID {venta_id}, mostrando mensaje")
                QMessageBox.information(
                    self,
                    "Éxito",
                    "La venta se ha guardado correctamente.\n\n"
                    f"ID de venta: {venta_id}"
                )
                print("Mensaje mostrado, emitiendo señal y cerrando ventana")
                self.venta_guardada.emit()
                self.close()
                print("Ventana cerrada")
            else:
                print("guardar_venta retornó ID falso o None")
        
        except Exception as e:
            print(f"Error en guardar_venta: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar la venta: {str(e)}")
    
    def validar_campos_obligatorios(self):
        # Validar campos obligatorios básicos
        campos_obligatorios = [
            (self.txt_comp_nombre.text(), "Nombre del comprador"),
            (self.txt_comp_rut.text(), "RUT del comprador"),
            (self.txt_vend_nombre.text(), "Nombre del vendedor"),
            (self.txt_vend_rut.text(), "RUT del vendedor"),
            (self.txt_prop_codigo.text(), "Código de propiedad"),
            (self.txt_prop_direccion.text(), "Dirección de propiedad"),
            (self.txt_prop_rol.text(), "ROL de propiedad"),
            (self.txt_prop_comuna.text(), "Comuna de propiedad")
        ]
        
        for valor, nombre in campos_obligatorios:
            if not valor.strip():
                QMessageBox.warning(self, "Campo obligatorio", f"El campo {nombre} es obligatorio")
                return False
        
        # Validar RUTs
        if not self.validar_rut(self.txt_comp_rut.text()):
            QMessageBox.warning(self, "RUT inválido", "El RUT del comprador no es válido")
            return False
        
        if not self.validar_rut(self.txt_vend_rut.text()):
            QMessageBox.warning(self, "RUT inválido", "El RUT del vendedor no es válido")
            return False
        
        # Validar herederos si es posesión efectiva
        if not self.en_proceso and self.cmb_tipo_venta.currentText() == "Posesion Efectiva":
            if self.tabla_herederos.rowCount() == 0:
                QMessageBox.warning(self, "Herederos requeridos", "Debe agregar al menos un heredero para posesión efectiva")
                return False
            
            for row in range(self.tabla_herederos.rowCount()):
                if not self.tabla_herederos.item(row, 0).text().strip() or not self.tabla_herederos.item(row, 1).text().strip():
                    QMessageBox.warning(self, "Datos incompletos", "Todos los herederos deben tener nombre y RUT")
                    return False
                
                if not self.validar_rut(self.tabla_herederos.item(row, 1).text()):
                    QMessageBox.warning(self, "RUT inválido", f"El RUT del heredero en la fila {row+1} no es válido")
                    return False
        
        return True
    
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