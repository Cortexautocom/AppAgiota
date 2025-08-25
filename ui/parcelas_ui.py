from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor


class ParcelasWindow(QWidget):
    """Janela para visualizar/editar parcelas de um empréstimo."""
    def __init__(self, emprestimo):
        super().__init__()
        self.emprestimo = emprestimo
        self.setWindowTitle(f"Parcelas - Empréstimo {emprestimo['id']}")
        self.setFixedSize(650, 450)
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

        # Preenche as parcelas recebidas
        for linha, (num, valor, venc, pago, data_pag) in enumerate(emprestimo["parcelas"]):
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

    def atualizar_pagamento(self, row, state):
        """Marca ou desmarca pagamento e atualiza valores."""
        pago = (state == Qt.Checked)
        data_item = self.tabela.item(row, 4)

        if pago:
            # Marca data atual
            data_item.setText(QDate.currentDate().toString("dd/MM/yyyy"))
        else:
            data_item.setText("")

        self.calcular_totais()

    def calcular_totais(self):
        """Recalcula capital e juros pagos com base nas parcelas quitadas."""
        # 🔹 Valores principais do empréstimo (para cálculo proporcional)
        total_capital = self.emprestimo.get("capital", 1000)  # fallback para testes
        total_juros = self.emprestimo.get("juros", 500)
        total = total_capital + total_juros

        prop_juros = total_juros / total if total > 0 else 0
        prop_capital = total_capital / total if total > 0 else 0

        pago_capital = 0
        pago_juros = 0

        for linha in range(self.tabela.rowCount()):
            chk = self.tabela.cellWidget(linha, 3)
            if chk and chk.isChecked():
                valor = float(self.tabela.item(linha, 1).text().replace("R$", "").replace(",", "."))
                pago_capital += valor * prop_capital
                pago_juros += valor * prop_juros

        # Atualiza labels
        self.lbl_total_capital.setText(f"Capital pago: R$ {pago_capital:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self.lbl_total_juros.setText(f"Juros pagos: R$ {pago_juros:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
