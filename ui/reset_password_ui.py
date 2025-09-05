from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from supabase_utils import criar_usuario  # depois adaptaremos para update de senha

class ResetPasswordWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Redefinir Senha")
        self.setFixedSize(350, 220)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        layout = QVBoxLayout(self)

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

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Digite seu email")
        self.input_email.setStyleSheet("padding:8px; border-radius:6px; background:#1c2331; color:white;")
        inner_layout.addWidget(QLabel("Email cadastrado:"))
        inner_layout.addWidget(self.input_email)

        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Nova senha")
        self.input_senha.setEchoMode(QLineEdit.Password)
        self.input_senha.setStyleSheet("padding:8px; border-radius:6px; background:#1c2331; color:white;")
        inner_layout.addWidget(QLabel("Nova senha:"))
        inner_layout.addWidget(self.input_senha)

        btn_reset = QPushButton("Redefinir")
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color:#3498db; color:white;
                padding:10px; border-radius:6px; font-weight:bold;
            }
            QPushButton:hover { background-color:#2980b9; }
        """)
        btn_reset.clicked.connect(self.resetar_senha)
        inner_layout.addWidget(btn_reset)

        layout.addWidget(panel)

    def resetar_senha(self):
        email = self.input_email.text().strip()
        senha = self.input_senha.text().strip()

        if not email or not senha:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos.")
            return

        from supabase_utils import redefinir_senha
        ok = redefinir_senha(email, senha)
        if ok:
            QMessageBox.information(self, "Sucesso", "Senha redefinida com sucesso.")
            self.close()
        else:
            QMessageBox.critical(self, "Erro", "Não foi possível redefinir a senha.")
