from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QPushButton, QFrame, QAbstractItemView, QLineEdit, QHBoxLayout, QTextEdit, QFileDialog, QMessageBox
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

from PySide6.QtPrintSupport import QPrinter

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QColor, QFont, QRegularExpressionValidator, QTextDocument
from parcelas import parcelas, salvar_parcelas, sincronizar_parcelas_upload
import uuid

from parcelas import carregar_parcelas_por_emprestimo

class ParcelasWindow(QWidget):
    """Janela para visualizar/editar parcelas de um empréstimo."""
    def __init__(self, emprestimo, id_usuario, parent=None, on_save_callback=None, readonly=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.emprestimo = emprestimo
        self.id_usuario = id_usuario
        self.on_save_callback = on_save_callback
        self.linhas_zeradas = set()
        self.readonly = readonly


        self.setWindowTitle(f"Parcelas - Empréstimo de {emprestimo.get('data_inicio', '')} - {emprestimo.get('cliente', '')}")
        self.setFixedSize(1150, 550)
        self.setStyleSheet("background-color: #1c2331; color: white;")

        layout = QVBoxLayout(self)

        # 🔹 Título principal
        lbl = QLabel(f"Parcelas do Empréstimo de {emprestimo.get('data_inicio', '')} - {emprestimo.get('cliente', '')}")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #9fb0c7;")
        layout.addWidget(lbl)

        # 🔹 Linha extra com capital, juros, nº de parcelas e botão ➕
        capital_valor = float(emprestimo.get("capital", 0) or 0)
        juros_valor = float(emprestimo.get("juros", 0) or 0)

        capital_txt = self._fmt(capital_valor)
        juros_txt = self._fmt(juros_valor)
        montante_txt = self._fmt(capital_valor + juros_valor)
        parcelas_txt = emprestimo.get("meses", "0")

        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)

        lbl_info = QLabel(
            f"Montante do empréstimo: {montante_txt} "
            f"(Capital inicial: {capital_txt} + Juros iniciais: {juros_txt})    "
            f"|    Número de parcelas: {parcelas_txt}"
        )
        lbl_info.setStyleSheet("font-size: 14px; color: #cccccc; margin-bottom: 8px;")

        info_layout.addWidget(lbl_info)
        info_layout.addStretch()

        if not self.readonly:
            btn_add_parcela = QPushButton("➕ Nova Parcela")
            btn_add_parcela.setStyleSheet("""
                QPushButton {
                    background-color:#27ae60; color:white;
                    padding:4px 10px; border-radius:6px; font-weight:bold;
                }
                QPushButton:hover { background-color:#2ecc71; }
            """)
            btn_add_parcela.clicked.connect(self.adicionar_parcela)
            info_layout.addWidget(btn_add_parcela)

        layout.addLayout(info_layout)


        # 🔹 Criação da tabela
        self.tabela = QTableWidget(0, 12)
        self.tabela.setHorizontalHeaderLabels([
            "Nº", "Vencimento", "Valor", "Juros", "Desconto",
            "Calc.", "Pg. Principal", "Pg. Juros",
            "Valor Pago", "Saldo", "Data do Pag.", "Zerar"
        ])
        if self.readonly:
            self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Habilitar menu de contexto (clique direito)
        self.tabela.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabela.customContextMenuRequested.connect(self.abrir_menu_contexto)

        # Aparência da tabela
        header = self.tabela.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #374157;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tabela.setColumnWidth(0, 40)

        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.tabela.setColumnWidth(5, 40)

        header.setSectionResizeMode(11, QHeaderView.Fixed)
        self.tabela.setColumnWidth(11, 40)

        # As demais continuam elásticas
        for col in range(1, self.tabela.columnCount()):
            if col not in [5, 11]:
                header.setSectionResizeMode(col, QHeaderView.Stretch)


        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabela.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446;
                color: white;
                border: 1px solid #3a455b;
            }
        """)
        layout.addWidget(self.tabela)

        # 🔹 Carregar parcelas reais
        parcelas_do_emprestimo = carregar_parcelas_por_emprestimo(emprestimo["id"])
        # 🔹 Ordena antes de popular a tabela
        try:
            parcelas_do_emprestimo.sort(key=lambda p: int(p[2]))
        except Exception:
            pass

        fonte_negrito = QFont()
        fonte_negrito.setBold(True)

        for linha, parcela in enumerate(parcelas_do_emprestimo):
            (
                _id, id_emp, num, valor, venc,
                juros, desconto, pg_principal, pg_juros,
                valor_pago, residual, data_pag, id_usuario,
                data_prevista, comentario
            ) = parcela

            self.tabela.insertRow(linha)

            # Nº
            item_num = QTableWidgetItem(str(num))
            item_num.setTextAlignment(Qt.AlignCenter)
            item_num.setFlags(item_num.flags() & ~Qt.ItemIsEditable)
            item_num.setFont(fonte_negrito)
            self.tabela.setItem(linha, 0, item_num)

            # Vencimento
            item_venc = QTableWidgetItem(venc or "")
            item_venc.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 1, item_venc)

            # Valor
            item_valor = QTableWidgetItem(valor if str(valor).startswith("R$") else f"R$ {valor}")
            item_valor.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 2, item_valor)

            # Juros
            item_juros = QTableWidgetItem(juros or "")
            item_juros.setTextAlignment(Qt.AlignCenter)
            item_juros.setForeground(QColor("#78ddff"))
            self.tabela.setItem(linha, 3, item_juros)

            # Desconto
            item_desc = QTableWidgetItem(desconto or "")
            item_desc.setTextAlignment(Qt.AlignCenter)
            item_desc.setForeground(QColor("#ffaeae"))
            self.tabela.setItem(linha, 4, item_desc)

            if not self.readonly:
                # Botão de cálculo
                btn_calc = QPushButton("⚡")
                btn_calc.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #3498db;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        color: #5dade2;  /* tom mais claro ao passar o mouse */
                    }
                """)                
                btn_calc.clicked.connect(self.handle_calc_click)
                self.tabela.setCellWidget(linha, 5, btn_calc)
            else:
                self.tabela.setCellWidget(linha, 5, QLabel(""))  # ocupa o espaço

            # Pg. Principal
            item_pg_principal = QTableWidgetItem(pg_principal or "")
            item_pg_principal.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 6, item_pg_principal)

            # Pg. Juros
            item_pg_juros = QTableWidgetItem(pg_juros or "")
            item_pg_juros.setTextAlignment(Qt.AlignCenter)
            self.tabela.setItem(linha, 7, item_pg_juros)

            # Valor Pago
            item_pago = QTableWidgetItem(valor_pago or "")
            item_pago.setTextAlignment(Qt.AlignCenter)
            item_pago.setFlags(item_pago.flags() & ~Qt.ItemIsEditable)  # 🔹 bloqueia edição manual
            self.tabela.setItem(linha, 8, item_pago)

            # Saldo (não editável)
            item_saldo = QTableWidgetItem(residual or "")
            item_saldo.setTextAlignment(Qt.AlignCenter)
            item_saldo.setFlags(item_saldo.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(linha, 9, item_saldo)
            
            # Data do Pag. (validador de data, inicia vazio)
            edit_data = QLineEdit()
            edit_data.setPlaceholderText("dd/mm/aaaa")
            if data_pag and data_pag.strip():
                edit_data.setText(data_pag)

            # 🔹 Regex que aceita apenas datas dd/mm/yyyy (01/01/1900 até 31/12/2099)
            regex = QRegularExpression(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[0-9]{4}$")
            validator = QRegularExpressionValidator(regex, edit_data)
            edit_data.setValidator(validator)

            edit_data.setAlignment(Qt.AlignCenter)
            self.tabela.setCellWidget(linha, 10, edit_data)

            if not self.readonly:
                # Botão de zerar saldo
                btn_zerar = QPushButton("✂️")
                btn_zerar.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #e74c3c;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        color: #ff6b6b;
                    }
                """)
                btn_zerar.clicked.connect(self.handle_zerar_click)
                self.tabela.setCellWidget(linha, 11, btn_zerar)
            else:
                self.tabela.setCellWidget(linha, 11, QLabel(""))

        # 🔹 Calcula saldo inicial de cada linha
        for row in range(self.tabela.rowCount()):
            try:
                # Se já existe residual gravado no banco, respeita esse valor
                residual_item = self.tabela.item(row, 9)
                residual_txt = residual_item.text().replace("R$", "").replace(".", "").replace(",", ".").strip() if residual_item else ""

                if residual_txt and float(residual_txt or 0) == 0.0:
                    # Mantém formatado como R$ 0,00
                    self.tabela.item(row, 9).setText(self._fmt(0.0))
                    self.tabela.item(row, 9).setTextAlignment(Qt.AlignCenter)
                    continue

                valor = self._get_valor(row, 2)
                juros = self._get_valor(row, 3)
                desconto = self._get_valor(row, 4)
                pg_principal = self._get_valor(row, 6)
                pg_juros = self._get_valor(row, 7)
                saldo = valor + juros - desconto - pg_principal - pg_juros
                self.tabela.item(row, 9).setText(self._fmt(saldo))
                self.tabela.item(row, 9).setTextAlignment(Qt.AlignCenter)
            except:
                pass

        parcelas_do_emprestimo = carregar_parcelas_por_emprestimo(emprestimo["id"])
        parcelas_do_emprestimo.sort(key=lambda p: int(p[2]))  # 🔹 ordena pelo número (coluna 2 = numero)
        

        spacer = QFrame(); spacer.setFixedHeight(12)
        layout.addWidget(spacer)

        self.adicionar_totalizadores(fonte_negrito)
        self.tabela.itemChanged.connect(self.formatar_valores)

        # 🔹 Linha com os botões Salvar e Arquivar
        if not self.readonly:
            # 🔹 Linha com os botões Salvar e Arquivar
            btns_layout = QHBoxLayout()

            # Botão salvar
            btn_salvar = QPushButton("💾 Salvar Parcelas")
            btn_salvar.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60; color: white;
                    padding: 8px; border-radius: 6px; font-weight: bold;
                }
                QPushButton:hover { background-color: #2ecc71; }
            """)
            btn_salvar.clicked.connect(self.salvar_modificacoes)
            btns_layout.addWidget(btn_salvar, alignment=Qt.AlignLeft)

            btns_layout.addStretch()

            # Botão PDF
            btn_pdf = QPushButton("📥 Gerar PDF")
            btn_pdf.setStyleSheet("""
                QPushButton {
                    background-color:#3498db; color: white;
                    padding: 8px; border-radius: 6px; font-weight: bold;
                }
                QPushButton:hover { background-color:#2980b9; }
            """)
            btn_pdf.clicked.connect(self.gerar_pdf)
            btns_layout.addWidget(btn_pdf, alignment=Qt.AlignCenter)

            # Botão arquivar
            btn_arquivar = QPushButton("🗑 Arquivar Empréstimo")
            btn_arquivar.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c; color: white;
                    padding: 8px; border-radius: 6px; font-weight: bold;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            btn_arquivar.clicked.connect(self.arquivar_emprestimo)
            btns_layout.addWidget(btn_arquivar, alignment=Qt.AlignRight)

            layout.addLayout(btns_layout)


        self.atualizar_totalizadores()
        self._colorir_linhas()
    
    def abrir_menu_contexto(self, pos):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)

        # Descobre em qual linha o clique foi feito
        row = self.tabela.indexAt(pos).row()
        if row < 0 or row >= self.tabela.rowCount() - 1:  # ignora totalizador
            return

        # Verifica se a parcela já foi paga
        valor_pago = self.tabela.item(row, 8).text() if self.tabela.item(row, 8) else ""
        if valor_pago.strip():
            return  # não mostrar opção se já está paga

        # Adiciona opção "Adiar pagamento"
        adiar_action = menu.addAction("⏩ Adiar pagamento")
        adiar_action.triggered.connect(lambda: self.abrir_adiar_pagamento(row))

        menu.exec(self.tabela.viewport().mapToGlobal(pos))


    def abrir_adiar_pagamento(self, row):
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QTextEdit, QLineEdit, QHBoxLayout, QSpacerItem, QSizePolicy
        )
        from PySide6.QtGui import QRegularExpressionValidator
        from PySide6.QtCore import QRegularExpression

        dialog = QDialog(self)
        dialog.setWindowTitle("Adiar Pagamento")
        dialog.setStyleSheet("background-color:#1c2331; color:white;")
        dialog.setFixedSize(360, 280)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(2)  # 🔹 bem mais compacto
        layout.setContentsMargins(12, 10, 12, 10)  # menos margem interna

        # Campo comentário
        lbl_coment = QLabel("Comentário (máx. 100):")
        inp_coment = QTextEdit()
        inp_coment.setFixedHeight(70)  # ~3 linhas
        inp_coment.setStyleSheet("background-color:#2c3446; color:white; padding:4px; border-radius:6px;")
        layout.addWidget(lbl_coment)
        layout.addWidget(inp_coment)

        # 🔹 Limite de caracteres (sem apagar texto já digitado)
        def limitar_caracteres():
            texto = inp_coment.toPlainText()
            if len(texto) > 100:
                cursor = inp_coment.textCursor()
                pos = cursor.position()
                inp_coment.blockSignals(True)
                inp_coment.setPlainText(texto[:100])
                inp_coment.blockSignals(False)
                # mantém o cursor no final do texto
                if pos > 100:
                    pos = 100
                cursor.setPosition(pos)
                inp_coment.setTextCursor(cursor)
        inp_coment.textChanged.connect(limitar_caracteres)

        # Campo data prevista
        lbl_data = QLabel("Data prevista (dd/mm/aaaa):")
        inp_data = QLineEdit()
        inp_data.setPlaceholderText("dd/mm/aaaa")
        regex = QRegularExpression(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[0-9]{4}$")
        validator = QRegularExpressionValidator(regex, inp_data)
        inp_data.setValidator(validator)
        inp_data.setAlignment(Qt.AlignCenter)
        inp_data.setStyleSheet("background-color:#2c3446; color:white; padding:4px; border-radius:6px;")
        layout.addWidget(lbl_data)
        layout.addWidget(inp_data)

        # 🔹 Espaço extra entre input de data e botões
        layout.addSpacerItem(QSpacerItem(20, 18, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Pré-carregar dados já existentes
        from parcelas import parcelas
        if row < len(parcelas):
            atual = parcelas[row]
            if len(atual) > 14:
                if atual[14]:
                    inp_coment.setPlainText(atual[14])
                if atual[13]:
                    inp_data.setText(atual[13])

        # Layout de botões lado a lado
        btn_layout = QHBoxLayout()

        btn_save = QPushButton("Salvar")
        btn_save.setFixedWidth(120)
        btn_save.setStyleSheet("background-color:#27ae60; color:white; padding:6px; border-radius:6px; font-weight:bold;")
        btn_layout.addWidget(btn_save)

        btn_excluir = QPushButton("Excluir acordo")
        btn_excluir.setFixedWidth(120)
        btn_excluir.setStyleSheet("background-color:#e74c3c; color:white; padding:6px; border-radius:6px; font-weight:bold;")
        btn_layout.addWidget(btn_excluir)

        layout.addLayout(btn_layout)

        # === Funções internas (salvar/excluir) — mantêm igual ao que já fizemos ===
        def salvar():
            comentario = inp_coment.toPlainText().strip()[:100]
            data_prevista = inp_data.text().strip()
            if not data_prevista:
                QMessageBox.warning(dialog, "Erro", "Informe a data prevista.")
                return
            from PySide6.QtWidgets import QTableWidgetItem
            self.tabela.setItem(row, 10, QTableWidgetItem(data_prevista))
            from parcelas import parcelas, salvar_parcelas, sincronizar_parcelas_upload
            if row < len(parcelas):
                id_parcela = parcelas[row][0]
                for i, p in enumerate(parcelas):
                    if p[0] == id_parcela:
                        antiga = list(p)
                        if len(antiga) < 15:
                            antiga.extend(["", ""])
                        antiga[13] = data_prevista
                        antiga[14] = comentario
                        parcelas[i] = tuple(antiga)
                        break
            salvar_parcelas(parcelas)
            sincronizar_parcelas_upload()
            self._colorir_linhas()
            QMessageBox.information(dialog, "Sucesso", "Pagamento adiado com sucesso.")
            dialog.accept()

        def excluir_acordo():
            reply = QMessageBox.question(
                dialog,
                "Excluir acordo",
                "A exclusão do acordo torna a parcela \"em atraso\", "
                "e essa informação também é atualizada em seus relatórios.\n\n"
                "Tem certeza que deseja remover o acordo?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            from parcelas import parcelas, salvar_parcelas, sincronizar_parcelas_upload
            if row < len(parcelas):
                id_parcela = parcelas[row][0]
                for i, p in enumerate(parcelas):
                    if p[0] == id_parcela:
                        antiga = list(p)
                        if len(antiga) < 15:
                            antiga.extend(["", ""])
                        antiga[13] = ""
                        antiga[14] = ""
                        parcelas[i] = tuple(antiga)
                        break
            salvar_parcelas(parcelas)
            sincronizar_parcelas_upload()
            self._colorir_linhas()
            QMessageBox.information(dialog, "Excluído", "Acordo removido. A parcela voltou a constar como em atraso.")
            dialog.accept()

        btn_save.clicked.connect(salvar)
        btn_excluir.clicked.connect(excluir_acordo)

        dialog.exec()



    def handle_zerar_click(self):
        sender = self.sender()
        if not sender:
            return
        row = self.tabela.indexAt(sender.pos()).row()
        if row >= 0:
            # Marca na memória
            self.linhas_zeradas.add(row)
            self.tabela.item(row, 9).setText(self._fmt(0.0))

            # 🔹 Atualiza também em memória e banco
            from parcelas import parcelas, salvar_parcelas, sincronizar_parcelas_upload
            if row < len(parcelas):
                id_parcela = parcelas[row][0]
                for i, p in enumerate(parcelas):
                    if p[0] == id_parcela:
                        antiga = list(p)
                        if len(antiga) < 15:
                            antiga.extend(["", ""])
                        antiga[10] = self._fmt(0.0)
                        parcelas[i] = tuple(antiga)
                        break
                salvar_parcelas(parcelas)
                sincronizar_parcelas_upload()


    def handle_calc_click(self):
        sender = self.sender()
        if not sender:
            return

        row = self.tabela.indexAt(sender.pos()).row()
        if row >= 0:
            self.calcular_pg(row)

    def adicionar_totalizadores(self, fonte_negrito):
        row = self.tabela.rowCount()
        self.tabela.insertRow(row)

        for col in range(self.tabela.columnCount()):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setBackground(QColor("#4e586e"))

            # 🔹 aplica negrito em todas as colunas
            item.setFont(fonte_negrito)

            if col in [2, 3, 4, 6, 7, 8]:
                item.setText("R$ 0,00")
            elif col == 5:
                item.setText("")
            else:
                item.setText("")

            self.tabela.setItem(row, col, item)


    def formatar_valores(self, item):
        if not item or item.row() == self.tabela.rowCount() - 1:
            return

        col_monetarias = [2, 3, 4, 6, 7, 8]
        if item.column() in col_monetarias:
            texto = item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
            if texto:
                try:
                    valor = float(texto)
                    item.setText(self._fmt(valor))
                except:
                    item.setText("")
            else:
                item.setText("")

        # Valor Pago = Pg. Principal + Pg. Juros
        if item.column() in (6, 7):
            try:
                pg_principal = self._get_valor(item.row(), 6)
                pg_juros = self._get_valor(item.row(), 7)
                total = pg_principal + pg_juros
                celula = self.tabela.item(item.row(), 8)
                celula.setText(self._fmt(total) if total > 0 else "")
            except:
                pass

        # Saldo = Valor + Juros - Desconto - Pg. Principal - Pg. Juros
        try:
            if item.row() not in self.linhas_zeradas:  # 🔹 não recalcula se foi zerado manualmente
                valor = self._get_valor(item.row(), 2)
                juros = self._get_valor(item.row(), 3)
                desconto = self._get_valor(item.row(), 4)
                pg_principal = self._get_valor(item.row(), 6)
                pg_juros = self._get_valor(item.row(), 7)
                saldo = valor + juros - desconto - pg_principal - pg_juros
                celula = self.tabela.item(item.row(), 9)
                celula.setText(self._fmt(saldo))
        except:
            pass

        self.atualizar_totalizadores()

    def _get_valor(self, row, col):
        celula = self.tabela.item(row, col)
        if not celula: return 0.0
        txt = celula.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            return float(txt) if txt else 0.0
        except:
            return 0.0

    def _fmt(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def atualizar_totalizadores(self):
        row_total = self.tabela.rowCount() - 1
        for col in [2, 3, 4, 6, 7, 8, 9]:  # 🔹 agora inclui o Saldo
            total = 0.0
            for r in range(row_total):
                total += self._get_valor(r, col)
            celula = self.tabela.item(row_total, col)
            if celula:
                celula.setText(self._fmt(total))

    def salvar_modificacoes(self):
        from PySide6.QtWidgets import QMessageBox
        from parcelas import salvar_parcelas, parcelas, sincronizar_parcelas_upload
        import uuid

        # 🔹 Validação de parcelas parcialmente pagas
        for linha in range(self.tabela.rowCount() - 1):
            valor_pago_txt = self.tabela.item(linha, 8).text() if self.tabela.item(linha, 8) else ""
            saldo_txt = self.tabela.item(linha, 9).text() if self.tabela.item(linha, 9) else ""

            try:
                valor_pago = float(valor_pago_txt.replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)
            except:
                valor_pago = 0.0

            try:
                saldo = float(saldo_txt.replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)
            except:
                saldo = 0.0

            if valor_pago > 0 and saldo > 0:
                QMessageBox.warning(
                    self,
                    "Parcela parcialmente paga",
                    "Você não pode sair dessa tela com uma parcela parcialmente paga.\n\n"
                    "Se este cliente fez um acordo, faça os ajustes necessários."
                )
                return  # 🔹 Cancela o salvamento, mantém tela ativa

        # 🔹 Validação: se Valor pago > 0 mas não tem Data Pagamento
        for linha in range(self.tabela.rowCount() - 1):
            valor_pago_txt = self.tabela.item(linha, 8).text() if self.tabela.item(linha, 8) else ""
            data_pag_txt = ""

            widget = self.tabela.cellWidget(linha, 10)
            if widget:
                data_pag_txt = widget.text()
            elif self.tabela.item(linha, 10):
                data_pag_txt = self.tabela.item(linha, 10).text()

            try:
                valor_pago = float(valor_pago_txt.replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)
            except:
                valor_pago = 0.0

            if valor_pago > 0 and not data_pag_txt.strip():
                QMessageBox.warning(
                    self,
                    "Data de pagamento obrigatória",
                    "Insira a data de pagamento da parcela ⚠️"
                )
                return  # 🔹 Cancela salvamento

        # 🔹 Validação: se Data de Pagamento foi inserida mas Valor Pago está vazio
        for linha in range(self.tabela.rowCount() - 1):
            valor_pago_txt = self.tabela.item(linha, 8).text() if self.tabela.item(linha, 8) else ""
            data_pag_txt = ""

            widget = self.tabela.cellWidget(linha, 10)
            if widget:
                data_pag_txt = widget.text()
            elif self.tabela.item(linha, 10):
                data_pag_txt = self.tabela.item(linha, 10).text()

            try:
                valor_pago = float(valor_pago_txt.replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)
            except:
                valor_pago = 0.0

            if data_pag_txt.strip() and valor_pago == 0:
                QMessageBox.warning(
                    self,
                    "Valor pago obrigatório",
                    "Você deixou alguma parcela com data de pagamento registrada, "
                    "mas sem ter inserido o valor pago.\n\n"
                    "Insira os valores ou remova a data de pagamento antes de salvar."
                )
                return  # 🔹 Cancela salvamento

        # 🔹 Monta lista de parcelas atualizada
        novas_parcelas = []
        for linha in range(self.tabela.rowCount() - 1):
            numero = self.tabela.item(linha, 0).text()
            venc = self.tabela.item(linha, 1).text()
            valor = self.tabela.item(linha, 2).text().replace("R$", "").strip()
            juros = self.tabela.item(linha, 3).text()
            desconto = self.tabela.item(linha, 4).text()
            pg_principal = self.tabela.item(linha, 6).text()
            pg_juros = self.tabela.item(linha, 7).text()
            valor_pago = self.tabela.item(linha, 8).text()
            residual = self.tabela.item(linha, 9).text()
            if linha in self.linhas_zeradas:
                residual = "0"

            widget = self.tabela.cellWidget(linha, 10)
            if widget:
                data_pag = widget.text()
            else:
                data_pag = self.tabela.item(linha, 10).text() if self.tabela.item(linha, 10) else ""

            if linha < len(parcelas):
                parcela_id = parcelas[linha][0]
            else:
                parcela_id = str(uuid.uuid4())

            novas_parcelas.append((
                parcela_id,
                self.emprestimo["id"],
                numero,
                valor,
                venc,
                juros,
                desconto,
                pg_principal,
                pg_juros,
                valor_pago,
                residual,
                data_pag,
                self.id_usuario,
                "" if linha >= len(parcelas) else (parcelas[linha][13] if len(parcelas[linha]) > 13 else ""),
                "" if linha >= len(parcelas) else (parcelas[linha][14] if len(parcelas[linha]) > 14 else "")
            ))

        # 🔹 Atualiza lista global e sincroniza
        parcelas[:] = novas_parcelas
        salvar_parcelas(parcelas)
        sincronizar_parcelas_upload()

        # 🔹 Reaplica cores conforme situação
        self._colorir_linhas()

        # 🔹 Callback externo + fechar janela
        if self.on_save_callback:
            self.on_save_callback()
        self.close()




    def calcular_pg(self, row):
        """Calcula Pg. Principal e Pg. Juros da linha selecionada."""
        try:
            capital = float(self.emprestimo.get("capital", 0))
            n = int(str(self.emprestimo.get("meses", 1)).strip())
            total_juros = float(self.emprestimo.get("juros", 0))

            if capital <= 0 or n <= 0:
                return

            # Principal permanece igual
            pg_principal = capital / n

            # Juros agora considera entrada do usuário
            juros_base = total_juros / n

            def _parse_val(col):
                item = self.tabela.item(row, col)
                if not item:
                    return 0.0
                txt = item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
                try:
                    return float(txt) if txt else 0.0
                except:
                    return 0.0

            juros_extra = _parse_val(3)   # coluna Juros
            desconto = _parse_val(4)      # coluna Desconto

            pg_juros = juros_base + juros_extra - desconto

            # Atualiza células
            self.tabela.item(row, 6).setText(self._fmt(pg_principal))
            self.tabela.item(row, 7).setText(self._fmt(pg_juros))

        except Exception:
            pass



    def adicionar_parcela(self):
        """Adiciona uma nova parcela no final, obedecendo o padrão de datas e valores originais"""
        from datetime import datetime
        import calendar

        row_total = self.tabela.rowCount() - 1
        nova_linha = row_total  # insere antes do totalizador
        self.tabela.insertRow(nova_linha)

        # número da nova parcela = última parcela + 1
        numero = str(nova_linha + 1)

        # Valor da prestação
        valor_prestacao_raw = self.emprestimo.get("prestacao", 0)
        try:
            valor_prestacao = float(valor_prestacao_raw)
        except Exception:
            try:
                valor_prestacao = float(str(valor_prestacao_raw).replace("R$", "").replace(".", "").replace(",", "."))
            except Exception:
                try:
                    capital = float(self.emprestimo.get("capital", 0))
                    juros = float(self.emprestimo.get("juros", 0))
                    n = int(str(self.emprestimo.get("meses", 1)).strip())
                    valor_prestacao = (capital + juros) / n if n > 0 else 0
                except Exception:
                    valor_prestacao = 0

        valor_fmt = self._fmt(valor_prestacao)

        # 🔹 Data = 1 mês após a última parcela
        data_venc_ultima = self.tabela.item(row_total - 1, 1).text() if row_total > 0 else ""
        try:
            dt = datetime.strptime(data_venc_ultima, "%d/%m/%Y")
            dia_ref = dt.day
            mes = dt.month + 1
            ano = dt.year
            if mes > 12:
                mes = 1
                ano += 1
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            if dia_ref <= ultimo_dia:
                vencimento = datetime(ano, mes, dia_ref)
            else:
                mes += 1
                if mes > 12:
                    mes = 1
                    ano += 1
                vencimento = datetime(ano, mes, 1)
            novo_venc = vencimento.strftime("%d/%m/%Y")
        except Exception:
            novo_venc = ""

        # agora cria as células normalmente
        item_num = QTableWidgetItem(numero)
        item_num.setTextAlignment(Qt.AlignCenter)
        item_num.setFont(QFont("", weight=QFont.Bold))
        self.tabela.setItem(nova_linha, 0, item_num)

        item_venc = QTableWidgetItem(novo_venc)
        item_venc.setTextAlignment(Qt.AlignCenter)
        self.tabela.setItem(nova_linha, 1, item_venc)

        item_valor = QTableWidgetItem(valor_fmt)
        item_valor.setTextAlignment(Qt.AlignCenter)
        self.tabela.setItem(nova_linha, 2, item_valor)

        # Juros
        item_juros = QTableWidgetItem("")
        item_juros.setTextAlignment(Qt.AlignCenter)
        self.tabela.setItem(nova_linha, 3, item_juros)

        # Desconto
        item_desc = QTableWidgetItem("")
        item_desc.setTextAlignment(Qt.AlignCenter)
        self.tabela.setItem(nova_linha, 4, item_desc)

        # Botão de cálculo
        btn_calc = QPushButton("⚡")
        btn_calc.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #3498db;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        color: #5dade2;  /* tom mais claro ao passar o mouse */
                    }
                """)
        btn_calc.clicked.connect(self.handle_calc_click)
        self.tabela.setCellWidget(nova_linha, 5, btn_calc)

        # Pg. Principal
        item_pg_principal = QTableWidgetItem("")
        item_pg_principal.setTextAlignment(Qt.AlignCenter)
        self.tabela.setItem(nova_linha, 6, item_pg_principal)

        # Pg. Juros
        item_pg_juros = QTableWidgetItem("")
        item_pg_juros.setTextAlignment(Qt.AlignCenter)
        self.tabela.setItem(nova_linha, 7, item_pg_juros)

        # Valor Pago
        item_pago = QTableWidgetItem("")
        item_pago.setTextAlignment(Qt.AlignCenter)
        item_pago.setFlags(item_pago.flags() & ~Qt.ItemIsEditable)  # 🔹 bloqueia edição manual
        self.tabela.setItem(nova_linha, 8, item_pago)

        # Saldo
        item_saldo = QTableWidgetItem(valor_fmt)
        item_saldo.setTextAlignment(Qt.AlignCenter)
        item_saldo.setFlags(item_saldo.flags() & ~Qt.ItemIsEditable)
        self.tabela.setItem(nova_linha, 9, item_saldo)

        # Data do Pag. (QLineEdit com validador de data)
        from PySide6.QtGui import QRegularExpressionValidator
        from PySide6.QtCore import QRegularExpression

        edit_data = QLineEdit()
        edit_data.setPlaceholderText("dd/mm/aaaa")

        regex = QRegularExpression(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[0-9]{4}$")
        validator = QRegularExpressionValidator(regex, edit_data)
        edit_data.setValidator(validator)
        edit_data.setAlignment(Qt.AlignCenter)

        if self.readonly:
            edit_data.setReadOnly(True)
            edit_data.setStyleSheet("background-color: #3a455b; color: #aaa;")  # cinza desativado

        self.tabela.setCellWidget(nova_linha, 10, edit_data)

        # Botão Zerar
        btn_zerar = QPushButton("✂️")
        btn_zerar.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #e74c3c;
                        border: none;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        color: #ff6b6b;
                    }
                """)
        btn_zerar.clicked.connect(self.handle_zerar_click)
        self.tabela.setCellWidget(nova_linha, 11, btn_zerar)


    def arquivar_emprestimo(self):
        """Arquiva o empréstimo atual e fecha a janela."""
        from emprestimos import arquivar_emprestimo
        from PySide6.QtWidgets import QMessageBox

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmação")
        msg_box.setText(
            "Tem certeza que deseja arquivar este empréstimo?\n\n"
            "Ele não aparecerá mais nos relatórios ou no financeiro, e também não poderá ser reativado, "
            "mas poderá ser consultado no menu \"Empréstimos Arquivados\"."
        )
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        # Personaliza os textos dos botões
        msg_box.button(QMessageBox.Yes).setText("Sim")
        msg_box.button(QMessageBox.Cancel).setText("Cancelar")

        reply = msg_box.exec()

        if reply == QMessageBox.Yes:
            arquivar_emprestimo(self.emprestimo["id"])
            QMessageBox.information(self, "Arquivado", "Empréstimo arquivado com sucesso!")
            if self.on_save_callback:
                self.on_save_callback()
            self.close()

    def _colorir_linhas(self):
        """Aplica cor de fonte nas parcelas conforme situação (vencimento/data prevista),
        mas somente se o saldo da linha não estiver zerado e a data de pagamento estiver vazia."""
        from datetime import datetime
        from PySide6.QtGui import QColor

        hoje = datetime.today()

        for row in range(self.tabela.rowCount() - 1):  # ignora totalizador
            try:
                # 🔹 Verifica se saldo está zerado
                saldo_txt = self.tabela.item(row, 9).text() if self.tabela.item(row, 9) else ""
                saldo_val = 0.0
                try:
                    saldo_val = float(saldo_txt.replace("R$", "").replace(".", "").replace(",", "."))
                except:
                    saldo_val = 0.0

                if saldo_val == 0:
                    continue  # não aplica cor em parcelas já quitadas

                # 🔹 Verifica se já existe Data de Pagamento
                data_pag_txt = ""
                widget = self.tabela.cellWidget(row, 10)
                if widget:
                    data_pag_txt = widget.text()
                elif self.tabela.item(row, 10):
                    data_pag_txt = self.tabela.item(row, 10).text()

                if data_pag_txt.strip():
                    continue  # já tem data de pagamento → não aplica cor

                # 🔹 Pega valores da linha
                vencimento_txt = self.tabela.item(row, 1).text() if self.tabela.item(row, 1) else ""
                data_prevista_txt = ""
                from parcelas import parcelas
                if row < len(parcelas) and len(parcelas[row]) > 13:
                    data_prevista_txt = parcelas[row][13] or ""

                # 🔹 Converte datas
                vencimento = None
                data_prevista = None
                try:
                    if vencimento_txt:
                        vencimento = datetime.strptime(vencimento_txt, "%d/%m/%Y")
                except:
                    pass
                try:
                    if data_prevista_txt:
                        data_prevista = datetime.strptime(data_prevista_txt, "%d/%m/%Y")
                except:
                    pass

                # 🔹 Define cor apenas se vencimento já passou
                cor = None
                if vencimento and hoje < vencimento:
                    continue  # parcela ainda não venceu → sem cor

                if data_prevista:
                    if hoje <= data_prevista:
                        cor = QColor("#FFC518")  # amarelo (texto)
                    else:
                        cor = QColor("#FF6456")  # vermelho (texto)
                elif vencimento:
                    if hoje > vencimento:
                        cor = QColor("#FF6456")  # vermelho (texto)

                # 🔹 Aplica cor na linha inteira (texto)
                if cor:
                    for col in range(self.tabela.columnCount()):
                        item = self.tabela.item(row, col)
                        if item:
                            item.setForeground(cor)

            except Exception:
                pass
    

    def gerar_pdf(self):

        if self.tabela.rowCount() == 0:
            QMessageBox.warning(self, "Aviso", "Não há dados para exportar.")
            return

        # 🔹 Sugere nome padrão baseado no cliente
        nome_cliente = self.emprestimo.get("cliente", "Cliente")
        nome_arquivo = f"Empréstimo - {nome_cliente}.pdf"

        # Pergunta onde salvar
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar relatório de parcelas",
            nome_arquivo,
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        # Documento base
        doc = SimpleDocTemplate(path, pagesize=A4)
        elementos = []
        estilos = getSampleStyleSheet()

        # 🔹 Título
        titulo = f"Parcelas - {self.emprestimo.get('cliente','')}"
        elementos.append(Paragraph(titulo, estilos['Title']))
        elementos.append(Spacer(1, 12))

        # 🔹 Cabeçalhos
        headers = ["Nº", "Vencimento", "Valor da parcela", "Valor pago", "Saldo", "Data do pag."]
        dados = [headers]


        # 🔹 Preencher linhas (ignora última linha = totalizador)
        for row in range(self.tabela.rowCount() - 1):
            # Nº
            num = self.tabela.item(row, 0).text() if self.tabela.item(row, 0) else ""

            # Vencimento
            venc = self.tabela.item(row, 1).text() if self.tabela.item(row, 1) else ""

            # Valor da parcela = Valor + Juros
            try:
                valor_txt = self.tabela.item(row, 2).text() if self.tabela.item(row, 2) else "0"
                juros_txt = self.tabela.item(row, 3).text() if self.tabela.item(row, 3) else "0"
                valor = float(str(valor_txt).replace("R$", "").replace(".", "").replace(",", ".") or 0)
                juros = float(str(juros_txt).replace("R$", "").replace(".", "").replace(",", ".") or 0)
                valor_total = valor + juros
                valor_fmt = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                valor_fmt = valor_txt

            # Valor pago
            valor_pago = self.tabela.item(row, 8).text() if self.tabela.item(row, 8) else ""

            # Saldo
            saldo = self.tabela.item(row, 9).text() if self.tabela.item(row, 9) else ""

            # Data do pagamento (QLineEdit)
            widget = self.tabela.cellWidget(row, 10)
            data_pag = widget.text() if widget else (self.tabela.item(row, 10).text() if self.tabela.item(row, 10) else "")

            # Monta linha final
            dados.append([num, venc, valor_fmt, valor_pago, saldo, data_pag])

        # 🔹 Criar tabela formatada
        tabela_pdf = Table(dados, repeatRows=1)
        tabela_pdf.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ]))

        elementos.append(tabela_pdf)

        # 🔹 Espaço antes do rodapé
        elementos.append(Spacer(1, 20))

        # 🔹 Data do relatório
        data_atual = datetime.today().strftime("%d/%m/%Y")
        elementos.append(Paragraph(f"Data do relatório: {data_atual}", estilos['Normal']))

        # 🔹 Gerar arquivo
        doc.build(elementos)
        QMessageBox.information(self, "Sucesso", f"Relatório salvo em:\n{path}")
