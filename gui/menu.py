from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton


class MenuWindow(QWidget):
    def __init__(self, user_id, rol, start_tab=0):
        super().__init__()
        self.user_id = user_id
        self.rol = rol
        self.setWindowTitle("Selecciona módulo")
        self.setFixedSize(300, 400)

        layout = QVBoxLayout()

        self.btn_ventas = QPushButton("Ventas")
        self.btn_arriendos = QPushButton("Arriendos")
        self.btn_rrhh = QPushButton("RRHH")
        self.btn_finanzas = QPushButton("Finanzas")
        self.btn_gest_usuarios = QPushButton("Gestión de usuarios")

        layout.addWidget(self.btn_ventas)
        layout.addWidget(self.btn_arriendos)
        layout.addWidget(self.btn_rrhh)
        layout.addWidget(self.btn_finanzas)
        layout.addWidget(self.btn_gest_usuarios)

        self.setLayout(layout)

        # Conexiones
        self.btn_ventas.clicked.connect(lambda: self.open_main(0))
        self.btn_arriendos.clicked.connect(lambda: self.open_main(1))
        self.btn_rrhh.clicked.connect(lambda: self.open_main(2))
        self.btn_finanzas.clicked.connect(lambda: self.open_main(3))
        self.btn_gest_usuarios.clicked.connect(lambda: self.open_main(4))


        if rol == "usuario":
            self.btn_rrhh.hide()
            self.btn_finanzas.hide()
            


    def open_main(self, index):
        from gui.main_window import MainWindow

        self.main_window = MainWindow(self.user_id, self.rol, index)
        self.main_window.show()
        self.close()