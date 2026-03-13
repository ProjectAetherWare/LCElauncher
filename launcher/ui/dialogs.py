import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QRadioButton, QButtonGroup, QMessageBox, QFileDialog,
    QWidget, QListWidget, QListWidgetItem, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal
from launcher.ui.styles import get_font, get_dark_stylesheet
from launcher.ui.image_button import ImageButton
from launcher.core.config import default_username
from launcher.core.installer import DEFAULT_URL, install_from_url, update_installation
from launcher.core.skin_service import install_skin_to_installation, install_skin_from_url_to_installation
from launcher.core.lan_discovery import discover_lan_servers


def center_dialog(dialog, width, height):
    dialog.resize(width, height)
    geo = dialog.frameGeometry()
    from PySide6.QtWidgets import QApplication
    screen = QApplication.primaryScreen().availableGeometry().center()
    geo.moveCenter(screen)
    dialog.move(geo.topLeft())


def _apply_dialog_style(dialog):
    dialog.setStyleSheet(get_dark_stylesheet())
    for t in (QLabel, QLineEdit, QCheckBox, QRadioButton, QListWidget):
        for w in dialog.findChildren(t):
            w.setFont(get_font(11))
    for w in dialog.findChildren(QPushButton):
        w.setFont(get_font(12))


class ProfileDialog(QDialog):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self.setWindowTitle('Profile')
        _apply_dialog_style(self)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Username:'))
        self.username_entry = QLineEdit()
        self.username_entry.setText(config.get('profile', {}).get('username', ''))
        self.username_entry.setFont(get_font(12))
        layout.addWidget(self.username_entry)
        layout.addWidget(QLabel('Skin (file):'))
        skin_row = QWidget()
        skin_layout = QHBoxLayout(skin_row)
        self.skin_path_entry = QLineEdit()
        self.skin_path_entry.setText(config.get('profile', {}).get('skin_path', '') or '')
        skin_layout.addWidget(self.skin_path_entry)
        browse_btn = ImageButton('Browse')
        browse_btn.clicked.connect(self._browse_skin)
        skin_layout.addWidget(browse_btn)
        layout.addWidget(skin_row)
        layout.addWidget(QLabel('Skin (URL):'))
        self.skin_url_entry = QLineEdit()
        self.skin_url_entry.setText(config.get('profile', {}).get('skin_url', '') or '')
        layout.addWidget(self.skin_url_entry)
        btn_layout = QHBoxLayout()
        save_btn = ImageButton('Save')
        save_btn.clicked.connect(self._save)
        cancel_btn = ImageButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        center_dialog(self, 400, 280)

    def _browse_skin(self):
        path = QFileDialog.getOpenFileName(self, 'Select Skin', '', 'PNG (*.png);;All (*.*)')[0]
        if path:
            self.skin_path_entry.setText(path)

    def _save(self):
        profile = self.config.setdefault('profile', {})
        profile['username'] = self.username_entry.text().strip() or profile.get('username') or default_username()
        profile['skin_path'] = self.skin_path_entry.text().strip() or None
        profile['skin_url'] = self.skin_url_entry.text().strip() or None
        self._install_skin_to_selected()
        self.on_save()
        self.accept()

    def _install_skin_to_selected(self):
        sel = self.config.get('selected_installation')
        if not sel:
            return
        inst = next((i for i in self.config.get('installations', []) if i['name'] == sel), None)
        if not inst or not inst.get('path'):
            return
        profile = self.config.get('profile', {})
        path = profile.get('skin_path')
        url = profile.get('skin_url')
        try:
            if path and os.path.isfile(path):
                install_skin_to_installation(path, inst['path'])
            elif url:
                install_skin_from_url_to_installation(url, inst['path'])
        except Exception:
            pass


class OptionsDialog(QDialog):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self.setWindowTitle('Options')
        _apply_dialog_style(self)
        layout = QVBoxLayout(self)
        opts = config.get('options', {})
        self.fullscreen_cb = QCheckBox('Fullscreen')
        self.fullscreen_cb.setChecked(opts.get('fullscreen', True))
        layout.addWidget(self.fullscreen_cb)
        btn_row = QHBoxLayout()
        save_btn = ImageButton('Save')
        save_btn.clicked.connect(self._save)
        cancel_btn = ImageButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        center_dialog(self, 350, 150)

    def _save(self):
        self.config.setdefault('options', {})['fullscreen'] = self.fullscreen_cb.isChecked()
        self.on_save()
        self.accept()


class AddInstallDialog(QDialog):
    def __init__(self, parent, config, installs_base, on_added):
        super().__init__(parent)
        self.config = config
        self.installs_base = installs_base
        self.on_added = on_added
        self.setWindowTitle('Add Installation')
        _apply_dialog_style(self)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Name:'))
        self.name_entry = QLineEdit()
        layout.addWidget(self.name_entry)
        layout.addWidget(QLabel('Icon (optional):'))
        icon_row = QWidget()
        icon_layout = QHBoxLayout(icon_row)
        self.icon_entry = QLineEdit()
        icon_layout.addWidget(self.icon_entry)
        browse_btn = ImageButton('Browse')
        browse_btn.clicked.connect(lambda: self.icon_entry.setText(QFileDialog.getOpenFileName(self, 'Select Icon', '', 'Images (*.png *.jpg *.ico)')[0] or self.icon_entry.text()))
        icon_layout.addWidget(browse_btn)
        layout.addWidget(icon_row)
        layout.addWidget(QLabel('Source:'))
        self.source_group = QButtonGroup()
        self.default_radio = QRadioButton('Default (LCE Nightly)')
        self.default_radio.setChecked(True)
        self.custom_radio = QRadioButton('Custom URL:')
        self.source_group.addButton(self.default_radio)
        self.source_group.addButton(self.custom_radio)
        layout.addWidget(self.default_radio)
        layout.addWidget(self.custom_radio)
        self.url_entry = QLineEdit()
        self.url_entry.setEnabled(False)
        self.custom_radio.toggled.connect(lambda c: self.url_entry.setEnabled(c))
        layout.addWidget(self.url_entry)
        self.progress_label = QLabel('')
        layout.addWidget(self.progress_label)
        install_btn = ImageButton('Install')
        install_btn.clicked.connect(self._install)
        cancel_btn = ImageButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(install_btn)
        layout.addWidget(cancel_btn)
        center_dialog(self, 450, 320)

    def _install(self):
        name = self.name_entry.text().strip()
        if not name:
            QMessageBox.critical(self, 'Error', 'Enter a name')
            return
        if any(i['name'] == name for i in self.config.get('installations', [])):
            QMessageBox.critical(self, 'Error', 'Name already exists')
            return
        url = DEFAULT_URL if self.default_radio.isChecked() else self.url_entry.text().strip()
        if not url:
            QMessageBox.critical(self, 'Error', 'Enter a URL')
            return

        def progress(done, total):
            if total:
                self.progress_label.setText(f'Downloading... {int(100 * done / total)}%')
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()

        try:
            self.progress_label.setText('Downloading...')
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            install_path = install_from_url(url, name, self.installs_base, progress)
            self.config.setdefault('installations', []).append({
                'name': name,
                'path': install_path,
                'icon_path': self.icon_entry.text().strip() or None,
                'source_url': url,
                'exe_path': None
            })
            if not self.config.get('selected_installation'):
                self.config['selected_installation'] = name
            self.on_added()
            QMessageBox.information(self, 'Success', 'Installation complete')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))


class EditInstallDialog(QDialog):
    def __init__(self, parent, config, idx, on_saved):
        super().__init__(parent)
        self.config = config
        self.idx = idx
        self.on_saved = on_saved
        self.setWindowTitle('Edit Installation')
        _apply_dialog_style(self)
        inst = config['installations'][idx]
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Name:'))
        self.name_entry = QLineEdit()
        self.name_entry.setText(inst.get('name', ''))
        layout.addWidget(self.name_entry)
        layout.addWidget(QLabel('Icon:'))
        icon_row = QWidget()
        icon_layout = QHBoxLayout(icon_row)
        self.icon_entry = QLineEdit()
        self.icon_entry.setText(inst.get('icon_path', '') or '')
        icon_layout.addWidget(self.icon_entry)
        browse_btn = ImageButton('Browse')
        browse_btn.clicked.connect(lambda: self.icon_entry.setText(QFileDialog.getOpenFileName(self, 'Select Icon', '', 'Images (*.png *.jpg *.ico)')[0] or self.icon_entry.text()))
        icon_layout.addWidget(browse_btn)
        layout.addWidget(icon_row)
        save_btn = ImageButton('Save')
        save_btn.clicked.connect(self._save)
        cancel_btn = ImageButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(save_btn)
        layout.addWidget(cancel_btn)
        center_dialog(self, 400, 200)

    def _save(self):
        name = self.name_entry.text().strip()
        if not name:
            QMessageBox.critical(self, 'Error', 'Enter a name')
            return
        installs = self.config['installations']
        old_name = installs[self.idx]['name']
        if any(installs[i]['name'] == name for i in range(len(installs)) if i != self.idx):
            QMessageBox.critical(self, 'Error', 'Name already exists')
            return
        installs[self.idx]['name'] = name
        installs[self.idx]['icon_path'] = self.icon_entry.text().strip() or None
        if self.config.get('selected_installation') == old_name:
            self.config['selected_installation'] = name
        self.on_saved()
        self.accept()


class SkinDialog(QDialog):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self.setWindowTitle('Change Skin')
        _apply_dialog_style(self)
        layout = QVBoxLayout(self)
        profile = config.get('profile', {})
        layout.addWidget(QLabel('Skin (file):'))
        skin_row = QWidget()
        skin_layout = QHBoxLayout(skin_row)
        self.skin_path_entry = QLineEdit()
        self.skin_path_entry.setText(profile.get('skin_path', '') or '')
        skin_layout.addWidget(self.skin_path_entry)
        browse_btn = ImageButton('Browse')
        browse_btn.clicked.connect(self._browse_skin)
        skin_layout.addWidget(browse_btn)
        layout.addWidget(skin_row)
        layout.addWidget(QLabel('Skin (URL):'))
        self.skin_url_entry = QLineEdit()
        self.skin_url_entry.setText(profile.get('skin_url', '') or '')
        layout.addWidget(self.skin_url_entry)
        layout.addWidget(QLabel('Skin will be copied to common/res/mob/char5.png in the selected installation.'))
        layout.addWidget(QLabel('Installation:'))
        sel = config.get('selected_installation')
        inst = next((i for i in config.get('installations', []) if i['name'] == sel), None)
        self._install_path = inst.get('path') if inst else None
        self._install_name_label = QLabel(inst.get('name', 'None') if inst else 'None')
        layout.addWidget(self._install_name_label)
        save_btn = ImageButton('Save')
        save_btn.clicked.connect(self._save)
        cancel_btn = ImageButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(save_btn)
        layout.addWidget(cancel_btn)
        center_dialog(self, 400, 320)

    def _browse_skin(self):
        path = QFileDialog.getOpenFileName(self, 'Select Skin', '', 'PNG (*.png);;All (*.*)')[0]
        if path:
            self.skin_path_entry.setText(path)

    def _save(self):
        profile = self.config.setdefault('profile', {})
        path = self.skin_path_entry.text().strip()
        url = self.skin_url_entry.text().strip()
        profile['skin_path'] = path or None
        profile['skin_url'] = url or None
        if self._install_path:
            try:
                if path and os.path.isfile(path):
                    install_skin_to_installation(path, self._install_path)
                elif url:
                    install_skin_from_url_to_installation(url, self._install_path)
            except Exception as e:
                QMessageBox.warning(self, 'Warning', f'Could not copy skin to installation: {e}')
        self.on_save()
        self.accept()


class ExeSelectDialog(QDialog):
    def __init__(self, parent, install_path, on_selected):
        super().__init__(parent)
        self.install_path = install_path
        self.on_selected = on_selected
        self.setWindowTitle('Select Executable')
        _apply_dialog_style(self)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Minecraft.Windows.exe not found. Select the game executable:'))
        browse_btn = ImageButton('Browse')
        browse_btn.clicked.connect(self._browse)
        cancel_btn = ImageButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(browse_btn)
        layout.addWidget(cancel_btn)
        center_dialog(self, 450, 120)

    def _browse(self):
        path = QFileDialog.getOpenFileName(self, 'Select Executable', self.install_path, 'Executable (*.exe);;All (*.*)')[0]
        if path:
            self.on_selected(path)
            self.accept()


class _LANDiscoveryThread(QThread):
    found = Signal(list)

    def run(self):
        servers = discover_lan_servers(timeout=5.0)
        self.found.emit(servers)


class ServersDialog(QDialog):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self._lan_thread = None
        self.setWindowTitle('Servers')
        _apply_dialog_style(self)
        layout = QVBoxLayout(self)
        lan_label = QLabel('LAN Games (local network)')
        lan_label.setFont(get_font(12))
        layout.addWidget(lan_label)
        lan_row = QHBoxLayout()
        self._lan_list = QListWidget()
        self._lan_list.setFont(get_font(11))
        self._lan_list.setMinimumHeight(80)
        self._lan_list.itemDoubleClicked.connect(self._on_lan_double_click)
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
        layout.addLayout(lan_row)
        layout.addWidget(QLabel('Saved servers (name : address)'))
        self._list = QListWidget()
        self._list.setFont(get_font(11))
        for s in config.get('servers', []):
            self._list.addItem(QListWidgetItem('%s : %s' % (s.get('name', ''), s.get('address', ''))))
        layout.addWidget(self._list)
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText('Server name')
        self._addr_edit = QLineEdit()
        self._addr_edit.setPlaceholderText('host:port')
        form.addRow('Name:', self._name_edit)
        form.addRow('Address:', self._addr_edit)
        layout.addLayout(form)
        btn_row = QHBoxLayout()
        add_btn = ImageButton('Add')
        add_btn.clicked.connect(self._add_server)
        remove_btn = ImageButton('Remove')
        remove_btn.clicked.connect(self._remove_server)
        ok_btn = ImageButton('OK')
        ok_btn.clicked.connect(self._save_and_close)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)
        center_dialog(self, 480, 520)

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

    def _on_lan_double_click(self, item):
        s = item.data(Qt.ItemDataRole.UserRole)
        if s:
            self._add_lan_server(s)

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
        self.config.setdefault('servers', []).append({'name': name, 'address': addr})
        self._list.addItem(QListWidgetItem('%s : %s' % (name, addr)))

    def _add_server(self):
        name = self._name_edit.text().strip()
        addr = self._addr_edit.text().strip()
        if not name or not addr:
            QMessageBox.warning(self, 'Error', 'Enter name and address')
            return
        self.config.setdefault('servers', []).append({'name': name, 'address': addr})
        self._list.addItem(QListWidgetItem('%s : %s' % (name, addr)))
        self._name_edit.clear()
        self._addr_edit.clear()

    def _remove_server(self):
        row = self._list.currentRow()
        if row >= 0:
            servers = self.config.get('servers', [])
            if row < len(servers):
                servers.pop(row)
                self._list.takeItem(row)

    def _save_and_close(self):
        self.on_save()
        self.accept()
