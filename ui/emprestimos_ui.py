from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QScrollArea, QHBoxLayout
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QMessageBox
from PySide6.QtCore import Qt


class EmprestimoForm(QWidget):
    """
    Formulário de empréstimo.
    Campos: Valor principal, Juros, Qtde de parcelas, botão Gerar.
    """
    def __init__(self, parent_callback, initial_data=None):
        super().__init__()
        self.setWindowTitle("Novo Empréstimo")
        self.setFixedSize(400, 550)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        self.parent_callback = parent_callback

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("EmprestimoFormPanel")
        panel.setStyleSheet("""
            QFrame#EmprestimoFormPanel {
                background-color: #1c2331;
                border-radius: 14px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 130))
        panel.setGraphicsEffect(shadow)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        outer.addWidget(panel)

        # Campos principais
        self.inp_capital = QLineEdit()
        self.inp_capital.setPlaceholderText("Valor principal (capital)")
        self.inp_capital.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")
        layout.addWidget(QLabel("Valor principal"))
        layout.addWidget(self.inp_capital)

        self.inp_juros = QLineEdit()
        self.inp_juros.setPlaceholderText("Valor total de juros")
        self.inp_juros.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")
        layout.addWidget(QLabel("Juros"))
        layout.addWidget(self.inp_juros)

        self.inp_qtd = QLineEdit()
        self.inp_qtd.setPlaceholderText("Quantidade de parcelas")
        self.inp_qtd.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")
        layout.addWidget(QLabel("Quantidade de parcelas"))
        layout.addWidget(self.inp_qtd)

        # Botão gerar
        btn_gerar = QPushButton("Gerar Parcelas")
        btn_gerar.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                padding: 8px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_gerar.clicked.connect(self.gerar_parcelas)
        layout.addWidget(btn_gerar)

        # Área para mostrar parcelas (scroll)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.parcelas_widget = QWidget()
        self.parcelas_layout = QVBoxLayout(self.parcelas_widget)
        self.scroll_area.setWidget(self.parcelas_widget)
        layout.addWidget(self.scroll_area, stretch=1)

        # Totais pagos (só leitura)
        self.lbl_capital_pago = QLabel("Capital pago: R$ 0,00")
        self.lbl_capital_pago.setStyleSheet("font-size: 14px; color: #9fb0c7;")
        self.lbl_juros_pago = QLabel("Juros pagos: R$ 0,00")
        self.lbl_juros_pago.setStyleSheet("font-size: 14px; color: #9fb0c7;")
        layout.addWidget(self.lbl_capital_pago)
        layout.addWidget(self.lbl_juros_pago)

        # Botão salvar
        btn_save = QPushButton("Salvar Empréstimo")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 10px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_save.clicked.connect(self.save_emprestimo)
        layout.addWidget(btn_save)

    def gerar_parcelas(self):
        """Gera parcelas com base no capital + juros / quantidade."""
        try:
            capital = float(self.inp_capital.text().replace(",", "."))
            juros = float(self.inp_juros.text().replace(",", "."))
            qtd = int(self.inp_qtd.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Preencha valores numéricos válidos.")
            return

        total = capital + juros
        valor_parcela = total / qtd if qtd > 0 else 0

        # Limpa a lista anterior
        for i in reversed(range(self.parcelas_layout.count())):
            widget = self.parcelas_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Cria novos campos de parcelas
        for i in range(1, qtd + 1):
            lbl = QLabel(f"Parcela {i}: R$ {valor_parcela:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            lbl.setStyleSheet("font-size: 13px; color: white;")
            self.parcelas_layout.addWidget(lbl)

    def save_emprestimo(self):
        """Envia os dados do empréstimo + parcelas para o callback."""
        try:
            capital = float(self.inp_capital.text().replace(",", "."))
            juros = float(self.inp_juros.text().replace(",", "."))
            qtd = int(self.inp_qtd.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Preencha valores numéricos válidos.")
            return

        total = capital + juros
        valor_parcela = total / qtd if qtd > 0 else 0

        # Gera lista de parcelas
        parcelas = []
        for i in range(1, qtd + 1):
            parcelas.append((i, f"{valor_parcela:.2f}", f"01/{i:02d}/2025", "Não", ""))

        data = {
            "capital": capital,
            "juros": juros,
            "qtd": qtd,
            "parcelas": parcelas
        }

        self.parent_callback(data)
        self.close()

