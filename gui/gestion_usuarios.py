from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QMessageBox, QDialog, QLineEdit, QComboBox, QLabel, QFormLayout, QInputDialog
)
from services.supabase_client import supabase, supabase_admin
from PySide6.QtCore import Qt
from utils.session_storage import SessionStorage
from PySide6.QtCore import Signal
from gui.diagnostico import DiagnosticoWindow
from gui.usuario_actual import UsuarioActual


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

        self.btn_ok = DoubleClickButton("Guardar")
        self.btn_ok.doubleClicked.connect(self.accept)
        lay.addRow(self.btn_ok)

    def datos(self):
        return {
            "email":  self.email.text().strip(),
            "nombre": self.nombre.text().strip(),
            "rol":    self.rol.currentText()
        }

class DashboardUsuarios(QWidget):
    logout_signal = Signal()
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Gestión de usuarios")
        self.resize(600, 400)

        vbox = QVBoxLayout(self)
        # tabla
        self.tabla = QTableWidget(0, 4, self)
        self.tabla.setHorizontalHeaderLabels(["ID", "Email", "Nombre", "Rol"])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        vbox.addWidget(self.tabla)

        # botones
        hbox = QHBoxLayout()
        self.btn_nuevo   = DoubleClickButton("Nuevo")
        self.btn_editar  = DoubleClickButton("Editar")
        self.btn_borrar  = DoubleClickButton("Eliminar")
        self.btn_logout  = DoubleClickButton("Cerrar sesión")   # <-- BOTÓN
        self.btn_diagnostico = DoubleClickButton("Diagnóstico")
        


        hbox.addWidget(self.btn_nuevo)
        hbox.addWidget(self.btn_editar)
        hbox.addWidget(self.btn_borrar)
        hbox.addWidget(self.btn_logout)                    # <-- BOTÓN
        hbox.addWidget(self.btn_diagnostico)

        vbox.addLayout(hbox)

        # señales
        self.btn_nuevo.doubleClicked.connect(self.alta)
        self.btn_editar.doubleClicked.connect(self.editar)
        self.btn_borrar.doubleClicked.connect(self.borrar)
        self.btn_logout.doubleClicked.connect(self.logout)       # <-- SEÑAL
        self.btn_diagnostico.doubleClicked.connect(self.open_diagnostico)
        self.cargar_datos()

    # ----- CRUD -----

    def setup_menu(self):
        # ... tu código actual
        if UsuarioActual.rol in ["admin", "superusuario"]:
            self.btn_diagnostico = DoubleClickButton("Diagnóstico")
            self.btn_diagnostico.doubleClicked.connect(self.open_diagnostico)
            self.layout.addWidget(self.btn_diagnostico)

    def get_user_role(self,user_id):

        response = supabase.table('usuarios').select('rol').eq('id',user_id).execute()

        if response.data:
            rol = response.data[0]['rol']
            UsuarioActual.id = user_id
            UsuarioActual.rol = rol
            self.message_label.setText(f"Rol: {rol}")
            self.redirect_to_dashboard(rol)
        else:
            self.message_label.setText("Usuario no encontrado en la base de datos")

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


    

    def open_diagnostico(self):
        self.diagnostico = DiagnosticoWindow(self.user_id)
        self.diagnostico.show()

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
        if not ok or not pwd:
            return

        try:
            auth = supabase_admin.auth.admin.create_user({
                "email": datos["email"],
                "password": pwd,
                "email_confirm": True
            })
            uid = auth.user.id

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
            supabase_admin.table("usuarios").update(datos).eq("id", usr["id"]).execute()
            self.cargar_datos()

    def borrar(self):
        usr = self.fila_sel()
        if not usr:
            return
        if QMessageBox.question(self, "Confirmar",
                                f"¿Eliminar usuario {usr['email']}?") == QMessageBox.Yes:
            supabase.table("usuarios").delete().eq("id", usr["id"]).execute()
            supabase_admin.auth.admin.delete_user(usr["id"])
            self.cargar_datos()

    # -------------------------------
    #   CERRAR SESIÓN
    # -------------------------------

    def logout(self):
        SessionStorage.clear_session()
        self.logout_signal.emit()



class DoubleClickButton(QPushButton):
    doubleClicked = Signal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()


        
    