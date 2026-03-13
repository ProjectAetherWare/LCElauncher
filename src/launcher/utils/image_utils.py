import os
import sys
from PIL import Image, ImageFilter, ImageTk


def get_assets_path():
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        return os.path.join(base, 'Assets')
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Assets')


def get_asset_path(*parts):
    return os.path.join(get_assets_path(), *parts)


def blur_image(img_path, radius=2):
    img = Image.open(img_path).convert('RGB')
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def load_image(path, size=None):
    img = Image.open(path).convert('RGBA')
    if size:
        img = img.resize(size, Image.Resampling.LANCZOS)
    return img


def pil_to_photo(img):
    return ImageTk.PhotoImage(img)


def load_image_tk(path, size=None):
    img = load_image(path, size)
    return pil_to_photo(img)
