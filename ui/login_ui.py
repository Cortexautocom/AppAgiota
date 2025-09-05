from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QLabel,
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from supabase_utils import validar_login

class LoginWindow(QWidget):
    def __init__(self, on_login_success, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - O Agiota")
        self.setFixedSize(350, 250)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        self.on_login_success = on_login_success

        # Layout principal
        layout = QVBoxLayout(self)

        # Painel estilizado
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #2c3446;
                border-radius: 14px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 130))
        panel.setGraphicsEffect(shadow)

        inner_layout = QVBoxLayout(panel)

        # Email
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email")
        self.input_email.setStyleSheet("padding:8px; border-radius:6px; background:#1c2331; color:white;")
        inner_layout.addWidget(QLabel("Email:"))
        inner_layout.addWidget(self.input_email)

        # Senha
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Senha")
        self.input_senha.setEchoMode(QLineEdit.Password)
        self.input_senha.setStyleSheet("padding:8px; border-radius:6px; background:#1c2331; color:white;")
        inner_layout.addWidget(QLabel("Senha:"))
        inner_layout.addWidget(self.input_senha)

        # Botão login
        btn_login = QPushButton("Entrar")
        btn_login.setStyleSheet("""
            QPushButton {
                background-color:#27ae60; color:white;
                padding:10px; border-radius:6px; font-weight:bold;
            }
            QPushButton:hover { background-color:#2ecc71; }
        """)
        btn_login.clicked.connect(self.tentar_login)
        inner_layout.addWidget(btn_login)

        link_reset = QPushButton("Esqueci a senha")
        link_reset.setStyleSheet("""
            QPushButton {
                background: none; color: #3498db;
                text-decoration: underline; border: none;
                font-size: 12px;
            }
            QPushButton:hover { color: #2980b9; }
        """)
        link_reset.clicked.connect(self.abrir_reset)
        inner_layout.addWidget(link_reset, alignment=Qt.AlignCenter)

        layout.addWidget(panel)

    def tentar_login(self):
        email = self.input_email.text().strip()
        senha = self.input_senha.text().strip()

        if not email or not senha:
            QMessageBox.warning(self, "Erro", "Digite email e senha.")
            return

        usuario = validar_login(email, senha)
        if usuario:
            QMessageBox.information(self, "Sucesso", f"Bem-vindo, {usuario['email']}!")
            self.on_login_success(usuario)  # passa usuário autenticado
            self.close()
        else:
            QMessageBox.critical(self, "Erro", "Email ou senha incorretos.")


    def abrir_reset(self):
        from ui.reset_password_ui import ResetPasswordWindow
        self.reset_window = ResetPasswordWindow(self)
        self.reset_window.show()


