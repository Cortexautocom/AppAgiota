from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QHBoxLayout, QPushButton,
    QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView, QCalendarWidget, QComboBox
)
from PySide6.QtCore import Qt, QDate

ultima_pesquisa = {
    "data_ini": None,
    "data_fim": None,
    "tipo": None,
    "modo": None
}


class RelatoriosWindow(QWidget):
    """Janela de Relatórios com sub-abas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.setWindowTitle("Relatórios")

        layout = QVBoxLayout(self)
        self.ultima_data_ini = None
        self.ultima_data_fim = None
        self.ultimo_tipo = None
        self.ultimo_modo = None

        # Título
        title = QLabel("📊 Relatórios")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)

        # Abas principais
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3a455b; }
            QTabBar::tab {
                background: #2c3446; color: white; padding: 8px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background: #374157; }
            QTabBar::tab:hover { background: #3f4b63; }
        """)

        # Aba 1: Previsão de Recebimentos
        self.tab_previsao = QWidget()
        self._setup_previsao_tab()
        self.tabs.addTab(self.tab_previsao, "📅 Previsão de Recebimentos")

        # Aba 2: Resumo Consolidado
        self.tab_resumo = QWidget()
        self._setup_resumo_tab()
        self.tabs.addTab(self.tab_resumo, "📈 Resumo Consolidado")

        # Aba 3: Relatório por Cliente
        self.tab_clientes = QWidget()
        self._setup_clientes_tab()
        self.tabs.addTab(self.tab_clientes, "👥 Relatório por Cliente")

        self.ultima_data_ini = None
        self.ultima_data_fim = None
        self.ultimo_tipo = None
        self.ultimo_modo = None

        layout.addWidget(self.tabs)

    # ------------------------
    def _setup_previsao_tab(self):
        layout = QVBoxLayout(self.tab_previsao)

        # Linha de filtros (datas + combos + botão)
        filtro_layout = QHBoxLayout()

        # ===== Data Inicial =====        

        self.data_inicial = QDateEdit()
        self.data_inicial.setDate(QDate.currentDate())
        self.data_inicial.setDisplayFormat("dd/MM/yyyy")
        self.data_inicial.setCalendarPopup(True)
        self.data_inicial.setStyleSheet("""
            QDateEdit {
                background-color:#2c3446;
                color:white;
                padding:6px;
                border-radius:6px;
                selection-background-color:#3498db;
                selection-color:white;
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

        # 🔹 Aplicar calendário customizado (sem coluna de semanas)
        cal_inicio = QCalendarWidget()
        cal_inicio.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        cal_inicio.setStyleSheet("""
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
        self.data_inicial.setCalendarWidget(cal_inicio)


        # ===== Data Final =====    

        self.data_final = QDateEdit()
        self.data_final.setDate(QDate.currentDate())
        self.data_final.setDisplayFormat("dd/MM/yyyy")
        self.data_final.setCalendarPopup(True)
        self.data_final.setStyleSheet("""
            QDateEdit {
                background-color:#2c3446;
                color:white;
                padding:6px;
                border-radius:6px;
                selection-background-color:#3498db;
                selection-color:white;
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

        # 🔹 Aplicar calendário customizado (sem coluna de semanas)
        cal_fim = QCalendarWidget()
        cal_fim.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        cal_fim.setStyleSheet("""
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
        self.data_final.setCalendarWidget(cal_fim)


        # 🔹 Criar calendário customizado para Data Final (reaproveita o estilo)
        cal_final = QCalendarWidget()
        cal_final.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)  # 🔹 remove coluna da semana
        cal_final.setStyleSheet(cal_inicio.styleSheet())
        self.data_final.setCalendarWidget(cal_final)

        # 🔹 Estilo dos QDateEdit
        dateedit_style = """
            QDateEdit {
                background-color:#2c3446;
                color:white;
                padding:6px;
                border-radius:6px;
                border: 1px solid #3a455b;
            }
            QAbstractSpinBox {
                border: none;
            }
        """
        self.data_inicial.setStyleSheet(dateedit_style)
        self.data_final.setStyleSheet(dateedit_style)

        # ===== Botão Gerar Previsão =====
        btn_filtrar = QPushButton("🔎 Gerar Previsão")
        btn_filtrar.setStyleSheet("""
            QPushButton {
                background-color:#3498db; color:white;
                padding:6px; border-radius:6px;
            }
            QPushButton:hover { background-color:#2980b9; }
        """)

        btn_filtrar.clicked.connect(self.gerar_previsao)

        # ===== Filtro "Mostrar" (Capital, Juros, Capital + Juros) =====        
        self.cb_mostrar = QComboBox()
        self.cb_mostrar.addItems(["Capital", "Juros", "Capital + Juros"])
        self.cb_mostrar.setCurrentIndex(2)  # começa em "Capital + Juros"
        self.cb_mostrar.setStyleSheet("""
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
                padding: 0px;
                margin: 0px;
            }
        """)

        # ===== Filtro "Relatório" (modo de exibição) =====
        self.cb_modo = QComboBox()
        self.cb_modo.addItems(["Por cliente", "Por parcela"])
        self.cb_modo.setCurrentIndex(0)  # começa em "Por cliente"
        self.cb_modo.setStyleSheet(self.cb_mostrar.styleSheet())

        # 1 - Mostrar
        filtro_layout.addWidget(QLabel("Mostrar:"))
        filtro_layout.addWidget(self.cb_mostrar)

        # 2 - Relatório
        filtro_layout.addWidget(QLabel("Relatório:"))
        filtro_layout.addWidget(self.cb_modo)

        # 3 - Datas
        filtro_layout.addWidget(QLabel("Data Inicial:"))
        filtro_layout.addWidget(self.data_inicial)
        filtro_layout.addWidget(QLabel("Data Final:"))
        filtro_layout.addWidget(self.data_final)

        # 4 - Botão
        filtro_layout.addStretch()
        filtro_layout.addWidget(btn_filtrar)

        # 🔹 Largura fixa para alinhar
        self.cb_mostrar.setFixedWidth(130)
        self.cb_modo.setFixedWidth(130)

        layout.addLayout(filtro_layout)


        # ===== Tabela de resultados =====
        # Agora com 4 colunas (Cliente + Data + Capital + Juros)
        self.tabela_previsao = QTableWidget(0, 4)
        self.tabela_previsao.setHorizontalHeaderLabels(["Cliente", "Data", "Capital", "Juros"])
        self.tabela_previsao.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 🔹 Estilo do cabeçalho
        header = self.tabela_previsao.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #374157;
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

        layout.addWidget(self.tabela_previsao)

        if self.ultima_data_ini and self.ultima_data_fim:
            self.gerar_previsao()

        # 🔹 Ação do combo: mostrar/ocultar colunas
        self.cb_mostrar.currentIndexChanged.connect(self._toggle_columns)

        if ultima_pesquisa["data_ini"] and ultima_pesquisa["data_fim"]:
            # restaurar filtros na tela
            self.data_inicial.setDate(QDate.fromString(ultima_pesquisa["data_ini"], "dd/MM/yyyy"))
            self.data_final.setDate(QDate.fromString(ultima_pesquisa["data_fim"], "dd/MM/yyyy"))
            self.cb_tipo.setCurrentText(ultima_pesquisa["tipo"])
            self.cb_modo.setCurrentText(ultima_pesquisa["modo"])

            # gerar relatório com os filtros salvos
            self.gerar_previsao()

    # ------------------------
    def _toggle_columns(self, index):
        """Mostra/oculta colunas de acordo com a seleção no combo"""
        if index == 0:  # Capital
            self.tabela_previsao.setColumnHidden(1, False)  # mostra Capital
            self.tabela_previsao.setColumnHidden(2, True)   # esconde Juros
        elif index == 1:  # Juros
            self.tabela_previsao.setColumnHidden(1, True)
            self.tabela_previsao.setColumnHidden(2, False)
        else:  # Capital + Juros
            self.tabela_previsao.setColumnHidden(1, False)
            self.tabela_previsao.setColumnHidden(2, False)

    # ------------------------
    def _setup_resumo_tab(self):
        layout = QVBoxLayout(self.tab_resumo)

        lbl = QLabel("📈 Resumo Consolidado")
        lbl.setStyleSheet("font-size:16px; font-weight:bold; color:#9fb0c7;")
        layout.addWidget(lbl)

        # Aqui futuramente podemos mostrar números grandes
        self.lbl_capital = QLabel("Capital na rua: R$ 0,00")
        self.lbl_capital.setStyleSheet("font-size:14px; color:white; margin:5px;")
        layout.addWidget(self.lbl_capital)

        self.lbl_alavancagem = QLabel("Alavancagem (total a receber): R$ 0,00")
        self.lbl_alavancagem.setStyleSheet("font-size:14px; color:white; margin:5px;")
        layout.addWidget(self.lbl_alavancagem)

    # ------------------------
    def _setup_clientes_tab(self):
        layout = QVBoxLayout(self.tab_clientes)

        # Tabela de relatório por cliente
        self.tabela_clientes = QTableWidget(0, 7)
        self.tabela_clientes.setHorizontalHeaderLabels([
            "Cliente", "Data Inicial", "Data Final",
            "Capital Pago", "Parcelas Totais",
            "Parcelas Pagas", "Parcelas Restantes"
        ])
        self.tabela_clientes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.tabela_clientes)

    def gerar_previsao(self):
        """Gera o relatório de previsão de recebimentos conforme filtros."""
        from parcelas import carregar_parcelas_por_emprestimo
        from emprestimos import carregar_emprestimos
        from clientes import carregar_clientes
        from datetime import datetime
        from PySide6.QtWidgets import QTableWidgetItem

        # limpar tabela
        self.tabela_previsao.setRowCount(0)

        # pegar filtros
        data_ini = self.data_inicial.date().toString("dd/MM/yyyy")
        data_fim = self.data_final.date().toString("dd/MM/yyyy")
        dt_ini = datetime.strptime(data_ini, "%d/%m/%Y")
        dt_fim = datetime.strptime(data_fim, "%d/%m/%Y")

        mostrar = self.cb_mostrar.currentText()
        modo = self.cb_modo.currentText()

        # 🔹 salvar como última pesquisa
        ultima_pesquisa["data_ini"] = data_ini
        ultima_pesquisa["data_fim"] = data_fim
        ultima_pesquisa["mostrar"] = mostrar
        ultima_pesquisa["modo"] = modo

        # carregar dados brutos
        emprestimos = carregar_emprestimos()
        clientes = {c[0]: c[1] for c in carregar_clientes()}  # dict id_cliente → nome

        linhas = []

        for emp in emprestimos:
            emp_id, id_cliente = emp[0], emp[1]
            nome_cliente = clientes.get(id_cliente, "Desconhecido")
            parcelas = carregar_parcelas_por_emprestimo(emp_id)

            for p in parcelas:
                (
                    _id, _id_emp, num, valor, venc,
                    juros, desconto, pg_principal, pg_juros,
                    valor_pago, residual, data_pag, _id_usuario
                ) = p

                if not venc:
                    continue

                try:
                    dt_venc = datetime.strptime(venc, "%d/%m/%Y")
                except:
                    continue

                if dt_venc < dt_ini or dt_venc > dt_fim:
                    continue

                # converter valores
                val_capital = 0.0
                val_juros = 0.0
                try:
                    v = float(str(valor).replace("R$", "").replace(".", "").replace(",", "."))
                    val_capital = v
                except:
                    pass
                try:
                    j = float(str(juros).replace("R$", "").replace(".", "").replace(",", "."))
                    val_juros = j
                except:
                    pass

                linhas.append({
                    "cliente": nome_cliente,
                    "data": venc,
                    "capital": val_capital,
                    "juros": val_juros
                })

        # gerar tabela conforme modo
        if modo == "Por parcela":
            for linha in linhas:
                row = self.tabela_previsao.rowCount()
                self.tabela_previsao.insertRow(row)
                self.tabela_previsao.setItem(row, 0, QTableWidgetItem(linha["cliente"]))
                self.tabela_previsao.setItem(row, 1, QTableWidgetItem(linha["data"]))

                if mostrar in ["Capital", "Capital + Juros"]:
                    self.tabela_previsao.setItem(
                        row, 2,
                        QTableWidgetItem(f"R$ {linha['capital']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    )
                else:
                    self.tabela_previsao.setItem(row, 2, QTableWidgetItem(""))

                if mostrar in ["Juros", "Capital + Juros"]:
                    self.tabela_previsao.setItem(
                        row, 3,
                        QTableWidgetItem(f"R$ {linha['juros']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    )
                else:
                    self.tabela_previsao.setItem(row, 3, QTableWidgetItem(""))

        else:  # Por cliente
            consol = {}
            for linha in linhas:
                key = linha["cliente"]
                if key not in consol:
                    consol[key] = {"capital": 0.0, "juros": 0.0}
                consol[key]["capital"] += linha["capital"]
                consol[key]["juros"] += linha["juros"]

            for cliente, vals in consol.items():
                row = self.tabela_previsao.rowCount()
                self.tabela_previsao.insertRow(row)
                self.tabela_previsao.setItem(row, 0, QTableWidgetItem(cliente))
                self.tabela_previsao.setItem(row, 1, QTableWidgetItem("-"))

                if mostrar in ["Capital", "Capital + Juros"]:
                    self.tabela_previsao.setItem(
                        row, 2,
                        QTableWidgetItem(f"R$ {vals['capital']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    )
                else:
                    self.tabela_previsao.setItem(row, 2, QTableWidgetItem(""))

                if mostrar in ["Juros", "Capital + Juros"]:
                    self.tabela_previsao.setItem(
                        row, 3,
                        QTableWidgetItem(f"R$ {vals['juros']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    )
                else:
                    self.tabela_previsao.setItem(row, 3, QTableWidgetItem(""))
