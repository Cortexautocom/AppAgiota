from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout, QHBoxLayout, QDateEdit, QCalendarWidget
)
from PySide6.QtGui import QColor, QIntValidator
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QDate
import uuid

import emprestimos
from parcelas import sincronizar_parcelas_upload, salvar_parcelas  


class EmprestimoForm(QWidget):
    def __init__(self, parent_callback, id_cliente, id_usuario, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setWindowTitle("Novo Empréstimo")
        self.setFixedSize(420, 400)        
        self.setStyleSheet("""
            background-color: #1c2331; color: white;
            QLineEdit {
                background-color:#2c3446; 
                color:white; 
                padding:6px; 
                border-radius:6px;
            }
            QLineEdit:focus, QLineEdit:disabled, QLineEdit:!focus {
                background-color:#2c3446;
                color:white;
            }
        """)

        self.parent_callback = parent_callback
        self.id_cliente = id_cliente
        self.id_usuario = id_usuario  # ✅ agora vem do construtor

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

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setVerticalSpacing(8)

        # ===== Data do empréstimo =====
        self.inp_data = QDateEdit()
        self.inp_data.setDisplayFormat("dd/MM/yyyy")
        self.inp_data.setDate(QDate.currentDate())  # já inicia com hoje
        self.inp_data.setCalendarPopup(True)
        self.inp_data.setStyleSheet("""
            QDateEdit {
                background-color:#2c3446;
                color:white;
                padding:6px;
                border-radius:6px;
                selection-background-color:#3498db;   /* cor do highlight */
                selection-color:white;                /* cor do texto selecionado */
            }
            QAbstractSpinBox {
                background-color:#2c3446;
                color:white;
                border-radius:6px;
                padding:6px;
                selection-background-color:#3498db;
                selection-color:white;
            }
        """)

        # 🔹 Aplicar calendário customizado sem coluna de semanas
        cal_emprestimo = QCalendarWidget()
        cal_emprestimo.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)  # 🔹 remove coluna da semana
        cal_emprestimo.setStyleSheet("""
            QCalendarWidget QWidget {
                background-color: #1c2331;
                color: white;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: #1c2331;
                color: white;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #555;
            }
            QCalendarWidget QTableView {
                background-color: #1c2331;
                alternate-background-color: #1c2331;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QCalendarWidget QTableView QHeaderView::section {
                background-color: #1c2331;
                color: #9fb0c7;
                border: none;
            }
        """)
        self.inp_data.setCalendarWidget(cal_emprestimo)

        form.addRow(QLabel("Data do empréstimo:"), self.inp_data)    

        # ===== Valor financiado =====
        self.inp_capital = QLineEdit()
        self.inp_capital.setPlaceholderText("R$ 0,00")
        self.inp_capital.setStyleSheet("background-color:#2c3446; color:white; padding:6px; border-radius:6px;")
        self.inp_capital.textChanged.connect(lambda: self.formatar_moeda(self.inp_capital))
        form.addRow(QLabel("Valor financiado:"), self.inp_capital)

        # ===== Quantidade de meses =====
        self.inp_meses = QLineEdit()
        self.inp_meses.setMaxLength(2)
        self.inp_meses.setFixedWidth(30)
        self.inp_meses.setStyleSheet("background-color:#2c3446; color:white; padding:6px; border-radius:6px;")
        self.inp_meses.setValidator(QIntValidator(1, 99, self))
        form.addRow(QLabel("Quantidade de meses:"), self.inp_meses)

        # ===== Taxa mensal % =====
        taxa_layout = QHBoxLayout()
        self.inp_taxa = QLineEdit()
        self.inp_taxa.setPlaceholderText("Ex: 15,00")
        self.inp_taxa.setStyleSheet("background-color:#2c3446; color:white; padding:6px; border-radius:6px;")
        taxa_layout.addWidget(self.inp_taxa)
        taxa_layout.addWidget(QLabel("% a.m"))
        form.addRow(QLabel("Taxa de juros mensal:"), taxa_layout)

        # ===== Total de juros =====
        self.inp_total_juros = QLineEdit()
        self.inp_total_juros.setPlaceholderText("R$ 0,00")
        self.inp_total_juros.setStyleSheet("background-color:#2c3446; color:#00bfff; padding:6px; border-radius:6px; font-weight:bold;")
        self.inp_total_juros.textChanged.connect(lambda: self.formatar_moeda(self.inp_total_juros))
        form.addRow(QLabel("Total dos juros:"), self.inp_total_juros)

        layout.addLayout(form)

        # Botão calcular
        btn_calc = QPushButton("📊 Simular Empréstimo")
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
        self.lbl_prestacao.setStyleSheet("font-size: 14px; color: #9fb0c7; margin-top:4px; margin-bottom:2px;")
        self.lbl_prestacao.setWordWrap(True)
        self.lbl_prestacao.hide()
        layout.addWidget(self.lbl_prestacao)

        self.lbl_resumo = QLabel("")
        self.lbl_resumo.setStyleSheet("font-size: 13px; color: #ccc; margin-top:2px; margin-bottom:6px;")
        self.lbl_resumo.setWordWrap(True)
        self.lbl_resumo.hide()
        layout.addWidget(self.lbl_resumo)

        # Botão criar
        btn_save = QPushButton("💾 Criar Empréstimo")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color:#27ae60; color:white;
                padding:8px; border-radius:6px; font-weight:bold;
            }
            QPushButton:hover { background-color:#2ecc71; }
        """)
        btn_save.clicked.connect(self.save_emprestimo)
        layout.addWidget(btn_save)

        layout.setSpacing(6)

    # ==============================
    def formatar_moeda(self, campo):
        texto = campo.text().replace("R$", "").replace(".", "").replace(",", "").strip()
        if not texto.isdigit():
            campo.blockSignals(True)
            campo.setText("")
            campo.blockSignals(False)
            return

        valor = int(texto) / 100
        campo.blockSignals(True)
        campo.setText(f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        campo.blockSignals(False)
        campo.setCursorPosition(len(campo.text()))

    # ==============================
    def calcular_prestacao(self):
        capital_txt = self.inp_capital.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
        juros_txt = self.inp_total_juros.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
        taxa_txt = self.inp_taxa.text().replace(",", ".").strip()
        meses_txt = self.inp_meses.text().strip()

        if not capital_txt or not meses_txt:
            QMessageBox.warning(self, "Erro", "Preencha capital e meses.")
            return

        capital = float(capital_txt)
        n = int(meses_txt)

        tem_taxa = bool(taxa_txt)
        tem_juros = bool(juros_txt)

        if tem_taxa and tem_juros:
            QMessageBox.warning(self, "Erro", "Preencha apenas um dos campos: ou juros ou taxa.")
            return

        def fmt_br(valor: float) -> str:
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        if tem_taxa:
            taxa = float(taxa_txt) / 100
            p = (capital * taxa) / (1 - (1 + taxa) ** -n)
            total_pago = p * n
            total_juros = total_pago - capital
        elif tem_juros:
            total_juros = float(juros_txt)
            total_pago = capital + total_juros
            p = total_pago / n

            # 🔹 Descobrir a taxa aproximada
            taxa = 0
            melhor_dif = float("inf")
            taxa_calc = 0
            for t in [i/10000 for i in range(1, 10000)]:  # 0.01% até 100% a.m
                p_calc = (capital * t) / (1 - (1 + t) ** -n)
                dif = abs(p_calc - p)
                if dif < melhor_dif:
                    melhor_dif = dif
                    taxa_calc = t
            taxa = taxa_calc
        else:
            QMessageBox.warning(self, "Erro", "Informe taxa ou juros.")
            return

        prestacao_fmt = fmt_br(p)
        total_pago_fmt = fmt_br(total_pago)
        total_juros_fmt = fmt_br(total_juros)
        self.inp_total_juros.setText(total_juros_fmt)

        self.lbl_prestacao.show()
        self.lbl_resumo.show()

        self.lbl_prestacao.setText(f"Valor da prestação: {prestacao_fmt}")
        taxa_fmt = f"{taxa*100:.2f}% a.m"
        self.lbl_resumo.setText(
            f"O total desse financiamento de {n} parcelas de {prestacao_fmt} "
            f"é {total_pago_fmt}, sendo {total_juros_fmt} de juros.\n"
            f"Taxa aproximada: {taxa_fmt}"
        )

        self._ultimo_calc = {
            "capital": capital,
            "meses": n,
            "taxa": taxa,
            "prestacao": p,
            "total_pago": total_pago,
            "total_juros": total_juros
        }

    # ==============================
    def save_emprestimo(self):
        if not hasattr(self, "_ultimo_calc"):
            QMessageBox.warning(self, "Erro", "Calcule a prestação antes de salvar.")
            return

        dados = self._ultimo_calc
        emprestimo_id = str(uuid.uuid4())
        id_usuario = self.id_usuario  # ✅ já vem do construtor

        novo_emprestimo = (
            emprestimo_id,
            self.id_cliente,
            str(dados["capital"]),
            self.inp_data.date().toString("dd/MM/yyyy"),
            str(dados["meses"]),
            f"Taxa {dados['taxa']*100:.2f}%",
            str(dados["total_juros"]),
            str(dados["prestacao"]),
            id_usuario
        )
        
        # 🔹 Salva localmente
        emprestimos.emprestimos.append(novo_emprestimo)        
        emprestimos.salvar_emprestimos()

        # 🔹 Envia empréstimo para o Supabase
        from emprestimos import sincronizar_emprestimos_upload
        sincronizar_emprestimos_upload()

        # 🔹 Gerar parcelas simuladas (pg_principal e pg_juros ficam sempre vazios)
        from datetime import datetime, timedelta
        import calendar

        data_inicio_str = self.inp_data.date().toString("dd/MM/yyyy")
        data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y")
        dia_ref = data_inicio.day

        novas_parcelas = []
        for i in range(1, dados["meses"] + 1):
            parcela_id = str(uuid.uuid4())
            valor_fmt = f"R$ {dados['prestacao']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # 🔹 calcula vencimento = mês seguinte ao da data de início + (i-1)
            ano = data_inicio.year
            mes = data_inicio.month + i
            while mes > 12:
                mes -= 12
                ano += 1

            ultimo_dia = calendar.monthrange(ano, mes)[1]

            if dia_ref <= ultimo_dia:
                vencimento = datetime(ano, mes, dia_ref)
            else:
                # caso não exista esse dia (exemplo 31/02), vai para o dia 1 do próximo mês
                mes += 1
                if mes > 12:
                    mes = 1
                    ano += 1
                vencimento = datetime(ano, mes, 1)

            venc_str = vencimento.strftime("%d/%m/%Y")

            nova_parcela = (
                parcela_id,
                emprestimo_id,
                str(i),             # número da parcela
                valor_fmt,          # valor da parcela
                venc_str,           # vencimento calculado
                "",                 # juros vazio
                "",                 # desconto vazio
                "",                 # pg_principal vazio
                "",                 # pg_juros vazio
                "",                 # valor_pago vazio
                "",                 # residual vazio
                "",                 # data_pagamento vazio
                id_usuario
            )
            novas_parcelas.append(nova_parcela)        

        salvar_parcelas(novas_parcelas)
        sincronizar_parcelas_upload()

        # 🔹 Passa o empréstimo + parcelas simuladas para a próxima tela
        self.parent_callback({
            "id": emprestimo_id,
            "capital": dados["capital"],
            "meses": dados["meses"],
            "taxa": dados["taxa"],
            "juros": dados["total_juros"],
            "prestacao": float(dados.get("prestacao", 0)),
            "parcelas": novas_parcelas,
            "data_inicio": self.inp_data.date().toString("dd/MM/yyyy")
        })

        self.close()
