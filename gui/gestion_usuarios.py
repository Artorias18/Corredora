from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QMessageBox, QDialog, QLineEdit, QComboBox, QLabel, QFormLayout, QInputDialog
)
from services.supabase_client import supabase
from PySide6.QtCore import Qt


class DialogUsuario(QDialog):
    def __init__(self, usuario=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Usuario" + (" - Editar" if usuario else " - Nuevo"))
        self.resize(300, 200)

        self.usuario = usuario  # None = alta

        lay = QFormLayout(self)

        self.email   = QLineEdit(usuario["email"] if usuario else "")
        self.nombre  = QLineEdit(usuario["nombre"] if usuario else "")
        self.rol     = QComboBox()
        self.rol.addItems(["usuario", "admin", "superusuario"])
        if usuario:
            self.rol.setCurrentText(usuario["rol"])

        lay.addRow("Email:",  self.email)
        lay.addRow("Nombre:", self.nombre)
        lay.addRow("Rol:",    self.rol)

        self.btn_ok = QPushButton("Guardar")
        self.btn_ok.clicked.connect(self.accept)
        lay.addRow(self.btn_ok)

    def datos(self):
        return {
            "email":  self.email.text().strip(),
            "nombre": self.nombre.text().strip(),
            "rol":    self.rol.currentText()
        }

class DashboardUsuarios(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de usuarios")
        self.resize(600, 400)

        vbox = QVBoxLayout(self)

        # tabla
        self.tabla = QTableWidget(0, 4, self)
        self.tabla.setHorizontalHeaderLabels(["ID", "Email", "Nombre", "Rol"])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        vbox.addWidget(self.tabla)

        # botones
        hbox = QHBoxLayout()
        self.btn_nuevo   = QPushButton("Nuevo")
        self.btn_editar  = QPushButton("Editar")
        self.btn_borrar  = QPushButton("Eliminar")
        hbox.addWidget(self.btn_nuevo)
        hbox.addWidget(self.btn_editar)
        hbox.addWidget(self.btn_borrar)
        vbox.addLayout(hbox)

        # señales
        self.btn_nuevo.clicked.connect(self.alta)
        self.btn_editar.clicked.connect(self.editar)
        self.btn_borrar.clicked.connect(self.borrar)

        self.cargar_datos()

    # ----- CRUD -----

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        res = supabase.table("usuarios").select("*").order("created_at").execute()
        for usr in res.data:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            self.tabla.setItem(fila, 0, QTableWidgetItem(usr["id"]))
            self.tabla.setItem(fila, 1, QTableWidgetItem(usr["email"]))
            self.tabla.setItem(fila, 2, QTableWidgetItem(usr["nombre"]))
            self.tabla.setItem(fila, 3, QTableWidgetItem(usr["rol"]))

    def alta(self):
        dlg = DialogUsuario(parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        datos = dlg.datos()

        # ─── solicitar contraseña ─────────────────────────
        pwd, ok = QInputDialog.getText(
            self,
            "Asignar contraseña",
            "Introduce la contraseña para el nuevo usuario:",
            QLineEdit.Password
        )
        if not ok or not pwd:          # canceló o dejó vacío
            return

        try:
            # 1) crear la cuenta en Auth con esa contraseña
            auth = supabase.auth.admin.create_user({
                "email": datos["email"],
                "password": pwd,
                "email_confirm": True          # opcional: lo marca como verificado
            })
            uid = auth.user.id

            # 2) insertar fila en la tabla usuarios
            datos["id"] = uid
            supabase.table("usuarios").insert(datos).execute()

            self.cargar_datos()
            QMessageBox.information(self, "Éxito", "Usuario creado correctamente.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el usuario:\n{e}")

        def fila_sel(self):
            idx = self.tabla.currentRow()
            if idx < 0:
                QMessageBox.warning(self, "Atención", "Selecciona un usuario.")
                return None
            return {
                "id":     self.tabla.item(idx, 0).text(),
                "email":  self.tabla.item(idx, 1).text(),
                "nombre": self.tabla.item(idx, 2).text(),
                "rol":    self.tabla.item(idx, 3).text()
            }

    def editar(self):
        usr = self.fila_sel()
        if not usr:
            return
        dlg = DialogUsuario(usr, self)
        if dlg.exec() == QDialog.Accepted:
            datos = dlg.datos()
            supabase.table("usuarios").update(datos).eq("id", usr["id"]).execute()
            self.cargar_datos()

    def borrar(self):
        usr = self.fila_sel()
        if not usr:
            return
        if QMessageBox.question(self, "Confirmar",
                                f"¿Eliminar usuario {usr['email']}?") == QMessageBox.Yes:
            # Borra en tabla usuarios …
            supabase.table("usuarios").delete().eq("id", usr["id"]).execute()
            # … y en Auth (requiere service_role o RPC)
            supabase.auth.admin.delete_user(usr["id"])
            self.cargar_datos()

