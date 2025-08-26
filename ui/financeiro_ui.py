from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

# Importa função para carregar empréstimos reais
from emprestimos import carregar_emprestimos
from parcelas import carregar_parcelas_por_emprestimo


class FinanceiroWindow(QWidget):
    """
    Tela financeira de um cliente.
    Contém menu lateral (Empréstimos, Garantias) e área de conteúdo.
    """
    def __init__(self, client_data, parent=None):
        super().__init__(parent)

        # 🔹 Define como janela independente, com X e minimizar
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setWindowModality(Qt.NonModal)  # não bloqueia a janela mãe

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

        # 🔹 Abre já na aba Empréstimos
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
        btn_novo.setFixedSize(160, 32)
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

        # 🔹 Carregar empréstimos reais do cliente
        todos_emprestimos = carregar_emprestimos()
        emprestimos_cliente = [e for e in todos_emprestimos if e[1] == self.client_data[0]]

        for linha, emp in enumerate(emprestimos_cliente):
            tabela.insertRow(linha)

            # emp = (id, id_cliente, valor, data_inicio, parcelas, observacao)

            # Data
            item_data = QTableWidgetItem(emp[3] or "")
            item_data.setFlags(item_data.flags() & ~Qt.ItemIsEditable)
            tabela.setItem(linha, 0, item_data)

            # Valor
            item_valor = QTableWidgetItem(emp[2] or "")
            item_valor.setFlags(item_valor.flags() & ~Qt.ItemIsEditable)
            tabela.setItem(linha, 1, item_valor)

            # Status (placeholder: em breve vamos calcular pelas parcelas)
            status = "Em andamento"
            item_status = QTableWidgetItem(status)
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)
            item_status.setForeground(Qt.yellow)
            tabela.setItem(linha, 2, item_status)

        # 🔹 Conectar duplo clique para abrir parcelas
        tabela.cellDoubleClicked.connect(lambda row, col: self.abrir_parcelas(row))
        self.tabela_emprestimos = tabela

        container.addWidget(tabela)
        self._set_content(frame)


    def abrir_parcelas(self, row):
        """Abre a janela de parcelas do empréstimo selecionado."""
        emprestimo_id = self.tabela_emprestimos.item(row, 0).text()
        parcelas = carregar_parcelas_por_emprestimo(emprestimo_id)

        from ui.parcelas_ui import ParcelasWindow
        self.parcelas_window = ParcelasWindow(
            {"id": emprestimo_id, "parcelas": parcelas},
            parent=self,
            on_save_callback=self.show_emprestimos
        )
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
                "id": data["id"],   # ✅ agora vai o UUID correto
                "capital": data["capital"],
                "juros": data["juros"],
                "parcelas": data["parcelas"]
            })
            self.parcelas_window.show()

        self.form_emprestimo = EmprestimoForm(callback, id_cliente=self.client_data[0], parent=self)

        self.form_emprestimo.show()

    # ==============================
    def show_garantias(self):
        self.content.setText("🏦 Garantias do cliente (em breve)")
