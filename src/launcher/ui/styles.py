import os
from PySide6.QtGui import QFont, QFontDatabase


def get_font(size=14):
    font_path = _get_font_path()
    if font_path and os.path.isfile(font_path):
        fid = QFontDatabase.addApplicationFont(font_path)
        if fid >= 0:
            families = QFontDatabase.applicationFontFamilies(fid)
            if families:
                return QFont(families[0], size)
    return QFont('Segoe UI', size)


def _get_font_path():
    from launcher.utils.path_utils import get_asset_path
    return get_asset_path('font.ttf')


def get_button_stylesheet(width=None, height=None, use_textures=True):
    norm_path = None
    hover_path = None
    if use_textures:
        from launcher.utils.path_utils import get_asset_path
        norm_path = get_asset_path('ButtonNormal.png')
        hover_path = get_asset_path('ButtonHover.png')
    if norm_path and hover_path and os.path.isfile(norm_path) and os.path.isfile(hover_path):
        # Qt stylesheet url() needs file:/// with forward slashes
        norm_url = 'file:///' + norm_path.replace('\\', '/')
        hover_url = 'file:///' + hover_path.replace('\\', '/')
        base = """
            QPushButton {
                border: none;
                background: transparent;
                background-image: url(%s);
                background-repeat: no-repeat;
                background-position: center;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover, QPushButton:pressed {
                background-image: url(%s);
            }
            QPushButton:disabled { opacity: 0.5; }
        """ % (norm_url, hover_url)
    else:
        base = """
            QPushButton {
                border: none;
                background: #4a6a4a;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover, QPushButton:pressed { background: #5a7a5a; }
            QPushButton:disabled { opacity: 0.5; }
        """
    if width and height:
        base += " QPushButton { min-width: %dpx; min-height: %dpx; }" % (width, height)
    return base


def get_dark_stylesheet():
    return """
        QWidget { background: #2d2d2d; color: white; }
        QLabel { color: white; background: transparent; }
        QLineEdit {
            background: #3d3d3d;
            color: white;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 6px;
        }
        QLineEdit:focus { border-color: #6a9; }
        QComboBox {
            background: #3d3d3d;
            color: white;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 6px;
            min-width: 120px;
        }
        QComboBox:hover { border-color: #6a9; }
        QComboBox::drop-down { border: none; }
        QCheckBox { color: white; }
        QCheckBox::indicator { width: 18px; height: 18px; background: #3d3d3d; border: 2px solid #555; border-radius: 3px; }
        QCheckBox::indicator:checked { background: #4a7; }
        QRadioButton { color: white; }
        QScrollArea { border: none; background: transparent; }
        QTabWidget::pane { border: 1px solid #444; border-radius: 4px; background: #2d2d2d; }
        QTabBar::tab { background: #3d3d3d; color: white; padding: 8px 16px; margin-right: 2px; }
        QTabBar::tab:selected { background: #4d4d4d; }
        QTabBar::tab:hover:!selected { background: #454545; }
        QFrame { background: transparent; }
        QMessageBox { background: #2d2d2d; color: white; }
    """
