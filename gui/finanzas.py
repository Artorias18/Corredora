from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFileDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from datetime import date
from services.finanzas_service import generar_excel_ffmm_anual


class DashboardFinanzas(QWidget):
    def __init__(self):
        super().__init__()

        # Layout principal (todo dentro de un contenedor)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # =========================
        # Contenedor general
        # =========================
        container = QFrame()
        container.setFrameShape(QFrame.StyledPanel)
        container.setFrameShadow(QFrame.Raised)
        container.setStyleSheet("""
            QFrame {
                background-color: #2B2B2B;   /* fondo oscuro */
                border: 1px solid #444;
                border-radius: 10px;
            }
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(25, 25, 25, 25)
        container_layout.setSpacing(10)  # menos espacio entre filtros y botón

        # =========================
        # Filtros (Año / Mes) - CENTRADOS
        # =========================
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(10)
        filtros_layout.setAlignment(Qt.AlignCenter)

        lbl_anio = QLabel("Año:")
        lbl_anio.setStyleSheet("color: white; font-size: 14px;")
        self.cmb_anio = QComboBox()
        self.cmb_anio.setFixedWidth(100)

        anio_actual = date.today().year
        for anio in range(anio_actual - 5, anio_actual + 1):
            self.cmb_anio.addItem(str(anio))

        lbl_mes = QLabel("Mes:")
        lbl_mes.setStyleSheet("color: white; font-size: 14px;")
        self.cmb_mes = QComboBox()
        self.cmb_mes.setFixedWidth(160)

        MESES_ES = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }

        for numero, nombre in MESES_ES.items():
            self.cmb_mes.addItem(nombre, numero)

        self.cmb_mes.setCurrentIndex(date.today().month - 1)

        filtros_layout.addWidget(lbl_anio)
        filtros_layout.addWidget(self.cmb_anio)
        filtros_layout.addWidget(lbl_mes)
        filtros_layout.addWidget(self.cmb_mes)

        container_layout.addLayout(filtros_layout)

        # =========================
        # Botón Generar Excel justo debajo de los filtros
        # =========================
        self.btn_generar_ffmm = DoubleClickButton("Generar Excel FFMM")
        self.btn_generar_ffmm.setFixedSize(220, 40)
        self.btn_generar_ffmm.doubleClicked.connect(self.generar_ffmm)

        container_layout.addWidget(self.btn_generar_ffmm, alignment=Qt.AlignCenter)

        # =========================
        # Agregar container al layout principal
        # =========================
        main_layout.addWidget(container)

    def generar_ffmm(self):
        anio = int(self.cmb_anio.currentText())
        mes = int(self.cmb_mes.currentData())

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Excel FFMM",
            f"FFMM_{anio}_{mes}.xlsx",
            "Excel (*.xlsx)"
        )

        if ruta:
            try:
                generar_excel_ffmm_anual(anio, mes, ruta)

                QMessageBox.information(
                    self,
                    "Éxito",
                    f"El Excel FFMM se generó correctamente:\n{ruta}"
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Ocurrió un error al generar el Excel:\n{str(e)}"
                )


class DoubleClickButton(QPushButton):
    doubleClicked = Signal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()


        
    