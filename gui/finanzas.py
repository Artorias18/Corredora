from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DashboardFinanzas(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dashboard de Finanzas"))
        self.setLayout(layout)