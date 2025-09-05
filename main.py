# 🔧 Sistema e banco
import os, sys
import uuid
from ui.login_ui import LoginWindow

from ui.clientes_ui import ClientForm
# 🎨 Interface gráfica (PySide6)
from PySide6.QtCore import (
    QRunnable, QThreadPool, Qt, QTimer,
    
)
from ui.emprestimos_ui import EmprestimoForm

from ui.splash import SplashScreen

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QGraphicsDropShadowEffect,
    QMessageBox, QStyleFactory, QAbstractItemView
)

from PySide6.QtGui import QColor
from ui.financeiro_ui import FinanceiroWindow

# Config
from config import criar_tabelas_local, get_local_db_path, verificar_tabelas

criar_tabelas_local()

# ☁️ Supabase (sincronização)
from supabase_utils import (
    baixar_clientes, enviar_clientes,
    baixar_emprestimos, enviar_emprestimos,
    baixar_parcelas, enviar_parcelas,
    baixar_movimentacoes, enviar_movimentacoes
)

# 📦 Módulos de dados
from clientes import (
    clientes, carregar_clientes, salvar_clientes,
    sincronizar_clientes_download, sincronizar_clientes_upload
)
from emprestimos import (
    emprestimos, carregar_emprestimos, salvar_emprestimos,
    sincronizar_emprestimos_download, sincronizar_emprestimos_upload
)
from parcelas import (
    parcelas, carregar_parcelas, salvar_parcelas,
    sincronizar_parcelas_download, sincronizar_parcelas_upload
)
from movimentacoes import (
    movimentacoes, carregar_movimentacoes, salvar_movimentacoes,
    sincronizar_movimentacoes_download, sincronizar_movimentacoes_upload
)


def resource_path(relative_path):
    """Obtém o caminho do recurso (funciona no .exe e no modo normal)."""
    try:
        # PyInstaller cria uma pasta temporária e guarda tudo lá
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



# =====================================================================
# ModernWindow
# =====================================================================
class ModernWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.offset = None

        self.setWindowTitle("O Agiota")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(1200, 700)
        self.setStyleSheet("""
            QScrollBar:vertical {
                background: #252d3c;
                width: 10px;
                margin: 4px 0 4px 0;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #3a455b;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a5671;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
        """)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 🔹 Dados em memória (vêm dos módulos)
        self.clients = clientes
        self.emprestimos = emprestimos
        self.parcelas = parcelas
        self.movimentacoes = movimentacoes

        # 🔹 Carrega dados do banco local na inicialização
        self.load_local_db()

        # 🔹 Layout principal da interface
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.create_top_bar())

        self.main_content_layout = QHBoxLayout()
        main_layout.addLayout(self.main_content_layout)

        # Menu lateral
        self.menu = self.create_menu()
        self.main_content_layout.addWidget(self.menu)

        # Área de conteúdo
        self.content_area = QLabel("Conteúdo principal aqui")
        self.content_area.setStyleSheet("color: #ccc; font-size: 24px;")
        self.content_area.setAlignment(Qt.AlignCenter)
        self.main_content_layout.addWidget(self.content_area)

        # 🔹 Casca visual com sombra e cantos arredondados
        shell = QFrame()
        shell.setObjectName("Shell")

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setObjectName("Content")
        content.setLayout(main_layout)
        shell_layout.addWidget(content)

        shell.setStyleSheet("""
            QFrame#Shell { background-color: transparent; }
            QWidget#Content {
                background-color: #1c2331;
                border-radius: 16px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 140))
        content.setGraphicsEffect(shadow)

        self.setCentralWidget(shell)
        self.center()

    # ======== Top bar ========
    def create_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(50)
        bar.setStyleSheet("""
            background-color: #2c3446;
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)

        # Logo
        logo = QLabel("🛡️ O Agiota")
        logo.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(logo)

        layout.addStretch()

        # Minimizar
        btn_min = QPushButton("➖")
        btn_min.setFixedSize(30, 30)
        btn_min.setStyleSheet("""
            QPushButton {
                background: none; color: white;
                font-size: 16px; border: none;
            }
            QPushButton:hover {
                background-color: #3b465e;
                border-radius: 6px;
            }
        """)
        btn_min.clicked.connect(self.showMinimized)
        layout.addWidget(btn_min)

        # Fechar
        btn_close = QPushButton("❌")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("""
            QPushButton {
                background: none; color: white;
                font-size: 16px; border: none;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                border-radius: 6px;
            }
        """)
        btn_close.clicked.connect(self.handle_close)
        layout.addWidget(btn_close)

        # Arrastar a janela
        bar.mousePressEvent = self.mouse_press_event
        bar.mouseMoveEvent = self.mouse_move_event

        return bar

    # ======== Ações de janela ========
    def handle_close(self):
        """Salva no SQLite e no Supabase antes de fechar, em segundo plano."""
        try:
            self.save_local_db_background()
        except Exception as e:
            print(f"⚠ Erro ao salvar antes de fechar: {e}")
        self.close()

    def mouse_press_event(self, event):
        """Captura a posição inicial para permitir arrastar a janela."""
        if event.button() == Qt.LeftButton:
            self.offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouse_move_event(self, event):
        """Permite mover a janela enquanto o botão esquerdo do mouse está pressionado."""
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)

    # ======== Menu lateral ========
    def create_menu(self):
        menu = QFrame()
        menu.setFixedWidth(220)
        menu.setStyleSheet("background-color: #252d3c;")

        menu_layout = QVBoxLayout(menu)

        # Botão para abrir pesquisa de clientes
        self.btn_clientes = QPushButton("👤 Clientes")
        self.btn_clientes.setStyleSheet("""
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
        self.btn_clientes.clicked.connect(self.show_search_screen)
        menu_layout.addWidget(self.btn_clientes)

        # Botão para funções extras
        self.btn_extras = QPushButton("⚙️ Funções Extras")
        self.btn_extras.setStyleSheet("""
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
        self.btn_extras.clicked.connect(self.show_extras_screen)
        menu_layout.addWidget(self.btn_extras)

        menu_layout.addStretch()
        return menu

    # ======== Formulário de Cliente ========
    def open_client_form(self, initial_data=None, edit_index=None):
        def callback(data):
            if edit_index is None:  # ✅ Novo cliente
                cliente_tuple = (
                    str(uuid.uuid4()),  # gera UUID apenas na criação
                    data.get("Nome", ""),
                    data.get("CPF", ""),
                    data.get("Telefone", ""),
                    data.get("Endereço", ""),
                    data.get("Cidade", ""),
                    data.get("Indicação", "")
                )
                self.clients.append(cliente_tuple)
            else:  # ✅ Edição de cliente existente
                id_cliente = self.clients[edit_index][0]  # mantém o mesmo ID
                cliente_tuple = (
                    id_cliente,
                    data.get("Nome", ""),
                    data.get("CPF", ""),
                    data.get("Telefone", ""),
                    data.get("Endereço", ""),
                    data.get("Cidade", ""),
                    data.get("Indicação", "")
                )
                self.clients[edit_index] = cliente_tuple

            

            # Salva no banco local
            self.save_local_db()

            # Atualiza a tabela da interface se existir
            if hasattr(self, "table_results"):
                self.rebuild_search_filters()
                self.apply_search_filters()

        # monta lista de cidades a partir da memória
        try:
            idx_cidade = 5  # agora 'cidade' é índice 5
            cities = sorted({
                str(c[idx_cidade]).strip()
                for c in self.clients
                if len(c) > idx_cidade and str(c[idx_cidade]).strip()
            })
        except Exception as e:
            print(f"ℹ Falha ao montar lista de cidades: {e}")
            cities = []

        self.form = ClientForm(callback, initial_data=initial_data, cities=cities)
        self.form.show()

    # ======== Tela de Pesquisa ========
    def show_search_screen(self):
        self.search_widget = QWidget()
        layout = QVBoxLayout(self.search_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Topo: título + "Novo Cliente"
        top_row = QHBoxLayout()
        title = QLabel("🔎 Clientes")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        top_row.addWidget(title)
        top_row.addStretch()

        btn_add = QPushButton("➕ Novo Cliente")
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71; color: white;
                padding: 6px 10px; font-size: 12px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        btn_add.setFixedWidth(max(120, self.width() // 8))
        btn_add.clicked.connect(self.open_client_form)
        top_row.addWidget(btn_add)

        layout.addLayout(top_row)

        # Linha de filtros com alinhamento inferior
        filters_row = QHBoxLayout()
        filters_row.setAlignment(Qt.AlignBottom)

        # ===== Nome =====
        box_nome = QVBoxLayout()
        lbl_nome = QLabel("Nome")
        lbl_nome.setStyleSheet("color:#9fb0c7; font-size:12px;")
        box_nome.addWidget(lbl_nome)

        self.cb_nome = QComboBox()
        self.cb_nome.setEditable(False)
        self.cb_nome.setStyleSheet("""
            QComboBox {
                background-color:#2c3446; color:white;
                padding:6px; border-radius:6px;
            }
            QComboBox QAbstractItemView {
                background-color:#2c3446; color:white;
                selection-background-color:#374157;
            }
        """)
        self.cb_nome.setPlaceholderText("Selecione um nome")
        box_nome.addWidget(self.cb_nome)
        filters_row.addLayout(box_nome)

        # ===== Cidade =====
        box_cidade = QVBoxLayout()
        lbl_cidade = QLabel("Cidade")
        lbl_cidade.setStyleSheet("color:#9fb0c7; font-size:12px;")
        box_cidade.addWidget(lbl_cidade)

        self.cb_cidade = QComboBox()
        self.cb_cidade.setEditable(False)
        self.cb_cidade.setStyleSheet("""
            QComboBox {
                background-color:#2c3446; color:white;
                padding:6px; border-radius:6px;
            }
            QComboBox QAbstractItemView {
                background-color:#2c3446; color:white;
                selection-background-color:#374157;
            }
        """)
        self.cb_cidade.setPlaceholderText("Selecione uma cidade")
        box_cidade.addWidget(self.cb_cidade)
        filters_row.addLayout(box_cidade)

        # ===== Indicação =====
        box_ind = QVBoxLayout()
        lbl_ind = QLabel("Indicação")
        lbl_ind.setStyleSheet("color:#9fb0c7; font-size:12px;")
        box_ind.addWidget(lbl_ind)

        self.cb_indicacao = QComboBox()
        self.cb_indicacao.setEditable(False)
        self.cb_indicacao.setStyleSheet("""
            QComboBox {
                background-color:#2c3446; color:white;
                padding:6px; border-radius:6px;
            }
            QComboBox QAbstractItemView {
                background-color:#2c3446; color:white;
                selection-background-color:#374157;
            }
        """)
        self.cb_indicacao.setPlaceholderText("Selecione uma indicação")
        box_ind.addWidget(self.cb_indicacao)
        filters_row.addLayout(box_ind)

        # Botões Buscar / Limpar
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setStyleSheet("""
            QPushButton {
                background-color:#3498db; color:white;
                padding:8px 12px; border-radius:8px;
            }
            QPushButton:hover { background-color:#2980b9; }
        """)
        btn_buscar.clicked.connect(self.apply_search_filters)
        filters_row.addWidget(btn_buscar, alignment=Qt.AlignBottom)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setStyleSheet("""
            QPushButton {
                background-color:#34495e; color:white;
                padding:8px 12px; border-radius:8px;
            }
            QPushButton:hover { background-color:#2c3e50; }
        """)
        btn_limpar.clicked.connect(self.clear_search_filters)
        filters_row.addWidget(btn_limpar, alignment=Qt.AlignBottom)

        layout.addLayout(filters_row)

        # Tabela de resultados
        self.table_results = QTableWidget(0, 7)
        self.table_results.cellDoubleClicked.connect(self.abrir_financeiro_cliente)

        self.table_results.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_results.setHorizontalHeaderLabels(
            ["Nome", "CPF", "Endereço", "Cidade", "Telefone", "Indicação", "Ações"]
        )
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_results.setStyleSheet("""
            QTableWidget {
                background-color: #2c3446; color: white;
                border: 1px solid #3a455b;
            }
            QHeaderView::section {
                background-color: #374157; color: white;
                padding: 6px; border: none;
            }
        """)
        layout.addWidget(self.table_results)

        self._replace_main_content(self.search_widget)

        # Popular filtros e mostrar tudo
        self.rebuild_search_filters()
        self.apply_search_filters()

    def abrir_financeiro_cliente(self, row, col):
        """Abre a aba Financeiro do cliente ao dar duplo clique na tabela."""
        if row < 0 or row >= len(self.clients):
            return

        cliente = self.clients[row]  # tupla (id_cliente, nome, cpf, telefone, endereco, cidade, indicacao)

        # 🔹 Abre a janela FinanceiroWindow já focada
        self.finance_window = FinanceiroWindow(cliente, parent=self)
        self.finance_window.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.finance_window.setAttribute(Qt.WA_DeleteOnClose)  
        self.finance_window.show()


    # ======== Filtros de pesquisa ========
    def rebuild_search_filters(self):
        """Atualiza as listas suspensas com valores únicos existentes nos clientes."""
        # NOVOS ÍNDICES com base na nova tupla:
        # (0:id_cliente, 1:nome, 2:cpf, 3:telefone, 4:endereco, 5:cidade, 6:indicacao)
        campos = {
            "Nome": 1,
            "Cidade": 5,
            "Indicação": 6
        }

        def unique_values(key):
            idx = campos.get(key)
            if idx is None:
                return [""]
            vals = sorted(set([
                str(c[idx]).strip() for c in self.clients if str(c[idx]).strip()
            ]))
            return [""] + vals

        cur_nome = self.cb_nome.currentText() if self.cb_nome.count() else ""
        cur_cidade = self.cb_cidade.currentText() if self.cb_cidade.count() else ""
        cur_ind = self.cb_indicacao.currentText() if self.cb_indicacao.count() else ""

        self.cb_nome.clear()
        self.cb_nome.addItems(unique_values("Nome"))
        self.cb_cidade.clear()
        self.cb_cidade.addItems(unique_values("Cidade"))
        self.cb_indicacao.clear()
        self.cb_indicacao.addItems(unique_values("Indicação"))

        self._set_combobox_if_present(self.cb_nome, cur_nome)
        self._set_combobox_if_present(self.cb_cidade, cur_cidade)
        self._set_combobox_if_present(self.cb_indicacao, cur_ind)


    def _set_combobox_if_present(self, cb: QComboBox, value: str):
        idx = cb.findText(value)
        cb.setCurrentIndex(idx if idx >= 0 else 0)

    def clear_search_filters(self):
        """Reseta todos os filtros e recarrega a lista completa."""
        if hasattr(self, "cb_nome"):
            self.cb_nome.setCurrentIndex(0)
        if hasattr(self, "cb_cidade"):
            self.cb_cidade.setCurrentIndex(0)
        if hasattr(self, "cb_indicacao"):
            self.cb_indicacao.setCurrentIndex(0)
        self.apply_search_filters()


    def apply_search_filters(self):
        """Filtra a lista de clientes de acordo com os filtros selecionados (sem salvar no SQLite)."""
        nome = self.cb_nome.currentText().strip().lower() if hasattr(self, "cb_nome") else ""
        cidade = self.cb_cidade.currentText().strip().lower() if hasattr(self, "cb_cidade") else ""
        indicacao = self.cb_indicacao.currentText().strip().lower() if hasattr(self, "cb_indicacao") else ""

        filtered = []
        for c in self.clients:
            # c = (id_cliente, nome, cpf, telefone, endereco, cidade, indicacao)
            ok_nome = (c[1].strip().lower() == nome) if nome else True
            ok_cidade = (c[5].strip().lower() == cidade) if cidade else True
            ok_ind = (c[6].strip().lower() == indicacao) if indicacao else True
            if ok_nome and ok_cidade and ok_ind:
                filtered.append(c)

        # Evita disparar handle_table_edit durante a repopulação
        if self.table_results.receivers("itemChanged(QTableWidgetItem*)") > 0:
            self.table_results.itemChanged.disconnect(self.handle_table_edit)

        self.table_results.setRowCount(0)

        for c in filtered:
            row = self.table_results.rowCount()
            self.table_results.insertRow(row)

            # Cabeçalhos visuais: ["Nome", "CPF", "Endereço", "Cidade", "Telefone", "Indicação", "Ações"]

            # Nome
            item_nome = QTableWidgetItem(c[1])
            item_nome.setFlags(item_nome.flags() & ~Qt.ItemIsEditable)
            self.table_results.setItem(row, 0, item_nome)

            # CPF
            item_cpf = QTableWidgetItem(c[2])
            item_cpf.setFlags(item_cpf.flags() & ~Qt.ItemIsEditable)
            self.table_results.setItem(row, 1, item_cpf)

            # Endereço
            item_endereco = QTableWidgetItem(c[4])
            item_endereco.setFlags(item_endereco.flags() & ~Qt.ItemIsEditable)
            self.table_results.setItem(row, 2, item_endereco)

            # Cidade
            item_cidade = QTableWidgetItem(c[5])
            item_cidade.setFlags(item_cidade.flags() & ~Qt.ItemIsEditable)
            self.table_results.setItem(row, 3, item_cidade)

            # Telefone
            item_tel = QTableWidgetItem(c[3])
            item_tel.setFlags(item_tel.flags() & ~Qt.ItemIsEditable)
            self.table_results.setItem(row, 4, item_tel)

            # Indicação
            item_indicacao = QTableWidgetItem(c[6])
            item_indicacao.setFlags(item_indicacao.flags() & ~Qt.ItemIsEditable)
            self.table_results.setItem(row, 5, item_indicacao)
            
            # Layout horizontal para os botões de ação
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(6)

            # Botão 📑 Financeiro
            btn_financeiro = QPushButton("📑")
            btn_financeiro.setFixedSize(28, 28)
            btn_financeiro.setToolTip("Financeiro")
            btn_financeiro.setStyleSheet("""
                QPushButton {
                    background: none; color: white;
                    border: none; font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #3a455b;
                    border-radius: 6px;
                }
            """)
            btn_financeiro.clicked.connect(lambda _, cliente=c: self.open_dados_cliente(cliente))
            action_layout.addWidget(btn_financeiro)

            # Botão ✏️ Editar Cliente
            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(28, 28)
            btn_edit.setToolTip("Editar dados")
            btn_edit.setStyleSheet("""
                QPushButton {
                    background: none; color: white;
                    border: none; font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #3a455b;
                    border-radius: 6px;
                }
            """)
            btn_edit.clicked.connect(lambda _, cliente=c: self.open_client_form(
                initial_data={
                    "Nome": cliente[1],
                    "CPF": cliente[2],
                    "Telefone": cliente[3],
                    "Endereço": cliente[4],
                    "Cidade": cliente[5],
                    "Indicação": cliente[6]
                },
                edit_index=next((i for i, cli in enumerate(self.clients) if cli[0] == cliente[0]), None)
            ))
            action_layout.addWidget(btn_edit)

            self.table_results.setCellWidget(row, 6, action_widget)

        self.table_results.itemChanged.connect(self.handle_table_edit)

    def open_finance_form(self, client_data):
        """Abre o formulário de empréstimo para o cliente selecionado."""
        def callback(data):
            print("💰 Empréstimo salvo para cliente:", client_data[1])
            print("Dados do empréstimo:", data)

        self.form_emprestimo = EmprestimoForm(callback)
        self.form_emprestimo.show()


    # ======== Edição inline da tabela ========
    def handle_table_edit(self, item):
        """Atualiza os dados do cliente na lista quando uma célula da tabela é editada."""
        row = item.row()
        col = item.column()
        novo_valor = item.text().strip()

        # Colunas visuais -> campos reais (índices na tupla)
        # Tabela mostra: 0 Nome, 1 CPF, 2 Endereço, 3 Cidade, 4 Telefone, 5 Indicação
        # Tupla real: (0:id_cliente, 1:nome, 2:cpf, 3:telefone, 4:endereco, 5:cidade, 6:indicacao)
        mapeamento = {
            2: 4,  # Endereço
            3: 5,  # Cidade
            4: 3,  # Telefone
            # 0 Nome, 1 CPF, 5 Indicação estão não editáveis (bloqueados)
        }

        if col not in mapeamento:
            return  # coluna não editável

        idx_real = mapeamento[col]
        cliente = self.clients[row]
        valor_antigo = cliente[idx_real]

        if novo_valor != valor_antigo:
            cliente_atualizado = list(cliente)
            cliente_atualizado[idx_real] = novo_valor
            self.clients[row] = tuple(cliente_atualizado)
            self.save_local_db()


    # ======== Banco Local ========
    def load_local_db(self):
        """Carrega dados locais de clientes, empréstimos, parcelas e movimentações."""
        try:
            self.clients = carregar_clientes()
            self.emprestimos = carregar_emprestimos()
            self.parcelas = carregar_parcelas()
            self.movimentacoes = carregar_movimentacoes()

            
        except Exception as e:
            print(f"⚠ Erro ao carregar banco local: {e}")


    def save_local_db(self):
        """Salva todos os dados locais no banco."""
        try:
            salvar_clientes(self.clients)
            salvar_emprestimos()
            salvar_parcelas()
            salvar_movimentacoes()
            
        except Exception as e:
            print(f"⚠ Erro ao salvar no banco local: {e}")

    # ======== Utilidades ========
    def _replace_main_content(self, new_widget: QWidget):
        old = self.main_content_layout.itemAt(1).widget()
        old.setParent(None)
        self.main_content_layout.addWidget(new_widget)

    def center(self):
        """Centraliza a janela na tela."""
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())

    # ======== Tela de Funções Extras ========
    def show_extras_screen(self):
        """Exibe uma tela de funções extras com opção de backup em nuvem."""
        self.extras_widget = QWidget()
        layout = QVBoxLayout(self.extras_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Título
        title = QLabel("⚙️ Funções Extras")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        layout.addSpacing(20)

        # Mensagem de status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ccc; font-size: 16px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addSpacing(20)

        # Botão de backup
        btn_backup = QPushButton("☁️ Enviar dados para núvem")
        btn_backup.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                padding: 10px; border-radius: 8px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_backup.clicked.connect(self._backup_em_nuvem)
        layout.addWidget(btn_backup, alignment=Qt.AlignCenter)
        layout.addSpacing(20)

        # Botão para baixar dados do Supabase
        btn_download = QPushButton("📥 Baixar dados da nuvem")
        btn_download.setStyleSheet("""
            QPushButton {
                background-color: #f39c12; color: white;
                padding: 10px; border-radius: 8px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #d68910; }
        """)
        btn_download.clicked.connect(self.acao_download_supabase)
        layout.addWidget(btn_download, alignment=Qt.AlignCenter)

        self._replace_main_content(self.extras_widget)

    # ======== Download do Supabase ========
    def acao_download_supabase(self):
        """Baixa dados da nuvem (Supabase) e atualiza a interface."""
        reply = QMessageBox.question(
            self,
            "Confirmação",
            "⚠ Esta ação pode gerar a exclusão de dados locais.\n\nTem certeza que deseja prosseguir?",
            QMessageBox.Yes | QMessageBox.Cancel
        )
        if reply != QMessageBox.Yes:
            print("ℹ Operação de download cancelada pelo usuário.")
            return

        # 🔹 Sincroniza dados de cada módulo
        try:
            sincronizar_clientes_download()
            sincronizar_emprestimos_download()
            sincronizar_parcelas_download()
            sincronizar_movimentacoes_download()

            self.load_local_db()
            self.show_search_screen()
            self.rebuild_search_filters()
            self.apply_search_filters()

            
        except Exception as e:
            print(f"⚠ Erro ao baixar dados do Supabase: {e}")

    # ======== Upload / Backup na nuvem ========
    def _backup_em_nuvem(self):
        """Executa salvamento local e em nuvem em segundo plano, com confirmação."""
        reply = QMessageBox.question(
            self,
            "Confirmação",
            "⚠ Esta ação pode gerar a exclusão de dados da nuvem.\n\nTem certeza que deseja prosseguir?",
            QMessageBox.Yes | QMessageBox.Cancel
        )
        if reply != QMessageBox.Yes:
            
            return

        self.status_label.setText("💾 Salvando em nuvem...")

        # 🔹 Salva no SQLite primeiro
        self.save_local_db_background()

        # 🔹 Depois envia cada tipo de dado para o Supabase
        try:
            sincronizar_clientes_upload()
            sincronizar_emprestimos_upload()
            sincronizar_parcelas_upload()
            sincronizar_movimentacoes_upload()

            QTimer.singleShot(
                2000,
                lambda: self.status_label.setText("✅ Pronto, tudo salvo. Pode ficar tranquilo!")
            )
        except Exception as e:
            print(f"⚠ Erro ao salvar na nuvem: {e}")
            self.status_label.setText("⚠ Erro ao salvar na nuvem.")

    def save_local_db_background(self):
        """Salva o banco local em segundo plano."""
        worker = SaveWorker(self.save_local_db, "Salvando no SQLite")
        QThreadPool.globalInstance().start(worker)

    def open_dados_cliente(self, client_data):
        """Abre a tela financeira do cliente selecionado."""
        self.finance_window = FinanceiroWindow(client_data, parent=self)
        self.finance_window.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.finance_window.setAttribute(Qt.WA_DeleteOnClose)  # fecha de vez ao clicar no X
        self.finance_window.show()
          


# =====================================================================
# SaveWorker (Thread para salvar em segundo plano)
# =====================================================================
class SaveWorker(QRunnable):
    def __init__(self, save_func, descricao="Salvando dados..."):
        super().__init__()
        self.save_func = save_func
        self.descricao = descricao

    def run(self):
        try:
            print(f"💾 {self.descricao} (em segundo plano)")
            self.save_func()
            print(f"✅ {self.descricao} concluído.")
        except Exception as e:
            print(f"⚠ Erro ao executar '{self.descricao}': {e}")


# =====================================================================
# Execução principal
# =====================================================================
from ui.login_ui import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    verificar_tabelas()

    def iniciar_app(usuario):
        app.usuario_logado = usuario
        main_window = ModernWindow()
        main_window.show()

    def abrir_login():
        app.login_window = LoginWindow(iniciar_app)
        app.login_window.show()

    splash = SplashScreen(on_finished=abrir_login)
    splash.show()

    sys.exit(app.exec())
