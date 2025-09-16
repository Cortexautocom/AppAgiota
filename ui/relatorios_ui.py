# ui/relatorios_ui.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTableWidget, QHeaderView, QTableWidgetItem
)
from PySide6.QtCore import Qt


class RelatoriosWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.setWindowTitle("Relatórios")

        layout = QVBoxLayout(self)

        # 🔹 Título
        title = QLabel("📊 Relatórios")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)

        # 🔹 Linha de filtros
        filtro_layout = QHBoxLayout()
        filtro_layout.setAlignment(Qt.AlignLeft)

        # ComboBox principal - Tipo
        lbl_tipo = QLabel("Tipo:")
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems([
            "Parcelas em aberto",
            "Parcelas recebidas",
            "Empréstimos Ativos",
            "Empréstimos Arquivados",
            "Clientes x Dívida (Ranking)"
        ])
        self.cb_tipo.setStyleSheet("""
            QComboBox {
                background-color:#2c3446;
                color:white;
                padding:6px;
                border-radius:6px;
            }
            QComboBox QAbstractItemView {
                background-color:#2c3446;
                color:white;
                selection-background-color:#374157;
            }
        """)

        filtro_layout.addWidget(lbl_tipo)
        filtro_layout.addWidget(self.cb_tipo)

        # ComboBox secundário - Mostrar (Capital, Juros, Capital + Juros)
        lbl_mostrar = QLabel("Mostrar:")
        self.cb_mostrar = QComboBox()
        self.cb_mostrar.addItems([
            "Capital",
            "Juros",
            "Capital + Juros"
        ])
        self.cb_mostrar.setCurrentIndex(2)  # começa em "Capital + Juros"
        self.cb_mostrar.setStyleSheet(self.cb_tipo.styleSheet())

        filtro_layout.addWidget(lbl_mostrar)
        filtro_layout.addWidget(self.cb_mostrar)

        layout.addLayout(filtro_layout)

        # 🔹 Tabela principal (Cliente, Capital, Juros)
        self.tabela = QTableWidget(0, 3)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Capital", "Juros"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446;
                color: white;
                border: 1px solid #3a455b;
            }
            QHeaderView::section {
                background-color: #374157;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)
        layout.addWidget(self.tabela)

        # 🔹 Conexões (mudança instantânea)
        self.cb_tipo.currentIndexChanged.connect(self.carregar_dados)
        self.cb_mostrar.currentIndexChanged.connect(self.carregar_dados)

    def carregar_dados(self):
        """Decide qual relatório exibir conforme o filtro selecionado."""
        filtro = self.cb_tipo.currentText()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Nº", "Capital", "Juros"])


        if filtro == "Parcelas em aberto":
            self._mostrar_parcelas_em_aberto()
        elif filtro == "Parcelas recebidas":
            self._mostrar_parcelas_recebidas()
        elif filtro == "Empréstimos Ativos":
            self._mostrar_emprestimos_ativos()
        elif filtro == "Empréstimos Arquivados":
            self._mostrar_emprestimos_arquivados()
        elif filtro == "Clientes x Dívida (Ranking)":
            self._mostrar_ranking_clientes()

    # Métodos ainda a implementar
    def _mostrar_parcelas_em_aberto(self): pass
    def _mostrar_parcelas_recebidas(self): pass
    def _mostrar_emprestimos_ativos(self): pass
    def _mostrar_emprestimos_arquivados(self): pass
    def _mostrar_ranking_clientes(self): pass

    def _fmt_br(self, valor):
        """Formata valor float no padrão brasileiro R$ 0,00"""
        try:
            return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "R$ 0,00"



    def _mostrar_parcelas_em_aberto(self):
        """Mostra todas as parcelas em aberto (não pagas)."""
        from parcelas import carregar_parcelas
        from emprestimos import carregar_emprestimos
        from clientes import carregar_clientes
        from PySide6.QtWidgets import QTableWidgetItem
        from PySide6.QtGui import QFont

        # Carregar dados
        todas_parcelas = carregar_parcelas()
        emprestimos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}  # só ativos
        clientes = {c[0]: c[1] for c in carregar_clientes()}  # id_cliente → nome

        linhas = []
        total_capital = 0.0
        total_juros = 0.0

        for p in todas_parcelas:
            (
                _id, id_emp, num, valor, venc,
                juros, desconto, pg_principal, pg_juros,
                valor_pago, residual, data_pag, id_usuario
            ) = p

            if id_emp not in emprestimos:
                continue

            # em aberto se não pago ou residual > 0
            pago = bool(valor_pago and str(valor_pago).strip() not in ("", "0", "R$ 0,00"))
            if pago:
                continue

            emp = emprestimos[id_emp]
            id_cliente = emp[1]
            nome_cliente = clientes.get(id_cliente, "Desconhecido")

            # Verifica se a parcela já foi paga (não deveria cair aqui, mas deixamos a lógica genérica)
            pago = bool(valor_pago and str(valor_pago).strip() not in ("", "0", "R$ 0,00"))

            # Guardamos os dados para preencher depois
            linhas.append((nome_cliente, pg_principal, pg_juros, pago, emp, num))        
            

        # Monta a tabela (+1 linha em branco, +1 linha totalizadora)
        self.tabela.setRowCount(len(linhas) + 2)
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Nº", "Capital", "Juros"])


        for i, (nome, cap, jur, pago, emp, num) in enumerate(linhas):
            # 🔹 Se já foi paga → usa os valores do banco
            if pago:
                cap_fmt = self._fmt_br(cap)
                jur_fmt = self._fmt_br(jur)
            else:
                # 🔹 Se ainda não foi paga → recalcula como no botão ⚡
                try:
                    capital_total = float(emp[2]) if emp[2] else 0.0
                except:
                    capital_total = 0.0
                try:
                    meses = int(emp[4]) if emp[4] else 1
                except:
                    meses = 1
                try:
                    juros_total = float(emp[6]) if emp[6] else 0.0
                except:
                    juros_total = 0.0

                cap_fmt = self._fmt_br(capital_total / meses if meses > 0 else 0.0)
                jur_fmt = self._fmt_br(juros_total / meses if meses > 0 else 0.0)

            # Preenche células
            self.tabela.setItem(i, 0, QTableWidgetItem(nome))
            self.tabela.setItem(i, 1, QTableWidgetItem(str(num)))
            self.tabela.setItem(i, 2, QTableWidgetItem(cap_fmt))
            self.tabela.setItem(i, 3, QTableWidgetItem(jur_fmt))

        for row in range(self.tabela.rowCount()):
            for col in range(self.tabela.columnCount()):
                item = self.tabela.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

            # Acumula para totalizador
            try:
                total_capital += float(cap_fmt.replace("R$", "").replace(".", "").replace(",", "."))
            except:
                pass
            try:
                total_juros += float(jur_fmt.replace("R$", "").replace(".", "").replace(",", "."))
            except:
                pass

        # Linha em branco
        row_blank = len(linhas)
        for col in range(3):
            self.tabela.setItem(row_blank, col, QTableWidgetItem(""))

        # Linha totalizadora (em negrito)
        row_total = len(linhas) + 1
        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        item_total = QTableWidgetItem("TOTAL")
        item_total.setFont(fonte_negrito)
        item_total.setTextAlignment(Qt.AlignCenter)
        self.tabela.setItem(row_total, 0, item_total)

        # Coluna Nº em branco
        self.tabela.setItem(row_total, 1, QTableWidgetItem(""))

        cap_item = QTableWidgetItem(self._fmt_br(total_capital))
        cap_item.setFont(fonte_negrito)
        cap_item.setTextAlignment(Qt.AlignCenter)
        self.tabela.setItem(row_total, 2, cap_item)

        jur_item = QTableWidgetItem(self._fmt_br(total_juros))
        jur_item.setFont(fonte_negrito)
        jur_item.setTextAlignment(Qt.AlignCenter)
        self.tabela.setItem(row_total, 3, jur_item)

        # Ajusta colunas conforme filtro "Mostrar"
        mostrar = self.cb_mostrar.currentText()
        if mostrar == "Capital":
            self.tabela.setColumnHidden(2, True)   # esconde Juros
            self.tabela.setColumnHidden(1, False)
        elif mostrar == "Juros":
            self.tabela.setColumnHidden(1, True)   # esconde Capital
            self.tabela.setColumnHidden(2, False)
        else:  # Capital + Juros
            self.tabela.setColumnHidden(1, False)
            self.tabela.setColumnHidden(2, False)

