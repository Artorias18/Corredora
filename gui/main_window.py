from PySide6.QtWidgets import QMainWindow, QLabel, QTabWidget
from PySide6.QtCore import Qt
from gui import ventas, arriendos, rrhh, finanzas, gestion_usuarios, admin_condominios

class MainWindow(QMainWindow):
    def __init__(self, rol):
        super().__init__()
        self.setWindowTitle("Panel Principal")

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.showMaximized()
        self.tabs.addTab(ventas.DashboardVentas(rol), "Ventas")
        self.tabs.addTab(finanzas.DashboardFinanzas(), "Finanzas")
        self.tabs.addTab(rrhh.DashboardRRHH(), "RRHH")
        self.tabs.addTab(arriendos.DashboardArriendos(), "Arriendos")
        self.tabs.addTab(admin_condominios.DashboardAdminCondominios(), "Propiedades")

        if rol == "superusuario":
            self.tabs.addTab(gestion_usuarios.DashboardUsuarios(), "Gestión de Usuarios")
        elif rol == "admin":
            pass  # mismo acceso que superusuario, sin gestión de usuarios
        elif rol == "usuario":
            # aquí podrías ocultar o restringir algunos módulos
            self.tabs.clear()  # ejemplo: quitar todo y mostrar solo uno
            self.tabs.addTab(ventas.DashboardVentas(rol), "Ventas")