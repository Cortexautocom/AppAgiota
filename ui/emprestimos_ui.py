from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QComboBox, QMessageBox
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect


class EmprestimoForm(QWidget):
    """
    Formulário de empréstimo.
    Campos: Data inicial, Valor total, Valor capital, Juros, Quantidade de parcelas.
    """
    def __init__(self, parent_callback, initial_data=None):
        super().__init__()
        self.setWindowTitle("Empréstimo")
        self.setFixedSize(340, 420)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        self.parent_callback = parent_callback

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("EmprestimoFormPanel")
        panel.setStyleSheet("""
            QFrame#EmprestimoFormPanel {
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

        self.inputs = {}
        campos = ["Data inicial", "Valor total", "Valor capital", "Juros (%)", "Parcelas"]

        for label_text in campos:
            lbl = QLabel(label_text)
            inp = QLineEdit()
            inp.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")
            layout.addWidget(lbl)
            layout.addWidget(inp)
            self.inputs[label_text] = inp

        # Preenche dados iniciais (edição)
        if initial_data:
            for k, w in self.inputs.items():
                w.setText(initial_data.get(k, ""))

        # Botão salvar
        btn_save = QPushButton("Salvar")
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 10px; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_save.clicked.connect(self.save_emprestimo)
        layout.addWidget(btn_save)

    def save_emprestimo(self):
        data = {}
        for k, w in self.inputs.items():
            data[k] = w.text().strip()

        if not data["Valor total"]:
            QMessageBox.warning(self, "Atenção", "O valor total é obrigatório.")
            return

        self.parent_callback(data)  # Isso vai chamar a função que salva no banco
        self.close()
