from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QHBoxLayout, QPushButton,
    QDateEdit, QTableWidget, QHeaderView, QCalendarWidget
)
from PySide6.QtCore import Qt, QDate


class RelatoriosWindow(QWidget):
    """Janela de Relatórios com sub-abas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.setWindowTitle("Relatórios")

        layout = QVBoxLayout(self)

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

        layout.addWidget(self.tabs)

    # ------------------------
    def _setup_previsao_tab(self):
        layout = QVBoxLayout(self.tab_previsao)

        # Linha de filtros (datas + combo + botão)
        filtro_layout = QHBoxLayout()

        # ===== Data Inicial =====
        self.data_inicial = QDateEdit()
        self.data_inicial.setDate(QDate.currentDate())
        self.data_inicial.setDisplayFormat("dd/MM/yyyy")
        self.data_inicial.setCalendarPopup(True)

        # 🔹 Criar calendário customizado para Data Inicial
        
        cal_inicial = QCalendarWidget()
        cal_inicial.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)  # 🔹 remove coluna da semana
        cal_inicial.setStyleSheet("""
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
        self.data_inicial.setCalendarWidget(cal_inicial)

        # ===== Data Final =====
        self.data_final = QDateEdit()
        self.data_final.setDate(QDate.currentDate())
        self.data_final.setDisplayFormat("dd/MM/yyyy")
        self.data_final.setCalendarPopup(True)

        # 🔹 Criar calendário customizado para Data Final (reaproveita o estilo)
        cal_final = QCalendarWidget()
        cal_final.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)  # 🔹 remove coluna da semana
        cal_final.setStyleSheet(cal_inicial.styleSheet())
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

        # ===== Tipo de previsão (novo seletor) =====
        from PySide6.QtWidgets import QComboBox
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(["Capital", "Juros", "Capital + Juros"])
        self.cb_tipo.setCurrentIndex(2)  # começa em "Capital + Juros"
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
                padding: 0px;
                margin: 0px;
            }
        """)

        # Adicionando widgets na ordem pedida
        filtro_layout.addWidget(QLabel("Data Inicial:"))
        filtro_layout.addWidget(self.data_inicial)
        filtro_layout.addWidget(QLabel("Data Final:"))
        filtro_layout.addWidget(self.data_final)
        filtro_layout.addWidget(QLabel("Mostrar:"))
        filtro_layout.addWidget(self.cb_tipo)
        filtro_layout.addStretch()
        filtro_layout.addWidget(btn_filtrar)

        layout.addLayout(filtro_layout)

        # ===== Tabela de resultados =====
        self.tabela_previsao = QTableWidget(0, 3)
        self.tabela_previsao.setHorizontalHeaderLabels(["Data", "Capital", "Juros"])
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

        # 🔹 Ação do combo: mostrar/ocultar colunas
        self.cb_tipo.currentIndexChanged.connect(self._toggle_columns)

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
