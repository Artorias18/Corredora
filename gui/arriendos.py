from PySide6.QtWidgets import QHeaderView,QGroupBox ,QSizePolicy, QFileDialog, QMainWindow,QHBoxLayout,QTextEdit,QTabWidget,QDoubleSpinBox,QHeaderView,QFrame,QWidget,QLabel, QVBoxLayout,QAbstractItemView,QTableWidget,QTableWidgetItem,QScrollArea, QFormLayout, QLineEdit, QComboBox, QPushButton,QLabel, QDateEdit, QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem,QSpinBox, QDialog
from services.arriendos_service import obtener_arriendos_resumen, obtener_detalle_arriendo,obtener_arriendos_finanzas,obtener_arriendos_por_estado, guardar_arriendo
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QIntValidator, QColor, QDoubleValidator
from gui.usuario_actual import UsuarioActual
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from services.supabase_client import supabase
import json
import pandas as pd


class DetalleArriendoWindow(QWidget):
    def __init__(self, arriendo_id,):
        super().__init__()

        self.arriendo_id = arriendo_id
        self.setWindowTitle(f"Detalle de Arriendo #{arriendo_id}")
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


        self.detalle_arriendo = obtener_detalle_arriendo(arriendo_id)

        if not self.detalle_arriendo:
            layout_contenido.addWidget(QLabel("No se encontraron detalles para esta venta"))
            return
        
        self.tabs = QTabWidget()
        layout_contenido.addWidget(self.tabs)
        

        self.setup_tab_arrendador()
       
        self.setup_tab_arrendatario()

        self.setup_tab_propiedad()
       
        self.setup_tab_evaluacion()
    
        self.setup_tab_arriendo()
      








         # Botón para cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.close)
        layout_contenido.addWidget(btn_cerrar)
        
        # self.btn_editar = QPushButton("Editar Venta")
        # self.btn_editar.clicked.connect(self.abrir_formulario_edicion)
        # layout_contenido.addWidget(self.btn_editar)

        # self.btnEliminar = QPushButton("Eliminar Venta")
        # self.btnEliminar.clicked.connect(self.eliminar_venta)
        # layout_contenido.addWidget(self.btnEliminar)
        

    def setup_tab_arrendador(self):
        tab = QWidget()
        self.tabs.addTab(tab,"Arrendador")
        layout = QFormLayout(tab)

        arrendador = self.detalle_arriendo.get('arrendador', {})

        campos = [
            ("Nombre", arrendador.get('nombre')),
            ("Rut", arrendador.get('rut')),
            ("Teléfono", arrendador.get('telefono')),
            ("Dirección", arrendador.get('direccion')),
            ('Correo', arrendador.get('correo_electronico'))
        ]

        for label, value in campos:
            if value:
                layout.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))
        


    
    def setup_tab_arrendatario(self):
        tab = QWidget()
        self.tabs.addTab(tab,"Arrendatario")
        layout = QFormLayout(tab)

        arrendatario = self.detalle_arriendo.get('arrendatario', {})

        campos = [
            ("Nombre", arrendatario.get('nombre')),
            ("Rut", arrendatario.get('rut')),
            ("Teléfono", arrendatario.get('telefono')),
            ("Dirección", arrendatario.get('direccion')),
            ('Correo', arrendatario.get('email')),
            ("Tipo de Trabajador", arrendatario.get('tipo_trabajador')),
            ("Antigüedad Laboral", arrendatario.get('antiguedad_laboral')),
            ("¿Tiene Dicom?", arrendatario.get('dicom')),
            ("Estado de Evaluación", arrendatario.get('evaluacion_estado')),
            ("Renta", arrendatario.get('renta')),
            ("Comentarios", arrendatario.get('comentarios'))
            ]
        
        for label, value in campos:
            if value:
                layout.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))

    def setup_tab_propiedad(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Propiedad")
        layout = QFormLayout(tab)
        
        propiedad = self.detalle_arriendo.get('propiedad', {})

        campos= [
            ("Código interno", propiedad.get('codigo_interno')),
            ("Dirección", propiedad.get('direccion')),
            ("ROL", propiedad.get('rol')),
            ("Comuna", propiedad.get('comuna')),
            ("Dominio vigente", propiedad.get('dominio_vigente'))
        ]

        for label, value in campos:
            if value:
                layout.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))


    def setup_tab_evaluacion(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Evaluación Arriendo")
        layout = QFormLayout(tab)
        
        evaluacion= self.detalle_arriendo.get('evaluacion_arrendatario', {})

        campos = [
            ("Fecha de Evaluación", evaluacion.get('fecha_evaluacion')),
            ("Sueldo Base", evaluacion.get('sueldo_base')),
            ("Gratificación", evaluacion.get('gratificacion')),
            ("Total Imponible", evaluacion.get('total_imponible')),
            ("Total no Imponible", evaluacion.get('total_no_imponible')),
            ("Descuentos Legales", evaluacion.get('descuentos_legales')),
            ("Impuesto Renta", evaluacion.get('im_renta')),
            ("Total Haberes", evaluacion.get('total_haberes')),
            ("Líquido a Pago", evaluacion.get('liquido_pago')),
            ("Anticipo", evaluacion.get('anticipo')),
            ("Descuentos Varios", evaluacion.get('desc_varios')),
            ("Locomoción", evaluacion.get('locomocion')),
            ("Resultado", evaluacion.get('resultado')),
            ("Comentarios", evaluacion.get('comentarios'))
        ]


        for label, value in campos:
            if value:
                layout.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))

        
    def setup_tab_arriendo(self):
        tab = QWidget()
        self.tabs.addTab(tab, "Arriendo")
        layout = QFormLayout(tab)
        
        arriendo = self.detalle_arriendo.get('arriendo', {})

        box_basicos = QGroupBox("Datos Básicos del Arriendo")
        layout_basicos = QFormLayout()

        campos_basicos = [
            ("Fecha Inicio", arriendo.get("fecha_inicio")),
            ("Fecha de Término", arriendo.get("fecha_termino")),
            ("Renta Mensual", arriendo.get("renta_mensual")),
            ("Garantía", arriendo.get("garantia")),
            ("Gastos comunes incluidos", "Sí" if arriendo.get("gastos_comunes_incluidos") else "No"),
            ("Estado del arriendo", arriendo.get("estado")),
            ("Tipo de contrato", arriendo.get("tipo_contrato")),
        ]

        for label, value in campos_basicos:
            if value not in (None, "", 0):
                layout_basicos.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))

        box_basicos.setLayout(layout_basicos)
        layout.addWidget(box_basicos)

        # ======================================
        #   SECCIÓN 2: PAGOS
        # ======================================
        box_pagos = QGroupBox("Datos de Pago")
        layout_pagos = QFormLayout()

        campos_pagos = [
            ("Forma de pago", arriendo.get("forma_pago")),
            ("Periodo de pago", arriendo.get("periodo_pago")),
            ("Día de pago", arriendo.get("dia_pago")),
            ("Cuenta FM", arriendo.get("cuenta_fm")),
        ]

        for label, value in campos_pagos:
            if value not in (None, "", 0):
                layout_pagos.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))

        box_pagos.setLayout(layout_pagos)
        layout.addWidget(box_pagos)

        # ======================================
        #   SECCIÓN 3: DEPÓSITOS / CUENTA DESTINO
        # ======================================
        box_depositos = QGroupBox("Depósitos / Cuenta destino")
        layout_depositos = QFormLayout()

        campos_depositos = [
            ("Número de cuenta", arriendo.get("nro_cuenta")),
            ("Banco destino", arriendo.get("banco_destino")),
            ("Tipo de cuenta", arriendo.get("tipo_cuenta")),
            ("RUT para depósito", arriendo.get("rut_para_deposito")),
            ("Titular depósito", arriendo.get("titular_deposito")),
            ("Quién deposita", arriendo.get("quien_deposita")),
            ("Correo depósito", arriendo.get("correo_deposito")),
        ]

        for label, value in campos_depositos:
            if value not in (None, "", 0):
                layout_depositos.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))

        box_depositos.setLayout(layout_depositos)
        layout.addWidget(box_depositos)

        # ======================================
        #   SECCIÓN 4: HONORARIOS
        # ======================================
        box_honorarios = QGroupBox("Honorarios")
        layout_honorarios = QFormLayout()

        campos_honorarios = [
            ("Honorarios (%)", arriendo.get("honorarios_porcentaje")),
            ("Honorarios (monto)", arriendo.get("honorarios_monto")),
        ]

        for label, value in campos_honorarios:
            if value not in (None, "", 0):
                layout_honorarios.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))

        box_honorarios.setLayout(layout_honorarios)
        layout.addWidget(box_honorarios)

        # ======================================
        #   SECCIÓN 5: INFORMACIÓN ADICIONAL
        # ======================================
        box_extra = QGroupBox("Información adicional")
        layout_extra = QFormLayout()

        campos_extra = [
            ("Último mes pago", arriendo.get("ultimo_mes_pago")),
            ("Aseo municipal", arriendo.get("aseo_municipal")),
            ("Reajuste", arriendo.get("reajuste")),
            ("GGCC", arriendo.get("ggcc")),
            ("Cuenta GGCC", arriendo.get("cuenta_ggcc")),
            ("Dirección consulta", arriendo.get("direccion_consulta")),
            ("Periodo anterior", arriendo.get("periodo_anterior")),
            ("Monto anterior", arriendo.get("monto_anterior")),
            ("Naturaleza bien raíz", arriendo.get("naturaleza_bien_raiz")),
            ("DFL 2", arriendo.get("dfl12")),
            ("Destino", arriendo.get("destino")),
            ("Amoblado", arriendo.get("amoblado")),
            ("Observaciones", arriendo.get("observaciones")),
        ]

        for label, value in campos_extra:
            if value not in (None, "", 0):
                layout_extra.addRow(QLabel(f"<b>{label}:</b>"), QLabel(str(value)))

        box_extra.setLayout(layout_extra)
        layout.addWidget(box_extra)






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
        self.btn_exportar.clicked.connect(self.exportar_excel)
        
 
        
       
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
        
    def mostrar_detalle_arriendo(self, item):
        arriendo_id = int(self.tabla_arriendos.item(item.row(), 0).text())
        self.ventana_detalle = DetalleArriendoWindow(arriendo_id)
        self.ventana_detalle.show()

    def generar_excel_finanzas(self, datos, ruta):
        wb = Workbook()
        wb.remove(wb.active)

        df = pd.DataFrame(datos)

        if "id" in df.columns:
            df.drop(columns=["id"], inplace=True)

        # Convertir booleano GC incluido
        if "gastos_comunes_incluidos" in df.columns:
            df["GASTO COMUN"] = df["gastos_comunes_incluidos"].apply(
                lambda x: "Incluido" if x else "No incluido"
            )

        # Renombrar columnas
        df.rename(columns={
            "rol": "ROL",
            "comuna": "COMUNA",
            "direccion": "DIRECCION",
            "nombre_arrendatario": "NOMBRE ARRENDATARIO",
            "rut_arrendatario": "RUT ARRENDATARIO",
            "renta_mensual": "MONTO RENTA",
            "estado": "ESTADO",
            "fecha_inicio": "FECHA INICIO",
            "fecha_termino": "FECHA TERMINO",
            "nombre_propietario": "NOMBRE PROPIETARIO",
            "rut_propietario": "RUT PROPIETARIO",
            "correo_arrendatario": "CORREO ARRENDATARIO",
            "telefono_arrendatario": "TELEFONO",
            "forma_pago": "TIPO PAGO",
            "garantia": "GARANTIA"
        }, inplace=True)

        df["FECHA INICIO"] = pd.to_datetime(df["FECHA INICIO"])
        df["FECHA TERMINO"] = pd.to_datetime(df["FECHA TERMINO"])

        años = sorted(df["FECHA INICIO"].dt.year.unique(), reverse=True)

        # Estilos
        bold = Font(bold=True)
        header_fill = PatternFill(start_color="D9D9D9", fill_type="solid")
        center = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        hojas_por_año = {}

        # ============================================
        #   GENERAR HOJAS POR AÑO
        # ============================================
        for año in años:
            ws = wb.create_sheet(f"Arriendos {año}")
            hojas_por_año[año] = ws

            df_año = df[df["FECHA INICIO"].dt.year == año]
            df_vigentes = df_año[df_año["ESTADO"] == "Vigente"]
            df_finalizados = df_año[df_año["ESTADO"] != "Vigente"]

            # Título centrado
            ws.merge_cells("A1:R1")
            t = ws["A1"]
            t.value = f"Arriendos del Año {año}"
            t.font = Font(size=16, bold=True)
            t.alignment = center

            row_cursor = 3

            # ===============================
            #  FUNCIÓN PARA INSERTAR UNA TABLA
            # ===============================
            def insertar_tabla(df_tabla, titulo):
                nonlocal row_cursor

                # Subtítulo centrado encima de la tabla
                ws.merge_cells(start_row=row_cursor, start_column=1,
                            end_row=row_cursor, end_column=len(df.columns))
                cell_title = ws.cell(row=row_cursor, column=1, value=titulo)
                cell_title.font = Font(bold=True, size=14)
                cell_title.alignment = center
                row_cursor += 1

                # Crear tabla
                for r_idx, row in enumerate(dataframe_to_rows(df_tabla, index=False, header=True), row_cursor):
                    for c_idx, value in enumerate(row, 1):
                        c = ws.cell(row=r_idx, column=c_idx, value=value)

                        # Cabeceras
                        if r_idx == row_cursor:
                            c.font = bold
                            c.fill = header_fill
                            c.alignment = center

                        c.border = border

                row_cursor += len(df_tabla) + 2

            # ---- TABLAS ----
            if not df_vigentes.empty:
                insertar_tabla(df_vigentes, "ARRIENDOS VIGENTES")

            if not df_finalizados.empty:
                insertar_tabla(df_finalizados, "ARRIENDOS FINALIZADOS")

            hojas_por_año[año] = (ws, row_cursor)

        # ============================================
        #   CONTINUIDAD EN LA HOJA DEL AÑO ACTUAL
        # ============================================
        año_actual = max(años)
        ws, row_cursor = hojas_por_año[año_actual]

        df_cont = df[(df["FECHA INICIO"].dt.year < año_actual) & (df["ESTADO"] == "Vigente")]

        if not df_cont.empty:

            # Título centrado
            ws.merge_cells(start_row=row_cursor, start_column=1,
                        end_row=row_cursor, end_column=len(df.columns))
            t2 = ws.cell(row=row_cursor, column=1, value=f"CONTINUIDAD DESDE {año_actual - 1}")
            t2.font = Font(bold=True, size=14)
            t2.alignment = center

            row_cursor += 2

            # Tabla de continuidad
            for r_idx, row in enumerate(dataframe_to_rows(df_cont, index=False, header=True), row_cursor):
                for c_idx, value in enumerate(row, 1):
                    c = ws.cell(row=r_idx, column=c_idx, value=value)

                    if r_idx == row_cursor:
                        c.font = bold
                        c.fill = header_fill
                        c.alignment = center

                    c.border = border

            row_cursor += len(df_cont) + 2

        # ============================================
        #   AJUSTAR ANCHOS
        # ============================================
        for ws in wb.worksheets:
            for col_idx, column_cells in enumerate(ws.columns, 1):
                length = 0
                for cell in column_cells:
                    if cell.value:
                        length = max(length, len(str(cell.value)))
                ws.column_dimensions[get_column_letter(col_idx)].width = length + 3

        wb.save(ruta)
    #### ---------------- EXPORTADOR ---------------- ####

    def exportar_excel(self):
        datos = obtener_arriendos_finanzas()

        if not datos:
            QMessageBox.warning(self, "Sin datos", "No se encontraron arriendos para exportar.")
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Excel",
            "consolidado_arriendos",
            "Archivos Excel (*.xlsx)"
        )

        if not ruta:
            return

        if not ruta.endswith(".xlsx"):
            ruta += ".xlsx"

        try:
            self.generar_excel_finanzas(datos, ruta)
            QMessageBox.information(self, "Éxito", f"Excel generado correctamente:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar Excel:\n{e}")



    def abrir_formulario_arriendo(self):
        self.formulario_arriendo = FormularioArriendo()
        self.formulario_arriendo.arriendo_guardado.connect(self.cargar_arriendos)
        self.formulario_arriendo.show()

        
    

class FormularioArriendo(QWidget):
    arriendo_guardado = Signal()

    def __init__(self,arriendo_id=None, parent=None):
        super().__init__(parent)
        self.arriendo_id = arriendo_id
        self.rentas_tributables = []

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
        self.setup_tab_evaluacion_index = self.tabs.indexOf(tab_evaluacion)

        tab_evaluacion_independiente = QWidget()
        self.tabs.addTab(tab_evaluacion_independiente, "Evaluación")
        self.setup_tab_evaluacion_independiente(tab_evaluacion_independiente)
        self.setup_tab_evaluacion_independiente_index = self.tabs.indexOf(tab_evaluacion_independiente )

        tab_arriendo = QWidget()
        self.tabs.addTab(tab_arriendo, "Arriendo")
        self.setup_tab_arriendo(tab_arriendo)


        self.cmb_tipo_trabajador.currentTextChanged.connect(self.toggle_evaluacion_tab)
        self.toggle_evaluacion_tab(self.cmb_tipo_trabajador.currentText())

        self.cmb_tipo_trabajador.currentTextChanged.connect(self.toggle_evaluacion_independiente_tab)
        self.toggle_evaluacion_independiente_tab(self.cmb_tipo_trabajador.currentText())

        


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
        layout.addRow(self.crear_label("Antigüedad Laboral(Meses):"), self.txt_antiguedad_laboral)

        # --- Evaluación ---
        layout.addRow(self.crear_label("¿Tiene DICOM?"), self.cmb_dicom)
        layout.addRow(self.crear_label("Comentarios:"), self.txt_comentarios)
        layout.addRow(self.crear_label("Estado de Evaluación:"), self.cmb_evaluacion_estado)
        layout.addRow(self.crear_label("Fecha Evaluación:"), self.fecha_evaluacion)
        layout.addRow(self.crear_label("Renta Mensual:"), self.txt_renta)



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

        self.txt_impuesto_renta = QLineEdit()
        layout.addRow(self.crear_label("Impuesto Renta"), self.txt_impuesto_renta)

        self.btn_calcular_impuesto = QPushButton("Calcular Impuesto Renta")
        self.btn_calcular_impuesto.clicked.connect(self.abrir_dialogo_impuesto)
        layout.addRow(self.btn_calcular_impuesto)

        self.tbl_evaluacion = QTableWidget()
        self.tbl_evaluacion.setRowCount(9)
        self.tbl_evaluacion.setColumnCount(5)

        # Tamaño mínimo más grande
        self.tbl_evaluacion.setMinimumWidth(700)
        self.tbl_evaluacion.setMinimumHeight(300)

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

    def setup_tab_evaluacion_independiente(self, tab):
        pass

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

        self.calcular_resultados_evaluacion()

    
    def obtener_diccionario_evaluacion(self):
        col = 4  # columna Resultado

        mapping = [
            "sueldo_base",
            "gratificacion",
            "total_imponible",
            "locomocion",
            "total_no_imponible",
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



                
            

        

    def setup_tab_arriendo(self,tab):


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


        self.txt_nro_cuenta = QLineEdit()
        self.txt_banco_destino = QLineEdit()
        self.txt_aseo_municipal  = QLineEdit()
        self.txt_reajuste = QLineEdit()
        self.txt_ggcc = QLineEdit()

        self.txt_honorarios_porcentaje  = QLineEdit()
        self.txt_titular_deposito  = QLineEdit()
        self.txt_quien_deposita  = QLineEdit()
        self.txt_correo_deposito = QLineEdit()
        self.txt_dia_pago  = QLineEdit()
        self.txt_honorarios_monto  = QLineEdit()
        self.txt_tipo_cuenta   = QLineEdit()
        self.txt_rut_para_deposito  = QLineEdit()
        self.txt_cuenta_ggcc  = QLineEdit()
        self.txt_ultimo_mes_pago = QLineEdit()
        self.txt_direccion_consulta = QLineEdit()
        self.txt_periodo_anterior  = QLineEdit()
        self.txt_monto_anterior  = QLineEdit()
        self.txt_naturaleza_bien_raiz = QLineEdit()

        self.cmb_dfl12= QComboBox()
        self.cmb_dfl12.addItems(["Si","No"])

        self.txt_destino = QLineEdit()

        self.cmb_amoblado= QComboBox()
        self.cmb_amoblado.addItems(["Si","No"])


        self.txt_observaciones = QTextEdit()

        """
        Versión robusta: todos los groupboxes van dentro de un content_widget
        que a su vez está embebido en un QScrollArea. Esto evita que los boxes
        estiren la ventana principal.
        """

        # =========================
        # Content widget (todo aquí va dentro del scroll)
        # =========================
        content_widget = QWidget()
        content_vbox = QVBoxLayout(content_widget)
        content_vbox.setContentsMargins(0, 0, 0, 0)
        content_vbox.setSpacing(10)
        content_vbox.setAlignment(Qt.AlignTop)


        # Crear layout principal del tab
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)  
        tab.setLayout(main_layout)

            # -------------------------
        # Box 1: Básicos
        # -------------------------
        box_basicos = QGroupBox("Datos básicos del arriendo")
        layout_basicos = QFormLayout()
        layout_basicos.addRow(self.crear_label("Fecha Inicio:", True), self.fecha_inicio)
        layout_basicos.addRow(self.crear_label("Fecha de Término:"), self.fecha_termino)
        layout_basicos.addRow(self.crear_label("Renta Mensual:"), self.txt_renta_mensual)
        layout_basicos.addRow(self.crear_label("Garantía:"), self.txt_garantia)
        layout_basicos.addRow(self.chk_gastos_comunes)
        layout_basicos.addRow(self.crear_label("Estado del arriendo:"), self.cmb_estado_arriendo)
        layout_basicos.addRow(self.crear_label("Tipo de contrato:"), self.cmb_tipo_contrato)
        box_basicos.setLayout(layout_basicos)

        # Evitar que el groupbox se expanda verticalmente
        box_basicos.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        

        content_vbox.addWidget(box_basicos)

        # -------------------------
        # Box 2: Pagos
        # -------------------------
        box_pagos = QGroupBox("Datos de Pago")
        layout_pagos = QFormLayout()
        layout_pagos.addRow(self.crear_label("Forma de pago:"), self.txt_forma_pago)
        layout_pagos.addRow(self.crear_label("Periodo de pago"), self.cmb_periodo_pago)
        layout_pagos.addRow(self.crear_label("Día de pago:"), self.txt_dia_pago)
        layout_pagos.addRow(self.crear_label("Cuenta FM"), self.cmb_cuenta_fm)
        box_pagos.setLayout(layout_pagos)
        box_pagos.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        content_vbox.addWidget(box_pagos)

        # -------------------------
        # Box 3: Depósitos
        # -------------------------
        box_depositos = QGroupBox("Depósitos / Cuenta destino")
        layout_depositos = QFormLayout()
        layout_depositos.addRow(self.crear_label("Número de cuenta:"), self.txt_nro_cuenta)
        layout_depositos.addRow(self.crear_label("Banco destino:"), self.txt_banco_destino)
        layout_depositos.addRow(self.crear_label("Tipo de cuenta:"), self.txt_tipo_cuenta)
        layout_depositos.addRow(self.crear_label("RUT para depósito:"), self.txt_rut_para_deposito)
        layout_depositos.addRow(self.crear_label("Titular depósito:"), self.txt_titular_deposito)
        layout_depositos.addRow(self.crear_label("Quién deposita:"), self.txt_quien_deposita)
        layout_depositos.addRow(self.crear_label("Correo depósito:"), self.txt_correo_deposito)

        box_depositos.setLayout(layout_depositos)
        box_depositos.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        content_vbox.addWidget(box_depositos)

        # -------------------------
        # Box 4: Honorarios
        # -------------------------
        box_honorarios = QGroupBox("Honorarios")
        layout_honorarios = QFormLayout()
        layout_honorarios.addRow(self.crear_label("Honorarios (%)"), self.txt_honorarios_porcentaje)
        layout_honorarios.addRow(self.crear_label("Honorarios (monto)"), self.txt_honorarios_monto)
        box_honorarios.setLayout(layout_honorarios)
        box_honorarios.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        content_vbox.addWidget(box_honorarios)

        # -------------------------
        # Box 5: Extra / Información adicional
        # -------------------------
        box_extra = QGroupBox("Información adicional")
        layout_extra = QFormLayout()
        layout_extra.addRow(self.crear_label("Último mes pago"), self.txt_ultimo_mes_pago)
        layout_extra.addRow(self.crear_label("Aseo municipal"), self.txt_aseo_municipal)
        layout_extra.addRow(self.crear_label("Reajuste"), self.txt_reajuste)
        layout_extra.addRow(self.crear_label("GGCC"), self.txt_ggcc)
        layout_extra.addRow(self.crear_label("Cuenta GGCC:"), self.txt_cuenta_ggcc)
        layout_extra.addRow(self.crear_label("Dirección consulta"), self.txt_direccion_consulta)
        layout_extra.addRow(self.crear_label("Periodo anterior"), self.txt_periodo_anterior)
        layout_extra.addRow(self.crear_label("Monto anterior"), self.txt_monto_anterior)
        layout_extra.addRow(self.crear_label("Naturaleza bien raíz"), self.txt_naturaleza_bien_raiz)
        layout_extra.addRow(self.crear_label("DFL 2"), self.cmb_dfl12)
        layout_extra.addRow(self.crear_label("Destino"), self.txt_destino)
        layout_extra.addRow(self.crear_label("Amoblado"), self.cmb_amoblado)
        layout_extra.addRow(self.crear_label("Observaciones"), self.txt_observaciones)
        box_extra.setLayout(layout_extra)
        box_extra.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        content_vbox.addWidget(box_extra)

        # =========================
        # SCROLL AREA: envuelve content_widget
        # =========================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(0)
        scroll.setWidget(content_widget)

        # Opcional: controlar la altura máxima del scroll para que la pestaña no crezca sin control
        # Ajusta el valor a lo que visualmente quieras (por ejemplo 520 ó 600)
        scroll.setMaximumHeight(620)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # =========================
        # Añadir scroll al layout principal del tab
        # =========================
        main_layout.addWidget(scroll)

        # Si quieres un botón o controles al final del tab (fuera del scroll),
        # agrégalos después del scroll. De este modo siempre estarán visibles.
        # Ejemplo (botón guardar fuera del scroll):
        # btn_guardar = QPushButton("Guardar Arriendo")
        # main_layout.addWidget(btn_guardar, alignment=Qt.AlignRight)

        # Fin de setup_tab_arriendo



    

        





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
                    'im_renta': self.txt_impuesto_renta.text(),
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
                    'cuenta_fm': self.cmb_cuenta_fm.currentText(),
                    

                    'nro_cuenta': self.txt_nro_cuenta.text(),
                    'banco_destino': self.txt_banco_destino.text(),
                    'aseo_municipal': self.txt_aseo_municipal.text(),
                    'reajuste': self.txt_reajuste.text(),
                    'ggcc': self.txt_ggcc.text(),

                    
                    'honorarios_porcentaje': self.txt_honorarios_porcentaje.text(),
                    'titular_deposito': self.txt_titular_deposito.text(),
                    'quien_deposita': self.txt_quien_deposita.text(),
                    'correo_deposito': self.txt_correo_deposito.text(),
                    'dia_pago': self.txt_dia_pago.text(),
                    'honorarios_monto': self.txt_honorarios_monto.text(),
                    'tipo_cuenta': self.txt_tipo_cuenta.text(),
                    'rut_para_deposito': self.txt_rut_para_deposito.text(),
                    'cuenta_ggcc': self.txt_cuenta_ggcc.text(),
                    'ultimo_mes_pago': self.txt_ultimo_mes_pago.text(),
                    'direccion_consulta': self.txt_direccion_consulta.text(),
                    'periodo_anterior': self.txt_periodo_anterior.text(),
                    'monto_anterior': self.txt_monto_anterior.text(),
                    'naturaleza_bien_raiz': self.txt_naturaleza_bien_raiz.text(),

                    # --- COMBOBOX Y DESTINO ---
                    'dfl2': self.cmb_dfl12.currentText(),
                    'destino': self.txt_destino.text(),
                    'amoblado': self.cmb_amoblado.currentText(),
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
        self.resize(650, 600)

        # --- LAYOUT PRINCIPAL ---
        layout_principal = QVBoxLayout(self)

        # --- SCROLL AREA ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout_principal.addWidget(scroll)

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
        btn_add = QPushButton("Agregar descuento")
        btn_del = QPushButton("Eliminar seleccionado")

        btn_add.clicked.connect(self.agregar_descuento)
        btn_del.clicked.connect(self.eliminar_descuento)

        btns.addWidget(btn_add)
        btns.addWidget(btn_del)
        layout.addLayout(btns)

        # Botones OK/Cancel
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
        btn_calcular = QPushButton("Calcular")
        btn_cancelar = QPushButton("Cancelar")

        btn_calcular.clicked.connect(self.calcular)
        btn_cancelar.clicked.connect(self.reject)

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