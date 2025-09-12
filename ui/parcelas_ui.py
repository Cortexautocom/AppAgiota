from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QPushButton, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import uuid

from parcelas import parcelas, salvar_parcelas, carregar_parcelas_por_emprestimo

from functools import partial

class ParcelasWindow(QWidget):
    """Janela para visualizar/editar parcelas de um empréstimo."""
    def __init__(self, emprestimo, id_usuario, parent=None, on_save_callback=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.emprestimo = emprestimo
        self.id_usuario = id_usuario
        self.on_save_callback = on_save_callback

        self.setWindowTitle(f"Parcelas - Empréstimo de {emprestimo.get('data_inicio', '')} - {emprestimo.get('cliente', '')}")
        self.setFixedSize(1150, 550)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        layout = QVBoxLayout(self)

        lbl = QLabel(f"Parcelas do Empréstimo de {emprestimo.get('data_inicio', '')} - {emprestimo.get('cliente', '')}")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #9fb0c7;")
        layout.addWidget(lbl)

        # 🔹 Criação da tabela
        self.tabela = QTableWidget(0, 11)
        self.tabela.setHorizontalHeaderLabels([
            "Nº", "Vencimento", "Valor", "Juros", "Desconto",
            "Calc.", "Pg. Principal", "Pg. Juros",
            "Valor Pago", "Saldo", "Data do Pag."
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

        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tabela.setColumnWidth(0, 40)

        for col in range(1, self.tabela.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Stretch)

        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionMode(QAbstractItemView.NoSelection)
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
        fonte_negrito = QFont(); fonte_negrito.setBold(True)

        for linha, parcela in enumerate(parcelas_do_emprestimo):
            (
                _id, _id_emp, num, valor, venc,
                juros, desconto, pg_principal, pg_juros,
                valor_pago, residual, data_pag, _id_usuario
            ) = parcela

            self.tabela.insertRow(linha)

            # Nº
            item_num = QTableWidgetItem(str(num))
            item_num.setTextAlignment(Qt.AlignCenter)
            item_num.setFlags(item_num.flags() & ~Qt.ItemIsEditable)
            item_num.setFont(fonte_negrito)
            self.tabela.setItem(linha, 0, item_num)

            # Vencimento
            item_venc = QTableWidgetItem(venc or "")
            item_venc.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 1, item_venc)

            # Valor
            item_valor = QTableWidgetItem(valor if str(valor).startswith("R$") else f"R$ {valor}")
            item_valor.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 2, item_valor)

            # Juros
            item_juros = QTableWidgetItem(juros or "")
            item_juros.setTextAlignment(Qt.AlignCenter)
            item_juros.setForeground(QColor("#78ddff"))
            self.tabela.setItem(linha, 3, item_juros)

            # Desconto
            item_desc = QTableWidgetItem(desconto or "")
            item_desc.setTextAlignment(Qt.AlignCenter)
            item_desc.setForeground(QColor("#ffaeae"))
            self.tabela.setItem(linha, 4, item_desc)

            # Botão de cálculo
            btn_calc = QPushButton("⚙️")
            btn_calc.setStyleSheet("background-color:#3498db; color:white; border-radius:6px;")
            print(f"[DEBUG] Criando botão de cálculo na linha {linha}")
            btn_calc.clicked.connect(self.handle_calc_click)
            self.tabela.setCellWidget(linha, 5, btn_calc)

            # Pg. Principal
            item_pg_principal = QTableWidgetItem(pg_principal or "")
            item_pg_principal.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 6, item_pg_principal)

            # Pg. Juros
            item_pg_juros = QTableWidgetItem(pg_juros or "")
            item_pg_juros.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 7, item_pg_juros)

            # Valor Pago
            item_pago = QTableWidgetItem(valor_pago or "")
            item_pago.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 8, item_pago)

            # Saldo (não editável)
            item_saldo = QTableWidgetItem(residual or "")
            item_saldo.setTextAlignment(Qt.AlignCenter)
            item_saldo.setFlags(item_saldo.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha, 9, item_saldo)

            # Data do Pag.
            item_data = QTableWidgetItem(data_pag or "")
            item_data.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 10, item_data)

        # 🔹 Calcula saldo inicial de cada linha
        for row in range(self.tabela.rowCount()):
            try:
                valor = self._get_valor(row, 2)
                juros = self._get_valor(row, 3)
                desconto = self._get_valor(row, 4)
                pg_principal = self._get_valor(row, 6)
                pg_juros = self._get_valor(row, 7)
                saldo = valor + juros - desconto - pg_principal - pg_juros
                self.tabela.item(row, 9).setText(self._fmt(saldo))
                self.tabela.item(row, 9).setTextAlignment(Qt.AlignCenter)
            except:
                pass

        parcelas_do_emprestimo = carregar_parcelas_por_emprestimo(emprestimo["id"])
        parcelas_do_emprestimo.sort(key=lambda p: int(p[2]))  # 🔹 ordena pelo número (coluna 2 = numero)
        

        spacer = QFrame(); spacer.setFixedHeight(12)
        layout.addWidget(spacer)

        self.adicionar_totalizadores(fonte_negrito)
        self.tabela.itemChanged.connect(self.formatar_valores)

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

        self.atualizar_totalizadores()
    
    def handle_calc_click(self):
        sender = self.sender()
        print(f"[DEBUG] Botão clicado: {sender}")
        if not sender:
            print("[DEBUG] Nenhum sender encontrado")
            return

        pos = sender.pos()
        print(f"[DEBUG] sender.pos() = {pos}")
        row = self.tabela.indexAt(sender.pos()).row()
        print(f"[DEBUG] indexAt(sender.pos()) retornou row={row}")

        if row >= 0:
            print(f"[DEBUG] Chamando calcular_pg para linha {row}")
            self.calcular_pg(row)
        else:
            print("[DEBUG] Nenhuma linha encontrada para esse botão")


    def adicionar_totalizadores(self, fonte_negrito):
        row = self.tabela.rowCount()
        self.tabela.insertRow(row)

        for col in range(self.tabela.columnCount()):
            if col == 5:  # pula a coluna do botão
                continue
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setBackground(QColor("#4e586e"))

            if 2 <= col <= 8:
                item.setFont(fonte_negrito)
                item.setText("R$ 0,00")

            self.tabela.setItem(row, col, item)
            item.setTextAlignment(Qt.AlignCenter)



    def formatar_valores(self, item):
        if not item or item.row() == self.tabela.rowCount() - 1:
            return

        col_monetarias = [2, 3, 4, 6, 7, 8]
        if item.column() in col_monetarias:
            texto = item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
            if texto:
                try:
                    valor = float(texto)
                    item.setText(self._fmt(valor))
                except:
                    item.setText("")
            else:
                item.setText("")

        # Valor Pago = Pg. Principal + Pg. Juros
        if item.column() in (6, 7):
            try:
                pg_principal = self._get_valor(item.row(), 6)
                pg_juros = self._get_valor(item.row(), 7)
                total = pg_principal + pg_juros
                celula = self.tabela.item(item.row(), 8)
                celula.setText(self._fmt(total) if total > 0 else "")
            except:
                pass

        # Saldo = Valor + Juros - Desconto - Pg. Principal - Pg. Juros
        try:
            valor = self._get_valor(item.row(), 2)
            juros = self._get_valor(item.row(), 3)
            desconto = self._get_valor(item.row(), 4)
            pg_principal = self._get_valor(item.row(), 6)
            pg_juros = self._get_valor(item.row(), 7)
            saldo = valor + juros - desconto - pg_principal - pg_juros
            celula = self.tabela.item(item.row(), 9)
            celula.setText(self._fmt(saldo))
        except:
            pass

        self.atualizar_totalizadores()

    def _get_valor(self, row, col):
        celula = self.tabela.item(row, col)
        if not celula: return 0.0
        txt = celula.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            return float(txt) if txt else 0.0
        except:
            return 0.0

    def _fmt(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def atualizar_totalizadores(self):
        row_total = self.tabela.rowCount() - 1
        for col in [2, 3, 4, 6, 7, 8]:
            total = 0.0
            for r in range(row_total):
                total += self._get_valor(r, col)
            celula = self.tabela.item(row_total, col)
            if celula:
                celula.setText(self._fmt(total))

    def salvar_modificacoes(self):
        print("[DEBUG] salvar_modificacoes iniciado")
        from parcelas import salvar_parcelas, parcelas, sincronizar_parcelas_upload
        novas_parcelas = []
        for linha in range(self.tabela.rowCount() - 1):
            print(f"[DEBUG] Salvando linha {linha}")
            numero = self.tabela.item(linha, 0).text()
            venc = self.tabela.item(linha, 1).text()
            valor = self.tabela.item(linha, 2).text().replace("R$", "").strip()
            juros = self.tabela.item(linha, 3).text()
            desconto = self.tabela.item(linha, 4).text()
            pg_principal = self.tabela.item(linha, 6).text()
            pg_juros = self.tabela.item(linha, 7).text()
            valor_pago = self.tabela.item(linha, 8).text()
            residual = self.tabela.item(linha, 9).text()
            data_pag = self.tabela.item(linha, 10).text()
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
        print("[DEBUG] Salvando no banco local e sincronizando")
        parcelas[:] = novas_parcelas
        salvar_parcelas(parcelas)
        sincronizar_parcelas_upload()
        print("[DEBUG] Salvamento concluído")
        if self.on_save_callback:
            self.on_save_callback()
        self.close()

    def calcular_pg(self, row):
        """Calcula Pg. Principal e Pg. Juros da linha selecionada."""
        print(f"[DEBUG] calcular_pg chamado para linha {row}")
        try:
            capital = float(self.emprestimo.get("capital", 0))
            n = int(str(self.emprestimo.get("meses", 1)).strip())  # 🔹 força conversão para inteiro
            total_juros = float(self.emprestimo.get("juros", 0))

            print(f"[DEBUG] capital={capital}, meses={n}, total_juros={total_juros}")

            if capital <= 0 or n <= 0:
                print("[DEBUG] Dados inválidos para cálculo, abortando")
                return

            pg_principal = capital / n
            pg_juros = total_juros / n
            print(f"[DEBUG] pg_principal={pg_principal}, pg_juros={pg_juros}")

            self.tabela.item(row, 6).setText(self._fmt(pg_principal))
            self.tabela.item(row, 7).setText(self._fmt(pg_juros))
        except Exception as e:
            print(f"[DEBUG] Erro em calcular_pg: {e}")


