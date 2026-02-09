from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtGui import QGuiApplication
from services.supabase_client import supabase
from gui.usuario_actual import UsuarioActual
from utils.session_storage import SessionStorage


class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.setFixedSize(400, 300)
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
            session = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })

            if session:
                # Obtener user_id
                user_id = session.user.id

                # Obtener rol desde DB
                rol = self.get_user_role(user_id)

                # Guardar sesión encriptada
                SessionStorage.save_session({
                    "user_id": user_id,
                    "access_token": session.session.access_token,
                    "refresh_token": session.session.refresh_token,
                    "expires_in": session.session.expires_in,
                    "rol": rol
                })

                self.message_label.setText("Usuario autenticado correctamente")
                self.redirect_to_main(user_id, rol)

            else:
                self.message_label.setText("Error de autenticación")

        except Exception as e:
            self.message_label.setText(f"Error: {str(e)}")

    def get_user_role(self, user_id):
        response = supabase.table('usuarios').select('rol').eq('id', user_id).execute()

        if response.data:
            rol = response.data[0]['rol']
            UsuarioActual.id = user_id
            UsuarioActual.rol = rol
            return rol
        else:
            self.message_label.setText("Usuario no encontrado en la base de datos")
            return "usuario"
        
    def redirect_to_main(self, user_id, rol):
        from gui.menu import MenuWindow
        try:
            self.main = MenuWindow(user_id, rol)
            self.main.show()
            self.close()
        except Exception as e:
            self.message_label.setText("Error al abrir el dashboard.")
            
    def center_window(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
