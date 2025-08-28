from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton, QMessageBox, QGraphicsDropShadowEffect,
    QTextEdit, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class GarantiaForm(QWidget):
    """Formulário simples para cadastrar garantia."""
    def __init__(self, parent_callback, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Nova Garantia")
        self.setFixedSize(350, 350)  # aumentei altura pra caber a descrição + valor + espaçamento
        self.setStyleSheet("background-color: #1c2331; color: white;")

        self.parent_callback = parent_callback

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("GarantiaFormPanel")
        panel.setStyleSheet("""
            QFrame#GarantiaFormPanel {
                background-color: #1c2331;
                border-radius: 14px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 130))
        panel.setGraphicsEffect(shadow)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        outer.addWidget(panel)

        # Campo Descrição (multi-linha, com limite de 500 caracteres)
        self.inp_desc = QTextEdit()
        self.inp_desc.setPlaceholderText("Descrição e detalhes (máx. 500 caracteres)")
        self.inp_desc.setFixedHeight(200)
        self.inp_desc.setStyleSheet("""
            QTextEdit {
                background-color: #2c3446; 
                color: white; 
                padding: 6px; 
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        self.desc_limit = 500

        layout.addWidget(QLabel("Descrição"))
        layout.addWidget(self.inp_desc)

        # Campo Valor
        self.inp_valor = QLineEdit()
        self.inp_valor.setPlaceholderText("Valor da garantia (R$ 0,00)")
        self.inp_valor.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")
        layout.addWidget(QLabel("Valor"))
        layout.addWidget(self.inp_valor)

        # Espaço entre valor e botão
        layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Botão salvar
        btn_save = QPushButton("Salvar Garantia")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 10px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_save.clicked.connect(self.save_garantia)
        layout.addWidget(btn_save)

    def save_garantia(self):
        """Valida e retorna os dados da garantia."""
        desc = self.inp_desc.toPlainText().strip()
        valor = self.inp_valor.text().strip()

        # Valida descrição
        if not desc or not valor:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return
        if len(desc) > self.desc_limit:
            QMessageBox.warning(self, "Erro", f"A descrição não pode ter mais que {self.desc_limit} caracteres.")
            return

        # Valida e formata valor
        try:
            num = float(valor.replace("R$", "").replace(".", "").replace(",", ".").strip())
            valor_fmt = f"R$ {num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except ValueError:
            QMessageBox.warning(self, "Erro", "Digite um valor válido no formato R$ 999.999,99")
            return

        # Retorna pro FinanceiroWindow
        self.parent_callback({"descricao": desc, "valor": valor_fmt})
        self.close()
