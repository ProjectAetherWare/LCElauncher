import os
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from launcher.utils.path_utils import get_asset_path


class ImageButton(QPushButton):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self._normal = None
        self._hover = None
        self._hovered = False
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFlat(True)
        self._load_images()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def _load_images(self):
        norm_path = get_asset_path('ButtonNormal.png')
        hover_path = get_asset_path('ButtonHover.png')
        if os.path.isfile(norm_path):
            self._normal = QPixmap(norm_path)
        if os.path.isfile(hover_path):
            self._hover = QPixmap(hover_path)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pix = self._hover if (self._hovered or self.isDown()) and self._hover else self._normal
        if pix is None:
            pix = self._normal or self._hover
        if pix is not None:
            scaled = pix.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(0, 0, scaled)
        else:
            bg = QColor('#5a7a5a' if (self._hovered or self.isDown()) else '#4a6a4a')
            p.fillRect(self.rect(), bg)
        p.setPen(QColor('white'))
        f = self.font()
        if f.pointSize() <= 0:
            f.setPixelSize(max(12, self.height() // 2))
        p.setFont(f)
        p.drawText(QRect(0, 0, self.width(), self.height()), Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()
