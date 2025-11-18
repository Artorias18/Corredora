from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLabel, QFormLayout, QDialog, QDialogButtonBox,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt

from services import rrhh_service
import re
import os
from openpyxl import Workbook
from PySide6.QtWidgets import QFileDialog


# ====================================================
#  DASHBOARD PRINCIPAL RRHH
# ====================================================

class DashboardRRHH(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(TabTrabajadores(), " Trabajadores")
        self.tabs.addTab(TabLiquidaciones(), " Liquidaciones")
        layout.addWidget(self.tabs)
        self.setLayout(layout)


# ====================================================
# DIALOGO PARA AGREGAR / EDITAR TRABAJADOR
# ====================================================

class DialogoTrabajador(QDialog):
    def __init__(self, trabajador=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ficha de Trabajador")
        self.trabajador = trabajador or {}

        layout = QFormLayout(self)

        # Campos básicos
        self.rut = QLineEdit(self.trabajador.get("rut", ""))
        self.nombre = QLineEdit(self.trabajador.get("nombre", ""))
        self.fecha_ingreso = QLineEdit(self.trabajador.get("fecha_ingreso", ""))  # yyyy-mm-dd
        self.tipo_contrato = QComboBox()
        self.tipo_contrato.addItems(["Plazo Fijo", "Indefinido"])
        self.tipo_contrato.setCurrentText(self.trabajador.get("tipo_contrato", "Plazo Fijo"))
        self.cargo = QLineEdit(self.trabajador.get("cargo", ""))

        # AFP / Salud combos
        self.afp_combo = QComboBox()
        self.afps = rrhh_service.obtener_afps()
        self.afp_combo.addItem("-- Sin AFP --", None)
        for a in self.afps:
            self.afp_combo.addItem(a["nombre"], a["id"])

        afp_id_actual = self.trabajador.get("afp_id")
        if afp_id_actual:
            index = self.afp_combo.findData(afp_id_actual)
            if index >= 0:
                self.afp_combo.setCurrentIndex(index)

        self.salud_combo = QComboBox()
        self.sistemas_salud = rrhh_service.obtener_sistemas_salud()
        self.salud_combo.addItem("-- Sin Salud --", None)
        for s in self.sistemas_salud:
            self.salud_combo.addItem(f"{s['nombre']} ({s['tipo']})", s["id"])
        salud_id_actual = self.trabajador.get("sistema_salud_id")
        if salud_id_actual:
            idx = self.salud_combo.findData(salud_id_actual)
            if idx >= 0:
                self.salud_combo.setCurrentIndex(idx)

        # % salud y cargas
        self.porcentaje_salud = QDoubleSpinBox()
        self.porcentaje_salud.setSuffix(" %")
        self.porcentaje_salud.setDecimals(2)
        self.porcentaje_salud.setMaximum(100.0)
        self.porcentaje_salud.setValue(float(self.trabajador.get("porcentaje_salud", 7.0)))

        self.cargas_familiares = QSpinBox()
        self.cargas_familiares.setMinimum(0)
        self.cargas_familiares.setMaximum(50)
        self.cargas_familiares.setValue(int(self.trabajador.get("cargas_familiares", 0)))

        # Sueldo base
        self.sueldo_base = QDoubleSpinBox()
        self.sueldo_base.setMaximum(999_999_999)
        self.sueldo_base.setDecimals(0)
        self.sueldo_base.setValue(float(self.trabajador.get("sueldo_base", 0)))

        # Formulario
        layout.addRow("RUT:", self.rut)
        layout.addRow("Nombre:", self.nombre)
        layout.addRow("Fecha Ingreso (YYYY-MM-DD):", self.fecha_ingreso)
        layout.addRow("Tipo Contrato:", self.tipo_contrato)
        layout.addRow("Cargo:", self.cargo)
        layout.addRow("AFP:", self.afp_combo)
        layout.addRow("Sistema de Salud:", self.salud_combo)
        layout.addRow("% Salud:", self.porcentaje_salud)
        layout.addRow("Cargas Familiares:", self.cargas_familiares)
        layout.addRow("Sueldo Base:", self.sueldo_base)

        # Botones
        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.clicked.connect(self.exportar_excel)

        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.addButton(self.btn_exportar, QDialogButtonBox.ActionRole)

        self.botones.accepted.connect(self.validar_y_guardar)
        self.botones.rejected.connect(self.reject)
        layout.addWidget(self.botones)

        self.datos = None

    def validar_y_guardar(self):
        rut = self.rut.text().strip()
        nombre = self.nombre.text().strip()
        fecha_ingreso = self.fecha_ingreso.text().strip()

        if not rut or not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", rut):
            QMessageBox.warning(self, "Error", "Ingrese un RUT válido (formato 12.345.678-9).")
            return
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return
        if not fecha_ingreso:
            QMessageBox.warning(self, "Error", "La fecha de ingreso es obligatoria (YYYY-MM-DD).")
            return

        self.datos = {
            "rut": rut,
            "nombre": nombre,
            "fecha_ingreso": fecha_ingreso,
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

        # Botones
        boton_layout = QHBoxLayout()
        self.btn_agregar = QPushButton(" Agregar")
        self.btn_editar = QPushButton(" Editar")
        self.btn_eliminar = QPushButton(" Eliminar")
        boton_layout.addWidget(self.btn_agregar)
        boton_layout.addWidget(self.btn_editar)
        boton_layout.addWidget(self.btn_eliminar)
        layout.addLayout(boton_layout)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "RUT", "Nombre", "Fecha Ingreso", "Tipo Contrato",
            "Cargo", "AFP", "Salud", "Sueldo Base",
        ])
        layout.addWidget(self.tabla)

        # Conexiones
        self.btn_agregar.clicked.connect(self.agregar_trabajador)
        self.btn_editar.clicked.connect(self.editar_trabajador)
        self.btn_eliminar.clicked.connect(self.eliminar_trabajador)

        self.cargar_trabajadores()

    def cargar_trabajadores(self):
        self.tabla.setRowCount(0)
        trabajadores = rrhh_service.obtener_trabajadores()
        afps = {a["id"]: a["nombre"] for a in rrhh_service.obtener_afps()}
        sistemas = {s["id"]: s["nombre"] for s in rrhh_service.obtener_sistemas_salud()}

        for row, t in enumerate(trabajadores):
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(t.get("rut", "")))
            self.tabla.setItem(row, 1, QTableWidgetItem(t.get("nombre", "")))
            self.tabla.setItem(row, 2, QTableWidgetItem(str(t.get("fecha_ingreso", ""))))
            self.tabla.setItem(row, 3, QTableWidgetItem(t.get("tipo_contrato", "")))
            self.tabla.setItem(row, 4, QTableWidgetItem(t.get("cargo", "")))

            afp_nombre = afps.get(t.get("afp_id")) if t.get("afp_id") else ""
            self.tabla.setItem(row, 5, QTableWidgetItem(afp_nombre))

            sal_nombre = sistemas.get(t.get("sistema_salud_id")) if t.get("sistema_salud_id") else ""
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


# ====================================================
#  DIALOGO DE LIQUIDACIÓN (todos los campos del Excel)
# ====================================================

class DialogoLiquidacion(QDialog):



    def exportar_excel(self):
        """
        Genera un Excel similar al ejemplo proporcionado.
        Exporta todos los haberes, descuentos, totales y datos adicionales.
        """
        # --- Seleccionar ruta ---
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar liquidación",
            f"Liquidacion_{self.periodo_edit.text()}_{self.lbl_rut.text()}.xlsx",
            "Excel (*.xlsx)"
        )
        if not ruta:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Liquidación"

        fila = 1

        # =======================
        #   TITULO
        # =======================
        ws["A1"] = "LIQUIDACIÓN DE SUELDO"
        fila += 2

        # =======================
        #   HABERES IMPONIBLES
        # =======================
        ws[f"A{fila}"] = "HABERES IMPONIBLES"
        fila += 1

        for cid, spin in self.campos_concepto.items():
            info = self.info_concepto[cid]
            if info["grupo"] == "haber_imponible":
                ws[f"A{fila}"] = info["nombre"]
                ws[f"B{fila}"] = int(spin.value())
                fila += 1

        fila += 1
        ws[f"A{fila}"] = "TOTAL HABERES IMPONIBLES"
        ws[f"B{fila}"] = int(self.lbl_total_hab_impon.text())
        fila += 2

        # =======================
        #   HABERES NO IMPONIBLES
        # =======================
        ws[f"A{fila}"] = "HABERES NO IMPONIBLES"
        fila += 1

        for cid, spin in self.campos_concepto.items():
            info = self.info_concepto[cid]
            if info["grupo"] == "haber_no_imponible":
                ws[f"A{fila}"] = info["nombre"]
                ws[f"B{fila}"] = int(spin.value())
                fila += 1

        fila += 1
        ws[f"A{fila}"] = "TOTAL HABERES NO IMPONIBLES"
        ws[f"B{fila}"] = int(self.lbl_total_hab_no_impon.text())
        fila += 2

        # =======================
        #   DESCUENTOS PREVISIONALES
        # =======================
        ws[f"A{fila}"] = "DESCUENTOS PREVISIONALES"
        fila += 1

        for cid, spin in self.campos_concepto.items():
            info = self.info_concepto[cid]
            if info["grupo"] == "descuento_previsional":
                ws[f"A{fila}"] = info["nombre"]
                ws[f"B{fila}"] = int(spin.value())
                fila += 1

        fila += 1
        ws[f"A{fila}"] = "TOTAL DESCUENTOS PREVISIONALES"
        ws[f"B{fila}"] = int(self.lbl_total_desc_prev.text())
        fila += 2

        # =======================
        #   OTROS DESCUENTOS
        # =======================
        ws[f"A{fila}"] = "OTROS DESCUENTOS"
        fila += 1

        for cid, spin in self.campos_concepto.items():
            info = self.info_concepto[cid]
            if info["grupo"] == "descuento_otro":
                ws[f"A{fila}"] = info["nombre"]
                ws[f"B{fila}"] = int(spin.value())
                fila += 1

        fila += 1
        ws[f"A{fila}"] = "TOTAL OTROS DESCUENTOS"
        ws[f"B{fila}"] = int(self.lbl_total_desc_otros.text())
        fila += 2

        # =======================
        #   TOTALES GENERALES
        # =======================
        ws[f"A{fila}"] = "TOTAL HABERES"
        ws[f"B{fila}"] = int(self.lbl_total_haberes.text())
        fila += 1

        ws[f"A{fila}"] = "TOTAL DESCUENTO GENERAL"
        ws[f"B{fila}"] = int(self.lbl_total_desc_general.text())
        fila += 1

        ws[f"A{fila}"] = "LÍQUIDO A PAGAR"
        ws[f"B{fila}"] = int(self.lbl_liquido_pagar.text().replace("<b>", "").replace("</b>", ""))
        fila += 3

        # =======================
        #   DATOS ADICIONALES (lado derecho Excel)
        # =======================
        ws[f"A{fila}"] = "DATOS ADICIONALES"
        fila += 1

        ws[f"A{fila}"] = "DÍAS TRABAJADOS"
        ws[f"B{fila}"] = self.dias_trabajados.value()
        fila += 1

        ws[f"A{fila}"] = "Nº HORAS EXTRAS"
        ws[f"B{fila}"] = self.num_horas_extras.value()
        fila += 1

        ws[f"A{fila}"] = "BASE IMPONIBLE"
        ws[f"B{fila}"] = int(self.lbl_base_imponible.text())
        fila += 1

        ws[f"A{fila}"] = "BASE TRIBUTABLE"
        ws[f"B{fila}"] = int(self.lbl_base_tributable.text())
        fila += 1

        ws[f"A{fila}"] = "AFP Trabajador"
        ws[f"B{fila}"] = self.lbl_afp_trabajador.text()
        fila += 1

        ws[f"A{fila}"] = "Cotización AFP"
        ws[f"B{fila}"] = self.lbl_afp_tasa.text()
        fila += 1

        ws[f"A{fila}"] = "Previsión Trabajador"
        ws[f"B{fila}"] = self.lbl_prev_trabajador.text()
        fila += 1

        ws[f"A{fila}"] = "% a Cotizar"
        ws[f"B{fila}"] = self.lbl_prev_tasa.text()
        fila += 1

        ws[f"A{fila}"] = "RUT"
        ws[f"B{fila}"] = self.lbl_rut.text()
        fila += 1

        ws[f"A{fila}"] = "Observaciones"
        ws[f"B{fila}"] = self.observaciones_edit.text()
        fila += 2

        # =======================
        #   RETROACTIVO
        # =======================
        ws[f"A{fila}"] = "RETROACTIVO ASIGNACIÓN FAMILIAR"
        fila += 1

        ws[f"A{fila}"] = "Antiguo"
        ws[f"B{fila}"] = int(self.retro_antiguo.value())
        fila += 1

        ws[f"A{fila}"] = "Actual"
        ws[f"B{fila}"] = int(self.retro_actual.value())
        fila += 1

        ws[f"A{fila}"] = "Diferencia"
        ws[f"B{fila}"] = int(self.retro_diferencia.value())
        fila += 2

        # ==== Guardar ====
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
                spin = QDoubleSpinBox()
                spin.setDecimals(0)
                spin.setMaximum(999_999_999)
                spin.valueChanged.connect(self.actualizar_totales_preview)

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
        self.lbl_total_haberes = QLabel("0")

        self.lbl_total_desc_prev = QLabel("0")
        self.lbl_total_desc_otros = QLabel("0")
        self.lbl_total_desc_general = QLabel("0")

        self.lbl_liquido_pagar = QLabel("<b>0</b>")

        tot_layout.addRow("TOTAL HABERES IMPONIBLES:", self.lbl_total_hab_impon)
        tot_layout.addRow("TOTAL HABERES NO IMPONIBLES:", self.lbl_total_hab_no_impon)
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
        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.clicked.connect(self.exportar_excel)

        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.addButton(self.btn_exportar, QDialogButtonBox.ActionRole)

        self.botones.accepted.connect(self.guardar)
        self.botones.rejected.connect(self.reject)
        main_layout.addWidget(self.botones)

        # Eventos
        self.trabajador_combo.currentIndexChanged.connect(self._actualizar_datos_trabajador)

        # Edit / nuevo
        if self.liquidacion_existente:
            self._cargar_liquidacion_existente()
        else:
            self._actualizar_datos_trabajador()

    # ------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------

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

        self.actualizar_totales_preview()

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

        self.actualizar_totales_preview()

    def actualizar_totales_preview(self):
        total_impon = 0
        total_no_impon = 0
        total_desc_prev = 0
        total_desc_otro = 0

        for cid, spin in self.campos_concepto.items():
            monto = spin.value()
            info = self.info_concepto.get(cid, {})
            grupo = info.get("grupo")
            if grupo == "haber_imponible":
                total_impon += monto
            elif grupo == "haber_no_imponible":
                total_no_impon += monto
            elif grupo == "descuento_previsional":
                total_desc_prev += monto
            elif grupo == "descuento_otro":
                total_desc_otro += monto

        total_haberes = total_impon + total_no_impon
        total_desc_general = total_desc_prev + total_desc_otro
        liquido = total_haberes - total_desc_general

        self.lbl_total_hab_impon.setText(str(int(total_impon)))
        self.lbl_total_hab_no_impon.setText(str(int(total_no_impon)))
        self.lbl_total_haberes.setText(str(int(total_haberes)))
        self.lbl_total_desc_prev.setText(str(int(total_desc_prev)))
        self.lbl_total_desc_otros.setText(str(int(total_desc_otro)))
        self.lbl_total_desc_general.setText(str(int(total_desc_general)))
        self.lbl_liquido_pagar.setText(f"<b>{int(liquido)}</b>")

        self.lbl_base_imponible.setText(str(int(total_impon)))
        self.lbl_base_tributable.setText(str(int(total_impon)))

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

        cabecera = {
            "dias_trabajados": self.dias_trabajados.value(),
            "numero_horas_extras": self.num_horas_extras.value(),
            "retro_antiguo": self.retro_antiguo.value() or None,
            "retro_actual": self.retro_actual.value() or None,
            "retro_diferencia": self.retro_diferencia.value() or None,
            "observaciones": self.observaciones_edit.text().strip(),
        }

        montos_por_concepto = {cid: spin.value() for cid, spin in self.campos_concepto.items()}

        if self.liquidacion_existente:
            ok = rrhh_service.actualizar_liquidacion(
                self.liquidacion_existente["cabecera"]["id"],
                cabecera,
                montos_por_concepto,
            )
            if not ok:
                QMessageBox.warning(self, "Error", "No se pudo actualizar la liquidación.")
                return
        else:
            liq_id = rrhh_service.crear_liquidacion(
                trabajador_rut=t["rut"],
                periodo=periodo,
                datos_cabecera=cabecera,
                montos_por_concepto=montos_por_concepto,
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

        # Botones
        boton_layout = QHBoxLayout()
        self.btn_nueva = QPushButton(" Nueva Liquidación")
        self.btn_ver = QPushButton(" Ver / Editar")
        self.btn_eliminar = QPushButton(" Eliminar")
        boton_layout.addWidget(self.btn_nueva)
        boton_layout.addWidget(self.btn_ver)
        boton_layout.addWidget(self.btn_eliminar)
        layout.addLayout(boton_layout)

        # Tabla resumen
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Periodo", "RUT", "Nombre", "Total Haberes",
            "Total Descuentos", "Líquido a Pagar",
        ])
        layout.addWidget(self.tabla)

        # Conexiones
        self.btn_nueva.clicked.connect(self.crear_liquidacion)
        self.btn_ver.clicked.connect(self.ver_editar_liquidacion)
        self.btn_eliminar.clicked.connect(self.eliminar_liquidacion)

        self.cargar_liquidaciones()

    def cargar_liquidaciones(self):
        self.tabla.setRowCount(0)
        liquidaciones = rrhh_service.obtener_liquidaciones_resumen()
        self._ids = []
        for row, l in enumerate(liquidaciones):
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
