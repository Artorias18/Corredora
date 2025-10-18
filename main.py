import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from gui.login_window import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # === Cargar tema global ===
    theme_path = os.path.join(os.path.dirname(__file__), "styles", "theme.qss")
    with open(theme_path, "r") as f:
        app.setStyleSheet(f.read())

    # === Establecer el ícono global ===
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")  # o logo.ico
    app.setWindowIcon(QIcon(icon_path))

    # === Crear y mostrar la ventana ===
    window = LoginWindow()
    window.show()

    sys.exit(app.exec())
