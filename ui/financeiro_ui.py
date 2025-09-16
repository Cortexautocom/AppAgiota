from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from ui.parcelas_ui import ParcelasWindow

# Importa função para carregar empréstimos reais
from emprestimos import carregar_emprestimos
from parcelas import carregar_parcelas_por_emprestimo

from garantias import (
    carregar_garantias, salvar_garantias,
    adicionar_garantia, sincronizar_garantias_upload, excluir_garantia
)

class FinanceiroWindow(QWidget):
    """
    Tela financeira de um cliente.
    Contém menu lateral (Empréstimos, Garantias) e área de conteúdo.
    """
    def __init__(self, client_data, parent=None):
        super().__init__(parent)

        # 🔹 Define como janela independente, com X e minimizar
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setWindowModality(Qt.NonModal)  # não bloqueia a janela mãe

        self.client_data = client_data
        self.setWindowTitle(f"Financeiro - {client_data[1]}")
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.setFixedSize(900, 600)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Menu lateral
        menu = QFrame()
        menu.setFixedWidth(200)
        menu.setStyleSheet("background-color: #252d3c;")
        menu_layout = QVBoxLayout(menu)

        self.btn_emprestimos = QPushButton("💰 Empréstimos")
        self.btn_emprestimos.setStyleSheet("""
            QPushButton {
                background: none; color: white;
                padding: 12px; text-align: left;
                font-size: 15px; border: none;
            }
            QPushButton:hover {
                background-color: #374157;
                border-radius: 5px;
            }
        """)
        self.btn_emprestimos.clicked.connect(self.show_emprestimos)
        menu_layout.addWidget(self.btn_emprestimos)

        self.btn_garantias = QPushButton("🏦 Garantias")
        self.btn_garantias.setStyleSheet("""
            QPushButton {
                background: none; color: white;
                padding: 12px; text-align: left;
                font-size: 15px; border: none;
            }
            QPushButton:hover {
                background-color: #374157;
                border-radius: 5px;
            }
        """)
        self.btn_garantias.clicked.connect(self.show_garantias)
        menu_layout.addWidget(self.btn_garantias)

        self.btn_arquivados = QPushButton("📂 Empréstimos\n\t\t\t\t\t\t\tArquivados")
        self.btn_arquivados.setStyleSheet("""
            QPushButton {
                background: none; color: white;
                padding: 12px; text-align: left;
                font-size: 15px; border: none;
            }
            QPushButton:hover {
                background-color: #374157;
                border-radius: 5px;
            }
        """)
        self.btn_arquivados.clicked.connect(self.show_arquivados)
        menu_layout.addWidget(self.btn_arquivados)


        menu_layout.addStretch()
        main_layout.addWidget(menu)

        # Área de conteúdo inicial
        self.content = QLabel("Selecione uma opção no menu")
        self.content.setAlignment(Qt.AlignCenter)
        self.content.setStyleSheet("font-size: 18px; color: #9fb0c7;")
        main_layout.addWidget(self.content)

        # 🔹 Abre já na aba Empréstimos
        self.show_emprestimos()

    def _fmt_br(self, valor):
        try:
            valor_float = float(str(valor).replace(",", "."))
            return f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return valor or ""


    # ==============================
    # Aba de Empréstimos
    # ==============================
    def show_emprestimos(self):
        # Container principal
        container = QVBoxLayout()
        frame = QWidget()
        frame.setLayout(container)

        # Botão "Novo Empréstimo"
        btn_novo = QPushButton("➕ Novo Empréstimo")
        btn_novo.setFixedSize(160, 32)
        btn_novo.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 4px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_novo.clicked.connect(self.open_novo_emprestimo)
        container.addWidget(btn_novo)

        # Tabela de empréstimos (agora com 4 colunas: ID oculto + Data + Valor + Status)
        tabela = QTableWidget(0, 8)
        tabela.setSelectionMode(QAbstractItemView.NoSelection)
        tabela.setHorizontalHeaderLabels([
            "ID", "Data inicial", "Último venc.", "Valor", "Parcelas",
            "Juros", "Taxa", "Status"
        ])
        tabela.verticalHeader().setVisible(False)
        tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabela.setColumnHidden(0, True)  # 🔹 Esconde a coluna do ID
        tabela.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446; color: white;
                border: 1px solid #3a455b;
            }
            QHeaderView::section {
                background-color: #374157; color: white;
                padding: 6px; border: none;
            }
        """)

        # 🔹 Carregar empréstimos reais do cliente
        todos_emprestimos = carregar_emprestimos()
        emprestimos_cliente = [e for e in todos_emprestimos if e[1] == self.client_data[0]]

        for linha, emp in enumerate(emprestimos_cliente):
            tabela.insertRow(linha)

            # ID oculto
            item_id = QTableWidgetItem(emp[0])
            item_id.setTextAlignment(Qt.AlignCenter)
            tabela.setItem(linha, 0, item_id)

            # Data inicial
            item_data = QTableWidgetItem(emp[3] or "")
            item_data.setFlags(item_data.flags() & ~Qt.ItemIsEditable)
            item_data.setTextAlignment(Qt.AlignCenter)
            tabela.setItem(linha, 1, item_data)

            # Último venc. (maior vencimento das parcelas)
            from parcelas import carregar_parcelas_por_emprestimo
            parcelas_emp = carregar_parcelas_por_emprestimo(emp[0])  # emp[0] = id do empréstimo
            datas_venc = [p[4] for p in parcelas_emp if p[4]]  # índice 4 = vencimento
            ultimo_venc = max(datas_venc) if datas_venc else ""
            item_ultimo = QTableWidgetItem(ultimo_venc)
            item_ultimo.setFlags(item_ultimo.flags() & ~Qt.ItemIsEditable)
            item_ultimo.setTextAlignment(Qt.AlignCenter)
            tabela.setItem(linha, 2, item_ultimo)

            # Valor
            try:
                valor_float = float(str(emp[2]).replace(",", "."))
                valor_fmt = f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except (ValueError, TypeError):
                valor_fmt = emp[2] or ""
            item_valor = QTableWidgetItem(valor_fmt)
            item_valor.setFlags(item_valor.flags() & ~Qt.ItemIsEditable)
            item_valor.setTextAlignment(Qt.AlignCenter)
            tabela.setItem(linha, 3, item_valor)

            # Parcelas
            item_parcelas = QTableWidgetItem(str(emp[4]) or "")
            item_parcelas.setFlags(item_parcelas.flags() & ~Qt.ItemIsEditable)
            item_parcelas.setTextAlignment(Qt.AlignCenter)
            tabela.setItem(linha, 4, item_parcelas)

            # Juros
            item_juros = QTableWidgetItem(self._fmt_br(emp[6]))
            item_juros.setFlags(item_juros.flags() & ~Qt.ItemIsEditable)
            item_juros.setTextAlignment(Qt.AlignCenter)
            tabela.setItem(linha, 5, item_juros)

            # Taxa (antes Observação → agora na coluna 6)
            taxa_txt = emp[5] or ""
            if taxa_txt.lower().startswith("taxa "):
                taxa_txt = taxa_txt[5:]  # remove o prefixo "Taxa "
            item_taxa = QTableWidgetItem(taxa_txt)
            item_taxa.setFlags(item_taxa.flags() & ~Qt.ItemIsEditable)
            item_taxa.setTextAlignment(Qt.AlignCenter)
            tabela.setItem(linha, 6, item_taxa)

            # Status
            status = "Em andamento"
            item_status = QTableWidgetItem(status)
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)
            item_status.setForeground(Qt.green)
            item_status.setTextAlignment(Qt.AlignCenter)
            tabela.setItem(linha, 7, item_status)

        # 🔹 Conectar duplo clique para abrir parcelas
        tabela.cellDoubleClicked.connect(lambda row, col: self.abrir_parcelas(row))
        self.tabela_emprestimos = tabela

        container.addWidget(tabela)
        self._set_content(frame)

    def abrir_parcelas(self, row):
        emprestimo_id = self.tabela_emprestimos.item(row, 0).text()
        parcelas = carregar_parcelas_por_emprestimo(emprestimo_id)
        
        todos = carregar_emprestimos()
        emp = next((e for e in todos if e[0] == emprestimo_id), None)

        self.parcelas_window = ParcelasWindow(
            {
                "id": emprestimo_id,
                "capital": emp[2] if emp else "0",
                "meses": emp[4] if emp else "1",
                "juros": emp[6] if emp else "0",
                "prestacao": emp[7] if emp else "0",
                "parcelas": parcelas,
                "data_inicio": self.tabela_emprestimos.item(row, 1).text(),
                "cliente": self.client_data[1]
            },
            id_usuario=self.parent().id_usuario,
            parent=self,
            on_save_callback=self.show_emprestimos
        )

        self.parcelas_window.show()



    def _set_content(self, widget):
        """Substitui o conteúdo da área central."""
        old = self.content
        self.layout().removeWidget(old)
        old.deleteLater()
        self.content = widget
        self.layout().addWidget(self.content)

    def open_novo_emprestimo(self):
        from ui.emprestimos_ui import EmprestimoForm
        from ui.parcelas_ui import ParcelasWindow

        def callback(data):
            # 🔹 Recarregar do banco local para garantir que o novo empréstimo esteja disponível
            from emprestimos import carregar_emprestimos
            self.emprestimos = carregar_emprestimos()

            # 🔹 Atualizar a lista de empréstimos do cliente
            self.show_emprestimos()

            # 🔹 E só depois abrir a tela de parcelas
            self.parcelas_window = ParcelasWindow(
                {
                    "id": data["id"],
                    "capital": data["capital"],
                    "meses": data["meses"],           # 🔹 incluir
                    "juros": data["juros"],
                    "prestacao": data["prestacao"],   # 🔹 incluir
                    "parcelas": data["parcelas"],
                    "data_inicio": data.get("data_inicio", ""),
                    "cliente": self.client_data[1]
                },
                id_usuario=self.parent().id_usuario,
                parent=self
            )

            self.parcelas_window.show()

        # ✅ Passa o id_usuario do ModernWindow
        self.form_emprestimo = EmprestimoForm(
            callback,
            id_cliente=self.client_data[0],
            id_usuario=self.parent().id_usuario,
            parent=self
        )
        self.form_emprestimo.show()


    # ==============================
    def show_garantias(self):
        container = QVBoxLayout()
        frame = QWidget()
        frame.setLayout(container)

        # Botão "Nova Garantia" (AGORA VERDE, igual "Novo Cliente")
        btn_nova = QPushButton("➕ Nova Garantia")
        btn_nova.setFixedSize(160, 32)
        btn_nova.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71; color: white;
                padding: 6px 10px; font-size: 12px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        btn_nova.clicked.connect(self.open_nova_garantia)
        container.addWidget(btn_nova, alignment=Qt.AlignLeft)

        # Tabela de garantias
        self.tabela_garantias = QTableWidget(0, 4)
        self.tabela_garantias.cellDoubleClicked.connect(self.editar_garantia)
        self.tabela_garantias.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabela_garantias.setHorizontalHeaderLabels(["Nº", "Descrição e detalhes da garantia", "Valor", "Excluir"])

        header = self.tabela_garantias.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #374157; color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)

        # Colunas
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tabela_garantias.setColumnWidth(0, 40)

        header.setSectionResizeMode(1, QHeaderView.Stretch)

        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.tabela_garantias.setColumnWidth(2, 150)

        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.tabela_garantias.setColumnWidth(3, 60)

        # Estilo                
        self.tabela_garantias.verticalHeader().setVisible(False)
        self.tabela_garantias.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabela_garantias.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446; color: white;
                border: 1px solid #3a455b;
                font-size: 14px;
            }
        """)
        self.tabela_garantias.verticalHeader().setDefaultSectionSize(80)

        container.addWidget(self.tabela_garantias)

        # 🔹 carregar garantias reais do cliente
        garantias_cliente = [g for g in carregar_garantias(self.parent().id_usuario) if g[1] == self.client_data[0]]
        for idx, g in enumerate(garantias_cliente, start=1):
            row_atual = self.tabela_garantias.rowCount()
            self.tabela_garantias.insertRow(row_atual)

            # Nº
            num_item = QTableWidgetItem(str(idx))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.tabela_garantias.setItem(row_atual, 0, num_item)

            # Descrição
            desc_item = QTableWidgetItem(g[2])
            self.tabela_garantias.setItem(row_atual, 1, desc_item)

            # Valor
            val_item = QTableWidgetItem(g[3])
            val_item.setTextAlignment(Qt.AlignCenter)
            self.tabela_garantias.setItem(row_atual, 2, val_item)

            # Botão excluir
            btn_excluir = QPushButton("🗑")
            btn_excluir.setToolTip("Excluir garantia")
            btn_excluir.setFixedSize(28, 28)
            btn_excluir.setStyleSheet("""
                QPushButton {
                    background: none; color: #e74c3c;
                    border: none; font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #3a455b;
                    border-radius: 6px;
                }
            """)
            garantia_id = g[0]
            btn_excluir.clicked.connect(lambda _, r=row_atual, gid=garantia_id: self.excluir_garantia(r, gid))

            widget_excluir = QWidget()
            lay_excluir = QHBoxLayout(widget_excluir)
            lay_excluir.setContentsMargins(0, 0, 0, 0)
            lay_excluir.addStretch()
            lay_excluir.addWidget(btn_excluir)
            lay_excluir.addStretch()

            self.tabela_garantias.setCellWidget(row_atual, 3, widget_excluir)

        self.add_totalizador()
        self.atualizar_totalizador()

        self._set_content(frame)

    def excluir_garantia(self, row, garantia_id):
        from PySide6.QtWidgets import QMessageBox
        from garantias import excluir_garantia as excluir_garantia_db

        reply = QMessageBox.question(
            self,
            "Confirmação",
            "Tem certeza que deseja excluir esta garantia?",
            QMessageBox.Yes | QMessageBox.Cancel
        )
        if reply != QMessageBox.Yes:
            return

        # 🔹 Exclui do banco local + Supabase
        excluir_garantia_db(garantia_id)

        # 🔹 Remove da tabela
        self.tabela_garantias.removeRow(row)

        # 🔹 Atualiza totalizador
        self.atualizar_totalizador()


    def open_nova_garantia(self):
        from ui.garantias_ui import GarantiaForm

        def callback(data):
            nova = adicionar_garantia(
                id_cliente=self.client_data[0],
                descricao=data["descricao"],
                valor=data["valor"],
                id_usuario=self.parent().id_usuario
            )
            salvar_garantias()
            sincronizar_garantias_upload()

            row = self.tabela_garantias.rowCount() - 1
            self.tabela_garantias.insertRow(row)

            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.tabela_garantias.setItem(row, 0, num_item)

            desc_item = QTableWidgetItem(nova[2])
            self.tabela_garantias.setItem(row, 1, desc_item)

            val_item = QTableWidgetItem(nova[3])
            val_item.setTextAlignment(Qt.AlignCenter)
            self.tabela_garantias.setItem(row, 2, val_item)

            # Botão excluir
            btn_excluir = QPushButton("🗑")
            btn_excluir.setToolTip("Excluir garantia")
            btn_excluir.setFixedSize(28, 28)
            btn_excluir.setStyleSheet("""
                QPushButton {
                    background: none; color: #e74c3c;
                    border: none; font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #3a455b;
                    border-radius: 6px;
                }
            """)
            garantia_id = nova[0]
            btn_excluir.clicked.connect(lambda _, r=row, gid=garantia_id: self.excluir_garantia(r, gid))

            widget_excluir = QWidget()
            lay_excluir = QHBoxLayout(widget_excluir)
            lay_excluir.setContentsMargins(0, 0, 0, 0)
            lay_excluir.addStretch()
            lay_excluir.addWidget(btn_excluir)
            lay_excluir.addStretch()

            self.tabela_garantias.setCellWidget(row, 3, widget_excluir)

            self.atualizar_totalizador()

        self.form_garantia = GarantiaForm(callback, parent=self)
        self.form_garantia.show()


    
    def add_totalizador(self):
        """Adiciona linha de totalizadores na tabela de garantias."""
        row = self.tabela_garantias.rowCount()
        self.tabela_garantias.insertRow(row)

        # Coluna Nº (em branco)
        item_num = QTableWidgetItem("")
        item_num.setFlags(item_num.flags() & ~Qt.ItemIsEditable)
        item_num.setBackground(QColor("#2c3446"))
        self.tabela_garantias.setItem(row, 0, item_num)

        # Coluna descrição = "TOTAL"
        item_desc = QTableWidgetItem("TOTAL")
        item_desc.setFlags(item_desc.flags() & ~Qt.ItemIsEditable)
        item_desc.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_desc.setBackground(QColor("#2c3446"))
        font = item_desc.font()
        font.setBold(True)
        item_desc.setFont(font)
        item_desc.setForeground(QColor("#00bfff"))  # azul claro
        self.tabela_garantias.setItem(row, 1, item_desc)

        # Coluna valor
        item_total = QTableWidgetItem("R$ 0,00")
        item_total.setFlags(item_total.flags() & ~Qt.ItemIsEditable)
        item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_total.setBackground(QColor("#2c3446"))
        item_total.setFont(font)
        item_total.setForeground(QColor("#00bfff"))
        self.tabela_garantias.setItem(row, 2, item_total)

    def editar_garantia(self, row, col):
        """Abre o form para editar a garantia clicada."""
        # Ignora se clicou no totalizador (última linha)
        if row == self.tabela_garantias.rowCount() - 1:
            return

        desc = self.tabela_garantias.item(row, 1).text()
        val = self.tabela_garantias.item(row, 2).text()

        from ui.garantias_ui import GarantiaForm
        from garantias import garantias, salvar_garantias, sincronizar_garantias_upload

        # Descobre o id da garantia correspondente à linha
        garantia_id = None
        if row < len(garantias):
            garantia_id = garantias[row][0]

        def callback(data):
            # Atualiza a linha editada na tabela
            self.tabela_garantias.item(row, 1).setText(data["descricao"])
            self.tabela_garantias.item(row, 2).setText(data["valor"])

            # Atualiza na lista em memória também
            if garantia_id:
                for i, g in enumerate(garantias):
                    if g[0] == garantia_id:
                        garantias[i] = (g[0], g[1], data["descricao"], data["valor"], g[4])
                        break

            # 🔹 salvar no banco e sincronizar
            salvar_garantias()
            sincronizar_garantias_upload()

            # Recria o botão excluir para garantir que continua funcionando
            btn_excluir = QPushButton("🗑")
            btn_excluir.setToolTip("Excluir garantia")
            btn_excluir.setFixedSize(28, 28)
            btn_excluir.setStyleSheet("""
                QPushButton {
                    background: none; color: #e74c3c;
                    border: none; font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #3a455b;
                    border-radius: 6px;
                }
            """)
            btn_excluir.clicked.connect(lambda _, r=row, gid=garantia_id: self.excluir_garantia(r, gid))

            widget_excluir = QWidget()
            lay_excluir = QHBoxLayout(widget_excluir)
            lay_excluir.setContentsMargins(0, 0, 0, 0)
            lay_excluir.addStretch()
            lay_excluir.addWidget(btn_excluir)
            lay_excluir.addStretch()

            self.tabela_garantias.setCellWidget(row, 3, widget_excluir)

            # Atualiza o totalizador
            self.atualizar_totalizador()

        # 🔹 Abre o formulário preenchido com os dados atuais
        self.form_garantia = GarantiaForm(callback, parent=self)
        self.form_garantia.inp_desc.setPlainText(desc)
        self.form_garantia.inp_valor.setText(val)
        self.form_garantia.show()


    def atualizar_totalizador(self):
        """Recalcula o total das garantias."""
        total = 0.0
        row_count = self.tabela_garantias.rowCount()

        # percorre todas as linhas menos a última (totalizador)
        for r in range(row_count - 1):
            val_item = self.tabela_garantias.item(r, 2)
            if val_item:
                txt = val_item.text().replace("R$", "").replace(".", "").replace(",", ".").strip()
                try:
                    total += float(txt)
                except:
                    pass

        total_fmt = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self.tabela_garantias.item(row_count - 1, 2).setText(total_fmt)

    def show_arquivados(self):
        from ui.arquivados_ui import ArquivadosWindow
        self.arquivados_window = ArquivadosWindow(
            self.client_data,
            id_usuario=self.parent().id_usuario,  # ✅ aqui vem do ModernWindow
            parent=self
        )
        self._set_content(self.arquivados_window)

