from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt


class FinanceiroWindow(QWidget):
    """
    Tela financeira de um cliente.
    Contém menu lateral (Empréstimos, Garantias) e área de conteúdo.
    """
    def __init__(self, client_data):
        super().__init__()
        self.client_data = client_data
        self.setWindowTitle(f"Financeiro - {client_data[1]}")
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.setFixedSize(900, 600)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Menu lateral
        menu = QFrame()
        menu.setFixedWidth(200)
        menu.setStyleSheet("background-color: #252d3c;")
        menu_layout = QVBoxLayout(menu)

        self.btn_emprestimos = QPushButton("💰 Empréstimos")
        self.btn_emprestimos.setStyleSheet("""
            QPushButton {
                background: none; color: white;
                padding: 12px; text-align: left;
                font-size: 15px; border: none;
            }
            QPushButton:hover {
                background-color: #374157;
                border-radius: 5px;
            }
        """)
        self.btn_emprestimos.clicked.connect(self.show_emprestimos)
        menu_layout.addWidget(self.btn_emprestimos)

        self.btn_garantias = QPushButton("🏦 Garantias")
        self.btn_garantias.setStyleSheet("""
            QPushButton {
                background: none; color: white;
                padding: 12px; text-align: left;
                font-size: 15px; border: none;
            }
            QPushButton:hover {
                background-color: #374157;
                border-radius: 5px;
            }
        """)
        self.btn_garantias.clicked.connect(self.show_garantias)
        menu_layout.addWidget(self.btn_garantias)

        menu_layout.addStretch()
        main_layout.addWidget(menu)

        # Área de conteúdo inicial
        self.content = QLabel("Selecione uma opção no menu")
        self.content.setAlignment(Qt.AlignCenter)
        self.content.setStyleSheet("font-size: 18px; color: #9fb0c7;")
        main_layout.addWidget(self.content)

    # ==============================
    # Aba de Empréstimos
    # ==============================
    def show_emprestimos(self):
        # Container principal
        container = QVBoxLayout()
        frame = QWidget()
        frame.setLayout(container)

        # Botão "Novo Empréstimo"
        btn_novo = QPushButton("➕ Novo Empréstimo")
        btn_novo.setFixedSize(160, 32)   # menor
        btn_novo.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 4px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_novo.clicked.connect(self.open_novo_emprestimo)
        container.addWidget(btn_novo)

        # Tabela de empréstimos (placeholder)
        tabela = QTableWidget(0, 3)
        tabela.setHorizontalHeaderLabels(["Data", "Valor", "Status"])
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabela.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446; color: white;
                border: 1px solid #3a455b;
            }
            QHeaderView::section {
                background-color: #374157; color: white;
                padding: 6px; border: none;
            }
        """)

        # Exemplo de dados fictícios
        dados_fake = [
            ("01/08/2024", "R$ 1.000,00", "Quitado"),
            ("10/09/2024", "R$ 2.500,00", "Em andamento"),
            ("15/10/2024", "R$ 3.200,00", "Atrasado"),
        ]

        for linha, (data, valor, status) in enumerate(dados_fake):
            tabela.insertRow(linha)
            tabela.setItem(linha, 0, QTableWidgetItem(data))
            tabela.setItem(linha, 1, QTableWidgetItem(valor))
            item_status = QTableWidgetItem(status)

            # Destacar status em cores
            if status == "Atrasado":
                item_status.setForeground(Qt.red)
            elif status == "Quitado":
                item_status.setForeground(Qt.green)
            else:
                item_status.setForeground(Qt.yellow)

            tabela.setItem(linha, 2, item_status)

        container.addWidget(tabela)
        self._set_content(frame)

    def _set_content(self, widget):
        """Substitui o conteúdo da área central."""
        old = self.content
        self.layout().removeWidget(old)
        old.deleteLater()
        self.content = widget
        self.layout().addWidget(self.content)

    def open_novo_emprestimo(self):
        from ui.emprestimos_ui import EmprestimoForm

        def callback(data):
            print("Novo empréstimo cadastrado:", data)

        self.form_emprestimo = EmprestimoForm(callback)
        self.form_emprestimo.show()

    # ==============================
    def show_garantias(self):
        self.content.setText("🏦 Garantias do cliente (em breve)")
