from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QLineEdit, QLabel, QComboBox, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt
from services.documentos_service import DocumentosService

import os
import re


def normalizar_nombre(nombre):
    nombre = nombre.lower()
    nombre = re.sub(r"\s+", "_", nombre)
    nombre = re.sub(r"[^a-z0-9._-]", "", nombre)
    return nombre

class DocumentosWindow(QWidget):
    def __init__(self, rol):
        super().__init__()
        self.setWindowTitle("Documentos")
        self.resize(900, 600)

        self.rol = rol
        self.service = DocumentosService()

        self.layout = QVBoxLayout(self)

        # --- Filtros ---
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

        # --- Tabla ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Tipo", "Módulo", "Acciones"])
        self.layout.addWidget(self.tabla)

        # --- Botón subir ---
        btn_layout = QHBoxLayout()
        self.btn_subir = QPushButton("Subir documento")
        self.btn_subir.clicked.connect(self.subir_documento)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_subir)
        self.layout.addLayout(btn_layout)

        self.cargar_documentos()

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

            # --- Botones de acción ---
            btn_descargar = QPushButton("Descargar")
            btn_descargar.clicked.connect(
                lambda checked, d=doc: self.descargar_documento(d)
            )

            acciones = QWidget()
            layout = QHBoxLayout(acciones)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(btn_descargar)

            # 🔴 Botón eliminar SOLO para admin / superusuario
            if self.rol in ("admin", "superusuario"):
                btn_eliminar = QPushButton("Eliminar")
                btn_eliminar.setStyleSheet("color: red;")
                btn_eliminar.clicked.connect(
                    lambda checked, d=doc: self.eliminar_documento(d)
                )
                layout.addWidget(btn_eliminar)

            self.tabla.setCellWidget(row, 3, acciones)

        self.tabla.resizeColumnsToContents()

    def subir_documento(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo",
            "",
            "PDF (*.pdf);;Excel (*.xlsx *.xls);;Imagen (*.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        # Elegir módulo
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
        
        self.service.subir_documento(
            file_path=file_path,
            modulo=modulo
        )

        self.cargar_documentos()


   
    def descargar_documento(self, doc):
        self.service.descargar_documento(doc["ruta"], doc["nombre"])

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
            self.cargar_documentos()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
