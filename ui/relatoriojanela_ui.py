from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QHeaderView, QTableWidgetItem, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from parcelas import carregar_parcelas
from emprestimos import carregar_emprestimos
from clientes import carregar_clientes

class RelatorioJanelaWindow(QWidget):
    """Janela independente para exibir relatórios selecionados."""
    def __init__(self, tipo, mostrar, parent=None):
        super().__init__(parent)

        # Configuração da janela
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setWindowTitle(f"📑 Relatório - {tipo}")
        self.setFixedSize(900, 600)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        self.layout_principal = QVBoxLayout(self)

        # Título
        lbl_title = QLabel(f"📑 {tipo}")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #9fb0c7; margin-bottom: 8px;")
        self.layout_principal.addWidget(lbl_title)

        # Tabela principal
        self.tabela = QTableWidget()
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
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
        self.layout_principal.addWidget(self.tabela)

        # Totalizador (adicionado depois)
        self.totalizador_layout = None

        # Chamar relatório
        if tipo == "Parcelas em aberto":
            self._mostrar_parcelas_em_aberto(mostrar)
        elif tipo == "Empréstimos (com parcelas em atraso)":
            self._mostrar_emprestimos_em_atraso()
        elif tipo == "Empréstimos (com renegociação)":
            self._mostrar_emprestimos_com_renegociacao()
        elif tipo == "Empréstimos ativos":
            self._mostrar_emprestimos_ativos()
        elif tipo == "Empréstimos inativos":
            self._mostrar_emprestimos_inativos()

    def _fmt_br(self, valor):
        """Formata valor float no padrão brasileiro R$ 0,00"""
        try:
            return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "R$ 0,00"

    def _mostrar_parcelas_em_aberto(self, mostrar):
        """Mostra todas as parcelas em aberto (não pagas)."""
        self.tabela.clearContents()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Nº", "Capital", "Juros", "Saldo"])

        todas_parcelas = carregar_parcelas()
        emprestimos_ativos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}
        clientes_dict = {c[0]: c[1] for c in carregar_clientes()}

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
            if pago or id_emp not in emprestimos_ativos:
                continue

            emp = emprestimos_ativos[id_emp]
            id_cliente = emp[1]
            nome_cliente = clientes_dict.get(id_cliente, "Desconhecido")

            try:
                capital_total_emp = float(emp[2]) if emp[2] else 0.0
                meses = int(emp[4]) if emp[4] else 1
                juros_total_emp = float(emp[6]) if emp[6] else 0.0
            except (ValueError, IndexError):
                capital_total_emp = 0.0
                meses = 1
                juros_total_emp = 0.0

            # Cálculo proporcional
            capital_parc = capital_total_emp / meses if meses > 0 else 0.0
            juros_base = juros_total_emp / meses if meses > 0 else 0.0

            juros_lancado = float(str(p[5]).replace("R$", "").replace(".", "").replace(",", ".") or 0) if p[5] else 0.0
            desconto_lancado = float(str(p[6]).replace("R$", "").replace(".", "").replace(",", ".") or 0) if p[6] else 0.0

            juros_parc = juros_base + juros_lancado - desconto_lancado
            saldo_parc = capital_parc + juros_parc

            dados.append((nome_cliente, num, capital_parc, juros_parc, saldo_parc))
            total_capital += capital_parc
            total_juros += juros_parc

        # Popular tabela
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
            jur_item.setForeground(QColor("#78ddff"))
            self.tabela.setItem(i, 3, jur_item)

            sal_item = QTableWidgetItem(self._fmt_br(sal))
            sal_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 4, sal_item)

        # Adicionar totalizador
        self._adicionar_totalizador(total_capital, total_juros)

    def _adicionar_totalizador(self, total_capital, total_juros):
        """Adiciona linha de totalização abaixo da tabela."""
        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        lbl_total = QLabel("TOTAL:")
        lbl_total.setFont(fonte_negrito)
        lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lbl_capital = QLabel(self._fmt_br(total_capital))
        lbl_capital.setFont(fonte_negrito)
        lbl_capital.setAlignment(Qt.AlignCenter)

        lbl_juros = QLabel(self._fmt_br(total_juros))
        lbl_juros.setFont(fonte_negrito)
        lbl_juros.setAlignment(Qt.AlignCenter)

        lbl_saldo = QLabel(self._fmt_br(total_capital + total_juros))
        lbl_saldo.setFont(fonte_negrito)
        lbl_saldo.setAlignment(Qt.AlignCenter)

        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout_principal.addSpacerItem(spacer)

        from PySide6.QtWidgets import QHBoxLayout
        total_layout = QHBoxLayout()
        total_layout.addWidget(lbl_total, 1)
        total_layout.addWidget(lbl_capital, 1)
        total_layout.addWidget(lbl_juros, 1)
        total_layout.addWidget(lbl_saldo, 1)

        self.layout_principal.addLayout(total_layout)
        self.totalizador_layout = total_layout


    def _mostrar_emprestimos_em_atraso(self):
        """Lista empréstimos que tenham ao menos 1 parcela vencida e não paga."""
        from datetime import datetime
        from parcelas import carregar_parcelas
        from emprestimos import carregar_emprestimos
        from clientes import carregar_clientes

        self.tabela.clearContents()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(2)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Total em atraso"])

        todas_parcelas = carregar_parcelas()
        emprestimos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}  # ativos
        clientes = {c[0]: c[1] for c in carregar_clientes()}

        hoje = datetime.today()
        dados = {}
        total_geral = 0.0

        for p in todas_parcelas:
            (
                _id, id_emp, num, valor, venc,
                juros, desconto, pg_principal, pg_juros,
                valor_pago, residual, data_pag, _id_usuario,
                data_prevista, comentario
            ) = p

            if id_emp not in emprestimos:
                continue

            # Ignora já pagas
            if valor_pago and str(valor_pago).strip() not in ("", "0", "R$ 0,00"):
                continue

            # Converte datas
            venc_dt = None
            try:
                if venc:
                    venc_dt = datetime.strptime(venc, "%d/%m/%Y")
            except:
                pass

            if not venc_dt or hoje <= venc_dt:
                continue  # não venceu ainda

            # Valor da parcela (saldo se houver, senão valor cheio)
            try:
                valor_float = 0.0
                if residual and str(residual).strip():
                    valor_float = float(str(residual).replace("R$", "").replace(".", "").replace(",", "."))
                elif valor and str(valor).strip():
                    valor_float = float(str(valor).replace("R$", "").replace(".", "").replace(",", "."))
            except:
                valor_float = 0.0

            nome_cliente = clientes.get(emprestimos[id_emp][1], "Desconhecido")
            dados[nome_cliente] = dados.get(nome_cliente, 0.0) + valor_float
            total_geral += valor_float

        # Popular tabela
        self.tabela.setRowCount(len(dados))
        for i, (nome, total) in enumerate(dados.items()):
            nome_item = QTableWidgetItem(nome)
            nome_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 0, nome_item)

            total_item = QTableWidgetItem(self._fmt_br(total))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 1, total_item)

        # Adicionar totalizador
        self._adicionar_totalizador_atraso(total_geral)

    def _adicionar_totalizador_atraso(self, total_geral):
        """Adiciona linha de totalização abaixo da tabela de atrasos."""
        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        lbl_total = QLabel("TOTAL EM ATRASO:")
        lbl_total.setFont(fonte_negrito)
        lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lbl_valor = QLabel(self._fmt_br(total_geral))
        lbl_valor.setFont(fonte_negrito)
        lbl_valor.setAlignment(Qt.AlignCenter)

        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout_principal.addSpacerItem(spacer)

        from PySide6.QtWidgets import QHBoxLayout
        total_layout = QHBoxLayout()
        total_layout.addWidget(lbl_total, 2)
        total_layout.addWidget(lbl_valor, 1)

        self.layout_principal.addLayout(total_layout)
        self.totalizador_layout = total_layout

    def _mostrar_emprestimos_com_renegociacao(self):
        """Lista empréstimos ativos que possuem renegociação (data prevista futura ou atual)."""
        from datetime import datetime
        from parcelas import carregar_parcelas
        from emprestimos import carregar_emprestimos
        from clientes import carregar_clientes

        self.tabela.clearContents()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(2)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Total em renegociação"])

        todas_parcelas = carregar_parcelas()
        emprestimos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}  # ativos
        clientes = {c[0]: c[1] for c in carregar_clientes()}

        hoje = datetime.today()
        dados = {}
        total_geral = 0.0

        for p in todas_parcelas:
            (
                _id, id_emp, num, valor, venc,
                juros, desconto, pg_principal, pg_juros,
                valor_pago, residual, data_pag, _id_usuario,
                data_prevista, comentario
            ) = p

            if id_emp not in emprestimos:
                continue
            if not data_prevista:
                continue

            try:
                prev_dt = datetime.strptime(data_prevista, "%d/%m/%Y")
            except:
                continue

            if prev_dt >= hoje:  # renegociação válida
                try:
                    valor_float = 0.0
                    if residual and str(residual).strip():
                        valor_float = float(str(residual).replace("R$", "").replace(".", "").replace(",", "."))
                    elif valor and str(valor).strip():
                        valor_float = float(str(valor).replace("R$", "").replace(".", "").replace(",", "."))
                except:
                    valor_float = 0.0

                nome_cliente = clientes.get(emprestimos[id_emp][1], "Desconhecido")
                dados[nome_cliente] = dados.get(nome_cliente, 0.0) + valor_float
                total_geral += valor_float

        # Popular tabela
        self.tabela.setRowCount(len(dados))
        for i, (nome, total) in enumerate(dados.items()):
            nome_item = QTableWidgetItem(nome)
            nome_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 0, nome_item)

            total_item = QTableWidgetItem(self._fmt_br(total))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 1, total_item)

        # Adicionar totalizador
        self._adicionar_totalizador_reneg(total_geral)

    def _adicionar_totalizador_reneg(self, total_geral):
        """Adiciona linha de totalização abaixo da tabela de renegociação."""
        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        lbl_total = QLabel("TOTAL EM RENEGOCIAÇÃO:")
        lbl_total.setFont(fonte_negrito)
        lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lbl_valor = QLabel(self._fmt_br(total_geral))
        lbl_valor.setFont(fonte_negrito)
        lbl_valor.setAlignment(Qt.AlignCenter)

        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout_principal.addSpacerItem(spacer)

        from PySide6.QtWidgets import QHBoxLayout
        total_layout = QHBoxLayout()
        total_layout.addWidget(lbl_total, 2)
        total_layout.addWidget(lbl_valor, 1)

        self.layout_principal.addLayout(total_layout)
        self.totalizador_layout = total_layout

    def _mostrar_emprestimos_ativos(self):
        """Lista todos os empréstimos marcados como ativos (sim)."""
        from emprestimos import carregar_emprestimos
        from clientes import carregar_clientes

        self.tabela.clearContents()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Capital", "Juros", "Total"])

        emprestimos = [e for e in carregar_emprestimos() if e[9] == "sim"]
        clientes = {c[0]: c[1] for c in carregar_clientes()}

        total_capital = 0.0
        total_juros = 0.0
        total_geral = 0.0

        self.tabela.setRowCount(len(emprestimos))
        for i, emp in enumerate(emprestimos):
            nome_cliente = clientes.get(emp[1], "Desconhecido")

            try:
                capital = float(emp[2] or 0)
                juros = float(emp[6] or 0)
            except:
                capital = juros = 0.0

            total = capital + juros

            total_capital += capital
            total_juros += juros
            total_geral += total

            self.tabela.setItem(i, 0, QTableWidgetItem(nome_cliente))
            self.tabela.setItem(i, 1, QTableWidgetItem(self._fmt_br(capital)))
            self.tabela.setItem(i, 2, QTableWidgetItem(self._fmt_br(juros)))
            self.tabela.setItem(i, 3, QTableWidgetItem(self._fmt_br(total)))

            for col in range(4):
                item = self.tabela.item(i, col)
                item.setTextAlignment(Qt.AlignCenter)

        self._adicionar_totalizador_emp("ATIVOS", total_capital, total_juros, total_geral)

    def _mostrar_emprestimos_inativos(self):
        """Lista todos os empréstimos marcados como inativos (não)."""
        from emprestimos import carregar_emprestimos
        from clientes import carregar_clientes

        self.tabela.clearContents()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Capital", "Juros", "Total"])

        emprestimos = [e for e in carregar_emprestimos() if e[9] == "não"]
        clientes = {c[0]: c[1] for c in carregar_clientes()}

        total_capital = 0.0
        total_juros = 0.0
        total_geral = 0.0

        self.tabela.setRowCount(len(emprestimos))
        for i, emp in enumerate(emprestimos):
            nome_cliente = clientes.get(emp[1], "Desconhecido")

            try:
                capital = float(emp[2] or 0)
                juros = float(emp[6] or 0)
            except:
                capital = juros = 0.0

            total = capital + juros

            total_capital += capital
            total_juros += juros
            total_geral += total

            self.tabela.setItem(i, 0, QTableWidgetItem(nome_cliente))
            self.tabela.setItem(i, 1, QTableWidgetItem(self._fmt_br(capital)))
            self.tabela.setItem(i, 2, QTableWidgetItem(self._fmt_br(juros)))
            self.tabela.setItem(i, 3, QTableWidgetItem(self._fmt_br(total)))

            for col in range(4):
                item = self.tabela.item(i, col)
                item.setTextAlignment(Qt.AlignCenter)

        self._adicionar_totalizador_emp("INATIVOS", total_capital, total_juros, total_geral)

    def _adicionar_totalizador_emp(self, label, total_capital, total_juros, total_geral):
        """Adiciona totalizador para relatórios de empréstimos ativos/inativos."""
        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        lbl_total = QLabel(f"TOTAL ({label}):")
        lbl_total.setFont(fonte_negrito)
        lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lbl_capital = QLabel(self._fmt_br(total_capital))
        lbl_capital.setFont(fonte_negrito)
        lbl_capital.setAlignment(Qt.AlignCenter)

        lbl_juros = QLabel(self._fmt_br(total_juros))
        lbl_juros.setFont(fonte_negrito)
        lbl_juros.setAlignment(Qt.AlignCenter)

        lbl_saldo = QLabel(self._fmt_br(total_geral))
        lbl_saldo.setFont(fonte_negrito)
        lbl_saldo.setAlignment(Qt.AlignCenter)

        spacer = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout_principal.addSpacerItem(spacer)

        from PySide6.QtWidgets import QHBoxLayout
        total_layout = QHBoxLayout()
        total_layout.addWidget(lbl_total, 2)
        total_layout.addWidget(lbl_capital, 1)
        total_layout.addWidget(lbl_juros, 1)
        total_layout.addWidget(lbl_saldo, 1)

        self.layout_principal.addLayout(total_layout)
        self.totalizador_layout = total_layout
