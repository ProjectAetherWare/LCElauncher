import os
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QFrame
)
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QTimer
from PySide6.QtGui import QFont, QPixmap, QImage
from launcher.utils.path_utils import get_asset_path
from launcher.core.skin_service import get_skin_for_preview
from launcher.ui.model_viewer import ModelViewerWidget
from launcher.ui.image_button import ImageButton
from launcher.ui.styles import get_font


SPLASH_TEXTS = [
    "The best way to craft",
    "Legacy Console Edition",
    "Also try Terraria",
    "Now with more blocks",
    "Dig straight down",
    "Creeper? Aww man",
    "Pickaxe and chill",
    "Craft your adventure",
    "Block by block",
    "Minecraft!",
    "100% pure block",
    "As seen on TV",
    "May contain nuts",
    "Brought to you by blocks",
    "Works on my machine",
    "Not a bug, a feature",
    "Stay crafty",
]


def get_random_splash():
    return random.choice(SPLASH_TEXTS)


class BounceSplashLabel(QWidget):
    """Yellow splash text with bounce-in-out animation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self._base_font = get_font(18)
        self._label = QLabel(self)
        self._label.setStyleSheet('color: #ffd700; background: transparent;')
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._update_font()
        self._anim_group = QSequentialAnimationGroup(self)
        anim_in = QPropertyAnimation(self, b"bounceScale")
        anim_in.setDuration(400)
        anim_in.setStartValue(0.7)
        anim_in.setEndValue(1.15)
        anim_in.setEasingCurve(QEasingCurve.Type.OutBounce)
        anim_out = QPropertyAnimation(self, b"bounceScale")
        anim_out.setDuration(350)
        anim_out.setStartValue(1.15)
        anim_out.setEndValue(1.0)
        anim_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim_group.addAnimation(anim_in)
        self._anim_group.addAnimation(anim_out)
        self._anim_group.setLoopCount(1)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._start_bounce)
        self._timer.start(3000)

    def get_bounce_scale(self):
        return self._scale

    def set_bounce_scale(self, v):
        self._scale = v
        self._update_font()

    bounceScale = Property(float, get_bounce_scale, set_bounce_scale)

    def _update_font(self):
        f = QFont(self._base_font)
        f.setPointSizeF(max(10, 18 * self._scale))
        self._label.setFont(f)

    def _start_bounce(self):
        self._anim_group.stop()
        self._anim_group.start()

    def setText(self, text):
        self._label.setText(text)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._label.setGeometry(0, 0, self.width(), self.height())


class StartTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build()

    def _build(self):
        self.setStyleSheet('background: #2d2d2d;')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 76, 24, 20)
        self._bg = QLabel(self)
        self._bg.setScaledContents(True)
        self._bg.setAlignment(Qt.AlignCenter)
        self._bg.lower()
        self._load_bg()
        # Main content: center column + skin sidebar
        main_row = QHBoxLayout()
        main_row.setSpacing(24)
        center_col = QVBoxLayout()
        center_col.setSpacing(12)
        center_col.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        logo_frame = QFrame()
        logo_frame.setStyleSheet('background: transparent;')
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_layout.setSpacing(4)
        self._splash_label = BounceSplashLabel()
        self._splash_label.setText(get_random_splash())
        self._splash_label.setFixedHeight(36)
        logo_layout.addWidget(self._splash_label)
        self._logo_label = QLabel()
        self._logo_label.setStyleSheet('background: transparent;')
        self._logo_label.setAlignment(Qt.AlignCenter)
        self._logo_label.setScaledContents(False)
        logo_layout.addWidget(self._logo_label)
        center_col.addWidget(logo_frame, alignment=Qt.AlignCenter)
        center_col.addSpacing(4)
        self._play_btn = ImageButton('PLAY')
        self._play_btn.setFixedSize(320, 58)
        self._play_btn.setFont(get_font(18))
        self._play_btn.clicked.connect(self.app.on_play)
        center_col.addWidget(self._play_btn, alignment=Qt.AlignCenter)
        center_col.addSpacing(8)
        version_frame = QFrame()
        version_frame.setStyleSheet('background: transparent;')
        version_layout = QHBoxLayout(version_frame)
        version_layout.setSpacing(8)
        vlabel = QLabel('Version:')
        vlabel.setFont(get_font(12))
        vlabel.setStyleSheet('color: white; background: transparent;')
        version_layout.addWidget(vlabel)
        self._version_combo = QComboBox()
        self._version_combo.setFont(get_font(11))
        self._version_combo.setMinimumWidth(200)
        self._version_combo.currentTextChanged.connect(self._on_version_change)
        version_layout.addWidget(self._version_combo)
        self._update_btn = ImageButton('↻')
        self._update_btn.setFixedSize(40, 34)
        self._update_btn.setFont(get_font(14))
        self._update_btn.clicked.connect(self.app.on_update_current)
        version_layout.addWidget(self._update_btn)
        center_col.addWidget(version_frame, alignment=Qt.AlignCenter)
        center_col.addStretch()
        main_row.addLayout(center_col, 1)
        skin_widget = QWidget()
        skin_widget.setStyleSheet('background: transparent;')
        skin_col = QVBoxLayout(skin_widget)
        skin_col.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        skin_col.setSpacing(8)
        self._model_viewer = ModelViewerWidget(skin_widget, width=120, height=160)
        skin_col.addWidget(self._model_viewer, alignment=Qt.AlignCenter)
        change_skin_btn = ImageButton('CHANGE SKIN')
        change_skin_btn.setFixedSize(130, 40)
        change_skin_btn.setFont(get_font(11))
        change_skin_btn.clicked.connect(lambda: self.app._tabs.setCurrentIndex(2))
        skin_col.addWidget(change_skin_btn, alignment=Qt.AlignCenter)
        skin_col.addStretch()
        main_row.addWidget(skin_widget, 0, Qt.AlignTop | Qt.AlignRight)
        layout.addLayout(main_row, 1)
        self._status_label = QLabel('')
        self._status_label.setStyleSheet('color: #888; background: transparent; font-size: 11px;')
        layout.addWidget(self._status_label, alignment=Qt.AlignCenter)
        self._load_logo()
        self.refresh_skin()

    def _load_bg(self):
        self._bg_pil = None
        bg_path = get_asset_path('bg.png')
        if os.path.isfile(bg_path):
            try:
                from PIL import Image, ImageFilter
                img = Image.open(bg_path).convert('RGB')
                self._bg_pil = img.filter(ImageFilter.GaussianBlur(radius=8))
            except Exception:
                pass
        if self._bg_pil is None:
            self._bg.setStyleSheet('background: #2d2d2d;')

    def _update_bg_pixmap(self):
        if not hasattr(self, '_bg_pil') or self._bg_pil is None:
            return
        try:
            from PIL import Image
            w, h = self.width(), self.height()
            if w <= 0 or h <= 0:
                return
            bg = self._bg_pil.resize((w, h), Image.Resampling.LANCZOS)
            data = bg.tobytes('raw', 'RGB')
            qimg = QImage(data, bg.width, bg.height, bg.width * 3, QImage.Format_RGB888)
            self._bg.setPixmap(QPixmap.fromImage(qimg))
        except Exception:
            pass

    def _load_logo(self):
        logo_path = get_asset_path('logo.png')
        if os.path.isfile(logo_path):
            try:
                pix = QPixmap(logo_path)
                if not pix.isNull():
                    scaled = pix.scaled(400, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self._logo_label.setPixmap(scaled)
                    self._logo_label.setScaledContents(False)
                    return
            except Exception:
                pass
        self._logo_label.setText('Minecraft Legacy Console Edition')

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._bg.setGeometry(0, 0, self.width(), self.height())
        self._update_bg_pixmap()

    def _on_version_change(self, text):
        if text:
            self.app.config['selected_installation'] = text
            self.app._save_config()
        self.refresh_skin()

    def refresh_splash(self):
        self._splash_label.setText(get_random_splash())
        if hasattr(self._splash_label, '_start_bounce'):
            self._splash_label._start_bounce()

    def refresh_versions(self):
        config = self.app.config
        installs = config.get('installations', [])
        names = [i['name'] for i in installs]
        self._version_combo.clear()
        self._version_combo.addItems(names)
        sel = config.get('selected_installation')
        if sel and sel in names:
            self._version_combo.setCurrentText(sel)
        elif names:
            self._version_combo.setCurrentIndex(0)
        self.refresh_skin()

    def refresh_skin(self):
        profile = self.app.config.get('profile', {})
        sel = self.app.config.get('selected_installation')
        install_path = None
        if sel:
            inst = next((i for i in self.app.config.get('installations', []) if i['name'] == sel), None)
            if inst:
                install_path = inst.get('path')
        skin_path = get_skin_for_preview(profile, install_path)
        self._model_viewer.set_skin(skin_path)

    def set_status(self, text):
        self._status_label.setText(text)
