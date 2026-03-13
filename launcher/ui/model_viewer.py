import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage


class ModelViewerWidget(QWidget):
    def __init__(self, parent=None, width=180, height=240):
        super().__init__(parent)
        self.setMinimumSize(width, height)
        self.setStyleSheet('background: transparent;')
        self._skin_path = None
        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setStyleSheet('background: transparent; color: #aaa; font-size: 11px;')
        self._preview_label.setMinimumSize(width, height)
        self._preview_label.setScaledContents(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._preview_label)
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._do_render)

    def set_skin(self, skin_path):
        self._skin_path = skin_path
        self._update_timer.start(100)

    def _do_render(self):
        self._show_skin()

    def _show_skin(self):
        if self._skin_path and os.path.isfile(self._skin_path):
            try:
                from PIL import Image
                img = Image.open(self._skin_path).convert('RGB')
                if img.size[1] == 32:
                    img = img.resize((64, 64), Image.Resampling.NEAREST)
                else:
                    img = img.resize((64, 64), Image.Resampling.LANCZOS)
                data = img.tobytes('raw', 'RGB')
                qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
                pix = QPixmap.fromImage(qimg)
                if not pix.isNull():
                    scaled = pix.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self._preview_label.setPixmap(scaled)
                self._preview_label.setStyleSheet('background: transparent;')
            except Exception:
                self._preview_label.setPixmap(QPixmap())
                self._preview_label.setText('Skin Preview')
                self._preview_label.setStyleSheet('background: transparent; color: #aaa;')
        else:
            self._preview_label.setPixmap(QPixmap())
            self._preview_label.setText('No skin - add one in Profile or Change Skin')
            self._preview_label.setStyleSheet('background: transparent; color: #aaa;')

