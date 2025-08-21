from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPixmap, QGuiApplication


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
        from main import resource_path
        pixmap = QPixmap(resource_path("imginicio.png"))

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

