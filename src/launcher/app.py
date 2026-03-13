import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from launcher.core.config import load_config, save_config, get_installations_path
from launcher.core.launcher_logic import find_exe, launch_game
from launcher.core.installer import update_installation, DEFAULT_URL
from launcher.core.skin_service import install_skin_to_installation, install_skin_from_url_to_installation, get_skin_for_preview
from launcher.utils.path_utils import get_asset_path
from launcher.ui.start_tab import StartTab
from launcher.ui.manager_tab import ManagerTab
from launcher.ui.topbar import BlurredTopBar
from launcher.ui.pages import ProfilePage, ServersPage, OptionsPage
from launcher.ui.dialogs import (
    AddInstallDialog, EditInstallDialog, SkinDialog, ExeSelectDialog
)


class LauncherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('LegacyLauncher')
        self.setMinimumSize(800, 533)
        self.resize(900, 600)
        icon_path = get_asset_path('minilogo.png')
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.config = load_config()
        self.installs_base = get_installations_path()
        os.makedirs(self.installs_base, exist_ok=True)
        self._start_tab = None
        self._manager_tab = None
        self._build()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        self._tabs = QTabWidget()
        self._tabs.tabBar().hide()
        self._start_tab = StartTab(self)
        self._manager_tab = ManagerTab(self)
        self._profile_tab = ProfilePage(self)
        self._servers_tab = ServersPage(self)
        self._options_tab = OptionsPage(self)
        self._tabs.addTab(self._start_tab, 'Start')
        self._tabs.addTab(self._manager_tab, 'Instances')
        self._tabs.addTab(self._profile_tab, 'Profile')
        self._tabs.addTab(self._servers_tab, 'Servers')
        self._tabs.addTab(self._options_tab, 'Options')
        layout.addWidget(self._tabs, 1)
        self._topbar = BlurredTopBar(self)
        self._topbar.setParent(central)
        self._topbar.raise_()
        self._topbar.nav_play.connect(lambda: self._tabs.setCurrentIndex(0))
        self._topbar.nav_instances.connect(lambda: self._tabs.setCurrentIndex(1))
        self._topbar.nav_profile.connect(lambda: self._tabs.setCurrentIndex(2))
        self._topbar.nav_servers.connect(lambda: self._tabs.setCurrentIndex(3))
        self._topbar.nav_options.connect(lambda: self._tabs.setCurrentIndex(4))
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self._central = central
        self._start_tab.refresh_versions()
        self._manager_tab.refresh()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        w = self._central.width() if hasattr(self, '_central') else self.centralWidget().width()
        self._topbar.setGeometry(0, 0, w, self._topbar.height())

    def _on_tab_changed(self, idx):
        names = ['play', 'instances', 'profile', 'servers', 'options']
        self._topbar.set_active_tab(names[idx] if 0 <= idx < len(names) else 'play')
        self._topbar.refresh_username()

    def show_tab(self, idx):
        self._tabs.setCurrentIndex(idx)
        if idx == 0:
            self._start_tab.refresh_versions()
            self._start_tab.refresh_splash()
            self._start_tab.refresh_skin()
        elif idx == 1:
            self._manager_tab.refresh()

    def _save_config(self):
        save_config(self.config)

    def on_play(self):
        sel = self.config.get('selected_installation')
        if not sel:
            QMessageBox.information(self, 'Info', 'No installation selected. Add one first.')
            return
        installs = self.config.get('installations', [])
        inst = next((i for i in installs if i['name'] == sel), None)
        if not inst:
            QMessageBox.critical(self, 'Error', 'Installation not found')
            return
        path = inst.get('path')
        if not path or not os.path.isdir(path):
            QMessageBox.critical(self, 'Error', 'Installation path invalid')
            return
        exe_path = find_exe(path, inst.get('exe_path'))
        if not exe_path:
            ExeSelectDialog(self, path, lambda p: self._on_exe_selected(inst, p)).exec()
            return
        profile = self.config.get('profile', {})
        username = profile.get('username', 'Steve')
        opts = self.config.get('options', {})
        fullscreen = opts.get('fullscreen', True)
        launch_game(exe_path, username, fullscreen)
        self._start_tab.set_status('Launching...')

    def _on_exe_selected(self, inst, exe_path):
        inst['exe_path'] = exe_path
        self._save_config()
        profile = self.config.get('profile', {})
        username = profile.get('username', 'Steve')
        opts = self.config.get('options', {})
        fullscreen = opts.get('fullscreen', True)
        launch_game(exe_path, username, fullscreen)
        self._start_tab.set_status('Launching...')

    def on_update_current(self):
        sel = self.config.get('selected_installation')
        if not sel:
            QMessageBox.information(self, 'Info', 'No installation selected')
            return
        installs = self.config.get('installations', [])
        idx = next((i for i, x in enumerate(installs) if x['name'] == sel), None)
        if idx is not None:
            self.on_update_installation(idx)

    def on_update_installation(self, idx):
        installs = self.config.get('installations', [])
        if idx >= len(installs):
            return
        inst = installs[idx]
        path = inst.get('path')
        url = inst.get('source_url', DEFAULT_URL)
        if not path or not url:
            QMessageBox.critical(self, 'Error', 'Missing path or source URL')
            return

        def progress(done, total):
            if total:
                pct = int(100 * done / total)
                self._start_tab.set_status(f'Updating... {pct}%')
                QApplication.processEvents()

        try:
            self._start_tab.set_status('Updating...')
            QApplication.processEvents()
            update_installation(path, url, progress)
            self._start_tab.set_status('Updated!')
            self._manager_tab.refresh()
            QMessageBox.information(self, 'Success', 'Update complete')
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))
        finally:
            self._start_tab.set_status('')

    def show_skin_dialog(self):
        def on_save():
            self._save_config()
            self._start_tab.refresh_skin()
        SkinDialog(self, self.config, on_save).exec()

    def show_add_install_dialog(self):
        AddInstallDialog(self, self.config, self.installs_base, self._on_install_added).exec()

    def _on_install_added(self):
        self._save_config()
        self._start_tab.refresh_versions()
        self._manager_tab.refresh()

    def show_edit_install_dialog(self, idx):
        EditInstallDialog(self, self.config, idx, self._on_install_edited).exec()

    def _on_install_edited(self):
        self._save_config()
        self._start_tab.refresh_versions()
        self._manager_tab.refresh()

    def delete_installation(self, idx):
        installs = self.config.get('installations', [])
        if idx >= len(installs):
            return
        inst = installs.pop(idx)
        if self.config.get('selected_installation') == inst.get('name'):
            self.config['selected_installation'] = installs[0]['name'] if installs else None
        self._save_config()
        self._start_tab.refresh_versions()
        self._manager_tab.refresh()
