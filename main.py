# main.py
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                               QVBoxLayout, QLabel, QPushButton, QFrame)
from PySide6.QtGui import QPixmap, QGuiApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve


class SplashScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 400)

        # Centralizar na tela
        screen = QGuiApplication.primaryScreen().availableGeometry().center()
        self.move(screen.x() - self.width() // 2, screen.y() - self.height() // 2)

        # Layout com a imagem
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

        # Fade out suave
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1000)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.finished.connect(self.close_and_open_main)

        QTimer.singleShot(2000, self.anim.start)  # Espera 2s e inicia fade de 1s

    def close_and_open_main(self):
        self.close()
        self.parent().show()


class ModernWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Empréstimos App")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(1200, 700)
        self.setStyleSheet("background-color: #1c2331;")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.create_top_bar())
        main_layout.addLayout(self.create_main_content())

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.center()

    def create_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(50)
        bar.setStyleSheet("background-color: #2c3446;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)

        logo = QLabel("🛡️ Empréstimos App")
        logo.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(logo)

        layout.addStretch()

        btn_close = QPushButton("❌")
        btn_close.setFixedSize(30, 30)
        btn_close.setStyleSheet("""
            QPushButton {
                background: none;
                color: white;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                border-radius: 6px;
            }
        """)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        return bar

    def create_main_content(self):
        layout = QHBoxLayout()

        menu = QFrame()
        menu.setFixedWidth(220)
        menu.setStyleSheet("background-color: #252d3c;")
        menu_layout = QVBoxLayout(menu)

        for texto in ["🛡️ Próximos vencimentos", "🛡️ Vencidos", "🛡️ Previsões"]:
            btn = QPushButton(texto)
            btn.setStyleSheet("""
                QPushButton {
                    background: none;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-size: 15px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #374157;
                    border-radius: 5px;
                }
            """)
            menu_layout.addWidget(btn)

        menu_layout.addStretch()

        content_area = QLabel("Conteúdo principal aqui")
        content_area.setStyleSheet("color: #ccc; font-size: 24px;")
        content_area.setAlignment(Qt.AlignCenter)

        layout.addWidget(menu)
        layout.addWidget(content_area)

        return layout

    def center(self):
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Cria a janela principal mas não mostra ainda
    main_window = ModernWindow()

    # Cria a splash com fade
    splash = SplashScreen(parent=main_window)
    splash.show()

    sys.exit(app.exec())
