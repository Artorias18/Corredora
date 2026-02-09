# ---- Python estándar ----
import os
import re

# ---- Librerías externas ----
from openpyxl import Workbook
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.utils import column_index_from_string
from openpyxl.styles import Font, Border, Side, Alignment
from openpyxl.drawing.image import Image
from PySide6.QtWidgets import QFileDialog
from .rrhh_calculo import MotorCalculoLiquidacion, InputLiquidacion, ResultadoLiquidacion, MotorPersistenciaLiquidacion
from datetime import date
from services.get_user_role import get_user_role
from gui.usuario_actual import UsuarioActual
# ---- PySide6 ----
from PySide6.QtCore import QDate, Qt, Signal

from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QHeaderView
)

# ---- Proyecto ----
from services import rrhh_service
from services.supabase_client import supabase

# ====================================================
#  DASHBOARD PRINCIPAL RRHH
# ====================================================

class DashboardRRHH(QWidget):
    def __init__(self,user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(TabTrabajadores(), " Trabajadores")
        self.tabs.addTab(TabLiquidaciones(), " Liquidaciones")
        self.tabs.addTab(Tabdocs(self.user_id), "Gestor documentos")
        layout.addWidget(self.tabs)
        self.setLayout(layout)


# ====================================================
# DIALOGO PARA AGREGAR / EDITAR TRABAJADOR
# ====================================================

class DoubleClickButton(QPushButton):
    doubleClicked = Signal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()


        
    

class DialogoTrabajador(QDialog):
    def __init__(self, trabajador=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ficha de Trabajador")
        self.trabajador = trabajador or {}

        layout = QFormLayout(self)

        # ===== RUT =====
        self.rut = QLineEdit(self.trabajador.get("rut", ""))

        # ===== Nombre =====
        self.nombre = QLineEdit(self.trabajador.get("nombre", ""))

        # ===== Fecha de ingreso (QDateEdit) =====
        self.fecha_ingreso = QDateEdit()
        self.fecha_ingreso.setCalendarPopup(True)

        fecha_str = self.trabajador.get("fecha_ingreso")
        if fecha_str:
            try:
                anio, mes, dia = map(int, str(fecha_str).split("-"))
                self.fecha_ingreso.setDate(QDate(anio, mes, dia))
            except:
                self.fecha_ingreso.setDate(QDate.currentDate())
        else:
            self.fecha_ingreso.setDate(QDate.currentDate())

        # ===== Tipo de contrato =====
        self.tipo_contrato = QComboBox()
        self.tipo_contrato.addItems(["Plazo Fijo", "Indefinido"])
        self.tipo_contrato.setCurrentText(self.trabajador.get("tipo_contrato", "Plazo Fijo"))

        # ===== Cargo =====
        self.cargo = QLineEdit(self.trabajador.get("cargo", ""))

        # ====================================
        # AFP
        # ====================================
        self.afp_combo = QComboBox()
        self.afp_combo.addItem("-- Sin AFP --", None)

        self.afps = rrhh_service.obtener_afps()
        for a in self.afps:
            self.afp_combo.addItem(a["nombre"], a["id"])

        afp_id_actual = self.trabajador.get("afp_id")
        if afp_id_actual:
            idx = self.afp_combo.findData(afp_id_actual)
            if idx >= 0:
                self.afp_combo.setCurrentIndex(idx)

        # ====================================
        # Sistema de Salud (limpio)
        # ====================================
        self.salud_combo = QComboBox()
        self.salud_combo.addItem("-- Sin Salud --", None)

        self.sistemas_salud = rrhh_service.obtener_sistemas_salud()
        for s in self.sistemas_salud:
            self.salud_combo.addItem(s["nombre"], s["id"])

        salud_id_actual = self.trabajador.get("sistema_salud_id")
        if salud_id_actual:
            idx = self.salud_combo.findData(salud_id_actual)
            if idx >= 0:
                self.salud_combo.setCurrentIndex(idx)

        # % Salud
        self.porcentaje_salud = QDoubleSpinBox()
        self.porcentaje_salud.setSuffix(" %")
        self.porcentaje_salud.setDecimals(2)
        self.porcentaje_salud.setMaximum(100.0)
        self.porcentaje_salud.setValue(float(self.trabajador.get("porcentaje_salud", 7.0)))

        # Cargas
        self.cargas_familiares = QSpinBox()
        self.cargas_familiares.setRange(0, 50)
        self.cargas_familiares.setValue(int(self.trabajador.get("cargas_familiares", 0)))

        # Sueldo Base
        self.sueldo_base = QDoubleSpinBox()
        self.sueldo_base.setMaximum(999_999_999)
        self.sueldo_base.setDecimals(0)
        self.sueldo_base.setValue(float(self.trabajador.get("sueldo_base", 0)))

        # =====================================================
        # FORMULARIO
        # =====================================================
        layout.addRow("RUT:", self.rut)
        layout.addRow("Nombre:", self.nombre)
        layout.addRow("Fecha Ingreso:", self.fecha_ingreso)
        layout.addRow("Tipo Contrato:", self.tipo_contrato)
        layout.addRow("Cargo:", self.cargo)
        layout.addRow("AFP:", self.afp_combo)
        layout.addRow("Sistema de Salud:", self.salud_combo)
        layout.addRow("% Salud:", self.porcentaje_salud)
        layout.addRow("Cargas Familiares:", self.cargas_familiares)
        layout.addRow("Sueldo Base:", self.sueldo_base)

        # =====================================================
        # BOTONES
        # =====================================================
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.validar_y_guardar)
        self.botones.rejected.connect(self.reject)
        layout.addWidget(self.botones)

        self.datos = None

    # =====================================================
    # VALIDAR + GUARDAR
    # =====================================================
    def validar_y_guardar(self):
        rut = self.rut.text().strip()
        nombre = self.nombre.text().strip()

        if not rut or not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", rut):
            QMessageBox.warning(self, "Error", "Ingrese un RUT válido (formato 12.345.678-9).")
            return

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        fecha_ing = self.fecha_ingreso.date().toString("yyyy-MM-dd")

        self.datos = {
            "rut": rut,
            "nombre": nombre,
            "fecha_ingreso": fecha_ing,
            "tipo_contrato": self.tipo_contrato.currentText(),
            "cargo": self.cargo.text().strip(),
            "afp_id": self.afp_combo.currentData(),
            "sistema_salud_id": self.salud_combo.currentData(),
            "porcentaje_salud": float(self.porcentaje_salud.value()),
            "cargas_familiares": int(self.cargas_familiares.value()),
            "sueldo_base": float(self.sueldo_base.value()),
            "activo": True,
        }

        self.accept()



# ====================================================
# PESTAÑA DE TRABAJADORES
# ====================================================

class TabTrabajadores(QWidget):
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

        self.filtro_fecha = QComboBox()
        self.filtro_fecha.addItems([
            "Todas las fechas",
            "Últimos 3 meses",
            "Últimos 6 meses",
            "Último año"
        ])
        self.filtro_fecha.currentIndexChanged.connect(self.aplicar_filtros)

        filtros_layout.addWidget(QLabel("Filtros:"))
        filtros_layout.addWidget(self.search_input)
        filtros_layout.addWidget(QLabel("Fecha ingreso:"))
        filtros_layout.addWidget(self.filtro_fecha)

        layout.addLayout(filtros_layout)

        # -----------------------------
        # 2. TABLA (CENTRO)
        # -----------------------------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "RUT", "Nombre", "Fecha Ingreso", "Tipo Contrato",
            "Cargo", "AFP", "Salud", "Sueldo Base",
        ])
        layout.addWidget(self.tabla)

        # -----------------------------
        # 3. BOTONES (ABAJO)
        # -----------------------------
        boton_layout = QHBoxLayout()
        self.btn_agregar = DoubleClickButton("Agregar")
        self.btn_editar = DoubleClickButton("Editar")
        self.btn_eliminar = DoubleClickButton("Eliminar")
        self.btn_actualizar_tasa_afp = DoubleClickButton("Actualizar tasa afp")

        boton_layout.addWidget(self.btn_agregar)
        boton_layout.addWidget(self.btn_editar)
        boton_layout.addWidget(self.btn_eliminar)
        boton_layout.addWidget(self.btn_actualizar_tasa_afp)

        layout.addLayout(boton_layout)

        # Conexiones
        self.btn_agregar.doubleClicked.connect(self.agregar_trabajador)
        self.btn_editar.doubleClicked.connect(self.editar_trabajador)
        self.btn_eliminar.doubleClicked.connect(self.eliminar_trabajador)
        self.btn_actualizar_tasa_afp.doubleClicked.connect(self.abrir_dialogo)


        # Cargar datos
        self.todo_trabajadores = []
        self.cargar_trabajadores()


    def abrir_dialogo(self):
        dialogo = DialogActualizarTasaAFP(parent=self)
        dialogo.exec()

    # ----------------------------------------
    # CARGAR TRABAJADORES BASE
    # ----------------------------------------
    def cargar_trabajadores(self):
        self.todo_trabajadores = rrhh_service.obtener_trabajadores()
        self.aplicar_filtros()

    # ----------------------------------------
    # FILTROS
    # ----------------------------------------
    def aplicar_filtros(self):
        texto = self.search_input.text().lower()
        filtro_fechas = self.filtro_fecha.currentText()

        datos = []

        for t in self.todo_trabajadores:
            rut = t.get("rut", "").lower()
            nombre = t.get("nombre", "").lower()

            if texto and texto not in rut and texto not in nombre:
                continue

            fecha_ing = QDate.fromString(t.get("fecha_ingreso", ""), "yyyy-MM-dd")
            hoy = QDate.currentDate()

            if filtro_fechas == "Últimos 3 meses" and fecha_ing < hoy.addMonths(-3):
                continue
            if filtro_fechas == "Últimos 6 meses" and fecha_ing < hoy.addMonths(-6):
                continue
            if filtro_fechas == "Último año" and fecha_ing < hoy.addYears(-1):
                continue

            datos.append(t)

        self._poblar_tabla(datos)

    def _poblar_tabla(self, data):
        self.tabla.setRowCount(0)

        afps = {a["id"]: a["nombre"] for a in rrhh_service.obtener_afps()}
        sistemas = {s["id"]: s["nombre"] for s in rrhh_service.obtener_sistemas_salud()}

        for row, t in enumerate(data):
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(t.get("rut", "")))
            self.tabla.setItem(row, 1, QTableWidgetItem(t.get("nombre", "")))
            self.tabla.setItem(row, 2, QTableWidgetItem(t.get("fecha_ingreso", "")))
            self.tabla.setItem(row, 3, QTableWidgetItem(t.get("tipo_contrato", "")))
            self.tabla.setItem(row, 4, QTableWidgetItem(t.get("cargo", "")))

            afp_nombre = afps.get(t.get("afp_id"), "")
            self.tabla.setItem(row, 5, QTableWidgetItem(afp_nombre))

            sal_nombre = sistemas.get(t.get("sistema_salud_id"), "")
            self.tabla.setItem(row, 6, QTableWidgetItem(sal_nombre))

            self.tabla.setItem(row, 7, QTableWidgetItem(str(int(t.get("sueldo_base") or 0))))


    def _obtener_trabajador_fila(self, fila: int) -> dict | None:
        if fila < 0:
            return None
        rut = self.tabla.item(fila, 0).text()
        return rrhh_service.obtener_trabajador(rut)

    def agregar_trabajador(self):
        dlg = DialogoTrabajador(parent=self)
        if dlg.exec():
            data = dlg.datos
            if data:
                rrhh_service.crear_trabajador(data)
                self.cargar_trabajadores()

    def editar_trabajador(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un trabajador para editar.")
            return
        trabajador = self._obtener_trabajador_fila(fila)
        if not trabajador:
            QMessageBox.warning(self, "Error", "No se pudo cargar el trabajador seleccionado.")
            return

        dlg = DialogoTrabajador(trabajador, parent=self)
        if dlg.exec():
            data = dlg.datos
            if data:
                rrhh_service.actualizar_trabajador(trabajador["rut"], data)
                self.cargar_trabajadores()

    def eliminar_trabajador(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un trabajador para eliminar.")
            return
        rut = self.tabla.item(fila, 0).text()
        if QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar trabajador {rut} y TODAS sus liquidaciones?"
        ) == QMessageBox.Yes:
            rrhh_service.eliminar_trabajador(rut)
            self.cargar_trabajadores()



class Tabdocs(QWidget):
    def __init__(self,user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.rol = get_user_role(user_id)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        # ─── Card / Recuadro ─────────────────────────────
        card = QGroupBox("Gestión de documentos")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        descripcion = QLabel(
            "Accede al repositorio de documentos del sistema.\n"
            "Aquí podrás subir, descargar y administrar archivos."
        )
        descripcion.setWordWrap(True)

        self.btn_documentos = DoubleClickButton("📁 Abrir documentos")
        self.btn_documentos.setMinimumHeight(40)
        self.btn_documentos.setCursor(Qt.PointingHandCursor)

        card_layout.addWidget(descripcion)
        card_layout.addWidget(self.btn_documentos)

        main_layout.addWidget(card)

        self.btn_documentos.doubleClicked.connect(self.open_documentos)

    def open_documentos(self):
        from gui.docs_window import DocumentosWindow

        if not hasattr(self, "doc_window"):
            self.doc_window = DocumentosWindow(self.rol)

        self.doc_window.show()
        self.doc_window.raise_()
        self.doc_window.activateWindow()


# ====================================================
#  DIALOGO DE LIQUIDACIÓN (todos los campos del Excel)
# ====================================================

class DialogoLiquidacion(QDialog):

    def insertar_logo(self, ws, ruta_logo):
        # 1️⃣ Ajustar columnas A y B
        ws.column_dimensions["A"].width = 18
        ws.column_dimensions["B"].width = 18

        # 2️⃣ Ajustar filas 1 a 5
        for fila in range(1, 6):
            ws.row_dimensions[fila].height = 22

        # 3️⃣ Cargar imagen
        img = Image(ruta_logo)

        # 4️⃣ Ajustar tamaño aproximado (pixeles)
        # Conversión aproximada:
        # ancho columna ≈ width * 7 px
        # alto fila ≈ height * 1.33 px
        ancho_px = int((18 + 18) * 7)   # A + B
        alto_px = int((22 * 5) * 1.33)  # filas 1 a 5

        img.width = ancho_px
        img.height = alto_px

        # 5️⃣ Insertar en A1
        ws.add_image(img, "A1")



    def insertar_firma_empleador(self, ws, ruta_imagen, fila_base):
        img = Image(ruta_imagen)

        # Tamaño razonable de firma/timbre
        img.width = 280
        img.height = 250

        # 👇 Anclar cerca de la firma del empleador
        # Columna E = un poco a la derecha
        # fila_base - 1 = subirla un poco
        celda_ancla = f"B{fila_base - 8}"

        ws.add_image(img, celda_ancla)


    def exportar_excel(self):
        trabajador = self.trabajador_combo.currentData()
        if not isinstance(trabajador, dict):
            QMessageBox.warning(self, "Error", "Trabajador inválido.")
            return

        periodo = self.periodo_edit.text()
        rut = trabajador.get("rut", "")


        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar liquidación",
            f"Liquidacion_{periodo}_{rut}.xlsx",
            "Excel (*.xlsx)"
        )
        if not ruta:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Liquidación"

        self.insertar_logo(ws, "assets/logocorredoraoriginal.png")

        # =========================
        # ESTILOS
        # =========================
        bold = Font(bold=True)
        big_bold = Font(bold=True, size=12)
        center = Alignment(horizontal="center")
        right = Alignment(horizontal="right")

        thin = Side(style="thin")
        border_top = Border(top=thin)
        border_double = Border(top=Side(style="double"))

        moneda = "$ #,##0"

        # =========================
        # COLUMNAS
        # =========================
        ws.column_dimensions["A"].width = 36
        ws.column_dimensions["B"].width = 14
        ws.column_dimensions["C"].width = 3
        ws.column_dimensions["D"].width = 36
        ws.column_dimensions["E"].width = 14
        ws.column_dimensions["F"].width = 3
        ws.column_dimensions["G"].width = 28
        ws.column_dimensions["H"].width = 14

        # =========================
        # ENCABEZADO
        # =========================
        ws["C2"] = "CORREDORA LUZ MARIA CORREA SPA"
        ws["C3"] = "Corretaje de Propiedades"
        ws["C4"] = "Área de RRHH"

        ws["H2"] = "Fecha Emisión:"
        ws["H3"] = QDate.currentDate().toString("dd-MM-yyyy")

        ws.merge_cells("B6:F6")
        ws["B6"] = f"LIQUIDACION DE REMUNERACIONES: {periodo}"
        ws["B6"].font = big_bold
        ws["B6"].alignment = center
        ws["B6"].border = border_top

        ws["A8"] = f"NOMBRE: {trabajador.get('nombre','')}"
        ws["E8"] = f"FECHA DE INGRESO: {trabajador.get('fecha_ingreso','')}"
        ws["A9"] = f"RUT: {rut}"
        ws["E9"] = f"TIPO DE CONTRATO: {trabajador.get('tipo_contrato','')}"

        # =========================
        # TITULOS
        # =========================
        ws["A11"] = "HABERES"
        ws["D11"] = "DESCUENTOS"
        ws["G11"] = "DATOS ADICIONALES"

        for c in ["A11", "D11", "G11"]:
            ws[c].font = bold
            ws[c].border = border_top

        # =========================
        # LISTADO DE CONCEPTOS
        # =========================
        fila = 12
        haberes = []
        descuentos = []

        for cid, spin in self.campos_concepto.items():
            info = self.info_concepto[cid]
            valor = int(spin.value())

            if info["grupo"] in ("haber_imponible", "haber_no_imponible"):
                haberes.append((info["nombre"], valor))
            elif info["grupo"] in ("descuento_previsional", "descuento_otro"):
                descuentos.append((info["nombre"], valor))

        max_filas = max(len(haberes), len(descuentos))

        gratificacion = int(self.lbl_gratificacion.text())

        for idx, (nombre, valor) in enumerate(haberes):
            if nombre.upper().find("SUELDO") != -1:
                haberes.insert(idx + 1, ("GRATIFICACION", gratificacion))
                break

        for i in range(max_filas):
            if i < len(haberes):
                ws[f"A{fila}"] = haberes[i][0]
                ws[f"B{fila}"] = haberes[i][1]
                ws[f"B{fila}"].number_format = moneda
                ws[f"B{fila}"].alignment = right

            if i < len(descuentos):
                ws[f"D{fila}"] = descuentos[i][0]
                ws[f"E{fila}"] = descuentos[i][1]
                ws[f"E{fila}"].number_format = moneda
                ws[f"E{fila}"].alignment = right

            fila += 1

        # =========================
        # TOTALES EN POSICIÓN EXACTA (EXCEL)
        # =========================

        # TOTAL HABERES IMPONIBLES → A26
        ws["A26"] = "TOTAL HABERES IMPONIBLES"
        ws["A26"].font = bold
        ws["B26"] = int(self.lbl_total_hab_impon.text())
        ws["B26"].number_format = moneda
        ws["B26"].font = bold
        ws["B26"].alignment = right

        # TOTAL DESCUENTOS PREVISIONALES → D19
        ws["D19"] = "TOTAL DESCUENTOS PREVISIONALES"
        ws["D19"].font = bold
        ws["E19"] = int(self.lbl_total_desc_prev.text())
        ws["E19"].number_format = moneda
        ws["E19"].font = bold
        ws["E19"].alignment = right

        ws["D34"] = "TOTAL OTROS DESCUENTOS"
        ws["D34"].font = bold
        ws["E34"] = int(self.lbl_total_desc_otros.text())
        ws["E34"].number_format = moneda
        ws["E34"].font = bold
        ws["E34"].alignment = right

        # TOTAL HABERES NO IMPONIBLES → A34
        ws["A34"] = "TOTAL HABERES NO IMPONIBLES"
        ws["A34"].font = bold
        ws["B34"] = int(self.lbl_total_hab_no_impon.text())
        ws["B34"].number_format = moneda
        ws["B34"].font = bold
        ws["B34"].alignment = right

        # =========================
        # TOTALES FINALES
        # =========================
        fila_final = 37

        ws[f"A{fila_final}"] = "TOTAL HABERES"
        ws[f"A{fila_final}"].font = bold
        ws[f"A{fila_final}"].border = border_double
        ws[f"B{fila_final}"] = int(self.lbl_total_haberes.text())
        ws[f"B{fila_final}"].number_format = moneda
        ws[f"B{fila_final}"].font = bold
        ws[f"B{fila_final}"].alignment = right

        ws[f"D{fila_final}"] = "TOTAL DESCUENTO GENERAL"
        ws[f"D{fila_final}"].font = bold
        ws[f"D{fila_final}"].border = border_double
        ws[f"E{fila_final}"] = int(self.lbl_total_desc_general.text())
        ws[f"E{fila_final}"].number_format = moneda
        ws[f"E{fila_final}"].font = bold
        ws[f"E{fila_final}"].alignment = right

        ws[f"G{fila_final}"] = "LIQUIDO A PAGAR"
        ws[f"G{fila_final}"].font = big_bold
        ws[f"H{fila_final}"] = int(
            self.lbl_liquido_pagar.text().replace("<b>", "").replace("</b>", "")
        )
        ws[f"H{fila_final}"].number_format = moneda
        ws[f"H{fila_final}"].font = big_bold
        ws[f"H{fila_final}"].alignment = right

        # =========================
        # DATOS ADICIONALES
        # =========================
        ws["G12"] = "DIAS TRABAJADOS"
        ws["H12"] = self.dias_trabajados.value()

        ws["G13"] = "Nº DE HORAS EXTRAS"
        ws["H13"] = self.num_horas_extras.value()

        ws["G14"] = "BASE IMPONIBLE"
        ws["H14"] = int(self.lbl_base_imponible.text())
        ws["H14"].number_format = moneda

        ws["G15"] = "BASE TRIBUTABLE"
        ws["H15"] = int(self.lbl_base_tributable.text())
        ws["H15"].number_format = moneda

        ws["G16"] = "AFP_TRABAJADOR"
        ws["H16"] = self.ultimo_input.afp_nombre

        ws["G17"] = "COTIZACION AFP"
        ws["H17"] = self.ultimo_input.afp_tasa_txt

        ws["G18"] = "ISAPRE_TRABAJADOR"
        ws["H18"] = self.salud_nombre

        ws["G19"] = "IsapreACotizar%"
        ws["H19"] = f"{self.porcentaje_salud}%"
        # =========================
        # PIE
        # =========================

        pie = fila_final + 4

        # ------------------------------------------------
        # TEXTO LEGAL
        # ------------------------------------------------
        ws.merge_cells(f"A{pie}:F{pie+2}")
        cell = ws[f"A{pie}"]
        cell.value = (
            "Recibí conforme el alcance líquido de la presente liquidación, "
            "no teniendo cargo o cobro alguno que hacer por otro concepto."
        )
        cell.alignment = Alignment(
            wrap_text=True,
            horizontal="center",
            vertical="center"
        )

        for f in range(pie, pie + 3):
            ws.row_dimensions[f].height = 25


        linea_fila = pie + 7

        # Línea empleador (pegada a la izquierda)
        ws.merge_cells(f"A{linea_fila}:F{linea_fila}")
        ws[f"A{linea_fila}"] = "______________________________"
        ws[f"A{linea_fila}"].alignment = Alignment(
            horizontal="left",
            indent=1
        )

        # Línea trabajador (pegada a la izquierda)
        ws.merge_cells(f"G{linea_fila}:J{linea_fila}")
        ws[f"G{linea_fila}"] = "______________________________"
        ws[f"G{linea_fila}"].alignment = Alignment(
            horizontal="left",
            indent=1
        )

        # ------------------------------------------------
        # TEXTOS BAJO LAS LINEAS
        # ------------------------------------------------
        ws.merge_cells(f"A{linea_fila+1}:F{linea_fila+1}")
        ws[f"A{linea_fila+1}"] = "Firma y Timbre Empleador"
        ws[f"A{linea_fila+1}"].alignment = Alignment(
            horizontal="left",
            indent=1
        )

        ws.merge_cells(f"G{linea_fila+1}:J{linea_fila+1}")
        ws[f"G{linea_fila+1}"] = trabajador.get("nombre", "")
        ws[f"G{linea_fila+1}"].alignment = Alignment(
            horizontal="left",
            indent=1
        )

        ws.merge_cells(f"G{linea_fila+2}:J{linea_fila+2}")
        ws[f"G{linea_fila+2}"] = f"RUT: {rut}"
        ws[f"G{linea_fila+2}"].alignment = Alignment(
            horizontal="left",
            indent=1
        )

        # ------------------------------------------------
        # IMAGEN FIRMA / TIMBRE EMPLEADOR (CORRIDA A LA DERECHA)
        # ------------------------------------------------
        self.insertar_firma_empleador(
            ws,
            "assets/firma_timbre.png",
            linea_fila + 3
        )

        wb.save(ruta)




















    def __init__(self, liquidacion_existente=None, parent=None):
        """
        liquidacion_existente: dict -> rrhh_service.obtener_liquidacion_completa()
        """
        super().__init__(parent)
        self.setWindowTitle("Liquidación de sueldo")
        self.resize(900, 700)

        self.liquidacion_existente = liquidacion_existente
        self.campos_concepto = {}   # {concepto_id: QDoubleSpinBox}
        self.info_concepto = {}     # {concepto_id: {"grupo":..., "nombre":...}}

        self.ultimo_resultado = None
        
        self.motor = MotorCalculoLiquidacion()
        self.motor_bd = MotorPersistenciaLiquidacion(rrhh_service) 

        main_layout = QVBoxLayout(self)

        # Trabajador / periodo
        form_top = QFormLayout()
        self.trabajador_combo = QComboBox()
        self.trabajadores = rrhh_service.obtener_trabajadores()
        for t in self.trabajadores:
            self.trabajador_combo.addItem(f"{t['rut']} - {t['nombre']}", t)

        self.periodo_edit = QLineEdit()
        form_top.addRow("Trabajador:", self.trabajador_combo)
        form_top.addRow("Periodo (YYYY-MM):", self.periodo_edit)
        main_layout.addLayout(form_top)

        # Scroll con los bloques del Excel
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        scroll_layout = QVBoxLayout(cont)

        # ==== Haberes Imponibles ====
        self.grp_hab_impon = QGroupBox("Haberes Imponibles")
        layout_impon = QFormLayout()
        self.grp_hab_impon.setLayout(layout_impon)

        # ==== Haberes No Imponibles ====
        self.grp_hab_no_impon = QGroupBox("Haberes No Imponibles")
        layout_no_impon = QFormLayout()
        self.grp_hab_no_impon.setLayout(layout_no_impon)

        # ==== Descuentos Previsionales ====
        self.grp_desc_prev = QGroupBox("Descuentos Previsionales")
        layout_desc_prev = QFormLayout()
        self.grp_desc_prev.setLayout(layout_desc_prev)

        # ==== Otros Descuentos ====
        self.grp_desc_otro = QGroupBox("Otros Descuentos")
        layout_desc_otro = QFormLayout()
        self.grp_desc_otro.setLayout(layout_desc_otro)

        # Crear campos dinámicos según tabla concepto
        conceptos_agr = rrhh_service.obtener_conceptos_agrupados()
        for grupo, lista in conceptos_agr.items():
            for c in lista:
                if c["nombre"] == "GRATIFICACION":
                    continue

                spin = QDoubleSpinBox()
                spin.setDecimals(0)
                spin.setMaximum(999_999_999)
                spin.valueChanged.connect(self._evento_recalculo)

                self.campos_concepto[c["id"]] = spin
                self.info_concepto[c["id"]] = {
                    "grupo": c["grupo"],
                    "nombre": c["nombre"],
                }

                etiqueta = c["nombre"]
                if grupo == "haber_imponible":
                    layout_impon.addRow(etiqueta + ":", spin)
                elif grupo == "haber_no_imponible":
                    layout_no_impon.addRow(etiqueta + ":", spin)
                elif grupo == "descuento_previsional":
                    layout_desc_prev.addRow(etiqueta + ":", spin)
                elif grupo == "descuento_otro":
                    layout_desc_otro.addRow(etiqueta + ":", spin)

        scroll_layout.addWidget(self.grp_hab_impon)
        scroll_layout.addWidget(self.grp_hab_no_impon)
        scroll_layout.addWidget(self.grp_desc_prev)
        scroll_layout.addWidget(self.grp_desc_otro)

        # ==== Totales (igual que en el Excel) ====
        totales_box = QGroupBox("Totales")
        tot_layout = QFormLayout()
        totales_box.setLayout(tot_layout)

        self.lbl_total_hab_impon = QLabel("0")
        self.lbl_total_hab_no_impon = QLabel("0")
        self.lbl_gratificacion = QLabel("0")
        self.lbl_total_haberes = QLabel("0")

        self.lbl_total_desc_prev = QLabel("0")
        self.lbl_total_desc_otros = QLabel("0")
        self.lbl_total_desc_general = QLabel("0")
        self.lbl_gratificacion = QLabel("0")
        self.lbl_retroactivo = QLabel("0")
        self.lbl_liquido_pagar = QLabel("<b>0</b>")

        tot_layout.addRow("TOTAL HABERES IMPONIBLES:", self.lbl_total_hab_impon)
        tot_layout.addRow("TOTAL HABERES NO IMPONIBLES:", self.lbl_total_hab_no_impon)
        tot_layout.addRow("GRATIFICACION:", self.lbl_gratificacion)
        tot_layout.addRow("RETROACTIVO:", self.lbl_retroactivo)
        tot_layout.addRow("TOTAL HABERES:", self.lbl_total_haberes)
        tot_layout.addRow("TOTAL DESCUENTOS PREVISIONALES:", self.lbl_total_desc_prev)
        tot_layout.addRow("TOTAL OTROS DESCUENTOS:", self.lbl_total_desc_otros)
        tot_layout.addRow("TOTAL DESCUENTO GENERAL:", self.lbl_total_desc_general)
        tot_layout.addRow("LÍQUIDO A PAGAR:", self.lbl_liquido_pagar)

        scroll_layout.addWidget(totales_box)

        # ==== Datos adicionales (lado derecho Excel) ====
        datos_box = QGroupBox("Datos adicionales")
        datos_layout = QFormLayout()
        datos_box.setLayout(datos_layout)

        self.dias_trabajados = QSpinBox()
        self.dias_trabajados.setRange(0, 31)
        self.dias_trabajados.setValue(30)

        self.num_horas_extras = QSpinBox()
        self.num_horas_extras.setRange(0, 200)

        self.lbl_base_imponible = QLabel("0")
        self.lbl_base_tributable = QLabel("0")

        self.lbl_afp_trabajador = QLabel("-")
        self.lbl_afp_tasa = QLabel("-")
        self.lbl_prev_trabajador = QLabel("-")
        self.lbl_prev_tasa = QLabel("-")
        self.lbl_rut = QLabel("-")
        self.observaciones_edit = QLineEdit()

        datos_layout.addRow("DIAS TRABAJADOS:", self.dias_trabajados)
        datos_layout.addRow("Nº DE HORAS EXTRAS:", self.num_horas_extras)
        datos_layout.addRow("BASE IMPONIBLE:", self.lbl_base_imponible)
        datos_layout.addRow("BASE TRIBUTABLE:", self.lbl_base_tributable)
        datos_layout.addRow("AFP Trabajador:", self.lbl_afp_trabajador)
        datos_layout.addRow("Cotización AFP:", self.lbl_afp_tasa)
        datos_layout.addRow("Previsión Trabajador:", self.lbl_prev_trabajador)
        datos_layout.addRow("% a cotizar:", self.lbl_prev_tasa)
        datos_layout.addRow("RUT:", self.lbl_rut)
        datos_layout.addRow("Observaciones:", self.observaciones_edit)

        scroll_layout.addWidget(datos_box)

        # ==== Retroactivo Asignación Familiar ====
        retro_box = QGroupBox("Cálculo retroactivo Asignación Familiar")
        retro_layout = QFormLayout()
        retro_box.setLayout(retro_layout)

        self.retro_antiguo = QDoubleSpinBox()
        self.retro_antiguo.setMaximum(999_999_999)
        self.retro_antiguo.setDecimals(0)

        self.retro_actual = QDoubleSpinBox()
        self.retro_actual.setMaximum(999_999_999)
        self.retro_actual.setDecimals(0)

        self.retro_diferencia = QDoubleSpinBox()
        self.retro_diferencia.setMaximum(999_999_999)
        self.retro_diferencia.setDecimals(0)

        retro_layout.addRow("Antiguo:", self.retro_antiguo)
        retro_layout.addRow("Actual:", self.retro_actual)
        retro_layout.addRow("Diferencia:", self.retro_diferencia)

        scroll_layout.addWidget(retro_box)

        scroll.setWidget(cont)
        main_layout.addWidget(scroll)

        # Botones
        self.btn_exportar = DoubleClickButton("Exportar a Excel")
        self.btn_exportar.doubleClicked.connect(self.exportar_excel)

        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.addButton(self.btn_exportar, QDialogButtonBox.ActionRole)

        self.botones.accepted.connect(self.guardar)
        self.botones.rejected.connect(self.reject)
        main_layout.addWidget(self.botones)

        # Eventos
        self.trabajador_combo.currentIndexChanged.connect(self._actualizar_datos_trabajador)

        self.trabajador_combo.currentIndexChanged.connect(self._evento_recalculo)
        self.periodo_edit.textChanged.connect(self._evento_recalculo)
        self.retro_antiguo.valueChanged.connect(self._evento_recalculo)
        self.retro_actual.valueChanged.connect(self._evento_recalculo)

        # Edit / nuevo
        if self.liquidacion_existente:
            self._cargar_liquidacion_existente()
        else:
            self._actualizar_datos_trabajador()
    
            

    # ------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------

    def _obtener_fecha_periodo(self) -> date:
        texto = self.periodo_edit.text().strip()
        if not texto:
            return date.today()

        year, month = map(int, texto.split("-"))
        return date(year, month, 1)

    
    def _evento_recalculo(self):
        try:
            trabajador = self.trabajador_combo.currentData()
            if not trabajador:
                return

            periodo = self.periodo_edit.text().strip()
            if not periodo:
                return

            ficha = rrhh_service.obtener_trabajador(trabajador["rut"])
            if not ficha:
                return
            
            salud_nombre = rrhh_service.obtener_nombre_salud(ficha["sistema_salud_id"])

            self.salud_nombre = salud_nombre

            porcentaje_salud = float(ficha.get("porcentaje_salud") or 7.0)

            self.porcentaje_salud = porcentaje_salud

            # -----------------------------
            # 1) Separar montos por grupo (USAR codigo con fallback a nombre)
            # -----------------------------
            haberes_imponibles: dict[str, float] = {}
            haberes_no_imponibles: dict[str, float] = {}

            # IMM (fijo por ahora)
            imm = float(539000)

            for cid, spin in self.campos_concepto.items():
                info = self.info_concepto.get(cid, {}) or {}
                grupo = (info.get("grupo") or "").strip().lower()
                codigo_raw = info.get("codigo") or info.get("nombre")
                codigo = (
                    codigo_raw.strip()
                    .replace(" ", "_")
                    .replace("%", "")       # ❌ QUITA el porcentaje
                    .replace("-", "_")
                    .upper()
                ) # ← fallback seguro

                if not codigo:
                    # No tenemos cómo identificar el concepto
                    print(f"[WARN] Concepto {cid} sin 'codigo' ni 'nombre' en info_concepto: {info}")
                    continue

                try:
                    val = float(spin.value())
                except Exception:
                    print(f"[WARN] Valor inválido para {codigo} (cid={cid}) -> {spin.value()}")
                    continue

                if abs(val) < 0.5:
                    # Evitar llenar con ceros
                    continue

                if grupo in ("haber_imponible", "imponible"):
                    haberes_imponibles[codigo] = val
                elif grupo in ("haber_no_imponible", "no_imponible"):
                    haberes_no_imponibles[codigo] = val
                else:
                    # Si tu catálogo usa otro texto, log para ajustar
                    print(f"[INFO] Grupo desconocido '{grupo}' para {codigo}; no se clasifica.")

            # -----------------------------
            # 2) Tasas previsionales
            # -----------------------------
            fecha_periodo = self._obtener_fecha_periodo()

            rut = trabajador.get("rut")
            

            # Tasa AFP desde servicio (evita parseos frágiles)
            afp_info = rrhh_service.obtener_afp_trabajador(rut, fecha_periodo)
            afp_tasa = float(afp_info.get("tasa_total") or 0.0)
            
            
            self.lbl_afp_trabajador.setText(
                afp_info.get("afp_nombre", "")
            )

            self.lbl_afp_tasa.setText(
                f"{afp_info.get('afp_tasa', 0) * 100:.2f}%"
            )

            afp_nombre= afp_info["afp_nombre"]
            afp_tasa_txt = afp_info["tasa_total_txt"]

           



            salud_info = rrhh_service.obtener_salud_trabajador(ficha, fecha_periodo)


            self.lbl_prev_tasa.setText(salud_info["tasa_txt"])


            # Salud: si tienes plan fijo/tasa desde ficha/servicio, úsalo. Si no, parsea el label.
            salud_porcentaje, salud_plan = self._parse_salud(self.lbl_prev_tasa.text())

            # -----------------------------
            # 3) Construir INPUT
            # -----------------------------
            sueldo_base_val = float(ficha.get("sueldo_base") or 0)

            

            data = InputLiquidacion(
                periodo=periodo,
                sueldo_base=sueldo_base_val,
                haberes_imponibles=haberes_imponibles,
                haberes_no_imponibles=haberes_no_imponibles,
                imm=imm,
                afp_nombre=afp_nombre,
                afp_tasa_txt=afp_tasa_txt,
                afp_tasa=afp_tasa,
                salud_porcentaje=float(salud_porcentaje or 0.07),
                salud_plan_fijo=float(salud_plan) if salud_plan is not None else None,
                retro_antiguo=float(self.retro_antiguo.value() or 0),
                retro_actual=float(self.retro_actual.value() or 0),
                dias_trabajados=int(round((self.dias_trabajados.value() or 0))),
                numero_horas_extras=int(round((self.num_horas_extras.value() or 0))),
                observaciones=self.observaciones_edit.text() or "",
            )


            # -----------------------------
            # 4) Ejecutar motor
            # -----------------------------
            resultado = self.motor.calcular(data)
            self.ultimo_input = data
            self.ultimo_resultado = resultado


            # -----------------------------
            # 5) Reflejar resultados
            # -----------------------------
            self._reflejar_resultado_motor(resultado)

        except Exception as e:
            print("Error evento recálculo:", e)


    def _parse_porcentaje(self, txt: str) -> float:
        if "%" in txt:
            return float(txt.replace("%", "").strip()) / 100
        return 0.0


    def _parse_salud(self, txt: str):
        if "$" in txt:
            return 0.07, float(txt.replace("$", "").replace(",", ""))
        if "%" in txt:
            return float(txt.replace("%", "")) / 100, None
        return 0.07, None

    def _reflejar_resultado_motor(self, r: ResultadoLiquidacion):

        # Haberes
        self.lbl_total_hab_impon.setText(str(int(r.total_haberes_imponibles)))
        self.lbl_total_hab_no_impon.setText(str(int(r.total_haberes_no_imponibles)))

        self.lbl_gratificacion.setText(str(int(r.montos_por_concepto.get("GRATIFICACION", 0))))

        self.lbl_retroactivo.setText(str(int(r.montos_por_concepto.get("RETROACTIVO"))))

        self.lbl_total_haberes.setText(str(int(r.total_haberes)))

        # Descuentos
        self.lbl_total_desc_prev.setText(str(int(r.total_descuentos_previsionales)))
        self.lbl_total_desc_otros.setText(str(int(r.total_descuentos_otros)))

        self.lbl_total_desc_general.setText(str(int(r.total_descuentos_general)))

        # Líquido
        self.lbl_liquido_pagar.setText(f"<b>{int(r.liquido_pagar)}</b>")

        # Bases
        self.lbl_base_imponible.setText(str(int(r.base_imponible)))
        self.lbl_base_tributable.setText(str(int(r.base_tributable)))

        # AFP / Salud (montos)
        self.lbl_afp_trabajador.setText("AFP")
        self.lbl_afp_tasa.setText(
            str(int(r.montos_por_concepto.get("FONDO_PENSIONES", 0)))
        )

        self.lbl_prev_trabajador.setText("SALUD")
        self.lbl_prev_tasa.setText(
            str(int(r.montos_por_concepto.get("PREVISION_7", 0)))
        )

        






    def _actualizar_datos_trabajador(self):
        t = self.trabajador_combo.currentData()
        if not t:
            return

        # Ficha completa (para nombres AFP / Salud y % salud)
        ficha = rrhh_service.obtener_trabajador(t.get("rut"))
        if not ficha:
            ficha = t

        self.lbl_rut.setText(ficha.get("rut", ""))

        afps = {a["id"]: a["nombre"] for a in rrhh_service.obtener_afps()}
        sistemas = {s["id"]: s["nombre"] for s in rrhh_service.obtener_sistemas_salud()}

        afp_nombre = afps.get(ficha.get("afp_id")) if ficha.get("afp_id") else "-"
        self.lbl_afp_trabajador.setText(afp_nombre)

        # La tasa exacta la maneja la BD; aquí solo un texto referencial
        self.lbl_afp_tasa.setText("-")

        sal_nombre = sistemas.get(ficha.get("sistema_salud_id")) if ficha.get("sistema_salud_id") else "-"
        self.lbl_prev_trabajador.setText(sal_nombre)

        porc_salud = ficha.get("porcentaje_salud")
        self.lbl_prev_tasa.setText(f"{porc_salud} %" if porc_salud is not None else "-")

        # ================================
        #   Precargar SUELDO BASE automático
        # ================================
        try:
            sueldo_base_cid = "0f6be431-2c12-4765-9e73-7e563ada9f05"  # concepto SUELDO BASE
            spin_sb = self.campos_concepto.get(sueldo_base_cid)

            if spin_sb:
                valor_sb = float(ficha.get("sueldo_base") or 0)

                # Solo rellenar automáticamente si es liquidación nueva
                if not self.liquidacion_existente:
                    spin_sb.setValue(valor_sb)
        except Exception as e:
            print("Error precargando sueldo base:", e)


                # ==================================================
        #   Cargar tasas AFP / Salud según periodo
        # ==================================================
        try:
            periodo_txt = self.periodo_edit.text().strip()
            fecha_periodo = None
            if periodo_txt:
                # Convertir YYYY-MM -> YYYY-MM-01
                fecha_periodo = periodo_txt + "-01"

            # AFP
            if fecha_periodo:
                afp_info = rrhh_service.obtener_afp_trabajador(ficha, fecha_periodo)
                if afp_info:
                    self.lbl_afp_trabajador.setText(afp_info["afp_nombre"])
                    self.lbl_afp_tasa.setText(afp_info["tasa_txt"])
                else:
                    self.lbl_afp_trabajador.setText("-")
                    self.lbl_afp_tasa.setText("-")

            # Salud
            salud_id = ficha.get("sistema_salud_id")
            if salud_id and fecha_periodo:
                sal = rrhh_service.obtener_tasa_salud(salud_id, fecha_periodo)
                if sal:
                    porcentaje = sal.get("porcentaje", 0)
                    plan_fijo = sal.get("plan_fijo", 0)
                    if plan_fijo and plan_fijo > 0:
                        self.lbl_prev_tasa.setText(f"${plan_fijo:,}")
                    else:
                        self.lbl_prev_tasa.setText(f"{porcentaje * 100:.2f} %")

            self._evento_recalculo()
        except Exception as e:
            print("Error cargando tasas previsionales:", e)


    


        


    def _cargar_liquidacion_existente(self):
        data = self.liquidacion_existente
        cab = data.get("cabecera", {})
        detalles = data.get("detalles", [])

        # Trabajador / periodo
        rut = cab.get("trabajador_rut")
        for i in range(self.trabajador_combo.count()):
            if self.trabajador_combo.itemData(i).get("rut") == rut:
                self.trabajador_combo.setCurrentIndex(i)
                break
        self.periodo_edit.setText(cab.get("periodo", ""))

        # Datos adicionales
        self.dias_trabajados.setValue(int(cab.get("dias_trabajados", 30)))
        self.num_horas_extras.setValue(int(cab.get("numero_horas_extras", 0)))
        self.lbl_base_imponible.setText(str(cab.get("base_imponible", 0)))
        self.lbl_base_tributable.setText(str(cab.get("base_tributable", 0)))
        self.lbl_afp_trabajador.setText(cab.get("afp_nombre", "") or "-")
        self.lbl_afp_tasa.setText(str(cab.get("afp_tasa", "")) or "-")
        self.lbl_prev_trabajador.setText(cab.get("sistema_salud_nombre", "") or "-")
        self.lbl_prev_tasa.setText(str(cab.get("porcentaje_salud", "")) or "-")
        self.lbl_rut.setText(cab.get("trabajador_rut", ""))
        self.observaciones_edit.setText(cab.get("observaciones", "") or "")

        self.retro_antiguo.setValue(float(cab.get("retro_antiguo") or 0))
        self.retro_actual.setValue(float(cab.get("retro_actual") or 0))
        self.retro_diferencia.setValue(float(cab.get("retro_diferencia") or 0))

        # Detalles -> spin por concepto_id
        for d in detalles:
            cid = d.get("concepto_id")
            monto = d.get("monto", 0)
            spin = self.campos_concepto.get(cid)
            if spin:
                spin.setValue(float(monto))

       


        

    # ------------------------------------------------
    # Guardar
    # ------------------------------------------------
    def guardar(self):
        t = self.trabajador_combo.currentData()
        if not t:
            QMessageBox.warning(self, "Error", "Debe seleccionar un trabajador.")
            return

        periodo = self.periodo_edit.text().strip()
        if not periodo:
            QMessageBox.warning(self, "Error", "Debe ingresar el periodo (YYYY-MM).")
            return

        if not self.ultimo_resultado or not self.ultimo_input:
            QMessageBox.warning(
                self,
                "Error",
                "Debe calcular la liquidación antes de guardar."
            )
            return

        # ================================
        # 1) Construir persistencia (ÚNICA fuente para BD)
        # ================================
        self.motor_bd = MotorPersistenciaLiquidacion(rrhh_service)

        persistencia = self.motor_bd.construir(
            trabajador=t,
            periodo=periodo,
            data=self.ultimo_input,
            resultado=self.ultimo_resultado,
        )

        # ================================
        # 2) Crear o actualizar
        # ================================

        if self.liquidacion_existente:
            ok = rrhh_service.actualizar_liquidacion(
                liq_id=self.liquidacion_existente["cabecera"]["id"],
                datos_cabecera=persistencia.datos_cabecera,
                montos_por_concepto=persistencia.detalle,
            )
            if not ok:
                QMessageBox.warning(self, "Error", "No se pudo actualizar la liquidación.")
                return
        else:
            liq_id = rrhh_service.crear_liquidacion(
                trabajador_rut=t["rut"],
                periodo=periodo,
                datos_cabecera=persistencia.datos_cabecera,
                montos_por_concepto=persistencia.detalle,
            )

            if not liq_id:
                QMessageBox.warning(self, "Error", "No se pudo crear la liquidación.")
                return

        self.accept()

                

        


# ====================================================
#  PESTAÑA DE LIQUIDACIONES
# ====================================================

class TabLiquidaciones(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # -----------------------------
        # 1. FILTROS (ARRIBA)
        # -----------------------------
        filtros_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o RUT...")
        self.search_input.textChanged.connect(self.aplicar_filtros)

        self.filtro_periodo = QComboBox()
        self.filtro_periodo.addItems([
            "Todos los periodos",
            "Últimos 6 meses",
            "Último año"
        ])
        self.filtro_periodo.currentIndexChanged.connect(self.aplicar_filtros)

        filtros_layout.addWidget(QLabel("Filtros:"))
        filtros_layout.addWidget(self.search_input)
        filtros_layout.addWidget(QLabel("Periodo:"))
        filtros_layout.addWidget(self.filtro_periodo)

        layout.addLayout(filtros_layout)

        # -----------------------------
        # 2. TABLA (CENTRO)
        # -----------------------------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Periodo", "RUT", "Nombre", "Total Haberes",
            "Total Descuentos", "Líquido a Pagar",
        ])
        layout.addWidget(self.tabla)

        header = self.tabla.horizontalHeader()

        # Ajusta cada columna a su contenido
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        # -----------------------------
        # 3. BOTONES (ABAJO)
        # -----------------------------
        boton_layout = QHBoxLayout()
        self.btn_nueva = DoubleClickButton("Nueva Liquidación")
        self.btn_ver = DoubleClickButton("Ver / Editar")
        self.btn_eliminar = DoubleClickButton("Eliminar")

        boton_layout.addWidget(self.btn_nueva)
        boton_layout.addWidget(self.btn_ver)
        boton_layout.addWidget(self.btn_eliminar)

        layout.addLayout(boton_layout)

        # Conexiones
        self.btn_nueva.doubleClicked.connect(self.crear_liquidacion)
        self.btn_ver.doubleClicked.connect(self.ver_editar_liquidacion)
        self.btn_eliminar.doubleClicked.connect(self.eliminar_liquidacion)

        self.todo_liquidaciones = []
        self.cargar_liquidaciones()

    def cargar_liquidaciones(self):
        self.todo_liquidaciones = rrhh_service.obtener_liquidaciones_resumen()
        self.aplicar_filtros()

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
        if dlg.exec():
            self.cargar_liquidaciones()

    def ver_editar_liquidacion(self):
        liq_id = self._id_seleccionado()
        if not liq_id:
            QMessageBox.warning(self, "Atención", "Seleccione una liquidación.")
            return
        data = rrhh_service.obtener_liquidacion_completa(liq_id)
        if not data:
            QMessageBox.warning(self, "Error", "No se pudo cargar la liquidación.")
            return
        dlg = DialogoLiquidacion(liquidacion_existente=data, parent=self)
        if dlg.exec():
            self.cargar_liquidaciones()

    def eliminar_liquidacion(self):
        liq_id = self._id_seleccionado()
        if not liq_id:
            QMessageBox.warning(self, "Atención", "Seleccione una liquidación.")
            return
        if QMessageBox.question(self, "Confirmar", "¿Eliminar la liquidación seleccionada?") == QMessageBox.Yes:
            rrhh_service.eliminar_liquidacion(liq_id)
            self.cargar_liquidaciones()


class DialogActualizarTasaAFP(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Actualizar tasa AFP")

        self.afp_combo = QComboBox()
        self.cargar_afps()

        self.tasa_cotizacion = QDoubleSpinBox()
        self.tasa_cotizacion.setDecimals(4)
        self.tasa_cotizacion.setRange(0, 100)

        self.tasa_sis = QDoubleSpinBox()
        self.tasa_sis.setDecimals(4)
        self.tasa_sis.setRange(0, 100)

        self.fecha_vigencia = QDateEdit()
        self.fecha_vigencia.setCalendarPopup(True)
        self.fecha_vigencia.setDate(QDate.currentDate())

        btn_guardar = DoubleClickButton("Guardar")
        btn_guardar.doubleClicked.connect(self.guardar)

        layout = QFormLayout(self)
        layout.addRow("AFP", self.afp_combo)
        layout.addRow("Tasa cotización (%)", self.tasa_cotizacion)
        layout.addRow("Tasa SIS (%)", self.tasa_sis)
        layout.addRow("Vigente desde", self.fecha_vigencia)
        layout.addRow(btn_guardar)


    def validar(self):
        if self.afp_combo.currentData() is None:
            raise ValueError("Debe seleccionar una AFP")

        if self.tasa_cotizacion.value() <= 0:
            raise ValueError("La tasa de cotización debe ser mayor a 0")

        if self.tasa_sis.value() < 0:
            raise ValueError("La tasa SIS no puede ser negativa")
        
    def cargar_afps(self):
        afps = rrhh_service.obtener_afps()
        self.afp_combo.clear()
        for a in afps:
            self.afp_combo.addItem(a["nombre"], a["id"])

    def guardar(self):
        try:
            afp_id = self.afp_combo.currentData()
            if not afp_id:
                raise ValueError("Debe seleccionar una AFP")

            tasa = self.tasa_cotizacion.value() / 100
            sis = self.tasa_sis.value() / 100

            fecha = self.fecha_vigencia.date().toPython()

            rrhh_service.actualizar_tasa_afp_supabase(
                afp_id,
                fecha,
                tasa,
                sis
            )

            QMessageBox.information(
                self,
                "OK",
                "Tasa AFP actualizada correctamente"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

