# ui/relatorios_ui.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTableWidget, QHeaderView, QTableWidgetItem, QSpacerItem, QSizePolicy
)

from parcelas import carregar_parcelas
from emprestimos import carregar_emprestimos
from clientes import carregar_clientes
from PySide6.QtGui import QFont

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
            "Empréstimos (com parcelas em atraso)",
            "Empréstimos (com renegociação)",
            "Empréstimos (em dia)"
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

        header = self.tabela.horizontalHeader()
        header.setSectionsClickable(True)      # permite clicar no título
        header.setSortIndicatorShown(True)     # mostra a setinha
        self.tabela.setSortingEnabled(True)    # habilita ordenação

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
        # 🔹 Define padrão inicial: "Parcelas em aberto" + "Capital + Juros"
        self.cb_tipo.setCurrentText("Parcelas em aberto")
        self.cb_mostrar.setCurrentText("Capital + Juros")
        self.carregar_dados()


    def carregar_dados(self):
        """Decide qual relatório exibir conforme o filtro selecionado."""
        filtro = self.cb_tipo.currentText()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Nº", "Capital", "Juros"])

        if filtro == "Parcelas em aberto":
            self._mostrar_parcelas_em_aberto()
        elif filtro == "Empréstimos (com parcelas em atraso)":
            # será implementado depois
            pass
        elif filtro == "Empréstimos (com renegociação)":
            pass
        elif filtro == "Empréstimos (em dia)":
            pass

        # 🔹 Ordena sempre por Cliente
        self.tabela.sortItems(0, Qt.AscendingOrder)


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
        
        # Desativa temporariamente a ordenação para permitir a adição da linha de total
        self.tabela.setSortingEnabled(False) 

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
                valor_pago, residual, data_pag, id_usuario,
                data_prevista, comentario
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
        
        # Ajustado para acomodar apenas a linha de total
        self.tabela.setRowCount(len(linhas))
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

            # Preenche células e define o alinhamento central
            nome_item = QTableWidgetItem(nome)
            nome_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 0, nome_item)

            num_item = QTableWidgetItem(str(num))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 1, num_item)

            cap_item = QTableWidgetItem(cap_fmt)
            cap_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 2, cap_item)

            jur_item = QTableWidgetItem(jur_fmt)
            jur_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 3, jur_item)

            # Acumula para totalizador (essa parte precisa estar dentro do loop)
            try:
                total_capital += float(cap_fmt.replace("R$", "").replace(".", "").replace(",", "."))
            except:
                pass
            try:
                total_juros += float(jur_fmt.replace("R$", "").replace(".", "").replace(",", "."))
            except:
                pass
        
        # 🔹 Espaço em branco entre a tabela e o totalizador        
        self.layout().addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # 🔹 Cria uma tabela separada só para o totalizador
        self.tabela_total = QTableWidget(1, 4)
        self.tabela_total.horizontalHeader().setVisible(False)
        self.tabela_total.verticalHeader().setVisible(False)
        self.tabela_total.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela_total.setFixedHeight(40)
        self.tabela_total.setStyleSheet(self.tabela.styleSheet())

        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        item_total = QTableWidgetItem("TOTAL")
        item_total.setFont(fonte_negrito)
        item_total.setTextAlignment(Qt.AlignCenter)
        self.tabela_total.setItem(0, 0, item_total)

        self.tabela_total.setItem(0, 1, QTableWidgetItem(""))

        cap_item = QTableWidgetItem(self._fmt_br(total_capital))
        cap_item.setFont(fonte_negrito)
        cap_item.setTextAlignment(Qt.AlignCenter)
        self.tabela_total.setItem(0, 2, cap_item)

        jur_item = QTableWidgetItem(self._fmt_br(total_juros))
        jur_item.setFont(fonte_negrito)
        jur_item.setTextAlignment(Qt.AlignCenter)
        self.tabela_total.setItem(0, 3, jur_item)

        # Adiciona a tabelinha de total abaixo da principal
        self.layout().addWidget(self.tabela_total)

        
        # Ajusta colunas conforme filtro "Mostrar"
        mostrar = self.cb_mostrar.currentText()
        if mostrar == "Capital":
            # Cliente (0) e Nº (1) sempre visíveis
            self.tabela.setColumnHidden(2, False)  # Capital
            self.tabela.setColumnHidden(3, True)   # Juros
        elif mostrar == "Juros":
            self.tabela.setColumnHidden(2, True)   # Capital
            self.tabela.setColumnHidden(3, False)  # Juros
        else:  # Capital + Juros
            self.tabela.setColumnHidden(2, False)
            self.tabela.setColumnHidden(3, False)
        
        self.layout().addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Reativa a ordenação após o preenchimento total e aplica a ordenação inicial
        self.tabela.setSortingEnabled(True)
        self.tabela.sortItems(0, Qt.AscendingOrder)