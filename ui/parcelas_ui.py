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
    def __init__(self, emprestimo, id_usuario, parent=None, on_save_callback=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.emprestimo = emprestimo
        self.id_usuario = id_usuario   # ✅ agora guardamos o usuário logado
        self.on_save_callback = on_save_callback

        self.setWindowTitle(f"Parcelas - Empréstimo de {emprestimo.get('data_inicio', '')} - {emprestimo.get('cliente', '')}")
        self.setFixedSize(1050, 550)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        layout = QVBoxLayout(self)

        lbl = QLabel(f"Parcelas do Empréstimo de {emprestimo.get('data_inicio', '')} - {emprestimo.get('cliente', '')}")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #9fb0c7;")
        layout.addWidget(lbl)

        # 🔹 Criação da tabela
        self.tabela = QTableWidget(0, 10)
        self.tabela.setHorizontalHeaderLabels([
            "Nº", "Vencimento", "Valor", "Juros", "Desconto",
            "Pg. Principal", "Pg. Juros", "Valor Pago", "Saldo", "Data do Pag."
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
                juros, desconto, pg_principal, pg_juros,
                valor_pago, residual, data_pag, _id_usuario
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

            # Pg. Principal (editável)
            item_pg_principal = QTableWidgetItem(pg_principal if pg_principal else "")
            item_pg_principal.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 5, item_pg_principal)

            # Pg. Juros (editável)
            item_pg_juros = QTableWidgetItem(pg_juros or "")
            item_pg_juros.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 6, item_pg_juros)

            # Valor Pago (editável)
            item_pago = QTableWidgetItem(valor_pago or "")
            item_pago.setTextAlignment(Qt.AlignCenter)
            item_pago.setForeground(QColor("#78ddff"))
            self.tabela.setItem(linha, 7, item_pago)

            # Residual (não editável, calculado)
            item_residual = QTableWidgetItem(residual or "")
            item_residual.setTextAlignment(Qt.AlignCenter)
            item_residual.setForeground(QColor("#ffaeae"))
            item_residual.setFlags(item_residual.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha, 8, item_residual)

            # Data do Pag. (editável)
            item_data = QTableWidgetItem(data_pag or "")
            item_data.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 9, item_data)


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
            item.setBackground(QColor("#4e586e"))

            if 2 <= col <= 6:
                item.setFont(fonte_negrito)
                item.setText("R$ 0,00")

                if col in (3, 6):
                    item.setForeground(QColor("#00bfff"))

            if col == 4:
                item.setFont(fonte_negrito)
                item.setText("R$ 0,00")
                item.setForeground(QColor("#ff6e6e"))

            if col == 7:
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
                item.setText("")
            else:
                try:
                    valor = float(texto)
                    item.setText(self._fmt(valor))
                    item.setTextAlignment(Qt.AlignCenter)
                except ValueError:
                    valor = 0.0
                    item.setText("")

        # 🔹 Valor Pago = Pg. Principal + Pg. Juros
        if item.column() in (5, 6):  # se mudou Pg. Principal ou Pg. Juros
            try:
                pg_principal = self._get_valor(item.row(), 5)
                pg_juros = self._get_valor(item.row(), 6)
                total_pago = pg_principal + pg_juros

                celula = self.tabela.item(item.row(), 7)  # col 7 = Valor Pago
                if total_pago > 0:
                    celula.setText(self._fmt(total_pago))
                    celula.setTextAlignment(Qt.AlignCenter)
                else:
                    celula.setText("")  
            except:
                pass

        # 🔹 Saldo = Valor + Juros - Desconto + Pg. Principal + Pg. Juros
        try:
            valor = self._get_valor(item.row(), 2)
            juros = self._get_valor(item.row(), 3)
            desconto = self._get_valor(item.row(), 4)
            pg_principal = self._get_valor(item.row(), 5)
            pg_juros = self._get_valor(item.row(), 6)

            saldo = valor + juros - desconto - pg_principal - pg_juros
            celula_saldo = self.tabela.item(item.row(), 8)  # col 8 = Saldo
            if celula_saldo:
                celula_saldo.setText(self._fmt(saldo))
                celula_saldo.setTextAlignment(Qt.AlignCenter)
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
            # Colunas monetárias agora: Valor (2), Juros (3), Desconto (4),
            # Pg. Principal (5), Pg. Juros (6), Valor Pago (7)
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
            pg_principal = self.tabela.item(linha, 5).text()
            pg_juros = self.tabela.item(linha, 6).text()
            valor_pago = self.tabela.item(linha, 7).text()
            residual = self.tabela.item(linha, 8).text()
            data_pag = self.tabela.item(linha, 9).text()

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
                pg_principal,
                pg_juros,
                valor_pago,
                residual,
                data_pag,
                self.id_usuario
            ))

        parcelas[:] = novas_parcelas
        salvar_parcelas(parcelas)
        sincronizar_parcelas_upload()       

        if self.on_save_callback:
            self.on_save_callback()

        self.close()


