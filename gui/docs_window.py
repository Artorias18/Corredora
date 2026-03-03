from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QComboBox, QTableWidget, QTableWidgetItem, QPushButton,
    QFileDialog, QInputDialog, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt
from services.documentos_service import DocumentosService

class DocumentosWindow(QWidget):
    def __init__(self, rol):
        super().__init__()
        self.setWindowTitle("Documentos")
        self.resize(900, 600)

        self.rol = rol
        self.service = DocumentosService()

        self.layout = QVBoxLayout(self)

        # ---------------- ESTILOS ----------------
        self.setStyleSheet("""
            QPushButton {
                border-radius: 8px;
                padding: 6px 14px;
                font-weight: 600;
                min-height: 32px;
            }

            QPushButton#descargar {
                background-color: #2E86C1;
                color: white;
            }

            QPushButton#descargar:hover {
                background-color: #1F618D;
            }

            QPushButton#eliminar {
                background-color: #E74C3C;
                color: white;
            }

            QPushButton#eliminar:hover {
                background-color: #C0392B;
            }

            QPushButton#subir {
                background-color: #27AE60;
                color: white;
                padding: 8px 18px;
            }

            QPushButton#subir:hover {
                background-color: #1E8449;
            }
        """)

        # ---------------- FILTROS ----------------
        filtro_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre...")
        self.search_input.textChanged.connect(self.cargar_documentos)

        self.modulo_combo = QComboBox()
        self.modulo_combo.addItem("Todos", "")
        self.modulo_combo.addItem("Ventas", "ventas")
        self.modulo_combo.addItem("Arriendos", "arriendos")
        self.modulo_combo.addItem("Gestión Usuario", "gestion usuario")
        self.modulo_combo.addItem("RRHH", "rrhh")
        self.modulo_combo.addItem("Finanzas", "finanzas")
        self.modulo_combo.currentIndexChanged.connect(self.cargar_documentos)

        filtro_layout.addWidget(QLabel("Buscar:"))
        filtro_layout.addWidget(self.search_input)
        filtro_layout.addWidget(QLabel("Módulo:"))
        filtro_layout.addWidget(self.modulo_combo)

        self.layout.addLayout(filtro_layout)

        # ---------------- TABLA ----------------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Tipo", "Módulo", "Acciones"])

        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)

        self.layout.addWidget(self.tabla)

        # 🔥 CONFIGURACIÓN PROFESIONAL DE COLUMNAS
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)

        self.tabla.setColumnWidth(3, 260)  # ancho real para botones

        self.tabla.verticalHeader().setDefaultSectionSize(48)
        # ---------------- BOTÓN SUBIR ----------------
        btn_layout = QHBoxLayout()

        self.btn_subir = QPushButton("Subir documento")
        self.btn_subir.setObjectName("subir")
        self.btn_subir.setCursor(Qt.PointingHandCursor)
        self.btn_subir.clicked.connect(self.subir_documento)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_subir)

        self.layout.addLayout(btn_layout)

        self.cargar_documentos()

    # ---------------------------------------------------
    # CARGAR DOCUMENTOS
    # ---------------------------------------------------
    def cargar_documentos(self):
        nombre = self.search_input.text()
        modulo = self.modulo_combo.currentData()

        documentos = self.service.listar_documentos(nombre, modulo, self.rol)

        self.tabla.setRowCount(0)

        for doc in documentos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            self.tabla.setItem(row, 0, QTableWidgetItem(doc["nombre"]))
            self.tabla.setItem(row, 1, QTableWidgetItem(doc["tipo"]))
            self.tabla.setItem(row, 2, QTableWidgetItem(doc["modulo"]))

            # ----- CONTENEDOR DE BOTONES -----
            acciones = QWidget()
            acciones.setMinimumWidth(240)

            layout = QHBoxLayout(acciones)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(10)
            layout.setAlignment(Qt.AlignCenter)

            # ----- DESCARGAR -----
            btn_descargar = QPushButton("Descargar")
            btn_descargar.setObjectName("descargar")
            btn_descargar.setCursor(Qt.PointingHandCursor)
            btn_descargar.clicked.connect(
                lambda checked, d=doc: self.descargar_documento(d)
            )
            layout.addWidget(btn_descargar)

            # ----- ELIMINAR (solo admin) -----
            if self.rol in ("admin", "superusuario"):
                btn_eliminar = QPushButton("Eliminar")
                btn_eliminar.setObjectName("eliminar")
                btn_eliminar.setCursor(Qt.PointingHandCursor)
                btn_eliminar.clicked.connect(
                    lambda checked, d=doc: self.eliminar_documento(d)
                )
                layout.addWidget(btn_eliminar)

            self.tabla.setCellWidget(row, 3, acciones)

    # ---------------------------------------------------
    # SUBIR DOCUMENTO
    # ---------------------------------------------------
    def subir_documento(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo",
            "",
            "PDF (*.pdf);;Excel (*.xlsx *.xls);;Imagen (*.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        modulos = ["ventas", "arriendos", "propiedades", "rrhh", "finanzas"]

        modulo, ok = QInputDialog.getItem(
            self,
            "Seleccionar módulo",
            "Asignar documento a:",
            modulos,
            0,
            False
        )

        if not ok or not modulo:
            return

        try:
            self.service.subir_documento(
                file_path=file_path,
                modulo=modulo
            )

            QMessageBox.information(
                self,
                "Documento subido",
                "El documento se subió correctamente."
            )

            self.cargar_documentos()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo subir el documento.\n\n{str(e)}"
            )


    # ---------------------------------------------------
    # DESCARGAR
    # ---------------------------------------------------
    def descargar_documento(self, doc):
        try:
            self.service.descargar_documento(doc["ruta"], doc["nombre"])

            QMessageBox.information(
                self,
                "Descarga completa",
                f"El documento '{doc['nombre']}' se descargó correctamente."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo descargar el documento.\n\n{str(e)}"
            )


    # ---------------------------------------------------
    # ELIMINAR
    # ---------------------------------------------------
    def eliminar_documento(self, doc):
        confirm = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar el documento:\n\n{doc['nombre']}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            self.service.eliminar_documento(doc, self.rol)

            QMessageBox.information(
                self,
                "Documento eliminado",
                "El documento fue eliminado correctamente."
            )

            self.cargar_documentos()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo eliminar el documento.\n\n{str(e)}"
            )
