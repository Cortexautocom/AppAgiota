from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QPushButton, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import uuid

from parcelas import parcelas, salvar_parcelas, carregar_parcelas_por_emprestimo


class ParcelasWindow(QWidget):
    """Janela para visualizar/editar parcelas de um empréstimo."""
    def __init__(self, emprestimo, parent=None, on_save_callback=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.emprestimo = emprestimo
        self.on_save_callback = on_save_callback

        self.setWindowTitle(f"Parcelas - Empréstimo {emprestimo['id']}")
        self.setFixedSize(1050, 550)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        layout = QVBoxLayout(self)

        lbl = QLabel(f"Parcelas do Empréstimo {emprestimo['id']}")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #9fb0c7;")
        layout.addWidget(lbl)

        # Tabela de parcelas (9 colunas)
        self.tabela = QTableWidget(0, 9)
        self.tabela.setHorizontalHeaderLabels([
            "Nº", "Vencimento", "Valor", "Juros", "Desconto",
            "Parcela Atualizada", "Valor Pago", "Residual", "Data do Pag."
        ])

        # 🔹 Aparência da tabela
        header = self.tabela.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #374157;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

        # Coluna 0 (Nº) fixa em 40px e negrito
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tabela.setColumnWidth(0, 40)

        # Demais colunas expansivas
        for col in range(1, self.tabela.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)

        # Estilo geral
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionMode(QAbstractItemView.NoSelection)  # remove azul de seleção
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446;
                color: white;
                border: 1px solid #3a455b;
            }
        """)
        layout.addWidget(self.tabela)

        # 🔹 Carregar parcelas reais
        parcelas_do_emprestimo = carregar_parcelas_por_emprestimo(emprestimo["id"])
        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        for linha, parcela in enumerate(parcelas_do_emprestimo):
            _, _, num, valor, venc, _, _ = parcela
            self.tabela.insertRow(linha)

            # Nº parcela (não editável, negrito)
            item_num = QTableWidgetItem(str(num))
            item_num.setTextAlignment(Qt.AlignCenter)
            item_num.setFlags(item_num.flags() & ~Qt.ItemIsEditable)
            item_num.setFont(fonte_negrito)
            self.tabela.setItem(linha, 0, item_num)

            # Vencimento
            item_venc = QTableWidgetItem(venc)
            item_venc.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 1, item_venc)

            # Valor
            item_valor = QTableWidgetItem(f"R$ {valor}")
            item_valor.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 2, item_valor)

            # Juros (azul)
            item_juros = QTableWidgetItem("")
            item_juros.setTextAlignment(Qt.AlignCenter)
            item_juros.setForeground(QColor("blue"))
            self.tabela.setItem(linha, 3, item_juros)

            # Desconto (vermelho)
            item_desc = QTableWidgetItem("")
            item_desc.setTextAlignment(Qt.AlignCenter)
            item_desc.setForeground(QColor("red"))
            self.tabela.setItem(linha, 4, item_desc)

            # Parcela Atualizada (não editável)
            item_atual = QTableWidgetItem(f"R$ {valor}")
            item_atual.setTextAlignment(Qt.AlignCenter)
            item_atual.setFlags(item_atual.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha, 5, item_atual)

            # Valor Pago
            item_pago = QTableWidgetItem("")
            item_pago.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 6, item_pago)

            # Residual (não editável, vermelho)
            item_residual = QTableWidgetItem("")
            item_residual.setTextAlignment(Qt.AlignCenter)
            item_residual.setForeground(QColor("red"))
            item_residual.setFlags(item_residual.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha, 7, item_residual)

            # Data do Pag.
            item_data = QTableWidgetItem("")
            item_data.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 8, item_data)

        # 🔹 Espaço visual entre tabela e totalizadores
        spacer = QFrame()
        spacer.setFixedHeight(12)
        layout.addWidget(spacer)

        # 🔹 Linha de totais
        self.adicionar_totalizadores(fonte_negrito)

        # Conectar formatação automática
        self.tabela.itemChanged.connect(self.formatar_valores)

        # Botão salvar
        btn_salvar = QPushButton("💾 Salvar Parcelas")
        btn_salvar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 8px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_salvar.clicked.connect(self.salvar_modificacoes)
        layout.addWidget(btn_salvar, alignment=Qt.AlignCenter)

    def adicionar_totalizadores(self, fonte_negrito):
        """Adiciona linha de totais em negrito."""
        row = self.tabela.rowCount()
        self.tabela.insertRow(row)

        for col in range(self.tabela.columnCount()):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setBackground(QColor("#2c3446"))  # mesma cor da tabela

            if 2 <= col <= 6:  # colunas Valor até Valor Pago
                item.setFont(fonte_negrito)
                item.setText("R$ 0,00")

            self.tabela.setItem(row, col, item)

    def formatar_valores(self, item):
        """Formata valores monetários em R$."""
        if not item:
            return
        col_monetarias = [2, 3, 4, 5, 6, 7]
        if item.row() == self.tabela.rowCount() - 1:
            return
        if item.column() in col_monetarias:
            texto = item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
            if texto == "":
                return
            try:
                valor = float(texto)
                item.setText(f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                item.setTextAlignment(Qt.AlignCenter)
            except ValueError:
                item.setText("")

    def salvar_modificacoes(self):
        """Salva alterações no banco local."""
        global parcelas
        novas_parcelas = []
        for linha in range(self.tabela.rowCount() - 1):  # ignora totais
            numero = self.tabela.item(linha, 0).text()
            venc = self.tabela.item(linha, 1).text()
            valor = self.tabela.item(linha, 2).text().replace("R$", "").strip()
            juros = self.tabela.item(linha, 3).text()
            desconto = self.tabela.item(linha, 4).text()
            parcela_atual = self.tabela.item(linha, 5).text()
            valor_pago = self.tabela.item(linha, 6).text()
            residual = self.tabela.item(linha, 7).text()
            data_pag = self.tabela.item(linha, 8).text()

            if linha < len(parcelas):
                parcela_id = parcelas[linha][0]
            else:
                parcela_id = str(uuid.uuid4())

            novas_parcelas.append((
                parcela_id,
                self.emprestimo["id"],
                numero,
                valor,
                venc,
                "Não",
                data_pag
            ))

        parcelas[:] = novas_parcelas
        salvar_parcelas()
        print("✅ Parcelas salvas no banco local!")

        if self.on_save_callback:
            self.on_save_callback()

        self.close()
