from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal, Qt

class ModuloSesion(QWidget):
    logout_signal = Signal()

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        btn_logout = QPushButton("Cerrar sesión")
        btn_logout.setFixedSize(180, 40)
        btn_logout.setCursor(Qt.PointingHandCursor)

        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)

        btn_logout.clicked.connect(self.logout_signal.emit)

        layout.addWidget(btn_logout)
