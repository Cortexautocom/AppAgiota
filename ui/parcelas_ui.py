from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QCheckBox, QPushButton
)
from PySide6.QtCore import Qt, QDate
import uuid

from parcelas import parcelas, salvar_parcelas, carregar_parcelas_por_emprestimo


class ParcelasWindow(QWidget):
    """Janela para visualizar/editar parcelas de um empréstimo."""
    def __init__(self, emprestimo, parent=None, on_save_callback=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.emprestimo = emprestimo
        self.on_save_callback = on_save_callback  # callback para atualizar Financeiro

        self.setWindowTitle(f"Parcelas - Empréstimo {emprestimo['id']}")
        self.setFixedSize(650, 500)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        layout = QVBoxLayout(self)

        lbl = QLabel(f"Parcelas do Empréstimo {emprestimo['id']}")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #9fb0c7;")
        layout.addWidget(lbl)

        # Tabela de parcelas
        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(["Nº", "Valor", "Vencimento", "Pago", "Data Pagamento"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

        # 🔹 Carregar parcelas reais do banco pelo ID do empréstimo
        parcelas_do_emprestimo = carregar_parcelas_por_emprestimo(emprestimo["id"])

        for linha, parcela in enumerate(parcelas_do_emprestimo):
            # parcela = (id, id_emprestimo, numero, valor, vencimento, pago, data_pagamento)
            _, _, num, valor, venc, pago, data_pag = parcela

            self.tabela.insertRow(linha)
            self.tabela.setItem(linha, 0, QTableWidgetItem(str(num)))
            self.tabela.setItem(linha, 1, QTableWidgetItem(f"R$ {valor}"))
            self.tabela.setItem(linha, 2, QTableWidgetItem(venc))

            # Pago (checkbox)
            chk = QCheckBox()
            chk.setChecked(pago == "Sim")
            chk.stateChanged.connect(lambda state, row=linha: self.atualizar_pagamento(row, state))
            self.tabela.setCellWidget(linha, 3, chk)

            # Data Pagamento
            item_data = QTableWidgetItem(data_pag)
            item_data.setFlags(item_data.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha, 4, item_data)


        # Labels para totais
        self.lbl_total_capital = QLabel("Capital pago: R$ 0,00")
        self.lbl_total_capital.setStyleSheet("font-size: 14px; color: #9fb0c7;")
        self.lbl_total_juros = QLabel("Juros pagos: R$ 0,00")
        self.lbl_total_juros.setStyleSheet("font-size: 14px; color: #9fb0c7;")

        layout.addWidget(self.lbl_total_capital)
        layout.addWidget(self.lbl_total_juros)

        # 🔹 Botão salvar parcelas
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


    def atualizar_pagamento(self, row, state):
        """Marca ou desmarca pagamento e atualiza valores."""
        pago = (state == Qt.Checked)
        data_item = self.tabela.item(row, 4)

        if pago:
            # Marca data atual
            data_item.setText(QDate.currentDate().toString("dd/MM/yyyy"))
        else:
            data_item.setText("")


    def salvar_modificacoes(self):
        """Salva as alterações feitas nas parcelas no banco local e fecha a janela."""
        global parcelas

        novas_parcelas = []
        for linha in range(self.tabela.rowCount()):
            numero = self.tabela.item(linha, 0).text()
            valor = self.tabela.item(linha, 1).text().replace("R$", "").strip()
            venc = self.tabela.item(linha, 2).text()
            chk = self.tabela.cellWidget(linha, 3)
            pago = "Sim" if chk and chk.isChecked() else "Não"
            data_pag = self.tabela.item(linha, 4).text()

            # Mantém o mesmo ID se já existir
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
                pago,
                data_pag
            ))

        parcelas[:] = novas_parcelas
        salvar_parcelas()
        print("✅ Parcelas salvas no banco local!")

        # 🔹 Se tiver callback, chama para atualizar Financeiro
        if self.on_save_callback:
            self.on_save_callback()

        # Fecha a janela
        self.close()
