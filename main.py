import sys
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QComboBox,
    QDialog, QGridLayout, QToolButton, QGraphicsDropShadowEffect, QMessageBox
)

from PySide6.QtGui import QPixmap, QGuiApplication, QColor
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve


class SplashScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 400)

        screen = QGuiApplication.primaryScreen().availableGeometry().center()
        self.move(screen.x() - self.width() // 2, screen.y() - self.height() // 2)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel()
        pixmap = QPixmap("imginicio.png")
        if not pixmap.isNull():
            self.label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.label.setText("Imagem não carregada")
            self.label.setStyleSheet("color: white;")
            self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)
        self.setLayout(layout)

        # Fade-out animation
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1000)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.finished.connect(self.close_and_open_main)

        QTimer.singleShot(2000, self.anim.start)

    def close_and_open_main(self):
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
                # popula com cidades já existentes
                for city in (cities or []):
                    cb.addItem(city)
                layout.addWidget(lbl)
                layout.addWidget(cb)
                self.inputs[label_text] = cb  # armazena o combobox
            else:
                inp = QLineEdit()
                inp.setStyleSheet("background-color: #2c3446; color: white; padding: 6px; border-radius: 6px;")
                layout.addWidget(lbl)
                layout.addWidget(inp)
                self.inputs[label_text] = inp
                if label_text == "CPF":
                    # Máscara: força 11 dígitos no formato 000.000.000-00
                    inp.setInputMask("000.000.000-00;_")
                    # Opcional: impede colar letras etc. A máscara já faz boa parte do trabalho.

        # Preenche dados iniciais (edição)
        if initial_data:
            for k, w in self.inputs.items():
                val = initial_data.get(k, "")
                if isinstance(w, QComboBox):
                    # coloca a cidade do cliente como selecionada (se não existir, adiciona)
                    idx = w.findText(val)
                    if idx < 0 and val:
                        w.addItem(val)
                        idx = w.findText(val)
                    w.setCurrentIndex(max(0, idx))
                else:
                    w.setText(val)
        btn_save = QPushButton("Salvar")
        btn_save.setMinimumHeight(40)  # evita cortar o texto "Salvar"
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
            QMessageBox.warning(self, "CPF inválido", "CPF deve ter exatamente 11 dígitos.")
            return

        self.parent_callback(data)
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

        grid = QGridLayout()
        labels = ["Nome", "CPF", "Endereço", "Cidade", "Telefone", "Indicação"]
        row = 0
        for field in labels:
            k = QLabel(f"{field}:")
            k.setStyleSheet("color:#9fb0c7;")
            v = QLabel(client_data.get(field, ""))
            v.setStyleSheet("color:white;")
            grid.addWidget(k, row, 0, alignment=Qt.AlignRight)
            grid.addWidget(v, row, 1)
            row += 1

        layout.addLayout(grid)

        buttons = QHBoxLayout()
        buttons.addStretch()

        edit_btn = QToolButton()
        edit_btn.setText("🖉 Editar")  # ícone simples
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
        # Chama o callback para abrir o form de edição
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
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        # Arrastar a janela
        bar.mousePressEvent = self.mouse_press_event
        bar.mouseMoveEvent = self.mouse_move_event
        return bar

    def _unique_values(self, key):
        return sorted({c.get(key, "").strip() for c in self.clients if c.get(key, "").strip()})



    def mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouse_move_event(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.offset)

    # ======== Menu lateral ========
    def create_menu(self):
        menu = QFrame()
        menu.setFixedWidth(220)
        menu.setStyleSheet("background-color: #252d3c;")
        menu_layout = QVBoxLayout(menu)

        self.btn_clientes = QPushButton("👤 Clientes")
        self.btn_clientes.setStyleSheet("""
            QPushButton { background: none; color: white; padding: 12px; text-align: left; font-size: 15px; border: none; }
            QPushButton:hover { background-color: #374157; border-radius: 5px; }
        """)
        self.btn_clientes.clicked.connect(self.show_client_screen)
        menu_layout.addWidget(self.btn_clientes)

        self.btn_pesquisar = QPushButton("🔎 Pesquisar")
        self.btn_pesquisar.setStyleSheet("""
            QPushButton { background: none; color: white; padding: 12px; text-align: left; font-size: 15px; border: none; }
            QPushButton:hover { background-color: #374157; border-radius: 5px; }
        """)
        self.btn_pesquisar.clicked.connect(self.show_search_screen)
        menu_layout.addWidget(self.btn_pesquisar)

        menu_layout.addStretch()
        return menu

    # ======== Tela de Clientes ========
    def show_client_screen(self):
        self.client_list_widget = QWidget()
        layout = QVBoxLayout(self.client_list_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Topo: título + "Novo Cliente" pequeno (1/8 da largura)
        top_row = QHBoxLayout()
        title = QLabel("👥 Lista de Clientes")
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

        # ScrollArea com lista vertical
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        list_container = QWidget()
        self.client_container = QVBoxLayout(list_container)
        self.client_container.setContentsMargins(10, 10, 10, 10)
        self.client_container.setSpacing(8)
        self.client_container.addStretch()  # manter empurrado para cima; vamos controlar ao renderizar

        self.scroll_area.setWidget(list_container)
        layout.addWidget(self.scroll_area)

        # Renderiza clientes
        self.render_client_list()

        self._replace_main_content(self.client_list_widget)

    def render_client_list(self):
        if not hasattr(self, "client_container"):
            return

        # Limpa itens, preservando o stretch final
        while self.client_container.count() > 0:
            item = self.client_container.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        # Recria itens (um abaixo do outro)
        for idx, client in enumerate(self.clients):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color:#2c3446; border:1px solid #3a455b; border-radius:10px;
                }
                QPushButton#link {
                    color:#6fb1ff; text-align:left; background:transparent; border:none; padding:8px; font-size:16px;
                }
                QPushButton#link:hover { text-decoration: underline; }
                QLabel { color:#9fb0c7; }
            """)
            hl = QHBoxLayout(card)
            hl.setContentsMargins(10, 8, 10, 8)
            hl.setSpacing(8)

            # Botão-link com o nome do cliente
            link = QPushButton(client.get("Nome", "Sem Nome"))
            link.setObjectName("link")
            link.clicked.connect(lambda _, c=client: self.open_client_detail(c))
            hl.addWidget(link, 1)

            # Info secundária
            city = client.get("Cidade", "")
            secondary = QLabel(f"{city}")
            hl.addWidget(secondary, 0, Qt.AlignRight)

            self.client_container.addWidget(card)

        # adiciona um stretch para empurrar tudo para cima e manter layout
        self.client_container.addStretch()

    def open_client_form(self, initial_data=None, edit_index=None):
        def callback(data):
            if edit_index is None:
                # Novo cliente
                self.clients.append(data)
            else:
                # Edita cliente
                self.clients[edit_index] = data

            # Atualiza telas (lista e pesquisa) se estiverem abertas
            if hasattr(self, "client_container"):
                self.render_client_list()
            if hasattr(self, "table_results"):
                self.rebuild_search_filters()
                self.apply_search_filters()

        cities = self._unique_values("Cidade")
        self.form = ClientForm(callback, initial_data=initial_data, cities=cities)
        self.form.show()

    def open_client_detail(self, client_data):
        # acha o índice do cliente para edição
        try:
            idx = self.clients.index(client_data)
        except ValueError:
            idx = None

        def on_edit(data):
            self.open_client_form(initial_data=data, edit_index=idx)

        dlg = DetailDialog(client_data, on_edit)
        dlg.exec()

    # ======== Tela de Pesquisa ========
    def show_search_screen(self):
        self.search_widget = QWidget()
        layout = QVBoxLayout(self.search_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Topo: título + "Novo Cliente" replicado
        top_row = QHBoxLayout()
        title = QLabel("🔎 Pesquisar Clientes")
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

        # Linha de filtros: agora com rótulos acima (VBox para cada filtro)
        filters_row = QHBoxLayout()

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

        # Botões Buscar / Limpar
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setStyleSheet("""
            QPushButton {
                background-color:#3498db; color:white; padding:8px 12px; border-radius:8px;
            }
            QPushButton:hover { background-color:#2980b9; }
        """)
        btn_buscar.clicked.connect(self.apply_search_filters)
        filters_row.addWidget(btn_buscar)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setStyleSheet("""
            QPushButton {
                background-color:#34495e; color:white; padding:8px 12px; border-radius:8px;
            }
            QPushButton:hover { background-color:#2c3e50; }
        """)
        btn_limpar.clicked.connect(self.clear_search_filters)
        filters_row.addWidget(btn_limpar)

        layout.addLayout(filters_row)

        # Tabela de resultados (6 colunas, incluindo CPF)
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

        # tenta restaurar
        self._set_combobox_if_present(self.cb_nome, cur_nome)
        self._set_combobox_if_present(self.cb_cidade, cur_cidade)
        self._set_combobox_if_present(self.cb_indicacao, cur_ind)

    def _set_combobox_if_present(self, cb: QComboBox, value: str):
        idx = cb.findText(value)
        if idx >= 0:
            cb.setCurrentIndex(idx)
        else:
            cb.setCurrentIndex(0)

    def clear_search_filters(self):
        # volta todos para vazio e recarrega a lista completa
        if hasattr(self, "cb_nome"):
            self.cb_nome.setCurrentIndex(0)
        if hasattr(self, "cb_cidade"):
            self.cb_cidade.setCurrentIndex(0)
        if hasattr(self, "cb_indicacao"):
            self.cb_indicacao.setCurrentIndex(0)
        self.apply_search_filters()

    def apply_search_filters(self):
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

        self.table_results.setRowCount(0)
        for c in filtered:
            row = self.table_results.rowCount()
            self.table_results.insertRow(row)
            self.table_results.setItem(row, 0, QTableWidgetItem(c.get("Nome", "")))
            self.table_results.setItem(row, 1, QTableWidgetItem(c.get("CPF", "")))
            self.table_results.setItem(row, 2, QTableWidgetItem(c.get("Endereço", "")))
            self.table_results.setItem(row, 3, QTableWidgetItem(c.get("Cidade", "")))
            self.table_results.setItem(row, 4, QTableWidgetItem(c.get("Telefone", "")))
            self.table_results.setItem(row, 5, QTableWidgetItem(c.get("Indicação", "")))

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = ModernWindow()
    splash = SplashScreen(parent=main_window)
    splash.show()
    sys.exit(app.exec())
