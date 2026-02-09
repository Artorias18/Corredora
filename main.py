import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from gui.login_window import LoginWindow
from gui.menu import MenuWindow
from utils.session_storage import SessionStorage
from services.supabase_client import supabase
from datetime import datetime
from utils.file_utils import resource_path


class AppStarter:
    def start(self):
        session = SessionStorage.load_session()

        if not session:
            self.open_login()
            return

        expires_at = session.get("expires_at", 0)
        if datetime.utcnow().timestamp() > expires_at:
            SessionStorage.clear_session()
            self.open_login()
            return

        if "access_token" in session and "refresh_token" in session:
            supabase.auth.set_session(
                session["access_token"],
                session["refresh_token"]
            )
        else:
            self.open_login()
            return

        user_id = session.get("user_id")
        rol = session.get("rol", "usuario")

        if not user_id:
            self.open_login()
            return

        self.open_menu(user_id, rol)



    def open_login(self):
        self.login = LoginWindow()
        self.login.show()

    def open_menu(self, user_id, rol):
        self.menu = MenuWindow(user_id, rol)
        self.menu.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # === Tema global ===
    qss_path = resource_path("styles/theme.qss")
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    # === Ícono global ===
    icon_path = resource_path("assets/logo.png")
    app.setWindowIcon(QIcon(icon_path))

    # === Iniciar app ===
    starter = AppStarter()
    starter.start()

    sys.exit(app.exec())
