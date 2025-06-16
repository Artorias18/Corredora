from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DashboardArriendos(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dashboard de Arriendos"))
        self.setLayout(layout)