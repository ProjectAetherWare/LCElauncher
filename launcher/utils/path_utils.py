"""Asset path utilities - no PIL/ImageTk to avoid import conflicts."""
import os
import sys


def get_assets_path():
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        return os.path.join(base, 'Assets')
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Assets')


def get_asset_path(*parts):
    return os.path.join(get_assets_path(), *parts)
