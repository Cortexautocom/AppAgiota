from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtGui import QColor
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

        # Tabela de empréstimos (agora com 4 colunas: ID oculto + Data + Valor + Status)
        tabela = QTableWidget(0, 4)
        tabela.setHorizontalHeaderLabels(["ID", "Data", "Valor", "Status"])
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabela.setColumnHidden(0, True)  # 🔹 Esconde a coluna do ID
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

            # ID oculto
            item_id = QTableWidgetItem(emp[0])
            tabela.setItem(linha, 0, item_id)

            # Data
            item_data = QTableWidgetItem(emp[3] or "")
            item_data.setFlags(item_data.flags() & ~Qt.ItemIsEditable)
            tabela.setItem(linha, 1, item_data)

            # Valor
            item_valor = QTableWidgetItem(emp[2] or "")
            item_valor.setFlags(item_valor.flags() & ~Qt.ItemIsEditable)
            tabela.setItem(linha, 2, item_valor)

            # Status (placeholder: em breve vamos calcular pelas parcelas)
            status = "Em andamento"
            item_status = QTableWidgetItem(status)
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)
            item_status.setForeground(Qt.yellow)
            tabela.setItem(linha, 3, item_status)

        # 🔹 Conectar duplo clique para abrir parcelas
        tabela.cellDoubleClicked.connect(lambda row, col: self.abrir_parcelas(row))
        self.tabela_emprestimos = tabela

        container.addWidget(tabela)
        self._set_content(frame)


    def abrir_parcelas(self, row):
        """Abre a janela de parcelas do empréstimo selecionado."""
        emprestimo_id = self.tabela_emprestimos.item(row, 0).text()  # agora é o ID real
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
        container = QVBoxLayout()
        frame = QWidget()
        frame.setLayout(container)

        # Botão "Nova Garantia" (AGORA VERDE, igual "Novo Cliente")
        btn_nova = QPushButton("➕ Nova Garantia")
        btn_nova.setFixedSize(160, 32)
        btn_nova.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71; color: white;
                padding: 6px 10px; font-size: 12px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        btn_nova.clicked.connect(self.open_nova_garantia)
        container.addWidget(btn_nova, alignment=Qt.AlignLeft)

        # Tabela de garantias
        self.tabela_garantias = QTableWidget(0, 3)
        self.tabela_garantias.cellDoubleClicked.connect(self.editar_garantia)
        self.tabela_garantias.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabela_garantias.setHorizontalHeaderLabels(["Nº", "Descrição e detalhes da garantia", "Valor"])

        header = self.tabela_garantias.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #374157; color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

        # Colunas
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tabela_garantias.setColumnWidth(0, 40)

        header.setSectionResizeMode(1, QHeaderView.Stretch)

        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.tabela_garantias.setColumnWidth(2, 150)

        # Estilo                
        self.tabela_garantias.verticalHeader().setVisible(False)
        self.tabela_garantias.setSelectionMode(QAbstractItemView.NoSelection)  # remove seleção rosa
        self.tabela_garantias.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446; color: white;
                border: 1px solid #3a455b;
                font-size: 14px;
            }
        """)
        self.tabela_garantias.verticalHeader().setDefaultSectionSize(80)

        container.addWidget(self.tabela_garantias)

        # 🔹 adiciona linha de total no final
        self.add_totalizador()

        self._set_content(frame)


    def open_nova_garantia(self):
        from ui.garantias_ui import GarantiaForm

        def callback(data):
            # número da garantia = total de linhas (menos 1 do totalizador) + 1
            row = self.tabela_garantias.rowCount() - 1
            self.tabela_garantias.insertRow(row)

            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.tabela_garantias.setItem(row, 0, num_item)

            desc_item = QTableWidgetItem(data["descricao"])
            self.tabela_garantias.setItem(row, 1, desc_item)

            val_item = QTableWidgetItem(data["valor"])
            val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_garantias.setItem(row, 2, val_item)

            # 🔹 atualiza o totalizador
            self.atualizar_totalizador()


        self.form_garantia = GarantiaForm(callback, parent=self)
        self.form_garantia.show()
    
    def add_totalizador(self):
        """Adiciona linha de totalizadores na tabela de garantias."""
        row = self.tabela_garantias.rowCount()
        self.tabela_garantias.insertRow(row)

        # Coluna Nº (em branco)
        item_num = QTableWidgetItem("")
        item_num.setFlags(item_num.flags() & ~Qt.ItemIsEditable)
        item_num.setBackground(QColor("#2c3446"))
        self.tabela_garantias.setItem(row, 0, item_num)

        # Coluna descrição = "TOTAL"
        item_desc = QTableWidgetItem("TOTAL")
        item_desc.setFlags(item_desc.flags() & ~Qt.ItemIsEditable)
        item_desc.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_desc.setBackground(QColor("#2c3446"))
        font = item_desc.font()
        font.setBold(True)
        item_desc.setFont(font)
        item_desc.setForeground(QColor("#00bfff"))  # azul claro
        self.tabela_garantias.setItem(row, 1, item_desc)

        # Coluna valor
        item_total = QTableWidgetItem("R$ 0,00")
        item_total.setFlags(item_total.flags() & ~Qt.ItemIsEditable)
        item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_total.setBackground(QColor("#2c3446"))
        item_total.setFont(font)
        item_total.setForeground(QColor("#00bfff"))
        self.tabela_garantias.setItem(row, 2, item_total)

    def editar_garantia(self, row, col):
        """Abre o form para editar a garantia clicada."""
        # Ignora se clicou no totalizador (última linha)
        if row == self.tabela_garantias.rowCount() - 1:
            return

        desc = self.tabela_garantias.item(row, 1).text()
        val = self.tabela_garantias.item(row, 2).text()

        from ui.garantias_ui import GarantiaForm

        def callback(data):
            # Atualiza a linha editada
            self.tabela_garantias.item(row, 1).setText(data["descricao"])
            self.tabela_garantias.item(row, 2).setText(data["valor"])
            self.atualizar_totalizador()

        self.form_garantia = GarantiaForm(callback, parent=self)
        # Preenche os campos iniciais do form
        self.form_garantia.inp_desc.setPlainText(desc)
        self.form_garantia.inp_valor.setText(val)
        self.form_garantia.show()


    def atualizar_totalizador(self):
        """Recalcula o total das garantias."""
        total = 0.0
        row_count = self.tabela_garantias.rowCount()

        # percorre todas as linhas menos a última (totalizador)
        for r in range(row_count - 1):
            val_item = self.tabela_garantias.item(r, 2)
            if val_item:
                txt = val_item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
                try:
                    total += float(txt)
                except:
                    pass

        total_fmt = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.tabela_garantias.item(row_count - 1, 2).setText(total_fmt)
