import sys
import re
import sqlite3
from supabase import create_client, Client
from PySide6.QtCore import QRunnable, QThreadPool
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QComboBox,
    QDialog, QGridLayout, QToolButton, QGraphicsDropShadowEffect, QMessageBox
)
from PySide6.QtGui import QPixmap, QGuiApplication, QColor
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve


SUPABASE_URL = "https://zqvbgfqzdcejgxthdmht.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpxdmJnZnF6ZGNlamd4dGhkbWh0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUxMTI5ODAsImV4cCI6MjA3MDY4ODk4MH0.e4NhuarlGNnXrXUWKdLmGoa1DGejn2jmgpbRR_Ztyqw"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class SplashScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Janela sem bordas e sempre no topo
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 400)

        # Centralizar na tela
        screen = QGuiApplication.primaryScreen().availableGeometry().center()
        self.move(screen.x() - self.width() // 2, screen.y() - self.height() // 2)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Imagem ou texto alternativo
        self.label = QLabel()
        pixmap = QPixmap("imginicio.png")
        if not pixmap.isNull():
            self.label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.label.setText("Imagem não carregada")
            self.label.setStyleSheet("color: white;")
            self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)

        # Animação de fade-out
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1000)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.finished.connect(self.close_and_open_main)

        # Iniciar animação após 2 segundos
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, self.anim.start)

    def close_and_open_main(self):
        """Fecha a splash e mostra a janela principal."""
        self.close()
        self.parent().show()


class ClientForm(QWidget):
    """
    Formulário de cliente.
    Campos: Nome, CPF, Endereço, Cidade, Telefone, Indicação.
    Pode ser usado para criar ou editar (se data inicial for passada).
    """
    def __init__(self, parent_callback, initial_data=None, cities=None):
        super().__init__()
        self.setWindowTitle("Cliente")
        self.setFixedSize(340, 400)
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.parent_callback = parent_callback

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("ClientFormPanel")
        panel.setStyleSheet("""
            QFrame#ClientFormPanel {
                background-color: #1c2331;
                border-radius: 14px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 130))
        panel.setGraphicsEffect(shadow)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)

        outer.addWidget(panel)
        self.inputs = {}

        campos = ["Nome", "CPF", "Endereço", "Cidade", "Telefone", "Indicação"]
        for label_text in campos:
            lbl = QLabel(label_text)

            if label_text == "Cidade":
                cb = QComboBox()
                cb.setEditable(True)  # permite digitar cidade nova
                cb.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")
                cb.setInsertPolicy(QComboBox.NoInsert)  # evita duplicar item automaticamente
                for city in (cities or []):
                    cb.addItem(city)
                layout.addWidget(lbl)
                layout.addWidget(cb)
                self.inputs[label_text] = cb
            else:
                inp = QLineEdit()
                inp.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")
                layout.addWidget(lbl)
                layout.addWidget(inp)
                self.inputs[label_text] = inp

                if label_text == "CPF":
                    inp.setInputMask("000.000.000-00;_")

                if label_text == "Telefone":
                    inp.setInputMask("(00) 00000-0000;_")  # Máscara para telefone

        # Preenche dados iniciais (edição)
        if initial_data:
            for k, w in self.inputs.items():
                val = initial_data.get(k, "")
                if isinstance(w, QComboBox):
                    idx = w.findText(val)
                    if idx < 0 and val:
                        w.addItem(val)
                        idx = w.findText(val)
                    w.setCurrentIndex(max(0, idx))
                else:
                    w.setText(val)

        btn_save = QPushButton("Salvar")
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; padding: 10px; border-radius: 8px; font-weight: 600;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_save.clicked.connect(self.save_client)
        layout.addWidget(btn_save)

    def save_client(self):
        data = {}
        for k, w in self.inputs.items():
            if isinstance(w, QComboBox):
                data[k] = w.currentText().strip()
            else:
                data[k] = w.text().strip()

        cpf_digits = re.sub(r"\D", "", data.get("CPF", ""))
        if len(cpf_digits) != 11:
            QMessageBox.warning(self, "Presta atenção, infiliz!", "Tu já viu CPF com menos de 11 números?.")
            return

        self.parent_callback(data)  # Isso já vai chamar o salvamento no SQLite no ModernWindow
        self.close()


class DetailDialog(QDialog):
    """Janela pequena com os dados do cliente e botão para editar."""
    def __init__(self, client_data, on_edit):
        super().__init__()
        self.setWindowTitle("Detalhes do Cliente")
        self.setStyleSheet("background-color: #1c2331; color: white;")
        self.setFixedSize(360, 260)
        self.client_data = client_data
        self.on_edit = on_edit
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("DetailPanel")
        panel.setStyleSheet("""
            QFrame#DetailPanel {
                background-color: #1c2331;
                border-radius: 14px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 130))
        panel.setGraphicsEffect(shadow)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        outer.addWidget(panel)

        # Grade com as informações
        grid = QGridLayout()
        labels = ["Nome", "CPF", "Endereço", "Cidade", "Telefone", "Indicação"]
        for row, field in enumerate(labels):
            k = QLabel(f"{field}:")
            k.setStyleSheet("color:#9fb0c7;")
            v = QLabel(client_data.get(field, ""))
            v.setStyleSheet("color:white;")
            grid.addWidget(k, row, 0, alignment=Qt.AlignRight)
            grid.addWidget(v, row, 1)
        layout.addLayout(grid)

        # Botões
        buttons = QHBoxLayout()
        buttons.addStretch()

        edit_btn = QToolButton()
        edit_btn.setText("🖉 Editar")
        edit_btn.setStyleSheet("""
            QToolButton {
                background-color:#374157; color:white; padding:8px 12px; border-radius:8px;
            }
            QToolButton:hover { background-color:#3f4963; }
        """)
        edit_btn.clicked.connect(self.handle_edit)
        buttons.addWidget(edit_btn)

        close_btn = QPushButton("Fechar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color:#34495e; color:white; padding:8px 12px; border-radius:8px;
            }
            QPushButton:hover { background-color:#2c3e50; }
        """)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)

        layout.addLayout(buttons)

    def handle_edit(self):
        """Chama o callback para abrir o form de edição."""
        self.on_edit(self.client_data)
        self.accept()


class ModernWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.offset = None
        self.setWindowTitle("O Agiota")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(1200, 700)
        self.setStyleSheet("""
            QScrollBar:vertical {
                background: #252d3c; width: 10px; margin: 4px 0 4px 0; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #3a455b; min-height: 30px; border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a5671;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px; background: none;
            }
        """)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Armazena clientes em memória
        self.clients = []  # cada item: dict com campos

        # 🔹 Carrega dados do banco local na inicialização
        self.load_local_db()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.create_top_bar())

        self.main_content_layout = QHBoxLayout()
        main_layout.addLayout(self.main_content_layout)

        self.menu = self.create_menu()
        self.main_content_layout.addWidget(self.menu)

        self.content_area = QLabel("Conteúdo principal aqui")
        self.content_area.setStyleSheet("color: #ccc; font-size: 24px;")
        self.content_area.setAlignment(Qt.AlignCenter)
        self.main_content_layout.addWidget(self.content_area)

        shell = QFrame()
        shell.setObjectName("Shell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setObjectName("Content")
        content.setLayout(main_layout)
        shell_layout.addWidget(content)

        # Estilo da casca e do conteúdo com cantos arredondados
        shell.setStyleSheet("""
            QFrame#Shell { background-color: transparent; }
            QWidget#Content {
                background-color: #1c2331;
                border-radius: 16px;
            }
        """)

        # Sombra suave
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

        logo = QLabel("🛡️ O Agiota")
        logo.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(logo)
        layout.addStretch()

        # Minimizar
        btn_min = QPushButton("➖")
        btn_min.setFixedSize(30, 30)
        btn_min.setStyleSheet("""
            QPushButton { background: none; color: white; font-size: 16px; border: none; }
            QPushButton:hover { background-color: #3b465e; border-radius: 6px; }
        """)
        btn_min.clicked.connect(self.showMinimized)
        layout.addWidget(btn_min)

        # Fechar
        btn_close = QPushButton("❌")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("""
            QPushButton { background: none; color: white; font-size: 16px; border: none; }
            QPushButton:hover { background-color: #e74c3c; border-radius: 6px; }
        """)
        btn_close.clicked.connect(self.handle_close)
        layout.addWidget(btn_close)

        # Arrastar a janela
        bar.mousePressEvent = self.mouse_press_event
        bar.mouseMoveEvent = self.mouse_move_event
        return bar

    def handle_close(self):
        """Salva no SQLite e no Supabase antes de fechar, em segundo plano."""
        try:
            self.save_local_db_background()            
        except Exception as e:
            print(f"⚠ Erro ao salvar antes de fechar: {e}")
        self.close()

    def _unique_values(self, key):
        """Retorna valores únicos de um campo específico da lista de clientes."""
        return sorted({c.get(key, "").strip() for c in self.clients if c.get(key, "").strip()})

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

        # Botão para abrir diretamente a pesquisa de clientes
        self.btn_clientes = QPushButton("👤 Clientes")
        self.btn_clientes.setStyleSheet("""
            QPushButton { background: none; color: white; padding: 12px; text-align: left; font-size: 15px; border: none; }
            QPushButton:hover { background-color: #374157; border-radius: 5px; }
        """)
        self.btn_clientes.clicked.connect(self.show_search_screen)
        menu_layout.addWidget(self.btn_clientes)

        # Botão para Funções Extras
        self.btn_extras = QPushButton("⚙️ Funções Extras")
        self.btn_extras.setStyleSheet("""
            QPushButton { background: none; color: white; padding: 12px; text-align: left; font-size: 15px; border: none; }
            QPushButton:hover { background-color: #374157; border-radius: 5px; }
        """)
        self.btn_extras.clicked.connect(self.show_extras_screen)
        menu_layout.addWidget(self.btn_extras)

        menu_layout.addStretch()
        return menu

    def open_client_form(self, initial_data=None, edit_index=None):
        def callback(data):
            if edit_index is None:
                # Novo cliente
                self.clients.append(data)
            else:
                # Edita cliente
                self.clients[edit_index] = data

            # Salva no SQLite sempre que cadastrar/editar
            self.save_local_db()

            # Atualiza a tela de pesquisa, se aberta
            if hasattr(self, "table_results"):
                self.rebuild_search_filters()
                self.apply_search_filters()

        cities = self._unique_values("Cidade")
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
                background-color: #2ecc71; color: white; padding: 6px 10px; font-size: 12px; border-radius: 6px;
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
            QComboBox { background-color:#2c3446; color:white; padding:6px; border-radius:6px; }
            QComboBox QAbstractItemView { background-color:#2c3446; color:white; selection-background-color:#374157; }
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
            QComboBox { background-color:#2c3446; color:white; padding:6px; border-radius:6px; }
            QComboBox QAbstractItemView { background-color:#2c3446; color:white; selection-background-color:#374157; }
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
            QComboBox { background-color:#2c3446; color:white; padding:6px; border-radius:6px; }
            QComboBox QAbstractItemView { background-color:#2c3446; color:white; selection-background-color:#374157; }
        """)
        self.cb_indicacao.setPlaceholderText("Selecione uma indicação")
        box_ind.addWidget(self.cb_indicacao)
        filters_row.addLayout(box_ind)

        # Botões Buscar / Limpar alinhados pela base
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setStyleSheet("""
            QPushButton {
                background-color:#3498db; color:white; padding:8px 12px; border-radius:8px;
            }
            QPushButton:hover { background-color:#2980b9; }
        """)
        btn_buscar.clicked.connect(self.apply_search_filters)
        filters_row.addWidget(btn_buscar, alignment=Qt.AlignBottom)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setStyleSheet("""
            QPushButton {
                background-color:#34495e; color:white; padding:8px 12px; border-radius:8px;
            }
            QPushButton:hover { background-color:#2c3e50; }
        """)
        btn_limpar.clicked.connect(self.clear_search_filters)
        filters_row.addWidget(btn_limpar, alignment=Qt.AlignBottom)

        layout.addLayout(filters_row)

        # Tabela de resultados
        self.table_results = QTableWidget(0, 6)
        self.table_results.setHorizontalHeaderLabels(
            ["Nome", "CPF", "Endereço", "Cidade", "Telefone", "Indicação"]
        )
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_results.setStyleSheet("""
            QTableWidget { background-color: #2c3446; color: white; border: 1px solid #3a455b; }
            QHeaderView::section { background-color: #374157; color: white; padding: 6px; border: none; }
        """)
        layout.addWidget(self.table_results)

        self._replace_main_content(self.search_widget)

        # Popular filtros e mostrar tudo
        self.rebuild_search_filters()
        self.apply_search_filters()

    def rebuild_search_filters(self):
        """Atualiza as listas suspensas com valores únicos existentes nos clientes."""
        def unique_values(key):
            vals = sorted(set([c.get(key, "").strip() for c in self.clients if c.get(key, "").strip()]))
            return [""] + vals  # primeiro item vazio = sem filtro

        # salva seleções atuais para tentar manter (opcional)
        cur_nome = self.cb_nome.currentText() if self.cb_nome.count() else ""
        cur_cidade = self.cb_cidade.currentText() if self.cb_cidade.count() else ""
        cur_ind = self.cb_indicacao.currentText() if self.cb_indicacao.count() else ""

        self.cb_nome.clear()
        self.cb_nome.addItems(unique_values("Nome"))
        self.cb_cidade.clear()
        self.cb_cidade.addItems(unique_values("Cidade"))
        self.cb_indicacao.clear()
        self.cb_indicacao.addItems(unique_values("Indicação"))

        # tenta restaurar seleções anteriores
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
            ok_nome = (c.get("Nome", "").lower() == nome) if nome else True
            ok_cidade = (c.get("Cidade", "").lower() == cidade) if cidade else True
            ok_ind = (c.get("Indicação", "").lower() == indicacao) if indicacao else True
            if ok_nome and ok_cidade and ok_ind:
                filtered.append(c)

        # Desconecta temporariamente para evitar salvamento ao atualizar a tabela
        if self.table_results.receivers("itemChanged(QTableWidgetItem*)") > 0:
            self.table_results.itemChanged.disconnect(self.handle_table_edit)

        self.table_results.setRowCount(0)
        
        for c in filtered:
            row = self.table_results.rowCount()
            self.table_results.insertRow(row)

            # Coluna 0 - Nome (bloqueada para edição)
            item_nome = QTableWidgetItem(c.get("Nome", ""))
            item_nome.setFlags(item_nome.flags() & ~Qt.ItemIsEditable)
            self.table_results.setItem(row, 0, item_nome)

            # Coluna 1 - CPF (bloqueada para edição)
            item_cpf = QTableWidgetItem(c.get("CPF", ""))
            item_cpf.setFlags(item_cpf.flags() & ~Qt.ItemIsEditable)
            self.table_results.setItem(row, 1, item_cpf)

            # Colunas editáveis
            self.table_results.setItem(row, 2, QTableWidgetItem(c.get("Endereço", "")))
            self.table_results.setItem(row, 3, QTableWidgetItem(c.get("Cidade", "")))
            self.table_results.setItem(row, 4, QTableWidgetItem(c.get("Telefone", "")))

            # Coluna 5 - Indicação (bloqueada para edição)
            item_indicacao = QTableWidgetItem(c.get("Indicação", ""))
            item_indicacao.setFlags(item_indicacao.flags() & ~Qt.ItemIsEditable)
            self.table_results.setItem(row, 5, item_indicacao)
        # Reconecta evento de edição de célula
        self.table_results.itemChanged.connect(self.handle_table_edit)


    def handle_table_edit(self, item):
        """Evento disparado quando uma célula da tabela é editada pelo usuário."""
        row = item.row()
        col = item.column()
        col_names = ["Nome", "CPF", "Endereço", "Cidade", "Telefone", "Indicação"]

        if row < len(self.clients) and col < len(col_names):
            novo_valor = item.text()
            valor_antigo = self.clients[row].get(col_names[col], "")

            # Só salva se realmente houve alteração
            if novo_valor != valor_antigo:
                self.clients[row][col_names[col]] = novo_valor
                self.save_local_db_background()  # salva em segundo plano

    def load_local_db(self):
        """Carrega clientes do banco local SQLite para self.clients."""
        try:
            conn = sqlite3.connect("clientes.db")
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Nome TEXT,
                    CPF TEXT,
                    Endereço TEXT,
                    Cidade TEXT,
                    Telefone TEXT,
                    Indicação TEXT
                )
            """)
            conn.commit()

            cur.execute("SELECT Nome, CPF, Endereço, Cidade, Telefone, Indicação FROM clientes")
            rows = cur.fetchall()

            self.clients = [
                {
                    "Nome": row[0] or "",
                    "CPF": row[1] or "",
                    "Endereço": row[2] or "",
                    "Cidade": row[3] or "",
                    "Telefone": row[4] or "",
                    "Indicação": row[5] or ""
                }
                for row in rows
            ]

            conn.close()
            print(f"✅ {len(self.clients)} clientes carregados do banco local.")
        except Exception as e:
            print(f"⚠ Erro ao carregar banco local: {e}")

    def save_local_db(self):
        """Salva todos os clientes de self.clients no banco local SQLite."""
        try:
            conn = sqlite3.connect("clientes.db")
            cur = conn.cursor()

            # Limpa todos os registros
            cur.execute("DELETE FROM clientes")

            # Insere todos novamente
            for c in self.clients:
                cur.execute("""
                    INSERT INTO clientes (Nome, CPF, Endereço, Cidade, Telefone, Indicação)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    c.get("Nome", ""),
                    c.get("CPF", ""),
                    c.get("Endereço", ""),
                    c.get("Cidade", ""),
                    c.get("Telefone", ""),
                    c.get("Indicação", "")
                ))

            conn.commit()
            conn.close()
            print("💾 Banco local atualizado com sucesso.")
        except Exception as e:
            print(f"⚠ Erro ao salvar no banco local: {e}")



    # ======== Utilidades ========
    def _replace_main_content(self, new_widget: QWidget):
        old = self.main_content_layout.itemAt(1).widget()
        old.setParent(None)
        self.main_content_layout.addWidget(new_widget)

    def center(self):
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())

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
        btn_backup = QPushButton("☁️ Backup em nuvem")
        btn_backup.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; padding: 10px;
                border-radius: 8px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_backup.clicked.connect(self._backup_em_nuvem)
        layout.addWidget(btn_backup, alignment=Qt.AlignCenter)

        self._replace_main_content(self.extras_widget)

    def _backup_em_nuvem(self):
        """Executa salvamento local e em nuvem em segundo plano."""
        self.status_label.setText("💾 Salvando em nuvem...")

        # Salva no SQLite primeiro
        self.save_local_db_background()

        # Depois salva no Supabase
        self.save_to_supabase_background()

        # Atualiza mensagem de sucesso após 2s
        QTimer.singleShot(2000, lambda: self.status_label.setText("✅ Pronto, tudo salvo. Pode ficar tranquilo!"))

    def save_to_supabase_background(self):
        """Dispara salvamento no Supabase em segundo plano."""
        worker = SaveWorker(self.save_to_supabase, "Salvando no Supabase")
        QThreadPool.globalInstance().start(worker)

    def save_local_db_background(self):
        """Salva o banco local em segundo plano."""
        worker = SaveWorker(self.save_local_db, "Salvando no SQLite")
        QThreadPool.globalInstance().start(worker)


    def save_to_supabase(self):
        try:
            data = []
            for c in self.clients:
                data.append({
                    "Nome": c.get("Nome", ""),
                    "CPF": c.get("CPF", ""),
                    "Endereço": c.get("Endereço", ""),
                    "Cidade": c.get("Cidade", ""),
                    "Telefone": c.get("Telefone", ""),
                    "Indicação": c.get("Indicação", "")
                })

            # Limpa a tabela antes de inserir (opcional)
            supabase.table("Clientes").delete().neq("id", 0).execute()

            # Insere todos os dados de uma vez
            supabase.table("Clientes").insert(data).execute()

            print("☁️ Backup no Supabase concluído.")
        except Exception as e:
            print(f"⚠ Erro ao salvar no Supabase: {e}")

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

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ModernWindow()
    splash = SplashScreen(parent=main_window)
    splash.show()
    sys.exit(app.exec())

    #nota