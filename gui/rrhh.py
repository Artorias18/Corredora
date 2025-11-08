from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLabel, QFormLayout, QDialog, QDialogButtonBox,
    QLineEdit, QComboBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from services import rrhh_service
from services.rrhh_service import calcular_liquidacion

import re

# ====================================================
#  DASHBOARD PRINCIPAL RRHH
# ====================================================

class DashboardRRHH(QWidget):
    def __init__(self):
        super().__init__()
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
        self.setWindowTitle("Agregar / Editar Trabajador")
        self.trabajador = trabajador or {}

        layout = QFormLayout(self)

        self.rut = QLineEdit(self.trabajador.get("rut", ""))
        self.nombre = QLineEdit(self.trabajador.get("nombre", ""))
        self.tipo_contrato = QComboBox()
        self.tipo_contrato.addItems(["Plazo Fijo", "Indefinido"])
        self.tipo_contrato.setCurrentText(self.trabajador.get("tipo_contrato", "Plazo Fijo"))
        self.afp = QLineEdit(self.trabajador.get("afp", ""))

        self.prevision_salud = QComboBox()
        self.prevision_salud.addItems(["Fonasa", "Isapre"])
        self.prevision_salud.setCurrentText(self.trabajador.get("prevision_salud", "Fonasa"))

        self.cotizacion_salud = QDoubleSpinBox()
        self.cotizacion_salud.setSuffix(" %")
        self.cotizacion_salud.setMaximum(99.9)
        self.cotizacion_salud.setValue(float(self.trabajador.get("cotizacion_salud", 7.0)))

        self.sueldo_base = QDoubleSpinBox()
        self.sueldo_base.setMaximum(99999999)
        self.sueldo_base.setValue(float(self.trabajador.get("sueldo_base", 0)))

        layout.addRow("RUT:", self.rut)
        layout.addRow("Nombre:", self.nombre)
        layout.addRow("Tipo Contrato:", self.tipo_contrato)
        layout.addRow("AFP:", self.afp)
        layout.addRow("Previsión de Salud:", self.prevision_salud)
        layout.addRow("Cotización Salud:", self.cotizacion_salud)
        layout.addRow("Sueldo Base:", self.sueldo_base)

        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.validar_y_guardar)
        self.botones.rejected.connect(self.reject)
        layout.addWidget(self.botones)

        self.datos = None

    def validar_y_guardar(self):
        rut = self.rut.text().strip()
        nombre = self.nombre.text().strip()

        if not rut or not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$", rut):
            QMessageBox.warning(self, "Error", "Ingrese un RUT válido (formato 12.345.678-9).")
            return
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        if self.prevision_salud.currentText() == "Fonasa":
            self.cotizacion_salud.setValue(7.0)

        self.datos = {
            "rut": rut,
            "nombre": nombre,
            "tipo_contrato": self.tipo_contrato.currentText(),
            "afp": self.afp.text().strip(),
            "prevision_salud": self.prevision_salud.currentText(),
            "cotizacion_salud": self.cotizacion_salud.value(),
            "sueldo_base": self.sueldo_base.value()
        }

        self.accept()


# ====================================================
# PESTAÑA DE TRABAJADORES
# ====================================================

class TabTrabajadores(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # ----------------------------
        # Botones de acción
        # ----------------------------
        boton_layout = QHBoxLayout()
        self.btn_agregar = QPushButton(" Agregar")
        self.btn_editar = QPushButton(" Editar")
        self.btn_eliminar = QPushButton(" Eliminar")
        boton_layout.addWidget(self.btn_agregar)
        boton_layout.addWidget(self.btn_editar)
        boton_layout.addWidget(self.btn_eliminar)
        layout.addLayout(boton_layout)

        # ----------------------------
        # Tabla de trabajadores
        # ----------------------------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "RUT", "Nombre", "Tipo Contrato", "AFP",
            "Previsión Salud", "Cotización Salud", "Sueldo Base"
        ])
        layout.addWidget(self.tabla)

        # ----------------------------
        # Conexiones
        # ----------------------------
        self.btn_agregar.clicked.connect(self.agregar_trabajador)
        self.btn_editar.clicked.connect(self.editar_trabajador)
        self.btn_eliminar.clicked.connect(self.eliminar_trabajador)

        # ----------------------------
        # Cargar datos iniciales
        # ----------------------------
        self.cargar_trabajadores()

    # ====================================================
    #  CARGAR TRABAJADORES
    # ====================================================
    def cargar_trabajadores(self):
        self.tabla.setRowCount(0)
        trabajadores = rrhh_service.obtener_trabajadores()
        for row, t in enumerate(trabajadores):
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(t.get("rut", "")))
            self.tabla.setItem(row, 1, QTableWidgetItem(t.get("nombre", "")))
            self.tabla.setItem(row, 2, QTableWidgetItem(t.get("tipo_contrato", "")))
            self.tabla.setItem(row, 3, QTableWidgetItem(t.get("afp", "")))
            self.tabla.setItem(row, 4, QTableWidgetItem(t.get("prevision_salud", "")))
            self.tabla.setItem(row, 5, QTableWidgetItem(str(t.get("cotizacion_salud", 0))))
            self.tabla.setItem(row, 6, QTableWidgetItem(str(t.get("sueldo_base", 0))))

    # ====================================================
    #  AGREGAR TRABAJADOR
    # ====================================================
    def agregar_trabajador(self):
        dialogo = DialogoTrabajador()
        if dialogo.exec():
            datos = dialogo.datos
            if datos:
                rrhh_service.crear_trabajador(datos)
                self.cargar_trabajadores()

    # ====================================================
    #  EDITAR TRABAJADOR
    # ====================================================
    def editar_trabajador(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un trabajador para editar.")
            return

        rut = self.tabla.item(fila, 0).text()
        nombre = self.tabla.item(fila, 1).text()
        tipo_contrato = self.tabla.item(fila, 2).text()
        afp = self.tabla.item(fila, 3).text()
        prevision = self.tabla.item(fila, 4).text()
        cotizacion_salud = float(self.tabla.item(fila, 5).text() or 0)
        sueldo_base = float(self.tabla.item(fila, 6).text() or 0)

        trabajador = {
            "rut": rut,
            "nombre": nombre,
            "tipo_contrato": tipo_contrato,
            "afp": afp,
            "prevision_salud": prevision,
            "cotizacion_salud": cotizacion_salud,
            "sueldo_base": sueldo_base,
        }

        dialogo = DialogoTrabajador(trabajador)
        if dialogo.exec():
            datos = dialogo.datos
            if datos:
                rrhh_service.actualizar_trabajador(rut, datos)
                self.cargar_trabajadores()

    # ====================================================
    #  ELIMINAR TRABAJADOR
    # ====================================================
    def eliminar_trabajador(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un trabajador para eliminar.")
            return

        rut = self.tabla.item(fila, 0).text()
        confirm = QMessageBox.question(self, "Confirmar", f"¿Eliminar trabajador {rut}?")
        if confirm == QMessageBox.Yes:
            rrhh_service.eliminar_trabajador(rut)
            self.cargar_trabajadores()


# ====================================================
#  PESTAÑA DE LIQUIDACIONES
# ====================================================

class DialogoLiquidacion(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generar Liquidación")
        layout = QFormLayout(self)

        # Combo con los trabajadores
        self.rut = QComboBox()
        trabajadores = rrhh_service.obtener_trabajadores()
        for t in trabajadores:
            self.rut.addItem(f"{t['rut']} - {t['nombre']}", t)

        self.periodo = QLineEdit("2025-11")

        # Campos base
        self.sueldo_base = QDoubleSpinBox(); self.sueldo_base.setMaximum(99999999)
        self.gratificacion = QDoubleSpinBox()
        self.horas_extras = QDoubleSpinBox()
        self.bonos = QDoubleSpinBox()
        self.colacion = QDoubleSpinBox()
        self.movilizacion = QDoubleSpinBox()
        self.otros_descuentos = QDoubleSpinBox()

        # Descuentos legales (autocalculados)
        self.afp = QDoubleSpinBox(); self.afp.setMaximum(9999999)
        self.salud = QDoubleSpinBox(); self.salud.setMaximum(9999999)

        # Totales mostrados
        self.total_imponibles = QLabel("0")
        self.total_descuentos = QLabel("0")
        self.liquido_pagar = QLabel("0")

        # Agregar al layout
        layout.addRow("Trabajador:", self.rut)
        layout.addRow("Periodo:", self.periodo)
        layout.addRow("Sueldo Base:", self.sueldo_base)
        layout.addRow("Gratificación:", self.gratificacion)
        layout.addRow("Horas Extras:", self.horas_extras)
        layout.addRow("Bonos:", self.bonos)
        layout.addRow("Colación:", self.colacion)
        layout.addRow("Movilización:", self.movilizacion)
        layout.addRow("Otros Descuentos:", self.otros_descuentos)
        layout.addRow(QLabel("<b>Descuentos Legales</b>"))
        layout.addRow("AFP:", self.afp)
        layout.addRow("Salud:", self.salud)
        layout.addRow(QLabel("<b>Totales</b>"))
        layout.addRow("Haberes Imponibles:", self.total_imponibles)
        layout.addRow("Descuentos:", self.total_descuentos)
        layout.addRow("Líquido a Pagar:", self.liquido_pagar)

        # Botones
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.calcular_y_guardar)
        self.botones.rejected.connect(self.reject)
        layout.addWidget(self.botones)
        self.setLayout(layout)

        # Conexiones
        self.rut.currentIndexChanged.connect(self.autocompletar_trabajador)
        for sp in [self.sueldo_base, self.gratificacion, self.horas_extras, self.bonos,
                   self.colacion, self.movilizacion, self.otros_descuentos]:
            sp.valueChanged.connect(self.actualizar_totales)

        self.datos = None
        self.autocompletar_trabajador()

    # Autocompletar desde trabajador
    def autocompletar_trabajador(self):
        t = self.rut.currentData()
        if not t:
            return
        self.sueldo_base.setValue(float(t.get("sueldo_base", 0)))
        self.afp.setValue(round(t.get("sueldo_base", 0) * 0.1144, 0))
        salud_pct = t.get("cotizacion_salud", 7.0)
        self.salud.setValue(round(t.get("sueldo_base", 0) * salud_pct / 100, 0))
        self.actualizar_totales()

    # Cálculo en vivo
    def actualizar_totales(self):
        datos = {
            "sueldo_base": self.sueldo_base.value(),
            "gratificacion": self.gratificacion.value(),
            "horas_extras": self.horas_extras.value(),
            "bonos": self.bonos.value(),
            "colacion": self.colacion.value(),
            "movilizacion": self.movilizacion.value(),
            "afp": self.afp.value(),
            "salud": self.salud.value(),
            "otros_descuentos": self.otros_descuentos.value(),
        }

        datos = rrhh_service.calcular_liquidacion(datos)
        self.total_imponibles.setText(str(datos["total_haberes_imponibles"]))
        self.total_descuentos.setText(str(datos["total_descuentos"]))
        self.liquido_pagar.setText(str(datos["liquido_pagar"]))

    # Guardar final
    def calcular_y_guardar(self):
        base_data = {
            "trabajador_rut": self.rut.currentText().split(" - ")[0],
            "periodo": self.periodo.text().strip(),
            "sueldo_base": self.sueldo_base.value(),
            "gratificacion": self.gratificacion.value(),
            "horas_extras": self.horas_extras.value(),
            "bonos": self.bonos.value(),
            "colacion": self.colacion.value(),
            "movilizacion": self.movilizacion.value(),
            "afp": self.afp.value(),
            "salud": self.salud.value(),
            "otros_descuentos": self.otros_descuentos.value(),
        }

        base_data = rrhh_service.calcular_liquidacion(base_data)

        detalles = [
            {"tipo": "imponible", "descripcion": "Sueldo Base", "monto": base_data["sueldo_base"]},
            {"tipo": "imponible", "descripcion": "Gratificación", "monto": base_data["gratificacion"]},
            {"tipo": "imponible", "descripcion": "Horas Extras", "monto": base_data["horas_extras"]},
            {"tipo": "imponible", "descripcion": "Bonos", "monto": base_data["bonos"]},
            {"tipo": "no_imponible", "descripcion": "Colación", "monto": base_data["colacion"]},
            {"tipo": "no_imponible", "descripcion": "Movilización", "monto": base_data["movilizacion"]},
            {"tipo": "descuento", "descripcion": "AFP", "monto": base_data["afp"]},
            {"tipo": "descuento", "descripcion": "Salud", "monto": base_data["salud"]},
            {"tipo": "descuento", "descripcion": "Otros", "monto": base_data["otros_descuentos"]},
        ]

        self.datos = (base_data, detalles)
        self.accept()






class TabLiquidaciones(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # ----------------------------
        # Botones principales
        # ----------------------------
        boton_layout = QHBoxLayout()
        self.btn_agregar = QPushButton(" Nueva Liquidación")
        self.btn_ver = QPushButton(" Ver Detalle")
        self.btn_eliminar = QPushButton(" Eliminar")
        self.btn_editar = QPushButton("Editar")
        boton_layout.addWidget(self.btn_editar)
        self.btn_editar.clicked.connect(self.editar_liquidacion)

        boton_layout.addWidget(self.btn_agregar)
        boton_layout.addWidget(self.btn_ver)
        boton_layout.addWidget(self.btn_eliminar)
        layout.addLayout(boton_layout)

        # ----------------------------
        # Tabla de liquidaciones
        # ----------------------------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Periodo", "RUT Trabajador", "Haberes Imponibles",
            "Descuentos", "Líquido a Pagar", "Fecha Emisión"
        ])
        layout.addWidget(self.tabla)

        # ----------------------------
        # Conexiones
        # ----------------------------
        self.btn_agregar.clicked.connect(self.crear_liquidacion)
        self.btn_ver.clicked.connect(self.ver_detalle)
        self.btn_eliminar.clicked.connect(self.eliminar_liquidacion)

        self.cargar_liquidaciones()

    # ====================================================
    #  CARGAR LIQUIDACIONES
    # ====================================================
    def cargar_liquidaciones(self):
        self.tabla.setRowCount(0)
        liquidaciones = rrhh_service.obtener_liquidaciones()
        for row, l in enumerate(liquidaciones):
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(l.get("periodo", "")))
            self.tabla.setItem(row, 1, QTableWidgetItem(l.get("trabajador_rut", "")))
            self.tabla.setItem(row, 2, QTableWidgetItem(str(l.get("total_haberes_imponibles", 0))))
            self.tabla.setItem(row, 3, QTableWidgetItem(str(l.get("total_descuentos", 0))))
            self.tabla.setItem(row, 4, QTableWidgetItem(str(l.get("liquido_pagar", 0))))
            self.tabla.setItem(row, 5, QTableWidgetItem(str(l.get("fecha_emision", ""))))

    # ====================================================
    #  CREAR LIQUIDACIÓN
    # ====================================================
    def crear_liquidacion(self):
        dialogo = DialogoLiquidacion()
        if dialogo.exec():
            data, detalles = dialogo.datos
            if data and detalles:
                rrhh_service.crear_liquidacion(data, detalles)
                self.cargar_liquidaciones()

    # ====================================================
    #  VER DETALLE
    # ====================================================
    def ver_detalle(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccione una liquidación para ver.")
            return

        liquidacion_id = rrhh_service.obtener_liquidaciones()[fila]["id"]
        detalles = rrhh_service.obtener_detalle_liquidacion(liquidacion_id)

        dlg = QDialog(self)
        dlg.setWindowTitle("Detalle de Liquidación")
        vbox = QVBoxLayout(dlg)

        tabla = QTableWidget()
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["Tipo", "Descripción", "Monto"])
        tabla.setRowCount(len(detalles))
        for i, d in enumerate(detalles):
            tabla.setItem(i, 0, QTableWidgetItem(d.get("tipo", "")))
            tabla.setItem(i, 1, QTableWidgetItem(d.get("descripcion", "")))
            tabla.setItem(i, 2, QTableWidgetItem(str(d.get("monto", 0))))
        vbox.addWidget(tabla)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dlg.close)
        vbox.addWidget(btn_cerrar)
        dlg.setLayout(vbox)
        dlg.exec()

    # ====================================================
    #  ELIMINAR LIQUIDACIÓN
    # ====================================================
    def eliminar_liquidacion(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccione una liquidación para eliminar.")
            return
        periodo = self.tabla.item(fila, 0).text()
        rut = self.tabla.item(fila, 1).text()
        confirm = QMessageBox.question(self, "Confirmar", f"¿Eliminar liquidación de {rut} ({periodo})?")
        if confirm == QMessageBox.Yes:
            liquidacion_id = rrhh_service.obtener_liquidaciones()[fila]["id"]
            rrhh_service.eliminar_liquidacion(liquidacion_id)
            self.cargar_liquidaciones()



    def editar_liquidacion(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Seleccione una liquidación para editar.")
            return

        liquidaciones = rrhh_service.obtener_liquidaciones()
        liquidacion = liquidaciones[fila]
        detalles = rrhh_service.obtener_detalle_liquidacion(liquidacion["id"])

        # Abre el diálogo precargado
        dialogo = DialogoLiquidacion()
        dialogo.periodo.setText(liquidacion["periodo"])
        dialogo.rut.setCurrentText(liquidacion["trabajador_rut"])

        # Cargamos datos básicos (si existen)
        dialogo.sueldo_base.setValue(float(liquidacion.get("sueldo_base", 0)))
        dialogo.gratificacion.setValue(next((d["monto"] for d in detalles if d["descripcion"] == "Gratificación"), 0))
        dialogo.horas_extras.setValue(next((d["monto"] for d in detalles if d["descripcion"] == "Horas Extras"), 0))
        dialogo.bonos.setValue(next((d["monto"] for d in detalles if d["descripcion"] == "Bonos"), 0))
        dialogo.colacion.setValue(next((d["monto"] for d in detalles if d["descripcion"] == "Colación"), 0))
        dialogo.movilizacion.setValue(next((d["monto"] for d in detalles if d["descripcion"] == "Movilización"), 0))
        dialogo.otros_descuentos.setValue(next((d["monto"] for d in detalles if d["descripcion"] == "Otros"), 0))

        if dialogo.exec():
            data, nuevos_detalles = dialogo.datos
            rrhh_service.actualizar_liquidacion(liquidacion["id"], data, nuevos_detalles)
            self.cargar_liquidaciones()

        



            
