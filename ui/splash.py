from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPixmap, QGuiApplication


class SplashScreen(QWidget):
    def __init__(self, on_finished=None, parent=None):
        super().__init__(parent)
        self.on_finished = on_finished  # callback a ser chamado no final

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

        # Imagem
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

        # Opacidade
        self.opacity_effect = QGraphicsOpacityEffect()
        self.label.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        # Fade-in
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(1000)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in.finished.connect(self.esperar_visivel)

        # Fade-out
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(1000)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out.finished.connect(self.close_and_open_main)

        self.fade_in.start()

    def esperar_visivel(self):
        QTimer.singleShot(2000, self.fade_out.start)

    def close_and_open_main(self):
        self.close()
        if self.on_finished:
            self.on_finished()  # chama a função passada pelo main
