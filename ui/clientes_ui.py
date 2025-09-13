from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QDialog, QGridLayout, QHBoxLayout, QToolButton,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import re



class ClientForm(QWidget):
    """
    Formulário de cliente.
    Campos: Nome, CPF, Endereço, Cidade, Telefone, Indicação.
    Pode ser usado para criar ou editar (se data inicial for passada).
    """
    def __init__(self, parent_callback, initial_data=None, cities=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Cliente")
        self.setFixedSize(340, 420)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        self.parent_callback = parent_callback

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("ClientFormPanel")
        panel.setStyleSheet("""
            QFrame#ClientFormPanel {
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
        campos = ["Nome", "CPF", "Endereço", "Cidade", "Telefone", "Indicação"]

        for label_text in campos:
            lbl = QLabel(label_text)

            if label_text == "Cidade":
                cb = QComboBox()
                cb.setEditable(True)  # permite digitar cidade nova
                cb.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")
                cb.setInsertPolicy(QComboBox.NoInsert)  # evita duplicar item automaticamente

                for city in (cities or []):
                    cb.addItem(city)

                layout.addWidget(lbl)
                layout.addWidget(cb)
                self.inputs[label_text] = cb
            else:
                inp = QLineEdit()
                inp.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")

                if label_text == "CPF":
                    inp.setInputMask("000.000.000-00;_")
                if label_text == "Telefone":
                    inp.setInputMask("(00) 00000-0000;_")

                layout.addWidget(lbl)
                layout.addWidget(inp)
                self.inputs[label_text] = inp

        # Preenche dados iniciais (edição)
        if initial_data:
            for k, w in self.inputs.items():
                val = initial_data.get(k, "")
                if isinstance(w, QComboBox):
                    idx = w.findText(val)
                    if idx < 0 and val:
                        w.addItem(val)
                        idx = w.findText(val)
                    w.setCurrentIndex(max(0, idx))
                else:
                    w.setText(val)

        # Botão salvar
        btn_save = QPushButton("Salvar")
        btn_save.setFixedSize(150, 30)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 8px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_save.clicked.connect(self.save_client)
        
        # Espaço flexível acima do botão
        layout.addStretch()        
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)  # 🔹 20 pixels de espaço acima
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Espaço flexível abaixo do botão
        layout.addStretch()

        #layout.addWidget(btn_save)

    def save_client(self):
        data = {}
        for k, w in self.inputs.items():
            if isinstance(w, QComboBox):
                data[k] = w.currentText().strip()
            else:
                data[k] = w.text().strip()

        cpf_digits = re.sub(r"\D", "", data.get("CPF", ""))
        if len(cpf_digits) != 11:
            QMessageBox.warning(self, "Presta atenção, infiliz!", "Tu já viu CPF com menos de 11 números?.")
            return

        self.parent_callback(data)  # Isso já vai chamar o salvamento no SQLite no ModernWindow
        self.close()



class DetailDialog(QDialog):
    """Janela pequena com os dados do cliente e botão para editar."""
    def __init__(self, client_data, on_edit):
        super().__init__()
        self.setWindowTitle("Detalhes do Cliente")
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.setFixedSize(360, 260)

        self.client_data = client_data
        self.on_edit = on_edit

        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Painel
        panel = QFrame()
        panel.setObjectName("DetailPanel")
        panel.setStyleSheet("""
            QFrame#DetailPanel {
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

        # Grade com as informações
        grid = QGridLayout()
        labels = ["Nome", "CPF", "Endereço", "Cidade", "Telefone", "Indicação"]

        for row, field in enumerate(labels):
            k = QLabel(f"{field}:")
            k.setStyleSheet("color:#9fb0c7;")

            v = QLabel(client_data.get(field, ""))
            v.setStyleSheet("color:white;")

            grid.addWidget(k, row, 0, alignment=Qt.AlignRight)
            grid.addWidget(v, row, 1)

        layout.addLayout(grid)

        # Botões
        buttons = QHBoxLayout()
        buttons.addStretch()

        edit_btn = QToolButton()
        edit_btn.setText("🖉 Editar")
        edit_btn.setStyleSheet("""
            QToolButton {
                background-color:#374157; color:white;
                padding:8px 12px; border-radius:8px;
            }
            QToolButton:hover { background-color:#3f4963; }
        """)
        edit_btn.clicked.connect(self.handle_edit)
        buttons.addWidget(edit_btn)

        close_btn = QPushButton("Fechar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color:#34495e; color:white;
                padding:8px 12px; border-radius:8px;
            }
            QPushButton:hover { background-color:#2c3e50; }
        """)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)

        layout.addLayout(buttons)

    def handle_edit(self):
        """Chama o callback para abrir o form de edição."""
        self.on_edit(self.client_data)
        self.accept()
