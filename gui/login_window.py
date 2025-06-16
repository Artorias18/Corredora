from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtGui import QGuiApplication
from gui.main_window import MainWindow
from services.supabase_client import supabase
from gui.usuarlo_actual import UsuarioActual

class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        
        # Tamaño fijo
        self.setFixedSize(400, 300)

        # Centrar la ventana
        self.center_window()

        layout = QVBoxLayout()

        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Iniciar sesión", self)
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.message_label = QLabel(self)
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    def login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        try:
            user = supabase.auth.sign_in_with_password({
                'email':email,
                'password':password
            })

            if user:
                user_id = user.user.id
                self.message_label.setText("Usuario autenticado correctamente")
                self.get_user_role(user_id)
            else:
                self.message_label.setText("Error de autenticacion")

            
        except Exception as e:
            self.message_label.setText(f"Error: {str(e)}")

    def get_user_role(self,user_id):

        response = supabase.table('usuarios').select('rol').eq('id',user_id).execute()

        if response.data:
            rol = response.data[0]['rol']
            UsuarioActual.id = user_id
            UsuarioActual.rol = rol
            self.message_label.setText(f"Rol: {rol}")
            self.redirect_to_dashboard(rol)
        else:
            self.message_label.setText("Usuario no encontrado en la base de datos")


            
    def redirect_to_dashboard(self, rol):
        try:
          self.main_window = MainWindow(rol)
          self.main_window.show()
          self.close()
        except Exception as e:
            print("Error al abrir el dashboard:", e)
            self.message_label.setText("Error al abrir el dashboard.")

    def center_window(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)