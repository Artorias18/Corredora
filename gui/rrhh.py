from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate

from services.database import (
    obtener_trabajadores,
    guardar_trabajador,
    calcular_liquidacion,
    guardar_liquidacion
)

# ==============================
# DASHBOARD PRINCIPAL DE RRHH
# ==============================
class DashboardRRHH(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Recursos Humanos")
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        titulo = QLabel("Gestión de Recursos Humanos")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "RUT", "Nombre", "Fecha ingreso", "Tipo contrato", "AFP", "Sueldo base"
        ])
        layout.addWidget(self.tabla)

        # Botones
        boton_layout = QHBoxLayout()
        self.btn_actualizar = QPushButton("Actualizar lista")
        self.btn_nuevo = QPushButton("Nuevo trabajador")
        self.btn_liquidacion = QPushButton("Generar liquidación")

        boton_layout.addWidget(self.btn_actualizar)
        boton_layout.addWidget(self.btn_nuevo)
        boton_layout.addWidget(self.btn_liquidacion)
        layout.addLayout(boton_layout)

        # Eventos
        self.btn_actualizar.clicked.connect(self.cargar_trabajadores)
        self.btn_liquidacion.clicked.connect(self.generar_liquidacion)
        self.btn_nuevo.clicked.connect(self.nuevo_trabajador)

        self.cargar_trabajadores()

    # ------------------------------
    # FUNCIONES DE LA INTERFAZ
    # ------------------------------
    def cargar_trabajadores(self):
        try:
            trabajadores = obtener_trabajadores()
            self.tabla.setRowCount(0)
            for i, t in enumerate(trabajadores):
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(t.get("rut", "")))
                self.tabla.setItem(i, 1, QTableWidgetItem(t.get("nombre", "")))
                self.tabla.setItem(i, 2, QTableWidgetItem(str(t.get("fecha_ingreso", ""))))
                self.tabla.setItem(i, 3, QTableWidgetItem(t.get("tipo_contrato", "")))
                self.tabla.setItem(i, 4, QTableWidgetItem(t.get("afp", "")))
                self.tabla.setItem(i, 5, QTableWidgetItem(str(t.get("sueldo_base", ""))))
            self.tabla.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los trabajadores:\n{e}")

    def generar_liquidacion(self):
        row = self.tabla.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atención", "Selecciona un trabajador primero.")
            return

        rut = self.tabla.item(row, 0).text()
        nombre = self.tabla.item(row, 1).text()

        trabajadores = obtener_trabajadores()
        trabajador = next((t for t in trabajadores if t["rut"] == rut), None)
        if not trabajador:
            QMessageBox.warning(self, "Error", "No se encontró el trabajador.")
            return

        liquidacion = calcular_liquidacion(trabajador)
        guardar_liquidacion(liquidacion)
        QMessageBox.information(
            self,
            "Liquidación generada",
            f"Se ha generado la liquidación para:\n\n{nombre}\n\n"
            f"Líquido a pagar: ${liquidacion['liquido_pagar']:,.0f}"
        )

    def nuevo_trabajador(self):
        dialogo = DialogNuevoTrabajador(self)
        if dialogo.exec():
            self.cargar_trabajadores()


# ==============================
# DIÁLOGO PARA NUEVO TRABAJADOR
# ==============================
class DialogNuevoTrabajador(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Trabajador")
        self.setFixedSize(400, 500)
        layout = QFormLayout(self)

        # Campos del formulario
        self.txt_rut = QLineEdit()
        self.txt_nombre = QLineEdit()
        self.date_ingreso = QDateEdit(QDate.currentDate())
        self.date_ingreso.setCalendarPopup(True)
        self.cmb_tipo_contrato = QComboBox()
        self.cmb_tipo_contrato.addItems(["Plazo Fijo", "Indefinido"])
        self.cmb_afp = QComboBox()
        self.cmb_afp.addItems(["Capital", "Modelo", "Habitat", "Planvital", "Provida", "Cuprum", "Uno"])
        self.cmb_isapre = QComboBox()
        self.cmb_isapre.addItems(["Fonasa", "Colmena", "Consalud", "Banmédica", "Vida Tres", "Nueva Masvida"])
        self.txt_sueldo_base = QLineEdit()
        self.txt_gratificacion = QLineEdit()
        self.txt_asignacion_familiar = QLineEdit()
        self.txt_colacion = QLineEdit()
        self.txt_movilizacion = QLineEdit()
        self.txt_viatico = QLineEdit()

        # Agregar campos al layout
        layout.addRow("RUT:", self.txt_rut)
        layout.addRow("Nombre:", self.txt_nombre)
        layout.addRow("Fecha de ingreso:", self.date_ingreso)
        layout.addRow("Tipo de contrato:", self.cmb_tipo_contrato)
        layout.addRow("AFP:", self.cmb_afp)
        layout.addRow("Isapre:", self.cmb_isapre)
        layout.addRow("Sueldo base:", self.txt_sueldo_base)
        layout.addRow("Gratificación:", self.txt_gratificacion)
        layout.addRow("Asignación familiar:", self.txt_asignacion_familiar)
        layout.addRow("Colación:", self.txt_colacion)
        layout.addRow("Movilización:", self.txt_movilizacion)
        layout.addRow("Viático:", self.txt_viatico)

        # Botones Guardar / Cancelar
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        layout.addRow(self.buttons)
        self.buttons.accepted.connect(self.guardar)
        self.buttons.rejected.connect(self.reject)

    def guardar(self):
        rut = self.txt_rut.text().strip()
        nombre = self.txt_nombre.text().strip()
        sueldo_base = self.txt_sueldo_base.text().strip()

        if not rut or not nombre or not sueldo_base:
            QMessageBox.warning(self, "Datos faltantes", "Debes completar al menos RUT, Nombre y Sueldo base.")
            return

        try:
            sueldo_base = float(sueldo_base)
        except ValueError:
            QMessageBox.warning(self, "Error", "El sueldo base debe ser un número.")
            return

        gratificacion = self.txt_gratificacion.text().strip()
        gratificacion = float(gratificacion) if gratificacion else sueldo_base / 4

        data = {
            "rut": rut,
            "nombre": nombre,
            "fecha_ingreso": self.date_ingreso.date().toString("yyyy-MM-dd"),
            "tipo_contrato": self.cmb_tipo_contrato.currentText(),
            "afp": self.cmb_afp.currentText(),
            "isapre": self.cmb_isapre.currentText(),
            "sueldo_base": sueldo_base,
            "gratificacion": gratificacion,
            "asignacion_familiar": self._to_float(self.txt_asignacion_familiar.text()),
            "colacion": self._to_float(self.txt_colacion.text()),
            "movilizacion": self._to_float(self.txt_movilizacion.text()),
            "viatico": self._to_float(self.txt_viatico.text()),
        }

        resultado = guardar_trabajador(data)
        if resultado:
            QMessageBox.information(self, "Éxito", "Trabajador guardado correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar el trabajador.")

    def _to_float(self, valor):
        try:
            return float(valor) if valor else 0
        except ValueError:
            return 0
        

