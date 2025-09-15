from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PySide6.QtCore import Qt
from parcelas import carregar_parcelas_por_emprestimo
from emprestimos import carregar_emprestimos
from ui.parcelas_ui import ParcelasWindow

class ArquivadosWindow(QWidget):
    def __init__(self, client_data, id_usuario, parent=None):
        super().__init__(parent)
        self.client_data = client_data
        self.id_usuario = id_usuario
        self.setWindowTitle(f"Empréstimos Arquivados - {client_data[1]}")
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.setFixedSize(900, 600)

        layout = QVBoxLayout(self)

        # Tabela de empréstimos arquivados
        self.tabela = QTableWidget(0, 7)
        self.tabela.setHorizontalHeaderLabels([
            "ID", "Data inicial", "Último venc.", "Valor", "Parcelas", "Juros", "Taxa"
        ])
        self.tabela.setColumnHidden(0, True)  # esconde ID
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446; color: white;
                border: 1px solid #3a455b;
            }
            QHeaderView::section {
                background-color: #374157; color: white;
                padding: 6px; border: none;
            }
        """)

        layout.addWidget(self.tabela)

        self.carregar_dados()

        # duplo clique abre parcelas em modo somente leitura
        self.tabela.cellDoubleClicked.connect(self.abrir_parcelas)

    def carregar_dados(self):
        todos = carregar_emprestimos(self.id_usuario, incluir_inativos=True)
        arquivados = [e for e in todos if len(e) > 9 and e[9] == "não" and e[1] == self.client_data[0]]

        for linha, emp in enumerate(arquivados):
            self.tabela.insertRow(linha)

            # ID oculto
            self.tabela.setItem(linha, 0, QTableWidgetItem(emp[0]))

            # Data inicial
            item_data = QTableWidgetItem(emp[3] or "")
            item_data.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 1, item_data)

            # Último vencimento
            parcelas_emp = carregar_parcelas_por_emprestimo(emp[0])
            datas_venc = [p[4] for p in parcelas_emp if p[4]]
            ultimo_venc = max(datas_venc) if datas_venc else ""
            item_ultimo = QTableWidgetItem(ultimo_venc)
            item_ultimo.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 2, item_ultimo)

            # Valor
            item_valor = QTableWidgetItem(emp[2])
            item_valor.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 3, item_valor)

            # Parcelas
            self.tabela.setItem(linha, 4, QTableWidgetItem(str(emp[4])))

            # Juros
            self.tabela.setItem(linha, 5, QTableWidgetItem(emp[6]))

            # Taxa
            taxa_txt = emp[5] or ""
            if taxa_txt.lower().startswith("taxa "):
                taxa_txt = taxa_txt[5:]
            self.tabela.setItem(linha, 6, QTableWidgetItem(taxa_txt))

    def abrir_parcelas(self, row, col):
        emp_id = self.tabela.item(row, 0).text()
        parcelas = carregar_parcelas_por_emprestimo(emp_id)

        todos = carregar_emprestimos(self.id_usuario, incluir_inativos=True)
        emp = next((e for e in todos if e[0] == emp_id), None)

        self.parcelas_window = ParcelasWindow(
            {
                "id": emp_id,
                "capital": emp[2] if emp else "0",
                "meses": emp[4] if emp else "1",
                "juros": emp[6] if emp else "0",
                "prestacao": emp[7] if emp else "0",
                "parcelas": parcelas,
                "data_inicio": self.tabela.item(row, 1).text(),
                "cliente": self.client_data[1]
            },
            id_usuario=self.id_usuario,
            parent=self,
            readonly=True  # ✅ modo somente leitura
        )

        self.parcelas_window.setWindowTitle(
            f"Parcelas (Somente Leitura) - {self.client_data[1]}"
        )
        self.parcelas_window.show()
