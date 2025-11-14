from PySide6.QtWidgets import QFileDialog, QMainWindow,QHBoxLayout,QTextEdit,QTabWidget,QDoubleSpinBox,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from services.ventas_service import obtener_ventas_resumen, obtener_detalle_venta, asignar_porcentajes_herencia, guardar_venta, asignar_porcentajes_herencia_testada, obtener_ventas_por_estado, eliminar_venta
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QIntValidator, QColor, QDoubleValidator
from gui.usuario_actual import UsuarioActual
from services.supabase_client import supabase
import json
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP



class DetalleVentaWindow(QWidget):
    def __init__(self, venta_id, rol, dashboard=None):
        super().__init__()
        self.venta_id = venta_id
        self.rol = rol
        self.dashboard = dashboard
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

        if self.detalle_venta.get('venta', {}).get('tipo_venta') in ["Subsidio", "Credito H.", "Credito H. + Subsidio"]:
            self.setup_tab_tasador()
        
        if self.detalle_venta.get('venta', {}).get('tipo_venta') in ["Credito H.","Credito H. + Subsidio"]:
            self.setup_tab_prea_cred()
            
        if self.detalle_venta.get('venta', {}).get('tipo_venta') in ["Credito H."]:
            self.setup_tab_confe_cred()

            
        if self.detalle_venta.get('venta', {}).get('tipo_venta') in ["Subsidio", "Credito H. + Subsidio"]:
            self.setup_tab_prea_sub()
            self.setup_tab_confe_subsidio()
            self.setup_tab_docs_pas()

        
            
        
        # Botón para cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout_contenido.addWidget(btn_cerrar)
        
        self.btn_editar = QPushButton("Editar Venta")
        self.btn_editar.clicked.connect(self.abrir_formulario_edicion)
        layout_contenido.addWidget(self.btn_editar)

        self.btnEliminar = QPushButton("Eliminar Venta")
        self.btnEliminar.clicked.connect(self.eliminar_venta)
        layout_contenido.addWidget(self.btnEliminar)


    def abrir_formulario_edicion(self):
        try:
            # Traer venta
            venta = self.detalle_venta.get('venta', {})

            if venta:
                es_venta_proceso = venta.get('es_venta_proceso', False)
            else:
                es_venta_proceso = False

            # Crea una instancia del formulario
            self.formulario = FormularioVenta(en_proceso=es_venta_proceso, venta_id=self.venta_id)
            
            
            # Llamas a la función que carga los datos en el formulario
            self.formulario.cargar_datos_venta(venta_id=self.venta_id)

            self.formulario.venta_guardada.connect(self.dashboard.cargar_ventas)

            # Muestras la ventana
            self.formulario.show()

            self.close()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el formulario: {e}")

    
    def eliminar_venta(self):
        try:
            # 1️⃣ Obtener el código interno de la venta
            codigo_interno = self.detalle_venta.get("propiedad", {}).get("codigo_interno")
            
            if not codigo_interno:
                QMessageBox.warning(self, "Eliminar venta", "No se encontró el código interno de esta venta.")
                return

            # 2️⃣ Confirmar con el usuario
            confirm = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Seguro que deseas eliminar la venta con código '{codigo_interno}'?\n"
                "Esto eliminará todos los registros.",
                QMessageBox.Yes | QMessageBox.No
            )

            if confirm != QMessageBox.Yes:
                return

            # 3️⃣ Llamar al backend
            resultado = eliminar_venta(codigo_interno)

            QMessageBox.information(self, "Eliminar venta", str(resultado))

            if self.dashboard:
                try:
                    self.dashboard.cargar_ventas()
                except:
                    pass
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al eliminar la venta:\n{str(e)}")
    
    def setup_tab_info_general(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Información General")
        layout = QFormLayout(tab)
        
        venta = self.detalle_venta.get('venta', {})
        
        # Campos de información general
        campos = [
            ("ID Venta", venta.get('id')),
            ("Fecha", venta.get('fecha_venta')),
            ("Monto", (f"${int(venta.get('monto_venta', 0)):,}".replace(",", ".") if venta.get('monto_venta') else "No especificado")),
            ("Tipo de venta", venta.get('tipo_venta')),
            ("Estado", venta.get('estado_venta', '').replace("_", " ").capitalize()),
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
            ("Email", comprador.get('correo')),
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
            ("Email", vendedor.get('correo')),
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
        venta = self.detalle_venta.get('venta', {})
        documentacion = self.detalle_venta.get('documentacion', {})
        
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
            ("Inscripción", venta.get('inscripcion')),
            ("Dominio vigente", propiedad.get('dominio_vigente')),
            ("Hipoteca", venta.get('hipoteca')),
            ("Gravamen", venta.get('gravamen')),
            ("Certificado número", venta.get('certificado_numero')),
            ("Aseo", venta.get('aseo')),
            ("No expropiación", venta.get('no_expropiacion')),   
        ]

        if self.detalle_venta.get('venta', {}).get('tipo_venta') in ["Subsidio", "Credito H.", "Credito H. + Subsidio"]:
            campos_doc.extend([
                ("Superficie", documentacion.get('superficie')),
                ("Edificada", documentacion.get('edificada')),
                ("Recepción", documentacion.get('recepcion'))
            ])

        for label, value in campos_doc:
            if value:
                form_total.addRow(QLabel(f"{label}:"), QLabel(str(value)))

        layout.addLayout(form_total)
    
    def setup_tab_pos_efectiva(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Posesión Efectiva")
        layout = QVBoxLayout(tab)
        
        # Obtener herederos de la venta y la venta

        herederos = self.detalle_venta.get('herederos', [])

        if isinstance(herederos, str):
            try:
                herederos = json.loads(herederos)
            except json.JSONDecodeError:
                herederos = []

        # Si es un solo dict (un solo heredero), lo ponemos en una lista
        if isinstance(herederos, dict):
            herederos = [herederos]

        # Si no es lista después de esto, forzamos una lista vacía
        if not isinstance(herederos, list):
            herederos = []

             
        
        if not herederos:
            layout.addWidget(QLabel("No hay información de posesión efectiva disponible"))
            return
        
        # Información de posesión efectiva
        posesion = self.detalle_venta.get('posesion', {})
        
        if posesion:
            form_pos = QFormLayout()
            campos_pos = [
                ("Tipo", posesion.get('tipo_posesion', '')),
                ("Canal", posesion.get('canal', '')),
                ("Estado del proceso", posesion.get('estado_proceso', ''))
            ]

            observaciones = posesion.get('observaciones')

            if observaciones:
                campos_pos.extend([
                    ("Observaciones", observaciones)
                ])
            
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

    def setup_tab_tasador(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Tasador")
        layout = QFormLayout(tab)

        tasacion = self.detalle_venta.get('tasacion', {})

        if tasacion:
            layout.addRow(QLabel("<b>Información Tasador:</b>"), QLabel(""))

            # Campos básicos del tasador
            campos_tas = [
                ("Nombre", tasacion.get('nombre', '')),
                ("Rut", tasacion.get('rut', '')),
                ("Teléfono", tasacion.get('telefono', '')),
                ("Email", tasacion.get('correo_electronico', '')),
                
            ]

            for label, value in campos_tas:
                layout.addRow(QLabel(f"{label}:"), QLabel(str(value)))

            # 👇 Ahora recién agregamos el encabezado de documentación
            layout.addRow(QLabel("<b>Documentación:</b>"), QLabel(""))

            campos_docs = [
                    ("Documento Propiedad", tasacion.get('doc_propiedad', '')),
                    ("Copia Subsidio", tasacion.get('copia_subsidio', '')),
                    ("Informe de Tasación", tasacion.get('informe_tasacion', '')),
                    ("Certificado Habitabilidad", tasacion.get('certif_habitabilidad', ''))
                ]
            
            for label, value in campos_docs:
                layout.addRow(QLabel(f"{label}:"), QLabel(str(value)))
                

    def setup_tab_prea_sub(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Preaprobación Subsidio")
        layout = QFormLayout(tab)

        subsidio = self.detalle_venta.get('subsidio', {})

        if subsidio:
            layout.addRow(QLabel("<b>Preaprobación de Subsidio:</b>"), QLabel(""))

            campos_subsidio = [
                ("Porcentaje de Financiamiento", f"{float(subsidio.get('porcentaje_subsidio') or 0) * 100:.1f}%"),
                ("Monto Financiamiento", (f"${int(subsidio.get('monto_subsidio')):,}".replace(",", ".") if subsidio.get('monto_subsidio') else "No especificado")),
                ("Estado Subsidio", subsidio.get('estado_subsidio')),
                
            ]

            resolucion = subsidio.get('resolucion_subsidio')

            if resolucion:
                campos_subsidio.extend([
                    ("Resolución", resolucion),
                ])

            for label, value in campos_subsidio:
                layout.addRow(QLabel(f"{label}:"), QLabel(str(value)))

    



    def setup_tab_confe_subsidio(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Confección")
        layout = QFormLayout(tab)
        
        confeccion = self.detalle_venta.get('confeccion', {})
        venta = self.detalle_venta.get('venta', {})

        if confeccion:
            layout.addRow(QLabel("<b>Documentos Confección:</b>"), QLabel(""))

            campos_confeccion = [
                ("Documento Propiedad", confeccion.get('doc_propiedad')),
                ("Documento Tasación", confeccion.get('doc_tasacion')),
                ("Declaración Jurada no parentesco comprador/vendedor", confeccion.get('dj_no_parent_comp_vend')),
                ("Documento Subsidio Original", confeccion.get('subsidio_original')),
                ("Declaración Jurada vendedor no habitual", confeccion.get('dj_vend_no_habitual')),
                ("Declaración Jurada No Inhabilidad", confeccion.get('dj_comp_no_parientes_cargos_publicos')),
            ]
            
            for label, value in campos_confeccion:
                layout.addRow(QLabel(f"{label}:"), QLabel(str(value)))


            layout.addRow(QLabel("<b>Abonos:</b>"), QLabel(""))

            campos_abonos = [
                ("Abono Previo",(f"${int(venta.get('abono_previsto')):,}".replace(",", ".") if venta.get('abono_previsto') else "No especificado")),
                ("Abono Real",(f"${int(venta.get('abono_real')):,}".replace(",", ".") if venta.get('abono_real') else "No especificado")),
                ("Saldo Pendiente",f"${int(venta.get('saldo_pendiente')):,}".replace(",", "."))
            ]

            for label, value in campos_abonos:
                layout.addRow(QLabel(f"{label}:"), QLabel(str(value)))

    def setup_tab_docs_pas(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Documentos PAS")
        layout = QFormLayout(tab)

        pas = self.detalle_venta.get('PAS', {})

        if pas:
            layout.addRow(QLabel("<b>Documentos PAS:</b>"), QLabel(""))
            campos_pas = [
                ("Fecha de ingreso documentos", pas.get('fecha_ingreso_docs')),
                ("Estado de Custodia y Pago", pas.get('supe_platas')),
            ]

            reparos = pas.get('reparos')

            if reparos:
                campos_pas.extend([
                ("Reparos", reparos),
                 ])
                
            for label, value in campos_pas:
                layout.addRow(QLabel(f"{label}:"), QLabel(str(value)))



    def setup_tab_prea_cred(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Preaprobación Credito")
        layout = QFormLayout(tab)
        credito = self.detalle_venta.get('aproba_cred', {})

        if credito:
            campos_credito = [
                ("Porcentaje de Financiamiento", f"{float(credito.get('porcentaje_financiamiento') or 0) * 100:.1f}%"),
                ("Monto Financiamiento",(f"${int(credito.get('monto_financiamiento')):,}".replace(",", ".") if credito.get('monto_financiamiento') else "No especificado")),
                ("Banco que concede el credito", credito.get('banco_credito','')),
                ("Estado Aprobación", credito.get('estado_preaprobacion'))
            ]

            diferencias = credito.get('diferencias')
            
            if diferencias:
                campos_credito.extend([
                    ('Diferencias', diferencias),
                ])

            for label, value in campos_credito:
                layout.addRow(QLabel(f"{label}:"), QLabel(str(value)))
    
    
    
    def setup_tab_confe_cred(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Confección")
        layout = QFormLayout(tab)
        confe_cred = self.detalle_venta.get('confeccion', {})
        

        if confe_cred:
            campos_cred = [
                ("Documento Propiedad", confe_cred.get('doc_propiedad')),
                ("Documento Tasación", confe_cred.get('doc_tasacion')),
                ("Declaración Jurada vendedor no habitual", confe_cred.get('dj_vend_no_habitual'))
            ]

            for label, value in campos_cred:
                layout.addRow(QLabel(f"{label}:"), QLabel(str(value)))




class DashboardVentas(QWidget):
    def __init__(self, rol, parent=None):
        super().__init__(parent)
        self.rol = rol
        self.setWindowTitle("Gestión de Ventas")
        self.resize(1200, 800)
        self.cargando_tabla = False
        # Widget central

        main_layout = QVBoxLayout(self)
        
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
        
        main_layout.addWidget(self.tabla_ventas)
        
        # Barra de botones
        button_layout = QHBoxLayout()

        
        self.btn_agregar_cerrada = QPushButton("Agregar Venta")
        self.btn_agregar_cerrada.clicked.connect(lambda: self.abrir_formulario_venta(en_proceso=False))
        
        self.btn_actualizar = QPushButton("Actualizar Lista")
        self.btn_actualizar.clicked.connect(self.cargar_ventas)
        
        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.clicked.connect(self.exportar_a_excel)
        
 
        
       
        button_layout.addWidget(self.btn_agregar_cerrada)
        button_layout.addWidget(self.btn_actualizar)
        button_layout.addWidget(self.btn_exportar)
        
        main_layout.addLayout(button_layout)
        
        # Cargar datos iniciales
        self.cargar_ventas()
    
    def cargar_ventas(self):
        try:
            self.cargando_tabla = True
            


            self.tabla_ventas.setRowCount(0)
            estado_filtro = self.filtro_estado.currentText()

            if estado_filtro == "Todas las ventas":
                ventas = obtener_ventas_resumen()
            else:
                ventas = obtener_ventas_por_estado(estado_filtro)

            if ventas:
                self.tabla_ventas.setRowCount(len(ventas))
                self.ventas = ventas or []
            

                self.tabla_ventas.setUpdatesEnabled(False)  # 🔸 Pausa el renderizado de la tabla
            try:
                for row, venta in enumerate(ventas):
                    self.tabla_ventas.setItem(row, 0, QTableWidgetItem(str(venta.get("id", ""))))
                    self.tabla_ventas.setItem(row, 1, QTableWidgetItem(venta.get("comprador", "")))
                    self.tabla_ventas.setItem(row, 2, QTableWidgetItem(venta.get("vendedor", "")))
                    self.tabla_ventas.setItem(row, 3, QTableWidgetItem(venta.get("propiedad", "")))
                    self.tabla_ventas.setItem(row, 4, QTableWidgetItem(str(venta.get("fecha_venta", ""))))

                    # ✅ Aquí aplicas tu mapeo sin problemas visuales
                    estado_venta = venta.get("estado_venta", "").replace("_", " ").capitalize()
                    self.tabla_ventas.setItem(row, 5, QTableWidgetItem(estado_venta))

                    self.tabla_ventas.setItem(row, 6, QTableWidgetItem(venta.get("tipo_venta", "")))
            finally:
                self.tabla_ventas.setUpdatesEnabled(True)   # 🔸 Reactiva el renderizado
                self.tabla_ventas.resizeColumnsToContents()
                self.tabla_ventas.setColumnHidden(0, True)
            

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
        venta_id = int(self.tabla_ventas.item(item.row(), 0).text())
        self.ventana_detalle = DetalleVentaWindow(venta_id, self.rol, dashboard=self)
        self.ventana_detalle.show()
    
    
    def exportar_a_excel(self):
        try:
            if not self.ventas:
                QMessageBox.warning(self, "Exportar a Excel", "No hay ventas para exportar.")
                return

            # Pedir ruta de guardado
            ruta, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar archivo Excel",
                "ventas.xlsx",
                "Excel Files (*.xlsx)"
            )
            if not ruta:
                return

            import pandas as pd

            # Convertir lista de diccionarios a DataFrame
            df = pd.DataFrame(self.ventas)

            # Separar por tipo de venta
            tipos_venta = df['tipo_venta'].unique() if 'tipo_venta' in df else []

            # Crear un ExcelWriter para varias hojas
            with pd.ExcelWriter(ruta, engine="xlsxwriter") as writer:
                tipos = df["tipo_venta"].unique()
                for tipo in tipos:
                    df_tipo = df[df["tipo_venta"] == tipo]
                    df_tipo.to_excel(writer, sheet_name=tipo[:31], index=False)

            QMessageBox.information(self, "Exportar", f"Ventas exportadas correctamente a:\n{ruta}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron exportar las ventas:\n{str(e)}")


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
    
    def __init__(self,en_proceso=False,venta_id=None, parent=None):
        super().__init__(parent)
        self.en_proceso = en_proceso
        self.venta_id = venta_id
        self.setWindowTitle("Editar Venta" if venta_id else "Nueva Venta Cerrada")
        self.resize(900, 700)
        self.detalle_venta = {}
        
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
        tab_pos_efectiva = QWidget()
        self.tabs.addTab(tab_pos_efectiva, "Posesión Efectiva")
        self.setup_tab_pos_efectiva(tab_pos_efectiva)
        self.tab_pos_efectiva_index = self.tabs.indexOf(tab_pos_efectiva) 


        tab_tasador = QWidget()
        self.tabs.addTab(tab_tasador, "Tasador")
        self.setup_tab_tasador(tab_tasador)
        self.tab_tasador_index = self.tabs.indexOf(tab_tasador)

        tab_prea_credito = QWidget()
        self.tabs.addTab(tab_prea_credito, "Pre aprobación crédito")
        self.setup_tab_prea_credito(tab_prea_credito)
        self.tab_prea_credito_index = self.tabs.indexOf(tab_prea_credito)

        tab_prea_subsidio = QWidget()
        self.tabs.addTab(tab_prea_subsidio, "Pre aprobación subsidio")
        self.setup_tab_prea_subsidio(tab_prea_subsidio)
        self.tab_prea_subsidio_index = self.tabs.indexOf(tab_prea_subsidio)

        tab_confeccion_subsidio = QWidget()
        self.tabs.addTab(tab_confeccion_subsidio, "Confección Subsidio")
        self.setup_tab_confeccion_subsidio(tab_confeccion_subsidio)
        self.tab_confeccion_subsidio_index = self.tabs.indexOf(tab_confeccion_subsidio)

        tab_confeccion_credito = QWidget()
        self.tabs.addTab(tab_confeccion_credito, "Confección Crédito")
        self.setup_tab_confeccion_credito(tab_confeccion_credito)
        self.tab_confeccion_credito_index = self.tabs.indexOf(tab_confeccion_credito)

        tab_docs_pas = QWidget()
        self.tabs.addTab(tab_docs_pas, "Documentos PAS")
        self.setup_tab_docs_pas(tab_docs_pas)
        self.tab_docs_pas_index = self.tabs.indexOf(tab_docs_pas)

        # === Estado de la venta (combo) ===
        # Aquí asumimos que en la pestaña de Información Básica tienes un combo self.cmb_estado
        self.cmb_estado.currentTextChanged.connect(lambda: self.aplicar_estado_ui(self.cmb_estado.currentText()))
           # Cambiar el nombre de la señal conectada para mayor claridad
           
        self.cmb_tipo_venta.currentTextChanged.connect(self.toggle_pos_efectiva_tab)
        self.toggle_pos_efectiva_tab(self.cmb_tipo_venta.currentText())

        self.cmb_tipo_venta.currentTextChanged.connect(self.toggle_tasador_tab)
        self.toggle_tasador_tab(self.cmb_tipo_venta.currentText())

        self.cmb_tipo_venta.currentTextChanged.connect(self.toggle_confeccion_subsidio_tab)
        self.toggle_confeccion_subsidio_tab(self.cmb_tipo_venta.currentText())

        self.cmb_tipo_venta.currentTextChanged.connect(self.toggle_confeccion_credito_tab)
        self.toggle_confeccion_credito_tab(self.cmb_tipo_venta.currentText())

        self.cmb_tipo_venta.currentTextChanged.connect(self.toggle_prea_credito_tab)
        self.toggle_prea_credito_tab(self.cmb_tipo_venta.currentText())

        self.cmb_tipo_venta.currentTextChanged.connect(self.toggle_prea_subsidio_tab)
        self.toggle_prea_subsidio_tab(self.cmb_tipo_venta.currentText())

        self.cmb_tipo_venta.currentTextChanged.connect(self.toggle_docs_pas)
        self.toggle_docs_pas(self.cmb_tipo_venta.currentText())

       

        
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

        if self.venta_id:
            self.detalle_venta = obtener_detalle_venta(self.venta_id)
            if not self.detalle_venta:
                layout_principal.addWidget(QLabel("No se encontraron detalles para esta venta"))
            else:
                self.cargar_datos_venta(self.venta_id)
        
        

    def aplicar_estado_ui(self, estado):
        """Ajusta las pestañas visibles según el estado de la venta."""
        # en_proceso = estado.lower() == "en proceso"

        # # Ocultar o mostrar pestañas según el estado
        # self.tabs.setTabVisible(self.tab_pos_efectiva_index, not en_proceso)
        # self.tabs.setTabVisible(self.tab_tasador_index, not en_proceso)
        # self.tabs.setTabVisible(self.tab_prea_credito_index, not en_proceso)
        # self.tabs.setTabVisible(self.tab_prea_subsidio_index, not en_proceso)
        # self.tabs.setTabVisible(self.tab_confeccion_subsidio_index, not en_proceso)
        # self.tabs.setTabVisible(self.tab_confeccion_credito_index, not en_proceso)
        # self.tabs.setTabVisible(self.tab_docs_pas_index, not en_proceso)
        return

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
        
        
        # Estado (solo para ventas cerradas)
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems([
            "En Proceso",
            "Negociandose",
            "Cerrada verbalmente",
            "Cerrada en notaria",
            "Inscrita"
        ])
        
        
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
        
        
        layout.addRow(self.crear_label("Estado:", True), self.cmb_estado)
        
        layout.addRow(self.crear_label("Fecha:", True), self.date_fecha)
        layout.addRow(self.crear_label("Monto:"), self.txt_monto)
        layout.addRow(self.crear_label("Observaciones:"), self.txt_observaciones)
        layout.addRow(self.crear_label("Propiedad ofrecida:", True), self.cmb_prop_ofrecida)
        layout.addRow(self.crear_label("Regularizaciones:"), self.cmb_regularizaciones)
        
    def toggle_pos_efectiva_tab(self, tipo_venta):
        if not hasattr(self, 'tab_pos_efectiva_index'):
            return  # protección por si aún no está
        mostrar = (not self.en_proceso) and (tipo_venta == "Posesion Efectiva")
        self.tabs.setTabVisible(self.tab_pos_efectiva_index, mostrar)

    def toggle_tasador_tab(self, tipo_venta):
        if not hasattr(self, 'tab_tasador_index'):
            return  # protección por si aún no está
        mostrar = (not self.en_proceso) and (tipo_venta in ["Subsidio", "Credito H.", "Credito H. + Subsidio"])
        self.tabs.setTabVisible(self.tab_tasador_index, mostrar)
    
    def toggle_confeccion_subsidio_tab(self, tipo_venta):
        if not hasattr(self, 'tab_confeccion_subsidio_index'):
            return  # protección por si aún no está
        mostrar = (not self.en_proceso) and (tipo_venta in ["Subsidio", "Credito H. + Subsidio"])
        self.tabs.setTabVisible(self.tab_confeccion_subsidio_index, mostrar)

    def toggle_confeccion_credito_tab(self, tipo_venta):
        if not hasattr(self, 'tab_confeccion_credito_index'):
            return
        mostrar = (not self.en_proceso) and (tipo_venta in ["Credito H."])
        self.tabs.setTabVisible(self.tab_confeccion_credito_index, mostrar)


    def toggle_prea_credito_tab(self, tipo_venta):
        if not hasattr(self,'tab_prea_credito_index'):
            return
        mostrar = (not self.en_proceso) and (tipo_venta in ["Credito H.", "Credito H. + Subsidio"])
        self.tabs.setTabVisible(self.tab_prea_credito_index, mostrar)

    def toggle_prea_subsidio_tab(self, tipo_venta):
        if not hasattr(self,'tab_prea_subsidio_index'):
            return
        mostrar = (not self.en_proceso) and (tipo_venta in ["Subsidio", "Credito H. + Subsidio"])
        self.tabs.setTabVisible(self.tab_prea_subsidio_index, mostrar)

    def toggle_docs_pas(self, tipo_venta):
        if not hasattr(self,'tab_docs_pas_index'):
            return
        mostrar = (not self.en_proceso) and (tipo_venta in ["Subsidio", "Credito H. + Subsidio"])
        self.tabs.setTabVisible(self.tab_docs_pas_index, mostrar)

   
    
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

        layout.addRow(self.crear_label("Nombre:", not self.en_proceso), self.txt_comp_nombre)
        layout.addRow(self.crear_label("RUT:", not self.en_proceso), self.txt_comp_rut)
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
        
        layout.addRow(self.crear_label("Nombre:", not self.en_proceso), self.txt_vend_nombre)
        layout.addRow(self.crear_label("RUT:", not self.en_proceso), self.txt_vend_rut)

        layout.addRow(self.crear_label("Dirección:"), self.txt_vend_direccion)
        layout.addRow(self.crear_label("Teléfono:"), self.txt_vend_telefono)
        layout.addRow(self.crear_label("Email:"), self.txt_vend_email)
        layout.addRow(self.crear_label("Banco:"), self.txt_vend_banco)
        layout.addRow(self.crear_label("Tipo de cuenta:"), self.txt_vend_tipo_cuenta)
        layout.addRow(self.crear_label("Número de cuenta:"), self.txt_vend_nro_cuenta)
        layout.addRow(self.crear_label("Poder judicial:"), self.cmb_vend_poder)
    

    def setup_tab_tasador(self, tab):
        layout = QFormLayout(tab)

        layout.addRow(QLabel("<b>Información Tasador:</b>"))
        
        # Campos del tasador
        self.txt_tas_nombre = QLineEdit()
        self.txt_tas_rut = QLineEdit()
        self.txt_tas_telefono = QLineEdit()
        self.txt_tas_email = QLineEdit()

        # campos documentacion
        self.cmb_doc_propiedad_tas = QComboBox()
        self.cmb_doc_propiedad_tas.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_copia_subsidio = QComboBox()
        self.cmb_copia_subsidio.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_informe_tasacion = QComboBox()
        self.cmb_informe_tasacion.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_certif_habitabilidad  = QComboBox()
        self.cmb_certif_habitabilidad .addItems(["Si Posee Documento", "No Posee Documento"])

        
        # Agregar campos

        layout.addRow(self.crear_label("Nombre:", not self.en_proceso), self.txt_tas_nombre)
        layout.addRow(self.crear_label("RUT:", not self.en_proceso), self.txt_tas_rut)
        layout.addRow(self.crear_label("Teléfono:"), self.txt_tas_telefono)
        layout.addRow(self.crear_label("Email:"), self.txt_tas_email)

        

        layout.addRow(QLabel("<b>Documentos Tasación:</b>"))

        layout.addRow(self.crear_label("Documento Propiedad:"), self.cmb_doc_propiedad_tas)
        layout.addRow(self.crear_label("Copia Subsidio:"), self.cmb_copia_subsidio)
        layout.addRow(self.crear_label("Informe de Tasación:"), self.cmb_informe_tasacion)
        layout.addRow(self.crear_label("Certificado Habitabilidad:"), self.cmb_certif_habitabilidad)


    def setup_tab_prea_credito(self, tab):
        layout = QFormLayout(tab)

        layout.addRow(QLabel("<b> Preaprobación de credito :</b>"))
        
        self.txt_porc_financiamiento = QLineEdit()
        self.txt_monto_financiamiento = QLineEdit()
        self.txt_diferencias_prea_credito = QTextEdit()
        self.cmb_estado_aprobacion = QComboBox()
        self.cmb_estado_aprobacion.addItems(["En trámite","Aprobado","Rechazado"])
        self.txt_banco_credito = QLineEdit()
        self.checkbox_dif = QCheckBox("¿Existen diferencias?")
        self.checkbox_dif.setChecked(False)

        layout.addRow(self.crear_label("Porcentaje de Financiamiento:"), self.txt_porc_financiamiento)
        layout.addRow(self.crear_label("Monto Financiamiento :"), self.txt_monto_financiamiento)
        layout.addRow(self.crear_label("Banco que concede el credito:"), self.txt_banco_credito)
        layout.addRow(self.crear_label("Estado Aprobación:"), self.cmb_estado_aprobacion)
        layout.addWidget(self.checkbox_dif)
        self.lbl_diferencias = self.crear_label("Diferencias:")
        layout.addRow(self.lbl_diferencias, self.txt_diferencias_prea_credito)
        self.lbl_diferencias.hide()
        self.txt_diferencias_prea_credito.hide()
        self.checkbox_dif.stateChanged.connect(self.verificar_dif)

    def setup_tab_prea_subsidio(self, tab):
        layout = QFormLayout(tab)

        layout.addRow(QLabel("<b> Preaprobación de subsidio :</b>"))

        self.txt_porc_subsidio = QLineEdit()
        self.txt_monto_subsidio = QLineEdit()
        self.cmb_estado_subsidio = QComboBox()
        self.cmb_estado_subsidio.addItems(["En trámite","Aprobado","Rechazado"])
        self.txt_resolucion_subsidio = QTextEdit()
        
        layout.addRow(self.crear_label("Porcentaje de Financiamiento:"), self.txt_porc_subsidio)
        layout.addRow(self.crear_label("Monto Financiamiento :"), self.txt_monto_subsidio)
        layout.addRow(self.crear_label("Estado Subsidio:"), self.cmb_estado_subsidio)
        layout.addRow(self.crear_label("Resolución Subsidio:"), self.txt_resolucion_subsidio)
        
                
        
    
    def verificar_dif(self):
        mostrar = self.checkbox_dif.isChecked()
        self.lbl_diferencias.setVisible(mostrar)
        self.txt_diferencias_prea_credito.setVisible(mostrar)

    
    
 

    def on_abono_previo_cambiado_subsidio(self, texto):
        try:
            texto_limpio = texto.replace(".", "").replace(",", ".")
            self.abono_previo_val = float(texto_limpio)
        except ValueError:
            self.abono_previo_val = None  # si no es número válido
        self.validar_abono_subsidio()

    def on_abono_real_cambiado_subsidio(self, texto):
        try:
            texto_limpio = texto.replace(".", "").replace(",", ".")
            self.abono_real_val = float(texto_limpio)
        except ValueError:
            self.abono_real_val = None
        self.validar_abono_subsidio()

    def validar_abono_subsidio(self):
            
            if self.abono_previo_val is None or self.abono_real_val is None:
                self.lbl_validacion_abono_subsidio.setText("Debe ingresar valores validos en los abonos para hacer la validación")
                self.lbl_validacion_abono_subsidio.setStyleSheet("color:red")
                return
            
            if self.abono_previo_val is not None and self.abono_real_val is not None:
                dif_a_pagar = self.abono_real_val - self.abono_previo_val
                dif_a_pagar_int = int(dif_a_pagar)

            if self.abono_previo_val >= self.abono_real_val:
                self.lbl_validacion_abono_subsidio.setText("El abono previo cubre o supera el abono real, el comprador no debe depositar.")
                self.lbl_validacion_abono_subsidio.setStyleSheet("color: green;")
            else:
                self.lbl_validacion_abono_subsidio.setText(f"El abono real es mayor al abono previo, el comprador debe depositar: {dif_a_pagar_int}")
                self.lbl_validacion_abono_subsidio.setStyleSheet("color: orange;")

       
 

    def setup_tab_confeccion_subsidio(self, tab):
        layout = QFormLayout(tab)

        # --- Documentos Confección ---
        layout.addRow(QLabel("<b>Documentos Confección:</b>"))

        self.cmb_doc_propiedad_confe = QComboBox()
        self.cmb_doc_propiedad_confe.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_doc_tasacion = QComboBox()
        self.cmb_doc_tasacion.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_doc_dj_no_parent_comp_vend = QComboBox()
        self.cmb_doc_dj_no_parent_comp_vend.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_doc_subsidio_original = QComboBox()
        self.cmb_doc_subsidio_original.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_doc_dj_vend_no_habitual = QComboBox()
        self.cmb_doc_dj_vend_no_habitual.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_doc_dj_comp_no_parientes_cargos_publicos = QComboBox()
        self.cmb_doc_dj_comp_no_parientes_cargos_publicos.addItems(["Si Posee Documento", "No Posee Documento"])

        layout.addRow(self.crear_label("Documento Propiedad:"), self.cmb_doc_propiedad_confe)
        layout.addRow(self.crear_label("Documento Tasación:"), self.cmb_doc_tasacion)
        layout.addRow(self.crear_label("Declaración Jurada no parentesco comprador/vendedor:"), self.cmb_doc_dj_no_parent_comp_vend)
        layout.addRow(self.crear_label("Documento Subsidio Original:"), self.cmb_doc_subsidio_original)
        layout.addRow(self.crear_label("Declaración Jurada vendedor no habitual:"), self.cmb_doc_dj_vend_no_habitual)
        layout.addRow(self.crear_label("Declaración Jurada No Inhabilidad:"), self.cmb_doc_dj_comp_no_parientes_cargos_publicos)

        # --- Validación de Abonos ---
        
        layout.addRow(QLabel("<b>Validación de Abonos:</b>"))

        # Crear campos de texto
        self.txt_abono_previo = QLineEdit()
        self.txt_abono_real = QLineEdit()

        # Configurar placeholders
        self.txt_abono_previo.setPlaceholderText("Ej: 4.0")
        self.txt_abono_real.setPlaceholderText("Ej: 2.0")
        

        layout.addRow(self.crear_label("Abono previo:"), self.txt_abono_previo)
        layout.addRow(self.crear_label("Abono real:"), self.txt_abono_real)

        self.lbl_validacion_abono_subsidio = QLabel("Ingrese ambos abonos para validar")
        self.lbl_validacion_abono_subsidio.setMinimumHeight(30)
        self.lbl_validacion_abono_subsidio.setAlignment(Qt.AlignLeft)
        layout.addRow(QLabel("Resultado validación:"), self.lbl_validacion_abono_subsidio)

        self.abono_previo_val = None
        self.abono_real_val = None

        # Conectar señales
        self.txt_abono_previo.textChanged.connect(self.on_abono_previo_cambiado_subsidio)
        self.txt_abono_real.textChanged.connect(self.on_abono_real_cambiado_subsidio)


                
    def setup_tab_confeccion_credito(self, tab):
        layout = QFormLayout(tab)

        layout.addRow(QLabel("<b>Documentos Confección:</b>"))

        self.cmb_doc_propiedad_confe = QComboBox()
        self.cmb_doc_propiedad_confe.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_doc_tasacion = QComboBox()
        self.cmb_doc_tasacion.addItems(["Si Posee Documento", "No Posee Documento"])
        self.cmb_doc_dj_vend_no_habitual = QComboBox()
        self.cmb_doc_dj_vend_no_habitual.addItems(["Si Posee Documento", "No Posee Documento"])
        
        


        layout.addRow(self.crear_label("Documento Propiedad:"), self.cmb_doc_propiedad_confe)
        layout.addRow(self.crear_label("Documento Tasación:"), self.cmb_doc_tasacion)
        layout.addRow(self.crear_label("Declaración Jurada vendedor no habitual:"), self.cmb_doc_dj_vend_no_habitual)
        


    def setup_tab_docs_pas(self, tab):
        layout = QFormLayout(tab)

        layout.addRow(QLabel("<b>Documentos PAS:</b>"))

        self.cmb_supe_platas = QComboBox()
        self.cmb_supe_platas.addItems(["Plata en custodia", "Inscripción en CBR", "Plata liberada"])

        self.fecha_ingreso_documentos = QDateEdit(QDate.currentDate())
        self.fecha_ingreso_documentos.setCalendarPopup(True)

        self.checkbox_reparos = QCheckBox("¿Existen reparos?")
        self.checkbox_reparos.setChecked(False)

        self.txt_reparos = QTextEdit()

        layout.addRow(self.crear_label("Fecha de ingreso documentos:"), self.fecha_ingreso_documentos)

        layout.addRow(self.crear_label("Estado de Custodia y Pago:"), self.cmb_supe_platas)

        layout.addWidget(self.checkbox_reparos)
        self.lbl_reparos = self.crear_label("Reparos:")
        layout.addRow(self.lbl_reparos, self.txt_reparos)
        self.lbl_reparos.hide()
        self.txt_reparos.hide()
        self.checkbox_reparos.stateChanged.connect(self.verificar_reparos)



    def verificar_reparos(self):
        mostrar = self.checkbox_reparos.isChecked()
        self.lbl_reparos.setVisible(mostrar)
        self.txt_reparos.setVisible(mostrar)


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

        self.cmb_superficie = QComboBox()
        self.cmb_superficie.addItems(["Si Posee Documento", "No Posee Documento"])

        self.cmb_edificada = QComboBox()
        self.cmb_edificada.addItems(["Si Posee Documento", "No Posee Documento"])

        self.cmb_recepcion = QComboBox()
        self.cmb_recepcion.addItems(["Si Posee Documento", "No Posee Documento"])


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

        

        self.titulo_tipo_venta = QLabel("<b>Documentos Subsidio/Credito Hipotecario/Credito Hipotecario + Subsidio:</b>")
        
        self.lbl_superficie = self.crear_label("Doc Superficie:")
        self.lbl_edificada = self.crear_label("Prop Edificada:")
        self.lbl_recepcion = self.crear_label("Doc Recepcion:")

        layout.addRow(self.titulo_tipo_venta)
        layout.addRow(self.lbl_superficie, self.cmb_superficie)
        layout.addRow(self.lbl_edificada, self.cmb_edificada)
        layout.addRow(self.lbl_recepcion, self.cmb_recepcion)

        self.titulo_tipo_venta.hide()
        self.lbl_superficie.hide()
        self.cmb_superficie.hide()
        self.lbl_edificada.hide()
        self.cmb_edificada.hide()
        self.lbl_recepcion.hide()
        self.cmb_recepcion.hide()

        # Conectar la señal para que muestre/oculte campos extras
        self.cmb_tipo_venta.currentTextChanged.connect(self.toggle_campos_propiedad)

    def toggle_campos_propiedad(self, texto_seleccionado):
        mostrar = texto_seleccionado in ["Subsidio", "Credito H.", "Credito H. + Subsidio"]
        self.titulo_tipo_venta.setVisible(mostrar)
        self.lbl_superficie.setVisible(mostrar)
        self.cmb_superficie.setVisible(mostrar)
        self.lbl_edificada.setVisible(mostrar)
        self.cmb_edificada.setVisible(mostrar)
        self.lbl_recepcion.setVisible(mostrar)
        self.cmb_recepcion.setVisible(mostrar)

    def setup_tab_pos_efectiva(self, tab):
        layout = QVBoxLayout(tab)
        
        # Tipo de posesión
        self.cmb_tipo_pos = QComboBox()
        self.cmb_tipo_pos.addItems(["Testada", "Intestada"])
        self.cmb_tipo_pos.currentTextChanged.connect(self.actualizar_formulario_herederos)
        
        # Canal
        self.cmb_canal = QComboBox()
        self.cmb_canal.addItems(["Justicia", "Registro Civil"])
        
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
        # Configurar columnas y encabezados según tipo de posesión
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

        # Recorrer todas las filas existentes y actualizar widgets según tipo de posesión
        for row in range(self.tabla_herederos.rowCount()):
            # --- Actualizar combobox columna 2 ---
            cmb_tipo = self.tabla_herederos.cellWidget(row, 2)
            if isinstance(cmb_tipo, QComboBox):
                # Guardar selección actual si existe
                seleccion = cmb_tipo.currentText()
                cmb_tipo.clear()
                if tipo_pos == "Testada":
                    cmb_tipo.addItems(["Forzoso", "Conyugue", "Hijo", "Padre"])
                else:
                    cmb_tipo.addItems(["Conyugue", "Hijo", "Padre", "Fisco", "Otro"])
                # Restaurar selección si sigue en la lista
                if seleccion in [cmb_tipo.itemText(i) for i in range(cmb_tipo.count())]:
                    cmb_tipo.setCurrentText(seleccion)
                else:
                    cmb_tipo.setCurrentIndex(0)  # O selecciona el primer item

            # --- Columnas 3 y 4 solo para Testada ---
            if tipo_pos == "Testada":
                # Columna 3: Recibe mejoras (checkbox)
                if self.tabla_herederos.item(row, 3) is None:
                    chk_mejoras = QTableWidgetItem()
                    chk_mejoras.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    chk_mejoras.setCheckState(Qt.Unchecked)
                    self.tabla_herederos.setItem(row, 3, chk_mejoras)

                # Columna 4: % Libre disposición (spinbox)
                if self.tabla_herederos.cellWidget(row, 4) is None:
                    spin_porcentaje = QDoubleSpinBox()
                    spin_porcentaje.setRange(0, 100)
                    spin_porcentaje.setValue(0)
                    self.tabla_herederos.setCellWidget(row, 4, spin_porcentaje)

            else:  # Intestada
                # Eliminar columna 3 y 4 si existían
                if self.tabla_herederos.item(row, 3) is not None:
                    self.tabla_herederos.setItem(row, 3, None)
                if self.tabla_herederos.cellWidget(row, 4) is not None:
                    self.tabla_herederos.removeCellWidget(row, 4)
    
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

            texto_estado = self.cmb_estado.currentText().lower()

            # Excepción para "En Proceso"
            if texto_estado == "en proceso":
                texto_estado = "en_proceso"



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
                'pre_aprobacion_credito':{
                    'porcentaje_financiamiento': self.txt_porc_financiamiento.text().replace("%", "").strip(),
                    'monto_financiamiento': self.txt_monto_financiamiento.text(),
                    'diferencias': self.txt_diferencias_prea_credito.toPlainText(),
                    'banco_credito': self.txt_banco_credito.text(),
                    'estado_preaprobacion': self.cmb_estado_aprobacion.currentText()
                },
                'subsidio_aprobado' : {
                    'monto_subsidio': self.txt_monto_subsidio.text(),
                    'porcentaje_subsidio': self.txt_porc_subsidio.text().replace("%", "").strip(),
                    'resolucion_subsidio': self.txt_resolucion_subsidio.toPlainText(),
                    'estado_subsidio': self.cmb_estado_subsidio.currentText()
                },

                'tasador':{
                    'nombre': self.txt_tas_nombre.text(),
                    'rut': self.txt_tas_rut.text(),
                    'telefono': self.txt_tas_telefono.text(),
                    'correo': self.txt_tas_email.text()
                },
                'documentos_tasacion':{
                    'doc_propiedad':self.cmb_doc_propiedad_tas.currentText(),
                    'copia_subsidio':self.cmb_copia_subsidio.currentText(),
                    'informe_tasacion':self.cmb_informe_tasacion.currentText(),
                    'certif_habitabilidad':self.cmb_certif_habitabilidad.currentText()
                },

                'documentos_escritura':{
                    'doc_propiedad': self.cmb_doc_propiedad_confe.currentText(),
                    'doc_tasacion': self.cmb_doc_tasacion.currentText(),
                    'dj_no_parent_comp_vend': self.cmb_doc_dj_no_parent_comp_vend.currentText(),
                    'subsidio_original': self.cmb_doc_subsidio_original.currentText(),
                    'dj_vend_no_habitual': self.cmb_doc_dj_vend_no_habitual.currentText(),
                    'dj_comp_no_parientes_cargos_publicos': self.cmb_doc_dj_comp_no_parientes_cargos_publicos.currentText()
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
                    'dominio_vigente': self.cmb_dominio_vigente.currentText()
                },
              
                'recepcion_definitiva':{
                    'superficie':self.cmb_superficie.currentText(),
                    'edificada':self.cmb_edificada.currentText(),
                    'recepcion':self.cmb_recepcion.currentText()
                },
                'documentos_pas':{
                    'fecha_ingreso_docs' : self.fecha_ingreso_documentos.date().toString("yyyy-MM-dd"),
                    'supe_platas' : self.cmb_supe_platas.currentText(),
                    'reparos' : self.txt_reparos.toPlainText()
                },

                'venta': {
                    'fecha_venta': self.date_fecha.date().toString("yyyy-MM-dd"),
                    'monto_venta': self.txt_monto.text() if self.txt_monto.text() else None,
                    'observaciones': self.txt_observaciones.toPlainText(),
                    'tipo_venta': self.cmb_tipo_venta.currentText(),
                    'estado_venta': texto_estado,
                    'propiedad_ofrecida': self.cmb_prop_ofrecida.currentText(),
                    'regularizaciones': self.cmb_regularizaciones.currentText(),
                    'limitaciones': 'No',  # Valor por defecto
                    'viabilidad': '', # Valor por defecto
                    'inscripcion': self.cmb_inscripcion.currentText(),
                    'hipoteca': self.cmb_hipoteca.currentText(),
                    'gravamen': self.cmb_gravamen.currentText(),
                    'certificado_numero': self.cmb_certificado_numero.currentText(),
                    'aseo': self.cmb_aseo.currentText(),
                    'no_expropiacion': self.cmb_no_expropiacion.currentText(),
                    'abono_previsto': self.txt_abono_previo.text(),
                    'abono_real': self.txt_abono_real.text()
                }
            }
            
            # Preparar datos de posesión efectiva si es venta cerrada y tipo es Posesión Efectiva
            posesion_efectiva = None
            herederos = []
            mejoras = []
            libre_disposicion = {}
            
            if not self.en_proceso and self.cmb_tipo_venta.currentText() == "Posesion Efectiva":
                posesion_efectiva = {
                    'tipo': self.cmb_tipo_pos.currentText(),
                    'canal': self.cmb_canal.currentText(),
                    'estado_proceso': self.cmb_estado_proceso.currentText(),
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
                self.venta_guardada.emit()
                self.close()
            else:
                print("guardar_venta retornó ID falso o None")
        
        except Exception as e:
            print(f"Error en guardar_venta: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar la venta: {str(e)}")
    
    def validar_campos_obligatorios(self):
        # Validar campos obligatorios básicos
        campos_obligatorios = [
            (self.txt_prop_codigo.text(), "Código de propiedad"),
            (self.txt_prop_direccion.text(), "Dirección de propiedad"),
            (self.txt_prop_rol.text(), "ROL de propiedad"),
            (self.txt_prop_comuna.text(), "Comuna de propiedad")
        ]
        
        if not self.en_proceso:

            campos_obligatorios += [
                (self.txt_comp_nombre.text(), "Nombre del comprador"),
                (self.txt_comp_rut.text(), "RUT del comprador"),
                (self.txt_vend_nombre.text(), "Nombre del vendedor"),
                (self.txt_vend_rut.text(), "RUT del vendedor"),
            ]


        for valor, nombre in campos_obligatorios:
            if not valor.strip():
                QMessageBox.warning(self, "Campo obligatorio", f"El campo {nombre} es obligatorio")
                return False
        
        # Validar RUTs
        if not self.en_proceso:
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
    

    def cargar_datos_venta(self, venta_id):
        try:
            # Obtener la venta
            
            venta = self.detalle_venta.get('venta', {})
            
    
            self.date_fecha.setDate(QDate.fromString(venta.get("fecha_venta", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
            self.txt_monto.setText(f"{(int(venta.get('monto_venta', 0))):,}".replace(",", "."))
            self.txt_observaciones.setPlainText(venta.get("observaciones", ""))


            self.cmb_tipo_venta.setCurrentText(venta.get("tipo_venta", ""))
            self.cmb_estado.setCurrentText(venta.get("estado_venta", ""))
            self.cmb_prop_ofrecida.setCurrentText(venta.get("propiedad_ofrecida", "No"))
            self.cmb_regularizaciones.setCurrentText(venta.get("regularizaciones_ampliaciones", "No"))

            tipo_venta = venta.get("tipo_venta", "")
            self.cmb_tipo_venta.setCurrentText(tipo_venta)

            estado_bd = venta.get("estado_venta", "")

            if estado_bd == "en_proceso":
                estado_combo = "En Proceso"
            else:
                # Convierte solo la primera letra a mayúscula, mantiene el resto igual
                estado_combo = estado_bd.replace("_", " ").capitalize()

            # Buscar y seleccionar el texto correcto en el combo
            index = self.cmb_estado.findText(estado_combo, Qt.MatchFixedString)
            if index >= 0:
                self.cmb_estado.setCurrentIndex(index)
                                    

            # Obtener comprador
            comp = self.detalle_venta.get('comprador', {})
            if comp and comp.get("rut"):
                self.txt_comp_nombre.setText(comp.get("nombre", ""))
                self.txt_comp_rut.setText(comp.get("rut", ""))
                self.txt_comp_direccion.setText(comp.get("direccion", ""))
                self.txt_comp_telefono.setText(comp.get("telefono", ""))
                self.txt_comp_email.setText(comp.get("correo", ""))
                self.txt_comp_banco.setText(comp.get("banco", ""))
                self.txt_comp_tipo_cuenta.setText(comp.get("tipo_cuenta", ""))
                self.txt_comp_nro_cuenta.setText(comp.get("nro_cuenta", ""))
                self.cmb_comp_poder.setCurrentText(comp.get("poder_judicial"))
                 

            # Obtener vendedor
            vend = self.detalle_venta.get('vendedor', {})
            if vend and vend.get("rut"):
                self.txt_vend_nombre.setText(vend.get("nombre", ""))
                self.txt_vend_rut.setText(vend.get("rut", ""))
                self.txt_vend_direccion.setText(vend.get("direccion", ""))
                self.txt_vend_telefono.setText(vend.get("telefono", ""))
                self.txt_vend_email.setText(vend.get("correo", ""))
                self.txt_vend_banco.setText(vend.get("banco", ""))
                self.txt_vend_tipo_cuenta.setText(vend.get("tipo_cuenta", ""))
                self.txt_vend_nro_cuenta.setText(vend.get("nro_cuenta", ""))
                self.cmb_vend_poder.setCurrentText(vend.get("poder_judicial"))


            # Obtener la propiedad
            propiedad = self.detalle_venta.get('propiedad', {})
            
            if propiedad:
                self.txt_prop_codigo.setText(propiedad.get("codigo_interno", ""))
                self.txt_prop_direccion.setText(propiedad.get("direccion", ""))
                self.txt_prop_rol.setText(str(propiedad.get("rol", "")))
                self.txt_prop_comuna.setText(propiedad.get("comuna", ""))
                self.cmb_estudio_titulos.setCurrentText(propiedad.get("estudio_titulos", "No Posee Documento"))
                self.cmb_inscripcion.setCurrentText(venta.get("inscripcion", "No Posee Documento"))
                self.cmb_dominio_vigente.setCurrentText(propiedad.get("dominio_vigente","No Posee Documento"))
                self.cmb_hipoteca.setCurrentText(venta.get("hipoteca","No Posee Documento"))
                self.cmb_gravamen.setCurrentText(venta.get("gravamen","No Posee Documento"))
                self.cmb_certificado_numero.setCurrentText(venta.get("certificado_numero","No Posee Documento"))
                self.cmb_aseo.setCurrentText(venta.get("aseo","No Posee Documento"))
                self.cmb_no_expropiacion.setCurrentText(venta.get("no_expropiacion","No Posee Documento"))
            
            if tipo_venta == "Posesion Efectiva":
                # Obtener posesion efectiva
                posesion = self.detalle_venta.get('posesion', {})
                
                if posesion:
                
                    self.cmb_tipo_pos.setCurrentText(posesion.get("tipo_posesion"))
                    self.cmb_canal.setCurrentText(posesion.get("canal"))
                    self.cmb_estado_proceso.setCurrentText(posesion.get("estado_proceso"))
                    self.txt_obs_pos.setPlainText(posesion.get("observaciones", ""))
                
                # Obtener herederos
                herederos = self.detalle_venta.get('herederos', [])
                if isinstance(herederos, str):
                    try:
                        herederos = json.loads(herederos)
                    except json.JSONDecodeError:
                        herederos = []

                # Si es un solo dict (un solo heredero), lo ponemos en una lista
                if isinstance(herederos, dict):
                    herederos = [herederos]

                # Si no es lista después de esto, forzamos una lista vacía
                if not isinstance(herederos, list):
                    herederos = []

                
                
                if herederos:
                    self.poblar_tabla_herederos(herederos, self.cmb_tipo_pos.currentText())

            
            if tipo_venta in ["Subsidio", "Credito H.", "Credito H. + Subsidio"]:
                # Obtener recepcion definitiva
                recep = self.detalle_venta.get('documentacion', {})
                if recep:
                    
                    self.cmb_superficie.setCurrentText(recep.get("superficie","No Posee Documento"))
                    self.cmb_edificada.setCurrentText(recep.get("edificada","No Posee Documento"))
                    self.cmb_recepcion.setCurrentText(recep.get("recepcion","No Posee Documento"))
                    
            
            
                # Obtener Tasador en caso de venta con "Subsidio", "Credito H.", "Credito H. + Subsidio"

                tas = self.detalle_venta.get('tasacion', {})

                if tas:
                    
                    self.txt_tas_nombre.setText(tas.get("nombre",""))
                    self.txt_tas_rut.setText(tas.get("rut",""))
                    self.txt_tas_telefono.setText(tas.get("telefono",""))
                    self.txt_tas_email.setText(tas.get("correo_electronico",""))

                # Obtener documentos tasacion


                    self.cmb_doc_propiedad_tas.setCurrentText(tas.get("doc_propiedad","No Posee Documento"))
                    self.cmb_copia_subsidio.setCurrentText(tas.get("copia_subsidio","No Posee Documento"))
                    self.cmb_informe_tasacion.setCurrentText(tas.get("informe_tasacion ","No Posee Documento"))
                    self.cmb_certif_habitabilidad.setCurrentText(tas.get("certif_habitabilidad","No Posee Documento"))
                    

                

            if tipo_venta in ["Subsidio", "Credito H. + Subsidio"]:

                # Obtener pre aprobacion subsidio

                prea = self.detalle_venta.get('subsidio', {})
                

                if prea:

                    porcentaje_finan_sub = prea.get("porcentaje_subsidio")

                    if porcentaje_finan_sub is not None:

                        try:
                            # Usa Decimal para precisión exacta
                            porcentaje_decimal_sub = Decimal(str(porcentaje_finan_sub)) * Decimal(100)
                                # Redondea a 2 decimales
                            porcentaje_finan_sub_str = str(porcentaje_decimal_sub.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
                        except Exception:
                            porcentaje_finan_sub_str = ""

                    else:
                        porcentaje_finan_sub_str = ""

                    
                    self.txt_porc_subsidio.setText(porcentaje_finan_sub_str)
                    self.txt_monto_subsidio.setText(f"{(int(prea.get('monto_subsidio', 0))):,}".replace(",", "."))
                    self.cmb_estado_subsidio.setCurrentText(prea.get("estado_subsidio", "Sin definir"))
                    self.txt_resolucion_subsidio.setPlainText(prea.get("resolucion_subsidio", ""))

                # Obtener confeccion escritura

                confe_sub  = self.detalle_venta.get('confeccion', {})

                if confe_sub:

                    self.cmb_doc_propiedad_confe.setCurrentText(confe_sub.get("doc_propiedad","No Posee Documento"))
                    self.cmb_doc_tasacion.setCurrentText(confe_sub.get("doc_tasacion","No Posee Documento"))
                    self.cmb_doc_dj_no_parent_comp_vend.setCurrentText(confe_sub.get("dj_no_parent_comp_vend","No Posee Documento"))
                    self.cmb_doc_subsidio_original.setCurrentText(confe_sub.get("subsidio_original","No Posee Documento"))
                    self.cmb_doc_dj_vend_no_habitual.setCurrentText(confe_sub.get("dj_vend_no_habitual","No Posee Documento"))
                    self.cmb_doc_dj_comp_no_parientes_cargos_publicos.setCurrentText(confe_sub.get("dj_comp_no_parientes_cargos_publicos","No Posee Documento"))

                    self.txt_abono_previo.setText(f"{(int(venta.get('abono_previsto', 0))):,}".replace(",", "."))
                    self.txt_abono_real.setText(f"{(int(venta.get('abono_real', 0))):,}".replace(",", "."))
                
                # Obtener docs pas

                doc_pas = self.detalle_venta.get('PAS', {})

                if doc_pas:

                    self.fecha_ingreso_documentos.setDate(QDate.fromString(doc_pas.get("fecha_ingreso_docs", QDate.currentDate().toString("yyyy-MM-dd")), "yyyy-MM-dd"))
                    self.cmb_supe_platas.setCurrentText(doc_pas.get("supe_platas"))
                    self.txt_reparos.setPlainText(doc_pas.get("reparos", ""))


            

            if tipo_venta in ["Credito H.", "Credito H. + Subsidio"]:
                
                # Obtener pre aprobacion de credito
                prea_cred = self.detalle_venta.get('aproba_cred', {})

                if prea_cred:

                    porcentaje_finan_cred = prea_cred.get("porcentaje_financiamiento")

                    if porcentaje_finan_cred is not None:

                        try:
                            # Usa Decimal para precisión exacta
                            porcentaje_decimal = Decimal(str(porcentaje_finan_cred)) * Decimal(100)
                            # Redondea a 2 decimales
                            porcentaje_finan_cred_str = str(porcentaje_decimal.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
                        except Exception:
                            porcentaje_finan_cred_str = ""
                    else:
                        porcentaje_finan_cred_str = ""

                    

                    self.txt_porc_financiamiento.setText(porcentaje_finan_cred_str)
                    self.txt_monto_financiamiento.setText(f"{(int(prea_cred.get('monto_financiamiento', 0))):,}".replace(",", "."))
                    self.txt_banco_credito.setText(prea_cred.get("banco_credito",""))
                    self.cmb_estado_aprobacion.setCurrentText(prea_cred.get("estado_preaprobacion"))
                    self.txt_diferencias_prea_credito.setPlainText(prea_cred.get("diferencias",""))


                # Obtener confección credito

                confe_cred = self.detalle_venta.get('confeccion', {})

                if confe_cred:
                    self.cmb_doc_propiedad_confe.setCurrentText(confe_cred.get("doc_propiedad","No Posee Documento"))
                    self.cmb_doc_tasacion.setCurrentText(confe_cred.get("doc_tasacion","No Posee Documento"))
                    self.cmb_doc_dj_vend_no_habitual.setCurrentText(confe_cred.get("dj_vend_no_habitual","No Posee Documento"))




        except Exception as e:
            print(f"Error al cargar venta: {str(e)}")
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los datos de la venta: {str(e)}")

    def poblar_tabla_herederos(self, herederos, tipo_pos):
        """Llena la tabla de herederos según tipo de posesión."""
        self.cmb_tipo_pos.setCurrentText(tipo_pos)
        self.actualizar_formulario_herederos(tipo_pos)

        self.tabla_herederos.setRowCount(0)

        for idx, heredero in enumerate(herederos):
            self.tabla_herederos.insertRow(idx)

            # Columna 0: Nombre
            self.tabla_herederos.setItem(idx, 0, QTableWidgetItem(heredero.get("nombre", "")))

            # Columna 1: RUT
            self.tabla_herederos.setItem(idx, 1, QTableWidgetItem(heredero.get("rut", "")))

            # Columna 2: Tipo Heredero (ComboBox)
            cmb_tipo = QComboBox()
            if tipo_pos == "Testada":
                cmb_tipo.addItems(["Forzoso", "Conyugue", "Hijo", "Padre"])
            else:
                cmb_tipo.addItems(["Conyugue", "Hijo", "Padre", "Fisco", "Otro"])
            
            tipo = heredero.get("tipo_heredero", "")
            if tipo:
                cmb_tipo.setCurrentText(tipo.capitalize())
            self.tabla_herederos.setCellWidget(idx, 2, cmb_tipo)

            # Columnas 3 y 4 solo para Testada
            if tipo_pos == "Testada":
                # Columna 3: Recibe mejoras (checkbox)
                chk_mejoras = QTableWidgetItem()
                chk_mejoras.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk_mejoras.setCheckState(Qt.Checked if heredero.get("recibe_mejoras", False) else Qt.Unchecked)
                self.tabla_herederos.setItem(idx, 3, chk_mejoras)

                # Columna 4: % Libre disposición (spinbox)
                spin_porcentaje = QDoubleSpinBox()
                spin_porcentaje.setRange(0, 100)
                spin_porcentaje.setValue(heredero.get("porcentaje_libre_disposicion", 0))
                self.tabla_herederos.setCellWidget(idx, 4, spin_porcentaje)
