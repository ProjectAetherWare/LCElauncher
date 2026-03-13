"""Baked-in pages (Profile, Servers, Options) - no dialogs."""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QListWidget, QListWidgetItem, QFormLayout, QFileDialog,
    QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QImage
from launcher.utils.path_utils import get_asset_path
from launcher.ui.styles import get_font, get_dark_stylesheet
from launcher.ui.image_button import ImageButton
from launcher.core.config import default_username
from launcher.core.skin_service import install_skin_to_installation, install_skin_from_url_to_installation
from launcher.core.lan_discovery import discover_lan_servers


def _load_blurred_bg(radius=4):
    """Load and blur bg.png. Returns PIL Image or None."""
    bg_path = get_asset_path('bg.png')
    if os.path.isfile(bg_path):
        try:
            from PIL import Image, ImageFilter
            img = Image.open(bg_path).convert('RGB')
            return img.filter(ImageFilter.GaussianBlur(radius=radius))
        except Exception:
            pass
    return None


class BasePage(QWidget):
    """Page with blurred background."""
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._bg = QLabel(self)
        self._bg.setScaledContents(True)
        self._bg.setAlignment(Qt.AlignCenter)
        self._bg.lower()
        self._bg_pil = _load_blurred_bg(radius=8)
        if self._bg_pil is None:
            self._bg.setStyleSheet('background: #2d2d2d;')
        self.setStyleSheet('background: transparent;')

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


class ProfilePage(BasePage):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(76, 76, 76, 76)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('background: transparent; border: none;')
        inner = QWidget()
        inner.setStyleSheet('background: transparent;')
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(16)
        title = QLabel('Profile')
        title.setStyleSheet('color: white; font-size: 20px; font-weight: bold;')
        title.setFont(get_font(20))
        inner_layout.addWidget(title)
        _lbl = QLabel('Username:')
        _lbl.setStyleSheet('color: white;')
        inner_layout.addWidget(_lbl)
        self.username_entry = QLineEdit()
        self.username_entry.setText(app.config.get('profile', {}).get('username', ''))
        self.username_entry.setFont(get_font(12))
        self.username_entry.setStyleSheet('background: rgba(61, 61, 61, 0.5); color: white; border: 1px solid rgba(85, 85, 85, 0.6); border-radius: 4px; padding: 6px;')
        inner_layout.addWidget(self.username_entry)
        _l = QLabel('Skin (file):')
        _l.setStyleSheet('color: white;')
        inner_layout.addWidget(_l)
        skin_row = QWidget()
        skin_layout = QHBoxLayout(skin_row)
        skin_layout.setContentsMargins(0, 0, 0, 0)
        self.skin_path_entry = QLineEdit()
        self.skin_path_entry.setText(app.config.get('profile', {}).get('skin_path', '') or '')
        self.skin_path_entry.setStyleSheet('background: rgba(61, 61, 61, 0.5); color: white; border: 1px solid rgba(85, 85, 85, 0.6); padding: 6px;')
        skin_layout.addWidget(self.skin_path_entry)
        browse_btn = ImageButton('Browse')
        browse_btn.clicked.connect(self._browse_skin)
        skin_layout.addWidget(browse_btn)
        inner_layout.addWidget(skin_row)
        _l = QLabel('Skin (URL):')
        _l.setStyleSheet('color: white;')
        inner_layout.addWidget(_l)
        self.skin_url_entry = QLineEdit()
        self.skin_url_entry.setText(app.config.get('profile', {}).get('skin_url', '') or '')
        self.skin_url_entry.setStyleSheet('background: rgba(61, 61, 61, 0.5); color: white; border: 1px solid rgba(85, 85, 85, 0.6); padding: 6px;')
        inner_layout.addWidget(self.skin_url_entry)
        _l = QLabel('Skin is copied to common/res/mob/char5.png in the selected installation.')
        _l.setStyleSheet('color: #aaa; font-size: 11px;')
        inner_layout.addWidget(_l)
        save_btn = ImageButton('Save')
        save_btn.clicked.connect(self._save)
        inner_layout.addWidget(save_btn)
        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _browse_skin(self):
        path = QFileDialog.getOpenFileName(self, 'Select Skin', '', 'PNG (*.png);;All (*.*)')[0]
        if path:
            self.skin_path_entry.setText(path)

    def _save(self):
        profile = self.app.config.setdefault('profile', {})
        profile['username'] = self.username_entry.text().strip() or profile.get('username') or default_username()
        profile['skin_path'] = self.skin_path_entry.text().strip() or None
        profile['skin_url'] = self.skin_url_entry.text().strip() or None
        self._install_skin_to_selected()
        self.app._save_config()
        self.app._start_tab.refresh_skin()
        QMessageBox.information(self, 'Saved', 'Profile saved.')

    def _install_skin_to_selected(self):
        sel = self.app.config.get('selected_installation')
        if not sel:
            return
        inst = next((i for i in self.app.config.get('installations', []) if i['name'] == sel), None)
        if not inst or not inst.get('path'):
            return
        profile = self.app.config.get('profile', {})
        path = profile.get('skin_path')
        url = profile.get('skin_url')
        try:
            if path and os.path.isfile(path):
                install_skin_to_installation(path, inst['path'])
            elif url:
                install_skin_from_url_to_installation(url, inst['path'])
        except Exception:
            pass


class OptionsPage(BasePage):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(76, 76, 76, 76)
        title = QLabel('Options')
        title.setStyleSheet('color: white; font-size: 20px; font-weight: bold;')
        title.setFont(get_font(20))
        layout.addWidget(title)
        opts = app.config.get('options', {})
        self.fullscreen_cb = QCheckBox('Fullscreen')
        self.fullscreen_cb.setChecked(opts.get('fullscreen', True))
        self.fullscreen_cb.setStyleSheet('color: white;')
        layout.addWidget(self.fullscreen_cb)
        save_btn = ImageButton('Save')
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)
        layout.addStretch()

    def _save(self):
        self.app.config.setdefault('options', {})['fullscreen'] = self.fullscreen_cb.isChecked()
        self.app._save_config()
        QMessageBox.information(self, 'Saved', 'Options saved.')


class _LANDiscoveryThread(QThread):
    found = Signal(list)

    def run(self):
        servers = discover_lan_servers(timeout=5.0)
        self.found.emit(servers)


class ServersPage(BasePage):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        self._lan_thread = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(76, 76, 76, 76)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('background: transparent; border: none;')
        inner = QWidget()
        inner.setStyleSheet('background: transparent;')
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(16)
        title = QLabel('Servers')
        title.setStyleSheet('color: white; font-size: 20px; font-weight: bold;')
        title.setFont(get_font(20))
        inner_layout.addWidget(title)
        _l = QLabel('LAN Games (local network)')
        _l.setStyleSheet('color: white;')
        inner_layout.addWidget(_l)
        lan_row = QHBoxLayout()
        self._lan_list = QListWidget()
        self._lan_list.setMinimumHeight(80)
        self._lan_list.setStyleSheet('background: rgba(61, 61, 61, 0.5); color: white;')
        lan_row.addWidget(self._lan_list)
        refresh_btn = ImageButton('Refresh')
        refresh_btn.clicked.connect(self._refresh_lan)
        add_lan_btn = ImageButton('Add to list')
        add_lan_btn.clicked.connect(self._add_selected_lan)
        lan_btns = QVBoxLayout()
        lan_btns.addWidget(refresh_btn)
        lan_btns.addWidget(add_lan_btn)
        lan_btns.addStretch()
        lan_row.addLayout(lan_btns)
        inner_layout.addLayout(lan_row)
        _l = QLabel('Saved servers (name : address)')
        _l.setStyleSheet('color: white;')
        inner_layout.addWidget(_l)
        self._list = QListWidget()
        self._list.setStyleSheet('background: rgba(61, 61, 61, 0.5); color: white;')
        for s in app.config.get('servers', []):
            self._list.addItem(QListWidgetItem('%s : %s' % (s.get('name', ''), s.get('address', ''))))
        inner_layout.addWidget(self._list)
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText('Server name')
        self._addr_edit = QLineEdit()
        self._addr_edit.setPlaceholderText('host:port')
        _input_style = 'background: rgba(61, 61, 61, 0.5); color: white; border: 1px solid rgba(85, 85, 85, 0.6); padding: 6px;'
        self._name_edit.setStyleSheet(_input_style)
        self._addr_edit.setStyleSheet(_input_style)
        _n = QLabel('Name:')
        _n.setStyleSheet('color: white;')
        _a = QLabel('Address:')
        _a.setStyleSheet('color: white;')
        form.addRow(_n, self._name_edit)
        form.addRow(_a, self._addr_edit)
        inner_layout.addLayout(form)
        add_btn = ImageButton('Add')
        add_btn.clicked.connect(self._add_server)
        remove_btn = ImageButton('Remove')
        remove_btn.clicked.connect(self._remove_server)
        inner_layout.addWidget(add_btn)
        inner_layout.addWidget(remove_btn)
        inner_layout.addStretch()
        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _refresh_lan(self):
        if self._lan_thread and self._lan_thread.isRunning():
            return
        self._lan_list.clear()
        self._lan_list.addItem(QListWidgetItem('Scanning...'))
        self._lan_thread = _LANDiscoveryThread()
        self._lan_thread.found.connect(self._on_lan_found)
        self._lan_thread.start()

    def _on_lan_found(self, servers):
        self._lan_list.clear()
        if not servers:
            self._lan_list.addItem(QListWidgetItem('No LAN games found'))
            return
        for s in servers:
            item = QListWidgetItem('%s - %s' % (s.get('name', 'LAN'), s.get('address', '')))
            item.setData(Qt.ItemDataRole.UserRole, s)
            self._lan_list.addItem(item)

    def _add_selected_lan(self):
        item = self._lan_list.currentItem()
        if item:
            s = item.data(Qt.ItemDataRole.UserRole)
            if s:
                self._add_lan_server(s)

    def _add_lan_server(self, s):
        name = s.get('name', 'LAN World')
        addr = s.get('address', '')
        if not addr:
            return
        self.app.config.setdefault('servers', []).append({'name': name, 'address': addr})
        self._list.addItem(QListWidgetItem('%s : %s' % (name, addr)))
        self.app._save_config()

    def _add_server(self):
        name = self._name_edit.text().strip()
        addr = self._addr_edit.text().strip()
        if not name or not addr:
            QMessageBox.warning(self, 'Error', 'Enter name and address')
            return
        self.app.config.setdefault('servers', []).append({'name': name, 'address': addr})
        self._list.addItem(QListWidgetItem('%s : %s' % (name, addr)))
        self._name_edit.clear()
        self._addr_edit.clear()
        self.app._save_config()

    def _remove_server(self):
        row = self._list.currentRow()
        if row >= 0:
            servers = self.app.config.get('servers', [])
            if row < len(servers):
                servers.pop(row)
                self._list.takeItem(row)
                self.app._save_config()
