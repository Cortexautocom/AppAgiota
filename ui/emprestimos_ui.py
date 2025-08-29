from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
import uuid
import math

from emprestimos import emprestimos, salvar_emprestimos
from parcelas import salvar_parcelas


class EmprestimoForm(QWidget):
    def __init__(self, parent_callback, id_cliente, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Novo Empréstimo")
        self.setFixedSize(420, 600)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        self.parent_callback = parent_callback
        self.id_cliente = id_cliente 

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

        # ===== Campos de entrada =====
        self.inp_capital = QLineEdit()
        self.inp_capital.setPlaceholderText("Valor financiado (R$)")
        self.inp_capital.setStyleSheet("background-color:#2c3446; color:white; padding:6px; border-radius:6px;")
        layout.addWidget(QLabel("Valor financiado"))
        layout.addWidget(self.inp_capital)

        self.inp_meses = QLineEdit()
        self.inp_meses.setPlaceholderText("Quantidade de meses")
        self.inp_meses.setStyleSheet("background-color:#2c3446; color:white; padding:6px; border-radius:6px;")
        layout.addWidget(QLabel("Quantidade de meses"))
        layout.addWidget(self.inp_meses)

        self.inp_taxa = QLineEdit()
        self.inp_taxa.setPlaceholderText("Taxa de juros mensal (%)")
        self.inp_taxa.setStyleSheet("background-color:#2c3446; color:white; padding:6px; border-radius:6px;")
        layout.addWidget(QLabel("Taxa de juros mensal (%)"))
        layout.addWidget(self.inp_taxa)

        # Botão calcular
        btn_calc = QPushButton("📊 Calcular prestação")
        btn_calc.setStyleSheet("""
            QPushButton {
                background-color:#3498db; color:white;
                padding:8px; border-radius:6px; font-weight:bold;
            }
            QPushButton:hover { background-color:#2980b9; }
        """)
        btn_calc.clicked.connect(self.calcular_prestacao)
        layout.addWidget(btn_calc)

        # ===== Resultados =====
        self.lbl_prestacao = QLabel("Valor da prestação: R$ 0,00")
        self.lbl_prestacao.setStyleSheet("font-size: 14px; color: #9fb0c7;")
        layout.addWidget(self.lbl_prestacao)

        self.lbl_resumo = QLabel("")
        self.lbl_resumo.setStyleSheet("font-size: 13px; color: #ccc;")
        layout.addWidget(self.lbl_resumo)

        # Botão salvar
        btn_save = QPushButton("💾 Salvar Empréstimo")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color:#27ae60; color:white;
                padding:10px; border-radius:6px; font-weight:bold;
            }
            QPushButton:hover { background-color:#2ecc71; }
        """)
        btn_save.clicked.connect(self.save_emprestimo)
        layout.addWidget(btn_save)

    # ==============================
    def calcular_prestacao(self):
        try:
            capital = float(self.inp_capital.text().replace(",", "."))
            n = int(self.inp_meses.text())
            taxa = float(self.inp_taxa.text().replace(",", ".")) / 100  # converte % para decimal
        except ValueError:
            QMessageBox.warning(self, "Erro", "Preencha todos os valores corretamente.")
            return

        # Fórmula do valor da prestação
        try:
            p = (capital * taxa) / (1 - (1 + taxa) ** -n)
        except ZeroDivisionError:
            QMessageBox.warning(self, "Erro", "Taxa inválida.")
            return

        total_pago = p * n
        total_juros = total_pago - capital

        self.lbl_prestacao.setText(f"Valor da prestação: R$ {p:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        self.lbl_resumo.setText(
            f"O total desse financiamento de {n} parcelas de R$ {p:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") +
            f" é R$ {total_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") +
            f", sendo R$ {total_juros:,.2f} de juros.".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        # guarda para salvar depois
        self._ultimo_calc = {"capital": capital, "meses": n, "taxa": taxa, "prestacao": p,
                             "total_pago": total_pago, "total_juros": total_juros}

    # ==============================
    def save_emprestimo(self):
        if not hasattr(self, "_ultimo_calc"):
            QMessageBox.warning(self, "Erro", "Calcule a prestação antes de salvar.")
            return

        dados = self._ultimo_calc
        emprestimo_id = str(uuid.uuid4())

        novo_emprestimo = (
            emprestimo_id,
            self.id_cliente,
            str(dados["capital"]),
            "01/09/2025",  # TODO: usar data atual
            str(dados["meses"]),
            f"Taxa {dados['taxa']*100:.2f}%"
        )

        emprestimos.append(novo_emprestimo)
        salvar_emprestimos()

        # gera parcelas
        novas_parcelas = []
        for i in range(1, dados["meses"] + 1):
            parcela_id = str(uuid.uuid4())
            valor_fmt = f"R$ {dados['prestacao']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            nova_parcela = (
                parcela_id,
                emprestimo_id,
                str(i),
                valor_fmt,
                f"01/{i:02d}/2025",
                "",
                "",
                valor_fmt,
                "",
                "",
                "Não",
                ""
            )
            novas_parcelas.append(nova_parcela)

        salvar_parcelas(novas_parcelas)

        # callback
        self.parent_callback({
            "id": emprestimo_id,
            "capital": dados["capital"],
            "meses": dados["meses"],
            "taxa": dados["taxa"],
            "prestacao": dados["prestacao"],
            "parcelas": novas_parcelas
        })
        self.close()
