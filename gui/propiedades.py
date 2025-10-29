from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class PropiedadesMain(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Módulo de Propiedades"))
        self.setLayout(layout)
