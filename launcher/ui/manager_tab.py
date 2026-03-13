import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
from launcher.utils.path_utils import get_asset_path
from launcher.ui.styles import get_font
from launcher.ui.image_button import ImageButton
from launcher.ui.pages import _load_blurred_bg


class ManagerTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._bg = QLabel(self)
        self._bg.setScaledContents(True)
        self._bg.setAlignment(Qt.AlignCenter)
        self._bg.lower()
        self._bg_pil = _load_blurred_bg(radius=8)
        if self._bg_pil is None:
            self._bg.setStyleSheet('background: #2d2d2d;')
        self.setStyleSheet('background: transparent;')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 76, 24, 24)
        title = QLabel('Installation Manager')
        title.setStyleSheet('color: white; font-size: 16px;')
        title.setFont(get_font(16))
        layout.addWidget(title)
        add_btn = ImageButton('Add Installation')
        add_btn.setFont(get_font(12))
        add_btn.setFixedSize(180, 40)
        add_btn.clicked.connect(self.app.show_add_install_dialog)
        layout.addWidget(add_btn)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet('background: transparent; border: none;')
        self._inner = QWidget()
        self._inner.setStyleSheet('background: transparent;')
        self._inner_layout = QVBoxLayout(self._inner)
        self._scroll.setWidget(self._inner)
        layout.addWidget(self._scroll)
        back_btn = ImageButton('Back')
        back_btn.setFont(get_font(12))
        back_btn.setFixedSize(120, 40)
        back_btn.clicked.connect(lambda: self.app.show_tab(0))
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._bg.setGeometry(0, 0, self.width(), self.height())
        self._update_bg()

    def _update_bg(self):
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

    def refresh(self):
        while self._inner_layout.count():
            child = self._inner_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        config = self.app.config
        installs = config.get('installations', [])
        for i, inst in enumerate(installs):
            row = QFrame()
            row.setStyleSheet('background: rgba(61, 61, 61, 0.5); padding: 8px; margin: 4px;')
            row_layout = QVBoxLayout(row)
            name_lbl = QLabel(inst.get('name', 'Unknown'))
            name_lbl.setStyleSheet('color: white; font-weight: bold;')
            row_layout.addWidget(name_lbl)
            path_lbl = QLabel(inst.get('path', ''))
            path_lbl.setStyleSheet('color: #888; font-size: 11px;')
            row_layout.addWidget(path_lbl)
            update_btn = ImageButton('Update')
            update_btn.setFont(get_font(10))
            update_btn.setFixedSize(85, 30)
            update_btn.clicked.connect(lambda checked, idx=i: self.app.on_update_installation(idx))
            edit_btn = ImageButton('Edit')
            edit_btn.setFont(get_font(10))
            edit_btn.setFixedSize(75, 30)
            edit_btn.clicked.connect(lambda checked, idx=i: self.app.show_edit_install_dialog(idx))
            delete_btn = ImageButton('Delete')
            delete_btn.setFont(get_font(10))
            delete_btn.setFixedSize(75, 30)
            delete_btn.clicked.connect(lambda checked, idx=i: self._on_delete(idx))
            btn_row = QWidget()
            btn_row_layout = QHBoxLayout(btn_row)
            btn_row_layout.addWidget(update_btn)
            btn_row_layout.addWidget(edit_btn)
            btn_row_layout.addWidget(delete_btn)
            row_layout.addWidget(btn_row)
            self._inner_layout.addWidget(row)

    def _on_delete(self, idx):
        from PySide6.QtWidgets import QMessageBox
        if QMessageBox.question(self, 'Delete', 'Delete this installation?',
                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.app.delete_installation(idx)
