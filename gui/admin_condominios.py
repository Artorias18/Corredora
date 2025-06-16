from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DashboardAdminCondominios(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dashboard de Administracion de condominios"))
        self.setLayout(layout)