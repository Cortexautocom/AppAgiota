# ui/relatorios_ui.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QTableWidget, QHeaderView, QTableWidgetItem, QSpacerItem, QSizePolicy, QPushButton, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtCore import Qt
from datetime import datetime
from PySide6.QtPrintSupport import QPrinter
import json, os, webbrowser
#from reportlab.lib.pagesizes import A4
#from reportlab.pdfgen import canvas

# Importações de dados
from parcelas import carregar_parcelas
from emprestimos import carregar_emprestimos
from clientes import carregar_clientes
from config import get_local_db_path


class RelatoriosWindow(QWidget):
    ultima_escolha_tipo = None   # 🔹 guarda última escolha de relatório
    ultima_escolha_mostrar = None
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
            "Empréstimos ativos",
            "Empréstimos inativos",
            "Todos os empréstimos (valor em aberto)"
        ])
        filtro_layout.addWidget(lbl_tipo)
        filtro_layout.addWidget(self.cb_tipo)        

        # Botão Gerar em nova janela
        self.btn_gerar = QPushButton("📑 Gerar")
        self.btn_gerar.setStyleSheet("""
            QPushButton {
                background-color:#3498db; color:white;
                padding:6px 12px; border-radius:6px;
                font-weight:bold;
            }
            QPushButton:hover { background-color:#2980b9; }
        """)
        self.btn_gerar.clicked.connect(self.abrir_em_nova_janela)
        filtro_layout.addWidget(self.btn_gerar)

        self.layout_principal.addLayout(filtro_layout)

        # 🔹 Tabela fixa de "Empréstimos em atraso"
        self.tabela = QTableWidget()
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446;
                color: white;
                border: 1px solid #3a455b;
                selection-background-color: transparent;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #374157;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: transparent;
                color: white;
                border: 1px solid #3498db;
            }
        """)
        self.layout_principal.addWidget(self.tabela)

        # Carregar relatório em atraso automaticamente
        self._popula_tabela_emprestimos_em_atraso()

        # Habilitar duplo clique para abrir parcelas
        self.tabela.cellDoubleClicked.connect(self._abrir_parcelas_do_emprestimo)


    def carregar_dados(self):
        RelatoriosWindow.ultima_escolha_tipo = self.cb_tipo.currentText()
        RelatoriosWindow.ultima_escolha_mostrar = self.cb_mostrar.currentText()
        
        self.tabela.setSortingEnabled(False)
        self.remover_widgets_dinamicos()

        filtro = self.cb_tipo.currentText()

        # 🔹 controla visibilidade do filtro "Mostrar"
        if filtro == "Empréstimos (com parcelas em atraso)":
            self.cb_mostrar.setEnabled(False)   # ou use self.cb_mostrar.setVisible(False)
        else:
            self.cb_mostrar.setEnabled(True)

        if filtro == "Parcelas em aberto":
            self._popula_tabela_parcelas_em_aberto()
        elif filtro == "Empréstimos (com parcelas em atraso)":
            self._popula_tabela_emprestimos_em_atraso()
        elif filtro == "Empréstimos (com renegociação)":
            self._popula_tabela_emprestimos_com_renegociacao()
            self.cb_mostrar.setEnabled(False)
        elif filtro == "Empréstimos (em dia)":
            self._popula_tabela_emprestimos_em_dia()
            self.cb_mostrar.setEnabled(False)
        else:
            self.cb_mostrar.setEnabled(True)
        
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
            
            # 🔹 cálculo base (fictício)
            capital_parc = capital_total_emp / meses if meses > 0 else 0.0
            juros_base = juros_total_emp / meses if meses > 0 else 0.0

            # 🔹 pega lançamentos feitos pelo usuário
            def _f(x):
                try:
                    return float(str(x).replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)
                except:
                    return 0.0

            juros_lancado = _f(p[5])   # coluna Juros da parcela
            desconto_lancado = _f(p[6])  # coluna Desconto da parcela

            juros_parc = juros_base + juros_lancado - desconto_lancado
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
        filtro = self.cb_tipo.currentText()
        if filtro == "Empréstimos (com parcelas em atraso)":
            return  # 🔹 não precisa ajustar nesse relatório

        mostrar = self.cb_mostrar.currentText()
        if hasattr(self, "lbl_capital_total"):
            self.lbl_capital_total.setHidden(mostrar == "Juros")
        if hasattr(self, "lbl_juros_total"):
            self.lbl_juros_total.setHidden(mostrar == "Capital")
        if hasattr(self, "lbl_saldo_total"):
            self.lbl_saldo_total.setHidden(mostrar != "Capital + Juros")

    def _ajusta_visibilidade_colunas(self):
        """Ajusta a visibilidade das colunas com base no ComboBox 'Mostrar'."""
        filtro = self.cb_tipo.currentText()
        if filtro == "Empréstimos (com parcelas em atraso)":
            return  # 🔹 não faz nada nesse relatório

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
            self.tabela.setColumnHidden(4, False)  # Exibe a coluna de saldo

        for col in range(5):
            if self.tabela_total:
                self.tabela_total.setColumnHidden(col, self.tabela.isColumnHidden(col))

        self._atualiza_totalizador()

    def _popula_tabela_emprestimos_em_atraso(self):
        """Carrega empréstimos que tenham ao menos 1 parcela em atraso sem renegociação,
        ou com data prevista (renegociação) já vencida.
        Mostra Cliente e Total em atraso, permitindo abrir a tela de parcelas com duplo clique."""
        from datetime import datetime

        self.tabela.clearContents()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(3)  # 🔹 Cliente | Total em atraso | id oculto
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Total em atraso", "id_emprestimo"])
        self.tabela.setColumnHidden(2, True)  # 🔹 oculta a coluna de ids

        todas_parcelas = carregar_parcelas()
        emprestimos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}  # ativos
        clientes = {c[0]: c[1] for c in carregar_clientes()}

        hoje = datetime.today()
        dados = []  # (nome_cliente, total_atraso, id_emprestimo)
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
            prev_dt = None
            try:
                if venc:
                    venc_dt = datetime.strptime(venc, "%d/%m/%Y")
            except:
                pass
            try:
                if data_prevista:
                    prev_dt = datetime.strptime(data_prevista, "%d/%m/%Y")
            except:
                pass

            # Regras de atraso
            atrasada = False
            if venc_dt and hoje > venc_dt and not prev_dt:
                atrasada = True
            elif venc_dt and hoje > venc_dt and prev_dt and hoje > prev_dt:
                atrasada = True

            if not atrasada:
                continue

            # Valor da parcela = saldo (se tiver) ou valor cheio
            try:
                valor_float = 0.0
                if residual and str(residual).strip():
                    valor_float = float(str(residual).replace("R$", "").replace(".", "").replace(",", "."))
                elif valor and str(valor).strip():
                    valor_float = float(str(valor).replace("R$", "").replace(".", "").replace(",", "."))
            except:
                valor_float = 0.0

            nome_cliente = clientes.get(emprestimos[id_emp][1], "Desconhecido")
            dados.append((nome_cliente, valor_float, id_emp))
            total_geral += valor_float

        # Popular tabela
        self.tabela.setRowCount(len(dados))
        for i, (nome, total, emp_id) in enumerate(dados):
            nome_item = QTableWidgetItem(nome)
            nome_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 0, nome_item)

            total_item = QTableWidgetItem(self._fmt_br(total))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 1, total_item)

            id_item = QTableWidgetItem(emp_id)
            self.tabela.setItem(i, 2, id_item)

        # Totalizador alinhado com as colunas
        self.spacer_total = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout_principal.addSpacerItem(self.spacer_total)

        self.totalizador_layout = QHBoxLayout()
        self.totalizador_layout.setSpacing(0)

        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        # Coluna 0 (Cliente) → título
        lbl_total_titulo = QLabel("Total em atraso:")
        lbl_total_titulo.setFont(fonte_negrito)
        lbl_total_titulo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.totalizador_layout.addWidget(lbl_total_titulo, 1)

        # Coluna 1 (Total em atraso) → valor somado
        lbl_total_valor = QLabel(self._fmt_br(total_geral))
        lbl_total_valor.setFont(fonte_negrito)
        lbl_total_valor.setAlignment(Qt.AlignCenter)
        self.totalizador_layout.addWidget(lbl_total_valor, 1)

        self.layout_principal.addLayout(self.totalizador_layout)

        # Guarda referência para poder atualizar depois, se necessário
        self.lbl_total_valor = lbl_total_valor        

    def _abrir_parcelas_do_emprestimo(self, row, col):
        """Abre a tela de parcelas do empréstimo ao dar duplo clique em uma linha."""
        item_id = self.tabela.item(row, 2)  # 🔹 coluna oculta com id do empréstimo
        if not item_id:
            return

        id_emprestimo = item_id.text().strip()
        if not id_emprestimo:
            return

        from ui.parcelas_ui import ParcelasWindow
        from emprestimos import carregar_emprestimos
        from clientes import carregar_clientes

        emprestimos = {e[0]: e for e in carregar_emprestimos()}
        clientes = {c[0]: c[1] for c in carregar_clientes()}

        if id_emprestimo not in emprestimos:
            return

        emp = emprestimos[id_emprestimo]
        emprestimo_dict = {
            "id": emp[0],
            "cliente": clientes.get(emp[1], "Desconhecido"),
            "capital": emp[2],
            "data_inicio": emp[3],
            "meses": emp[4],
            "taxa": emp[5],
            "juros": emp[6],
            "prestacao": emp[7]
        }

        win = ParcelasWindow(emprestimo_dict, emp[8], parent=self)
        win.show()

        # manter referência para não ser coletada pelo garbage collector
        self.parcelas_window = win



    def _popula_tabela_emprestimos_com_renegociacao(self):
        """Lista empréstimos que possuem renegociação (data prevista futura ou atual)."""
        from datetime import datetime

        self.tabela.clearContents()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(3)  # Cliente | Total em renegociação | id oculto
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Total em renegociação", "id_emprestimo"])
        self.tabela.setColumnHidden(2, True)  # oculta a coluna de IDs

        todas_parcelas = carregar_parcelas()
        emprestimos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}  # ativos
        clientes = {c[0]: c[1] for c in carregar_clientes()}

        hoje = datetime.today()
        dados = []
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
                dados.append((nome_cliente, valor_float, id_emp))
                total_geral += valor_float

        # Preencher tabela
        self.tabela.setRowCount(len(dados))
        for i, (nome, total, emp_id) in enumerate(dados):
            nome_item = QTableWidgetItem(nome)
            nome_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 0, nome_item)

            total_item = QTableWidgetItem(self._fmt_br(total))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 1, total_item)

            id_item = QTableWidgetItem(emp_id)
            self.tabela.setItem(i, 2, id_item)

        # Totalizador
        self.spacer_total = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout_principal.addSpacerItem(self.spacer_total)

        self.totalizador_layout = QHBoxLayout()
        self.totalizador_layout.setSpacing(0)

        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        lbl_total_titulo = QLabel("Total em renegociação:")
        lbl_total_titulo.setFont(fonte_negrito)
        lbl_total_titulo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.totalizador_layout.addWidget(lbl_total_titulo, 1)

        lbl_total_valor = QLabel(self._fmt_br(total_geral))
        lbl_total_valor.setFont(fonte_negrito)
        lbl_total_valor.setAlignment(Qt.AlignCenter)
        self.totalizador_layout.addWidget(lbl_total_valor, 1)

        self.layout_principal.addLayout(self.totalizador_layout)
        self.lbl_total_valor = lbl_total_valor

    def _popula_tabela_emprestimos_em_dia(self):
        """Lista empréstimos que não têm parcelas em atraso nem renegociação vencida.
        Mostra apenas Cliente e Total em dia."""
        from datetime import datetime

        self.tabela.clearContents()
        self.tabela.setRowCount(0)
        self.tabela.setColumnCount(3)  # Cliente | Total em dia | id oculto
        self.tabela.setHorizontalHeaderLabels(["Cliente", "Total em dia", "id_emprestimo"])
        self.tabela.setColumnHidden(2, True)  # oculta a coluna de IDs

        todas_parcelas = carregar_parcelas()
        emprestimos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}  # ativos
        clientes = {c[0]: c[1] for c in carregar_clientes()}

        hoje = datetime.today()
        atrasados = set()
        reneg_vencida = set()
        em_dia = {}

        # Primeiro: identificar atrasados ou renegociação vencida
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
            prev_dt = None
            try:
                if venc:
                    venc_dt = datetime.strptime(venc, "%d/%m/%Y")
            except:
                pass
            try:
                if data_prevista:
                    prev_dt = datetime.strptime(data_prevista, "%d/%m/%Y")
            except:
                pass

            # Marca como atraso
            if venc_dt and hoje > venc_dt and not prev_dt:
                atrasados.add(id_emp)
            elif venc_dt and hoje > venc_dt and prev_dt and hoje > prev_dt:
                atrasados.add(id_emp)
            # Marca como renegociação vencida
            elif prev_dt and hoje > prev_dt:
                reneg_vencida.add(id_emp)

        # Agora: os que sobraram são "em dia"
        total_geral = 0.0
        for id_emp, emp in emprestimos.items():
            if id_emp in atrasados or id_emp in reneg_vencida:
                continue

            nome_cliente = clientes.get(emp[1], "Desconhecido")

            try:
                capital_total = float(emp[2]) if emp[2] else 0.0
                juros_total = float(emp[6]) if emp[6] else 0.0
                total = capital_total + juros_total
            except:
                total = 0.0

            em_dia[id_emp] = (nome_cliente, total)
            total_geral += total

        # Preencher tabela
        self.tabela.setRowCount(len(em_dia))
        for i, (emp_id, (nome, total)) in enumerate(em_dia.items()):
            nome_item = QTableWidgetItem(nome)
            nome_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 0, nome_item)

            total_item = QTableWidgetItem(self._fmt_br(total))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(i, 1, total_item)

            id_item = QTableWidgetItem(emp_id)
            self.tabela.setItem(i, 2, id_item)

        # Totalizador
        self.spacer_total = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout_principal.addSpacerItem(self.spacer_total)

        self.totalizador_layout = QHBoxLayout()
        self.totalizador_layout.setSpacing(0)

        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        lbl_total_titulo = QLabel("Total em dia:")
        lbl_total_titulo.setFont(fonte_negrito)
        lbl_total_titulo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.totalizador_layout.addWidget(lbl_total_titulo, 1)

        lbl_total_valor = QLabel(self._fmt_br(total_geral))
        lbl_total_valor.setFont(fonte_negrito)
        lbl_total_valor.setAlignment(Qt.AlignCenter)
        self.totalizador_layout.addWidget(lbl_total_valor, 1)

        self.layout_principal.addLayout(self.totalizador_layout)
        self.lbl_total_valor = lbl_total_valor

    def gerar_pdf(self):
        """Exporta a tabela atual para PDF usando apenas PySide6."""
        if self.tabela.rowCount() == 0:
            QMessageBox.warning(self, "Aviso", "Não há dados para exportar.")
            return

        # Pergunta onde salvar
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar relatório", "relatorio.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return

        # Monta HTML simples com os dados da tabela
        html = "<h2>Relatório</h2><table border='1' cellspacing='0' cellpadding='4'>"
        html += "<tr>"
        for col in range(self.tabela.columnCount()):
            if self.tabela.isColumnHidden(col):
                continue
            html += f"<th>{self.tabela.horizontalHeaderItem(col).text()}</th>"
        html += "</tr>"

        for row in range(self.tabela.rowCount()):
            html += "<tr>"
            for col in range(self.tabela.columnCount()):
                if self.tabela.isColumnHidden(col):
                    continue
                item = self.tabela.item(row, col)
                texto = item.text() if item else ""
                html += f"<td>{texto}</td>"
            html += "</tr>"
        html += "</table>"

        # Converte HTML em PDF
        doc = QTextDocument()
        doc.setHtml(html)

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        doc.print_(printer)

        QMessageBox.information(self, "Sucesso", f"Relatório salvo em:\n{path}")

    def abrir_em_nova_janela(self):    
        tipo = self.cb_tipo.currentText()        

        # 🔹 Monta dados do relatório
        colunas = []
        linhas = []

        if tipo == "Parcelas em aberto":
            todas_parcelas = carregar_parcelas()
            emprestimos_dict = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}
            clientes_dict = {c[0]: c[1] for c in carregar_clientes()}

            colunas = ["Cliente", "Nº", "Capital", "Juros", "Saldo"]

            total_capital = 0.0
            total_juros = 0.0
            total_saldo = 0.0

            for p in todas_parcelas:
                (
                    _id, id_emp, num, _, _,
                    _, _, _, _,
                    valor_pago, _, _, _,
                    _, _
                ) = p

                pago = valor_pago and str(valor_pago).strip() not in ("", "0", "R$ 0,00")
                if pago or id_emp not in emprestimos_dict:
                    continue

                emp = emprestimos_dict[id_emp]
                id_cliente = emp[1]
                nome_cliente = clientes_dict.get(id_cliente, "Desconhecido")

                try:
                    capital_total_emp = float(emp[2]) if emp[2] else 0.0
                    meses = int(emp[4]) if emp[4] else 1
                    juros_total_emp = float(emp[6]) if emp[6] else 0.0
                except:
                    capital_total_emp = juros_total_emp = 0.0
                    meses = 1

                capital_parc = capital_total_emp / meses if meses > 0 else 0.0
                juros_parc = juros_total_emp / meses if meses > 0 else 0.0
                saldo = capital_parc + juros_parc

                linhas.append([
                    nome_cliente,
                    str(num),
                    f"R$ {capital_parc:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    f"R$ {juros_parc:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                ])

                total_capital += capital_parc
                total_juros += juros_parc
                total_saldo += saldo

            # Linha totalizadora
            linhas.append([
                "<b>TOTAL</b>",
                "",
                f"<b>R$ {total_capital:,.2f}</b>".replace(",", "X").replace(".", ",").replace("X", "."),
                f"<b>R$ {total_juros:,.2f}</b>".replace(",", "X").replace(".", ",").replace("X", "."),
                f"<b>R$ {total_saldo:,.2f}</b>".replace(",", "X").replace(".", ",").replace("X", "."),
            ])

        elif tipo == "Empréstimos (com parcelas em atraso)":
            from datetime import datetime
            todas_parcelas = carregar_parcelas()
            emprestimos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}
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
                if valor_pago and str(valor_pago).strip() not in ("", "0", "R$ 0,00"):
                    continue

                try:
                    venc_dt = datetime.strptime(venc, "%d/%m/%Y") if venc else None
                except:
                    venc_dt = None
                if not venc_dt or hoje <= venc_dt:
                    continue

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

            colunas = ["Cliente", "Total em atraso"]
            linhas = []
            for nome, total in dados.items():
                linhas.append([
                    nome,
                    f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                ])

            # Linha de totalização em negrito
            linhas.append([
                "<b>TOTAL</b>",
                f"<b>R$ {total_geral:,.2f}</b>".replace(",", "X").replace(".", ",").replace("X", "."),
            ])

        elif tipo == "Todos os empréstimos (em aberto)":
            todas_parcelas = carregar_parcelas()
            emprestimos = {e[0]: e for e in carregar_emprestimos() if e[9] == "sim"}
            clientes = {c[0]: c[1] for c in carregar_clientes()}

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

                # Ignora parcelas já pagas
                if valor_pago and str(valor_pago).strip() not in ("", "0", "R$ 0,00"):
                    continue

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

            colunas = ["Cliente", "Valor em aberto"]
            linhas = []
            for nome, total in dados.items():
                linhas.append([
                    nome,
                    f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                ])

            # Linha de totalização em negrito
            linhas.append([
                "<b>TOTAL</b>",
                f"<b>R$ {total_geral:,.2f}</b>".replace(",", "X").replace(".", ",").replace("X", "."),
            ])

        else:
            colunas = ["Aviso"]
            linhas = [[f"Implementar relatório '{tipo}' em HTML"]]

        # 🔹 Monta o HTML com dados embutidos
        html = f"""<!DOCTYPE html>
        <html lang="pt-BR">
        <head>
        <meta charset="UTF-8">
        <title>📑 Relatório</title>
        <style>
            body {{ background:#ffffff; color:#333; font-family: Arial, sans-serif; padding:20px; }}
            h2 {{ color:#2c3e50; }}
            table {{ width:100%; border-collapse: collapse; margin-top:20px; }}
            th, td {{ border:1px solid #ccc; padding:8px; text-align:center; }}
            th {{ background:#f0f0f0; color:#333; }}
            tr:nth-child(even) {{ background:#f9f9f9; }}
            .btn {{ background:#3498db; color:white; padding:8px 12px; border:none; border-radius:6px; cursor:pointer; }}
            .btn:hover {{ background:#2980b9; }}
        </style>
        </head>
        <body>
        <h2>📊 {tipo}</h2>
        <button class="btn" onclick="gerarPDF()">📥 Gerar PDF</button>

        <div id="relatorio">
            <table id="tabela">
                <thead><tr id="header"></tr></thead>
                <tbody id="corpo"></tbody>
            </table>
        </div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.9.2/html2pdf.bundle.min.js"></script>
        <script>
            const dados = {{
            tipo: "{tipo}",        
            colunas: {colunas},
            linhas: {linhas}
            }};

            // Cabeçalhos
            let headerRow = document.getElementById("header");
            dados.colunas.forEach(c => {{
                let th = document.createElement("th");
                th.textContent = c;
                headerRow.appendChild(th);
            }});

            // Linhas
            let corpo = document.getElementById("corpo");
            dados.linhas.forEach(linha => {{
                let tr = document.createElement("tr");
                linha.forEach(cel => {{
                    let td = document.createElement("td");
                    td.innerHTML = cel;  // 🔹 permite tags <b> para negrito
                    tr.appendChild(td);
                }});
                corpo.appendChild(tr);
            }});

            function gerarPDF() {{
                const relatorio = document.getElementById("relatorio");  // 🔹 só título + tabela
                html2pdf().from(relatorio).save("relatorio.pdf");
            }}
        </script>
        </body>
        </html>"""
