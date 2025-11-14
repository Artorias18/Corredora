# gui/rrhh.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLabel, QFormLayout, QDialog, QDialogButtonBox,
    QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit, QSpinBox
)
from PySide6.QtCore import Qt, QDate
from services import rrhh_service


# =========================================================================================
#   DASHBOARD PRINCIPAL
# =========================================================================================

class DashboardRRHH(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tab_trabajadores = TabTrabajadores()
        self.tab_liquidaciones = TabLiquidaciones()

        self.tabs.addTab(self.tab_trabajadores, " Trabajadores")
        self.tabs.addTab(self.tab_liquidaciones, " Liquidaciones")

        layout.addWidget(self.tabs)
        self.setLayout(layout)


# =========================================================================================
#   DIALOGO TRABAJADOR
# =========================================================================================

class DialogoTrabajador(QDialog):
    def __init__(self, trabajador=None):
        super().__init__()
        self.setWindowTitle("Ficha del Trabajador")

        layout = QFormLayout(self)
        self.trabajador = trabajador or {}

        # =============================
        # Campos del trabajador
        # =============================

        self.rut = QLineEdit(self.trabajador.get("rut", ""))
        self.nombre = QLineEdit(self.trabajador.get("nombre", ""))

        self.cargo = QLineEdit(self.trabajador.get("cargo", ""))

        self.tipo_contrato = QComboBox()
        self.tipo_contrato.addItems(["Indefinido", "Plazo Fijo"])
        self.tipo_contrato.setCurrentText(self.trabajador.get("tipo_contrato", "Indefinido"))

        # Fecha ingreso
        self.fecha_ingreso = QDateEdit()
        self.fecha_ingreso.setCalendarPopup(True)
        if "fecha_ingreso" in self.trabajador:
            self.fecha_ingreso.setDate(QDate.fromString(self.trabajador["fecha_ingreso"], "yyyy-MM-dd"))
        else:
            self.fecha_ingreso.setDate(QDate.currentDate())

        # Sueldo
        self.sueldo_base = QDoubleSpinBox()
        self.sueldo_base.setMaximum(99999999)
        self.sueldo_base.setValue(float(self.trabajador.get("sueldo_base", 0)))

        # Cargas familiares
        self.cargas = QSpinBox()
        self.cargas.setMaximum(20)
        self.cargas.setValue(self.trabajador.get("cargas_familiares", 0))

        # AFP (select real con ID)
        self.afp = QComboBox()
        self.afps = rrhh_service.obtener_afps()
        for a in self.afps:
            self.afp.addItem(a["nombre"], a["id"])
        if self.trabajador.get("afp_id"):
            self.afp.setCurrentIndex(
                next((i for i, a in enumerate(self.afps) if a["id"] == self.trabajador["afp_id"]), 0)
            )

        # Sistema de salud
        self.salud = QComboBox()
        self.saluds = rrhh_service.obtener_sistemas_salud()
        for s in self.saluds:
            self.salud.addItem(s["nombre"], s["id"])
        if self.trabajador.get("salud_id"):
            self.salud.setCurrentIndex(
                next((i for i, s in enumerate(self.saluds) if s["id"] == self.trabajador["salud_id"]), 0)
            )

        # =============================
        # Layout
        # =============================
        layout.addRow("RUT:", self.rut)
        layout.addRow("Nombre:", self.nombre)
        layout.addRow("Cargo:", self.cargo)
        layout.addRow("Tipo Contrato:", self.tipo_contrato)
        layout.addRow("Fecha Ingreso:", self.fecha_ingreso)
        layout.addRow("Sueldo Base:", self.sueldo_base)
        layout.addRow("Cargas Familiares:", self.cargas)
        layout.addRow("AFP:", self.afp)
        layout.addRow("Salud:", self.salud)

        # Botonera
        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.guardar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

        self.datos = None

    def guardar(self):
        if not self.rut.text().strip():
            QMessageBox.warning(self, "Error", "El RUT no puede estar vacío.")
            return
        if not self.nombre.text().strip():
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return

        self.datos = {
            "rut": self.rut.text().strip(),
            "nombre": self.nombre.text().strip(),
            "cargo": self.cargo.text().strip(),
            "tipo_contrato": self.tipo_contrato.currentText(),
            "fecha_ingreso": self.fecha_ingreso.date().toString("yyyy-MM-dd"),
            "sueldo_base": self.sueldo_base.value(),
            "cargas_familiares": self.cargas.value(),
            "afp_id": self.afp.currentData(),
            "salud_id": self.salud.currentData(),
        }

        self.accept()


# =========================================================================================
#   TAB TRABAJADORES
# =========================================================================================

class TabTrabajadores(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Botonera
        hbox = QHBoxLayout()
        self.btn_agregar = QPushButton("Agregar")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Eliminar")

        hbox.addWidget(self.btn_agregar)
        hbox.addWidget(self.btn_editar)
        hbox.addWidget(self.btn_eliminar)
        layout.addLayout(hbox)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "RUT", "Nombre", "Cargo", "Tipo Contrato",
            "Sueldo Base", "AFP", "Salud"
        ])
        layout.addWidget(self.tabla)

        # Conexión
        self.btn_agregar.clicked.connect(self.agregar)
        self.btn_editar.clicked.connect(self.editar)
        self.btn_eliminar.clicked.connect(self.eliminar)

        self.setLayout(layout)
        self.cargar()

    def cargar(self):
        self.tabla.setRowCount(0)
        trabajadores = rrhh_service.obtener_trabajadores()

        afps = {a["id"]: a["nombre"] for a in rrhh_service.obtener_afps()}
        saluds = {s["id"]: s["nombre"] for s in rrhh_service.obtener_sistemas_salud()}

        for row, t in enumerate(trabajadores):
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(t["rut"]))
            self.tabla.setItem(row, 1, QTableWidgetItem(t["nombre"]))
            self.tabla.setItem(row, 2, QTableWidgetItem(t.get("cargo", "")))
            self.tabla.setItem(row, 3, QTableWidgetItem(t.get("tipo_contrato", "")))
            self.tabla.setItem(row, 4, QTableWidgetItem(str(t.get("sueldo_base", 0))))
            self.tabla.setItem(row, 5, QTableWidgetItem(afps.get(t.get("afp_id"), "")))
            self.tabla.setItem(row, 6, QTableWidgetItem(saluds.get(t.get("salud_id"), "")))

    def agregar(self):
        dlg = DialogoTrabajador()
        if dlg.exec():
            rrhh_service.crear_trabajador(dlg.datos)
            self.cargar()

    def editar(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione un trabajador.")
            return

        rut = self.tabla.item(fila, 0).text()
        trabajadores = rrhh_service.obtener_trabajadores()
        trabajador = next((t for t in trabajadores if t["rut"] == rut), None)

        dlg = DialogoTrabajador(trabajador)
        if dlg.exec():
            rrhh_service.actualizar_trabajador(rut, dlg.datos)
            self.cargar()

    def eliminar(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione un trabajador.")
            return

        rut = self.tabla.item(fila, 0).text()

        if QMessageBox.question(self, "Confirmar", f"¿Eliminar trabajador {rut}?") == QMessageBox.Yes:
            rrhh_service.eliminar_trabajador(rut)
            self.cargar()


# =========================================================================================
#   DIALOGO LIQUIDACIÓN
# =========================================================================================

class DialogoLiquidacion(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nueva Liquidación")
        layout = QFormLayout(self)

        # Selección de trabajador
        self.trabajador = QComboBox()
        self.trabajadores = rrhh_service.obtener_trabajadores()
        for t in self.trabajadores:
            self.trabajador.addItem(f"{t['rut']} - {t['nombre']}", t)

        self.periodo = QLineEdit("2025-11")

        # Imponibles
        self.sueldo_base = QDoubleSpinBox()
        self.sueldo_base.setMaximum(99999999)

        self.gratificacion = QDoubleSpinBox()
        self.horas_extras = QDoubleSpinBox()
        self.bonos = QDoubleSpinBox()

        # No imponibles
        self.colacion = QDoubleSpinBox()
        self.movilizacion = QDoubleSpinBox()

        # Otros descuentos
        self.otros = QDoubleSpinBox()

        # Totales
        self.total_imponibles = QLabel("0")
        self.total_noimp = QLabel("0")
        self.total_descuentos = QLabel("0")
        self.liquido = QLabel("0")

        # Layout
        layout.addRow("Trabajador:", self.trabajador)
        layout.addRow("Periodo:", self.periodo)

        layout.addRow(QLabel("<b>Haberes Imponibles</b>"))
        layout.addRow("Sueldo Base:", self.sueldo_base)
        layout.addRow("Gratificación:", self.gratificacion)
        layout.addRow("Horas Extras:", self.horas_extras)
        layout.addRow("Bonos:", self.bonos)

        layout.addRow(QLabel("<b>No Imponibles</b>"))
        layout.addRow("Colación:", self.colacion)
        layout.addRow("Movilización:", self.movilizacion)

        layout.addRow(QLabel("<b>Otros Descuentos</b>"))
        layout.addRow("Otros:", self.otros)

        layout.addRow(QLabel("<b>Totales</b>"))
        layout.addRow("Imponibles:", self.total_imponibles)
        layout.addRow("No Imponibles:", self.total_noimp)
        layout.addRow("Descuentos:", self.total_descuentos)
        layout.addRow("Líquido:", self.liquido)

        # Conexiones
        self.trabajador.currentIndexChanged.connect(self.autocompletar)
        for w in [self.sueldo_base, self.gratificacion, self.horas_extras, self.bonos,
                  self.colacion, self.movilizacion, self.otros]:
            w.valueChanged.connect(self.calcular)

        self.autocompletar()

        # Botones
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.guardar)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.data = None

    def autocompletar(self):
        t = self.trabajador.currentData()
        if not t:
            return

        self.sueldo_base.setValue(t.get("sueldo_base", 0))
        self.calcular()

    def calcular(self):
        t = self.trabajador.currentData()
        if not t:
            return

        datos = {
            "sueldo_base": self.sueldo_base.value(),
            "gratificacion": self.gratificacion.value(),
            "horas_extras": self.horas_extras.value(),
            "bonos": self.bonos.value(),
            "colacion": self.colacion.value(),
            "movilizacion": self.movilizacion.value(),
            "otros_descuentos": self.otros.value(),
        }

        totales = rrhh_service.calcular_liquidacion(datos, t)

        self.total_imponibles.setText(str(totales["imponibles"]))
        self.total_noimp.setText(str(totales["no_imponibles"]))
        self.total_descuentos.setText(str(totales["total_descuentos"]))
        self.liquido.setText(str(totales["liquido_pagar"]))

        self.last_totales = totales

    def guardar(self):
        t = self.trabajador.currentData()

        cabecera = {
            "trabajador_rut": t["rut"],
            "periodo": self.periodo.text().strip(),
            "sueldo_base": t["sueldo_base"],
            "imponibles": self.last_totales["imponibles"],
            "no_imponibles": self.last_totales["no_imponibles"],
            "total_descuentos": self.last_totales["total_descuentos"],
            "liquido_pagar": self.last_totales["liquido_pagar"],
        }

        detalles = [
            {"tipo": "imponible", "descripcion": "Sueldo Base", "monto": self.sueldo_base.value()},
            {"tipo": "imponible", "descripcion": "Gratificación", "monto": self.gratificacion.value()},
            {"tipo": "imponible", "descripcion": "Horas Extras", "monto": self.horas_extras.value()},
            {"tipo": "imponible", "descripcion": "Bonos", "monto": self.bonos.value()},
            {"tipo": "no_imponible", "descripcion": "Colación", "monto": self.colacion.value()},
            {"tipo": "no_imponible", "descripcion": "Movilización", "monto": self.movilizacion.value()},
            {"tipo": "descuento", "descripcion": "Otros", "monto": self.otros.value()},
        ]

        self.data = (cabecera, detalles)
        self.accept()


# =========================================================================================
#   TAB LIQUIDACIONES
# =========================================================================================

class TabLiquidaciones(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Botonera
        hbox = QHBoxLayout()
        self.btn_nueva = QPushButton("Nueva")
        self.btn_ver = QPushButton("Ver Detalle")
        self.btn_eliminar = QPushButton("Eliminar")
        hbox.addWidget(self.btn_nueva)
        hbox.addWidget(self.btn_ver)
        hbox.addWidget(self.btn_eliminar)
        layout.addLayout(hbox)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["Periodo", "RUT", "Imponibles", "Descuentos", "Líquido"]
        )
        layout.addWidget(self.tabla)

        # Conexiones
        self.btn_nueva.clicked.connect(self.nueva)
        self.btn_ver.clicked.connect(self.ver)
        self.btn_eliminar.clicked.connect(self.eliminar)

        self.setLayout(layout)
        self.cargar()

    def cargar(self):
        self.tabla.setRowCount(0)
        liquidaciones = rrhh_service.obtener_liquidaciones()

        for row, l in enumerate(liquidaciones):
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(l["periodo"]))
            self.tabla.setItem(row, 1, QTableWidgetItem(l["trabajador_rut"]))
            self.tabla.setItem(row, 2, QTableWidgetItem(str(l["imponibles"])))
            self.tabla.setItem(row, 3, QTableWidgetItem(str(l["total_descuentos"])))
            self.tabla.setItem(row, 4, QTableWidgetItem(str(l["liquido_pagar"])))

    def nueva(self):
        dlg = DialogoLiquidacion()
        if dlg.exec():
            cabecera, detalles = dlg.data
            rrhh_service.crear_liquidacion(cabecera, detalles)
            self.cargar()

    def ver(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione una liquidación.")
            return

        liquidaciones = rrhh_service.obtener_liquidaciones()
        liquidacion = liquidaciones[fila]

        detalles = rrhh_service.obtener_detalle_liquidacion(liquidacion["id"])

        dlg = QDialog()
        dlg.setWindowTitle("Detalle Liquidación")
        vbox = QVBoxLayout(dlg)

        tabla = QTableWidget()
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["Tipo", "Descripción", "Monto"])
        tabla.setRowCount(len(detalles))

        for i, d in enumerate(detalles):
            tabla.setItem(i, 0, QTableWidgetItem(d["tipo"]))
            tabla.setItem(i, 1, QTableWidgetItem(d["descripcion"]))
            tabla.setItem(i, 2, QTableWidgetItem(str(d["monto"])))

        vbox.addWidget(tabla)
        dlg.exec()

    def eliminar(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Error", "Seleccione una liquidación.")
            return

        r = QMessageBox.question(self, "Confirmar", "¿Eliminar liquidación seleccionada?")
        if r != QMessageBox.Yes:
            return

        liquidaciones = rrhh_service.obtener_liquidaciones()
        liquidacion = liquidaciones[fila]

        rrhh_service.eliminar_liquidacion(liquidacion["id"])
        self.cargar()
