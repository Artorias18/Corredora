from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel
)
from services.supabase_client import supabase
from gui.usuario_actual import UsuarioActual
from services.get_user_role import get_user_role

class DiagnosticoWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.rol = get_user_role(user_id)
        self.setWindowTitle("Diagnóstico Supabase")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        btn_layout = QHBoxLayout()
        self.btn_check = QPushButton("Ejecutar diagnóstico")
        self.btn_check.clicked.connect(self.run_diagnostico)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_check)

        layout.addWidget(QLabel("Registro de diagnóstico:"))
        layout.addWidget(self.log)
        layout.addLayout(btn_layout)

    def log_text(self, text):
        self.log.append(text)

    def run_diagnostico(self):
        self.log.clear()

        self.log_text(f"Rol detectado: {self.rol}")

        if self.rol not in ["admin", "superusuario"]:
            self.log_text("Acceso denegado. Solo administradores pueden usar esta herramienta.")
            return

        # 1️⃣ Sesión actual
        session = supabase.auth.get_session()
        if not session:
            self.log_text("❌ No hay sesión activa")
            return

        self.log_text("✅ Sesión activa")

        # 2️⃣ Usuario logueado
        user = session.user
        self.log_text(f"Usuario ID: {user.id}")
        self.log_text(f"Email: {user.email}")

        # 3️⃣ Listar archivos en bucket
        try:
            res = supabase.storage.from_("documentos").list()
            self.log_text(f"📁 Bucket OK: {len(res)} archivos")
        except Exception as e:
            self.log_text(f"❌ Error listando bucket: {e}")
            return

        # 4️⃣ Probar signed URL
        try:
            if res:
                ruta = res[0]["name"]
                supabase.storage.from_("documentos").create_signed_url(ruta, 3600)
                self.log_text("🔑 Signed URL generada correctamente")
            else:
                self.log_text("ℹ️ Bucket vacío")
        except Exception as e:
            self.log_text(f"❌ Error Signed URL: {e}")
