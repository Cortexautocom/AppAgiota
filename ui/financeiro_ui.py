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
    def __init__(self, client_data, parent=None):
        super().__init__(parent)
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
        self.show_emprestimos()

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

        # Tabela de empréstimos
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

            # Data (somente leitura)
            item_data = QTableWidgetItem(data)
            item_data.setFlags(item_data.flags() & ~Qt.ItemIsEditable)
            tabela.setItem(linha, 0, item_data)

            # Valor (somente leitura)
            item_valor = QTableWidgetItem(valor)
            item_valor.setFlags(item_valor.flags() & ~Qt.ItemIsEditable)
            tabela.setItem(linha, 1, item_valor)

            # Status (somente leitura + cor)
            item_status = QTableWidgetItem(status)
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)

            if status == "Atrasado":
                item_status.setForeground(Qt.red)
            elif status == "Quitado":
                item_status.setForeground(Qt.green)
            else:
                item_status.setForeground(Qt.yellow)

            tabela.setItem(linha, 2, item_status)

        # 🔹 Conectar duplo clique para abrir parcelas
        tabela.cellDoubleClicked.connect(lambda row, col: self.abrir_parcelas(row))
        self.tabela_emprestimos = tabela

        container.addWidget(tabela)
        self._set_content(frame)


    def abrir_parcelas(self, row):
        """Abre a janela de parcelas do empréstimo selecionado."""
        # 🔹 Aqui vamos simular dados de parcelas (por enquanto fixos)
        emprestimo = {
            "id": row + 1,
            "parcelas": [
                (1, "100,00", "01/09/2024", "Não", ""),
                (2, "100,00", "01/10/2024", "Não", ""),
                (3, "100,00", "01/11/2024", "Não", ""),
            ]
        }

        from ui.parcelas_ui import ParcelasWindow
        self.parcelas_window = ParcelasWindow(emprestimo, parent=self)
        self.parcelas_window.show()

    def _set_content(self, widget):
        """Substitui o conteúdo da área central."""
        old = self.content
        self.layout().removeWidget(old)
        old.deleteLater()
        self.content = widget
        self.layout().addWidget(self.content)

    def open_novo_emprestimo(self):
        from ui.emprestimos_ui import EmprestimoForm
        from ui.parcelas_ui import ParcelasWindow

        def callback(data):
            print("Novo empréstimo cadastrado:", data)

            # Abre a tela de parcelas com os dados reais
            self.parcelas_window = ParcelasWindow({
                "id": 999,  # futuramente será ID do banco
                "capital": data["capital"],
                "juros": data["juros"],
                "parcelas": data["parcelas"]
            })
            self.parcelas_window.show()

        self.form_emprestimo = EmprestimoForm(callback, parent=self)
        self.form_emprestimo.show()

    # ==============================
    def show_garantias(self):
        self.content.setText("🏦 Garantias do cliente (em breve)")
