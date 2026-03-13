import sys
import os

# Must be set before any Qt imports to avoid GPU/OpenGL crashes
os.environ.setdefault('QT_OPENGL', 'software')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from launcher.ui.styles import get_font, get_dark_stylesheet
from launcher.app import LauncherApp

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(get_font(11))
    app.setStyleSheet(get_dark_stylesheet())
    window = LauncherApp()
    window.show()
    sys.exit(app.exec())
