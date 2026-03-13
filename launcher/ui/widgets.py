import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from launcher.utils.image_utils import get_asset_path, blur_image, pil_to_photo


def create_blurred_bg(parent):
    bg_path = get_asset_path('bg.png')
    raw = blur_image(bg_path, radius=2)
    raw = raw.resize((900, 600), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(raw)
    label = tk.Label(parent, image=photo, bg='#2d2d2d')
    label.image = photo
    return label
