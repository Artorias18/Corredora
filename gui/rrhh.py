from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DashboardRRHH(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dashboard de Recursos humanos"))
        self.setLayout(layout)