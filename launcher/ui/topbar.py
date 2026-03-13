"""Blurred topbar with glassmorphism style - matches Minecraft launcher reference."""
import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont
from launcher.utils.path_utils import get_asset_path
from launcher.ui.styles import get_font


class BlurredTopBar(QWidget):
    """Grey translucent topbar with nav tabs and user area."""
    nav_play = Signal()
    nav_instances = Signal()
    nav_profile = Signal()
    nav_servers = Signal()
    nav_options = Signal()

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setFixedHeight(56)
        self.setObjectName('BlurredTopBar')
        self.setStyleSheet("""
            #BlurredTopBar {
                background: rgba(60, 60, 60, 0.75);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(24)
        # Left: logo + title
        left = QWidget()
        left.setStyleSheet('background: transparent;')
        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        self._logo_small = QLabel()
        self._logo_small.setFixedSize(32, 32)
        self._logo_small.setScaledContents(True)
        self._logo_small.setStyleSheet('background: transparent;')
        logo_path = get_asset_path('minilogo.png')
        if os.path.isfile(logo_path):
            pix = QPixmap(logo_path)
            if not pix.isNull():
                self._logo_small.setPixmap(pix.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        left_layout.addWidget(self._logo_small)
        title_block = QWidget()
        title_block.setStyleSheet('background: transparent;')
        title_layout = QVBoxLayout(title_block)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_lbl = QLabel('LegacyLauncher')
        title_lbl.setStyleSheet('color: white; font-weight: bold; font-size: 14px; background: transparent;')
        title_lbl.setFont(get_font(14))
        sub_lbl = QLabel('Legacy Console Edition')
        sub_lbl.setStyleSheet('color: rgba(255,255,255,0.7); font-size: 11px; background: transparent;')
        sub_lbl.setFont(get_font(10))
        title_layout.addWidget(title_lbl)
        title_layout.addWidget(sub_lbl)
        left_layout.addWidget(title_block)
        layout.addWidget(left)
        layout.addStretch()
        # Center: nav tabs
        nav_w = QWidget()
        nav_w.setStyleSheet('background: transparent;')
        nav_layout = QHBoxLayout(nav_w)
        nav_layout.setSpacing(4)
        self._nav_btns = []
        for label, slot in [
            ('Play', 'play'),
            ('Instances', 'instances'),
            ('Profile', 'profile'),
            ('Servers', 'servers'),
            ('Options', 'options'),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: white;
                    border: none;
                    padding: 8px 14px;
                    font-size: 13px;
                }
                QPushButton:hover { color: #7dd87d; }
                QPushButton[active="true"] {
                    color: #5cb85c;
                    border-bottom: 2px solid #5cb85c;
                }
            """)
            btn.setFont(get_font(12))
            btn.setProperty('active', False)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if slot == 'play':
                btn.clicked.connect(lambda: self._set_active(0) or self.nav_play.emit())
            elif slot == 'instances':
                btn.clicked.connect(lambda: self._set_active(1) or self.nav_instances.emit())
            elif slot == 'profile':
                btn.clicked.connect(lambda: self._set_active(2) or self.nav_profile.emit())
            elif slot == 'servers':
                btn.clicked.connect(lambda: self._set_active(3) or self.nav_servers.emit())
            else:
                btn.clicked.connect(lambda: self._set_active(4) or self.nav_options.emit())
            self._nav_btns.append((btn, slot))
            nav_layout.addWidget(btn)
        layout.addWidget(nav_w, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        # Right: user
        right = QWidget()
        right.setStyleSheet('background: transparent;')
        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        profile = self.app.config.get('profile', {})
        username = profile.get('username', 'Player')
        self._user_lbl = QLabel(username)
        self._user_lbl.setStyleSheet('color: white; font-size: 13px; background: transparent;')
        self._user_lbl.setFont(get_font(12))
        right_layout.addWidget(self._user_lbl)
        layout.addWidget(right)
        self._set_active(0)

    def refresh_username(self):
        profile = self.app.config.get('profile', {})
        self._user_lbl.setText(profile.get('username', 'Player'))

    def _set_active(self, idx):
        for i, (btn, _) in enumerate(self._nav_btns):
            btn.setProperty('active', i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_active_tab(self, name):
        mapping = {'play': 0, 'instances': 1, 'profile': 2, 'servers': 3, 'options': 4}
        idx = mapping.get(name, 0)
        self._set_active(idx)
