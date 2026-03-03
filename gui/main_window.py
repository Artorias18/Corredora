from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from gui import ventas, arriendos, rrhh, finanzas, gestion_usuarios, propiedades, sesion_usuario, eva_arrendatario


class MainWindow(QMainWindow):
    def __init__(self, user_id, rol, start_tab=0):
        super().__init__()
        self.user_id = user_id
        self.rol = rol

        self.setWindowTitle("Panel Principal")
        self.showMaximized()

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # ─── Placeholders (QWidget, NO QLabel) ──────────────
        self.placeholders = []
        for _ in range(5):
            w = QWidget()
            w.setLayout(QVBoxLayout())
            w.layout().setContentsMargins(0, 0, 0, 0)
            self.placeholders.append(w)

        self.tabs.addTab(self.placeholders[0], "Ventas")
        self.tabs.addTab(self.placeholders[1], "Arriendos")
        self.tabs.addTab(self.placeholders[2], "Evaluaciones")
        self.tabs.addTab(self.placeholders[3], "RRHH")
        self.tabs.addTab(self.placeholders[4], "Finanzas")

        # ─── Lazy map ──────────────────────────────────────
        self.tab_map = {
            0: lambda: ventas.DashboardVentas(self.rol),
            1: lambda: arriendos.DashboardArriendos(),
            2: lambda: eva_arrendatario.DashboardEvaluaciones(),
            3: lambda: rrhh.DashboardRRHH(self.user_id),
            4: lambda: finanzas.DashboardFinanzas(),
        }

        self.loaded_tabs = set()

        # ─── Gestión por rol ───────────────────────────────
        if self.rol == "superusuario":
            w = QWidget()
            w.setLayout(QVBoxLayout())
            self.tabs.addTab(w, "Gestión de Usuarios")
            idx = self.tabs.count() - 1
            self.tab_map[idx] = lambda: gestion_usuarios.DashboardUsuarios(self.user_id)

        elif self.rol == "usuario":
            # ocultar módulos
            self.tabs.setTabVisible(2, False)  # Propiedades
            self.tabs.setTabVisible(3, False)  # RRHH
            self.tabs.setTabVisible(4, False)  # Finanzas

            # módulo sesión
            w = QWidget()
            w.setLayout(QVBoxLayout())
            self.tabs.addTab(w, "Mi sesión")
            idx = self.tabs.count() - 1
            self.tab_map[idx] = lambda: sesion_usuario.ModuloSesion()

        # ─── Señales ───────────────────────────────────────
        self.tabs.currentChanged.connect(self.cargar_tab)

        self.tabs.setCurrentIndex(start_tab)
        self.cargar_tab(start_tab)

    def cargar_tab(self, index):
        if index in self.loaded_tabs:
            return
        if index not in self.tab_map:
            return

        container = self.tabs.widget(index)
        widget = self.tab_map[index]()
        container.layout().addWidget(widget)

        if hasattr(widget, "logout_signal"):
            widget.logout_signal.connect(self.handle_logout)

        self.loaded_tabs.add(index)

    def handle_logout(self):
        from gui.login_window import LoginWindow
        from utils.session_storage import SessionStorage

        SessionStorage.clear_session()
        self.close()
        self.login = LoginWindow()
        self.login.show()
