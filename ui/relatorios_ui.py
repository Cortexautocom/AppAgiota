# ui/relatorios_ui.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTableWidget, QHeaderView, QTableWidgetItem, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# Importações de dados
from parcelas import carregar_parcelas
from emprestimos import carregar_emprestimos
from clientes import carregar_clientes


class RelatoriosWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.setWindowTitle("Relatórios")

        self.layout_principal = QVBoxLayout(self)

        # 🔹 Título
        title = QLabel("📊 Relatórios")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        self.layout_principal.addWidget(title)

        # 🔹 Linha de filtros
        filtro_layout = QHBoxLayout()
        filtro_layout.setAlignment(Qt.AlignLeft)

        lbl_tipo = QLabel("Tipo:")
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems([
            "Parcelas em aberto",
            "Empréstimos (com parcelas em atraso)",
            "Empréstimos (com renegociação)",
            "Empréstimos (em dia)"
        ])
        
        lbl_mostrar = QLabel("Mostrar:")
        self.cb_mostrar = QComboBox()
        self.cb_mostrar.addItems([
            "Capital",
            "Juros",
            "Capital + Juros"
        ])
        self.cb_mostrar.setCurrentIndex(2)

        for cb in [self.cb_tipo, self.cb_mostrar]:
            cb.setStyleSheet("""
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
        filtro_layout.addWidget(lbl_mostrar)
        filtro_layout.addWidget(self.cb_mostrar)
        self.layout_principal.addLayout(filtro_layout)

        # 🔹 Tabela principal
        self.tabela = QTableWidget()
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)

        header = self.tabela.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        self.tabela.setSortingEnabled(True)

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
        self.layout_principal.addWidget(self.tabela)

        # 🔹 Totalizador e spacer
        self.tabela_total = None
        self.spacer_total = None
        self.totalizador_layout = None # Adicione esta linha

        # 🔹 Conexões e carregamento inicial
        self.cb_tipo.currentIndexChanged.connect(self.carregar_dados)
        self.cb_mostrar.currentIndexChanged.connect(self._ajusta_visibilidade_colunas)
        self.carregar_dados()

    def carregar_dados(self):
        """Popula a tabela e o totalizador com base no filtro selecionado."""
        self.tabela.setSortingEnabled(False)
        self.remover_widgets_dinamicos()

        filtro = self.cb_tipo.currentText()
        if filtro == "Parcelas em aberto":
            self._popula_tabela_parcelas_em_aberto()
        # outros filtros virão aqui...

        self.tabela.setSortingEnabled(True)
        self.tabela.sortItems(0, Qt.AscendingOrder)
    
    def remover_widgets_dinamicos(self):
        """Remove o totalizador, independentemente do tipo, e o spacer."""
        # Remove a tabela de totalização antiga, se existir
        if hasattr(self, "tabela_total") and self.tabela_total is not None:
            if self.tabela_total.parent():
                self.layout_principal.removeWidget(self.tabela_total)
            self.tabela_total.deleteLater()
            self.tabela_total = None

        # Remove o layout de totalização novo, se existir
        if hasattr(self, "totalizador_layout") and self.totalizador_layout is not None:
            while self.totalizador_layout.count():
                item = self.totalizador_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.layout_principal.removeItem(self.totalizador_layout)
            self.totalizador_layout = None
            
        # Remove o spacer
        if hasattr(self, "spacer_total") and self.spacer_total is not None:
            self.layout_principal.removeItem(self.spacer_total)
            self.spacer_total = None

    def _fmt_br(self, valor):
        """Formata valor float no padrão brasileiro R$ 0,00"""
        try:
            return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "R$ 0,00"

    def _popula_tabela_parcelas_em_aberto(self):
        """Carrega e exibe os dados das parcelas em aberto."""
        self.tabela.clearContents()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Nº", "Capital", "Juros", "Saldo"])

        todas_parcelas = carregar_parcelas()
        emprestimos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}
        clientes = {c[0]: c[1] for c in carregar_clientes()}

        dados = []
        total_capital = 0.0
        total_juros = 0.0

        for p in todas_parcelas:
            (
                _id, id_emp, num, _, _,
                _, _, _, _,
                valor_pago, _, _, _,
                _, _
            ) = p

            pago = valor_pago and str(valor_pago).strip() not in ("", "0", "R$ 0,00")
            if pago or id_emp not in emprestimos:
                continue

            emp = emprestimos[id_emp]
            id_cliente = emp[1]
            nome_cliente = clientes.get(id_cliente, "Desconhecido")

            try:
                capital_total_emp = float(emp[2]) if emp[2] else 0.0
                meses = int(emp[4]) if emp[4] else 1
                juros_total_emp = float(emp[6]) if emp[6] else 0.0
            except (ValueError, IndexError):
                capital_total_emp = 0.0
                meses = 1
                juros_total_emp = 0.0
            
            capital_parc = capital_total_emp / meses if meses > 0 else 0.0
            juros_parc = juros_total_emp / meses if meses > 0 else 0.0
            saldo_parc = capital_parc + juros_parc

            dados.append((nome_cliente, num, capital_parc, juros_parc, saldo_parc))
            total_capital += capital_parc
            total_juros += juros_parc

        

        self.tabela.setRowCount(len(dados))
        for i, (nome, num, cap, jur, sal) in enumerate(dados):
            nome_item = QTableWidgetItem(nome)
            nome_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 0, nome_item)
            
            num_item = QTableWidgetItem(str(num))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 1, num_item)
            
            cap_item = QTableWidgetItem(self._fmt_br(cap))
            cap_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 2, cap_item)
            
            jur_item = QTableWidgetItem(self._fmt_br(jur))
            jur_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 3, jur_item)
            
            sal_item = QTableWidgetItem(self._fmt_br(sal))
            sal_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 4, sal_item)

        self._cria_e_popula_totalizador(total_capital, total_juros)
        self._ajusta_visibilidade_colunas()

    def _cria_e_popula_totalizador(self, total_capital, total_juros):
        """Cria e adiciona o totalizador ao layout usando labels."""
        self.spacer_total = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout_principal.addSpacerItem(self.spacer_total)

        self.totalizador_layout = QHBoxLayout()
        self.totalizador_layout.setSpacing(0)

        fonte_negrito = QFont()
        fonte_negrito.setBold(True)
        
        lbl_total_titulo = QLabel("TOTAL:")
        lbl_total_titulo.setFont(fonte_negrito)
        lbl_total_titulo.setAlignment(Qt.AlignCenter)

        lbl_capital_total = QLabel(self._fmt_br(total_capital))
        lbl_capital_total.setFont(fonte_negrito)
        lbl_capital_total.setAlignment(Qt.AlignCenter)

        lbl_juros_total = QLabel(self._fmt_br(total_juros))
        lbl_juros_total.setFont(fonte_negrito)
        lbl_juros_total.setAlignment(Qt.AlignCenter)

        saldo_total = total_capital + total_juros
        lbl_saldo_total = QLabel(self._fmt_br(saldo_total))
        lbl_saldo_total.setFont(fonte_negrito)
        lbl_saldo_total.setAlignment(Qt.AlignCenter)

        self.totalizador_layout.addWidget(lbl_total_titulo, 1) # Proporção 1
        self.totalizador_layout.addStretch(1) # Espaçador para alinhamento
        self.totalizador_layout.addWidget(lbl_capital_total, 1) # Proporção 1
        self.totalizador_layout.addWidget(lbl_juros_total, 1) # Proporção 1
        self.totalizador_layout.addWidget(lbl_saldo_total, 1) # Proporção 1

        self.layout_principal.addLayout(self.totalizador_layout)

        # Guarda referências para poder atualizar depois
        self.lbl_capital_total = lbl_capital_total
        self.lbl_juros_total = lbl_juros_total
        self.lbl_saldo_total = lbl_saldo_total

        # Aplica visibilidade inicial
        self._atualiza_totalizador()

    def _atualiza_totalizador(self):
        """Atualiza a visibilidade dos rótulos do totalizador conforme o filtro 'Mostrar'."""
        mostrar = self.cb_mostrar.currentText()
        if hasattr(self, "lbl_capital_total"):
            self.lbl_capital_total.setHidden(mostrar == "Juros")
        if hasattr(self, "lbl_juros_total"):
            self.lbl_juros_total.setHidden(mostrar == "Capital")
        if hasattr(self, "lbl_saldo_total"):
            self.lbl_saldo_total.setHidden(mostrar != "Capital + Juros")

    def _ajusta_visibilidade_colunas(self):
        """Ajusta a visibilidade das colunas com base no ComboBox 'Mostrar'."""
        mostrar = self.cb_mostrar.currentText()
        if mostrar == "Capital":
            self.tabela.setColumnHidden(2, False)
            self.tabela.setColumnHidden(3, True)
            self.tabela.setColumnHidden(4, True)  # Oculta a coluna de saldo
        elif mostrar == "Juros":
            self.tabela.setColumnHidden(2, True)
            self.tabela.setColumnHidden(3, False)
            self.tabela.setColumnHidden(4, True)  # Oculta a coluna de saldo
        else:  # Capital + Juros
            self.tabela.setColumnHidden(2, False)
            self.tabela.setColumnHidden(3, False)
            self.tabela.setColumnHidden(4, False) # Exibe a coluna de saldo

        for col in range(5):
            if self.tabela_total:
                self.tabela_total.setColumnHidden(col, self.tabela.isColumnHidden(col))

        self._atualiza_totalizador()