import tkinter.font as tkfont
from PIL import Image, ImageDraw, ImageFont
from launcher.utils.image_utils import get_asset_path, pil_to_photo

_text_cache = {}
_font_cache = {}


def get_font(size=12, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        try:
            path = get_asset_path('font.ttf')
            weight = 'bold' if bold else 'normal'
            _font_cache[key] = tkfont.Font(file=path, size=size, weight=weight)
        except Exception:
            _font_cache[key] = ('TkDefaultFont', size, 'bold' if bold else 'normal')
    return _font_cache[key]


def render_text(text, size=12, color='white', bold=False):
    key = (text, size, color, bold)
    if key not in _text_cache:
        try:
            path = get_asset_path('font.ttf')
            font = ImageFont.truetype(path, size)
        except Exception:
            font = ImageFont.load_default()
        bbox = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        img = Image.new('RGBA', (int(w) + 4, int(h) + 4), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2, 2), text, fill=color, font=font)
        _text_cache[key] = pil_to_photo(img)
    return _text_cache[key]


def render_text_uncached(text, size=12, color='white'):
    try:
        path = get_asset_path('font.ttf')
        font = ImageFont.truetype(path, size)
    except Exception:
        font = ImageFont.load_default()
    bbox = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new('RGBA', (int(w) + 4, int(h) + 4), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((2, 2), text, fill=color, font=font)
    return pil_to_photo(img)
