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

        # 🔹 Criação da tabela
        self.tabela = QTableWidget(0, 9)
        self.tabela.setHorizontalHeaderLabels([
            "Nº", "Vencimento", "Valor", "Juros", "Desconto",
            "Parcela Atualizada", "Valor Pago", "Residual", "Data do Pag."
        ])

        # Aparência da tabela
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
            (
                _id, _id_emp, num, valor, venc,
                juros, desconto, parcela_atual, valor_pago,
                residual, pago, data_pag
            ) = parcela

            self.tabela.insertRow(linha)

            # Nº parcela (não editável, negrito)
            item_num = QTableWidgetItem(str(num))
            item_num.setTextAlignment(Qt.AlignCenter)
            item_num.setFlags(item_num.flags() & ~Qt.ItemIsEditable)
            item_num.setFont(fonte_negrito)
            self.tabela.setItem(linha, 0, item_num)

            # Vencimento (editável)
            item_venc = QTableWidgetItem(venc or "")
            item_venc.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 1, item_venc)

            # Valor (editável, evita duplicar "R$")
            item_valor = QTableWidgetItem(valor if str(valor).startswith("R$") else f"R$ {valor}")
            item_valor.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 2, item_valor)

            # Juros (editável)
            item_juros = QTableWidgetItem(juros or "")
            item_juros.setTextAlignment(Qt.AlignCenter)
            item_juros.setForeground(QColor("#78ddff"))
            self.tabela.setItem(linha, 3, item_juros)

            # Desconto (editável)
            item_desc = QTableWidgetItem(desconto or "")
            item_desc.setTextAlignment(Qt.AlignCenter)
            item_desc.setForeground(QColor("#ffaeae"))
            self.tabela.setItem(linha, 4, item_desc)

            # Parcela Atualizada (não editável, calculada)
            item_atual = QTableWidgetItem(parcela_atual or f"R$ {valor}")
            item_atual.setTextAlignment(Qt.AlignCenter)
            item_atual.setFlags(item_atual.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha, 5, item_atual)

            # Valor Pago (editável)
            item_pago = QTableWidgetItem(valor_pago or "")
            item_pago.setTextAlignment(Qt.AlignCenter)
            item_pago.setForeground(QColor("#78ddff"))
            self.tabela.setItem(linha, 6, item_pago)

            # Residual (não editável, calculado)
            item_residual = QTableWidgetItem(residual or "")
            item_residual.setTextAlignment(Qt.AlignCenter)
            item_residual.setForeground(QColor("#ffaeae"))
            item_residual.setFlags(item_residual.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha, 7, item_residual)

            # Data do Pag. (editável)
            item_data = QTableWidgetItem(data_pag or "")
            item_data.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 8, item_data)

        # Espaço visual entre tabela e totalizadores
        spacer = QFrame()
        spacer.setFixedHeight(12)
        layout.addWidget(spacer)

        # Linha de totais
        self.adicionar_totalizadores(fonte_negrito)

        # 🔹 Conectar formatação automática (a tabela já existe aqui)
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

        # 🔹 Atualiza cálculos iniciais
        self.atualizar_totalizadores()
        for row in range(self.tabela.rowCount() - 1):  # ignora totalizadores
            try:
                valor = self._get_valor(row, 2)
                juros = self._get_valor(row, 3)
                desconto = self._get_valor(row, 4)
                atualizado = valor + juros - desconto
                self.tabela.item(row, 5).setText(self._fmt(atualizado))

                pago = self._get_valor(row, 6)
                residual = atualizado - pago
                self.tabela.item(row, 7).setText(self._fmt(residual))
            except:
                pass

    def adicionar_totalizadores(self, fonte_negrito):
        """Adiciona linha de totais em negrito."""
        row = self.tabela.rowCount()
        self.tabela.insertRow(row)

        for col in range(self.tabela.columnCount()):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setBackground(QColor("#4e586e"))  # mesma cor da tabela

            if 2 <= col <= 6:  # colunas Valor até Valor Pago
                item.setFont(fonte_negrito)
                item.setText("R$ 0,00")

                # Azul claro em Juros (3) e Valor Pago (6)
                if col in (3, 6):
                    item.setForeground(QColor("#00bfff"))

            if col == 4:  # Desconto
                item.setFont(fonte_negrito)
                item.setText("R$ 0,00")
                item.setForeground(QColor("#ff6e6e"))

            if col == 7:  # Residual
                item.setFont(fonte_negrito)
                item.setText("R$ 0,00")
                item.setForeground(QColor("#ff6e6e"))

            self.tabela.setItem(row, col, item)

    def formatar_valores(self, item):
        """Formata valores monetários e recalcula campos dependentes."""
        if not item or item.row() == self.tabela.rowCount() - 1:
            return

        col_monetarias = [2, 3, 4, 5, 6, 7]
        if item.column() in col_monetarias:
            texto = item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
            if texto == "":
                valor = 0.0
                item.setText("")  # mantém célula visualmente vazia
            else:
                try:
                    valor = float(texto)
                    item.setText(self._fmt(valor))
                    item.setTextAlignment(Qt.AlignCenter)
                except ValueError:
                    valor = 0.0
                    item.setText("")


        if item.column() in (2, 3, 4):
            try:
                valor = self._get_valor(item.row(), 2)
                juros = self._get_valor(item.row(), 3)
                desconto = self._get_valor(item.row(), 4)
                atualizado = valor + juros - desconto
                celula = self.tabela.item(item.row(), 5)
                if celula:
                    celula.setText(self._fmt(atualizado))
            except:
                pass

        if item.column() in (5, 6):
            try:
                atualizado = self._get_valor(item.row(), 5)
                pago = self._get_valor(item.row(), 6)
                residual = atualizado - pago
                celula = self.tabela.item(item.row(), 7)
                if celula:
                    celula.setText(self._fmt(residual))
            except:
                pass

        self.atualizar_totalizadores()

    def _get_valor(self, row, col):
        """Lê valor float de uma célula formatada."""
        celula = self.tabela.item(row, col)
        if not celula:
            return 0.0
        txt = celula.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            return float(txt) if txt else 0.0
        except:
            return 0.0
        
    def _fmt(self, valor):
        """Formata float em moeda BR."""
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def atualizar_totalizadores(self):
        """Recalcula os totais das colunas monetárias."""
        row_total = self.tabela.rowCount() - 1
        for col in [2, 3, 4, 5, 6, 7]:
            total = 0.0
            for r in range(row_total):
                try:
                    total += self._get_valor(r, col)
                except:
                    pass
            celula = self.tabela.item(row_total, col)
            if celula:
                celula.setText(self._fmt(total))

    def salvar_modificacoes(self):
        """Salva alterações no banco local e envia ao Supabase."""
        from parcelas import salvar_parcelas, parcelas, sincronizar_parcelas_upload

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
                juros,
                desconto,
                parcela_atual,
                valor_pago,
                residual,
                "Não",
                data_pag
            ))

        parcelas[:] = novas_parcelas
        salvar_parcelas(parcelas)        

        print("✅ Parcelas salvas no banco local e na nuvem!")

        if self.on_save_callback:
            self.on_save_callback()

        self.close()
