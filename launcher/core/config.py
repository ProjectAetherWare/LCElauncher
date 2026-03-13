import os
import json
import random
import sys


def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def get_config_path():
    return os.path.join(get_base_path(), 'config.json')


def get_installations_path():
    return os.path.join(get_base_path(), 'installations')


def default_username():
    return "User" + "".join(str(random.randint(0, 9)) for _ in range(5))


def default_config():
    return {
        "installations": [],
        "selected_installation": None,
        "profile": {
            "username": default_username(),
            "skin_path": None,
            "skin_url": None
        },
        "options": {
            "fullscreen": True,
            "width": 900,
            "height": 600
        },
        "servers": []
    }


def load_config():
    path = get_config_path()
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'profile' in data and not data['profile'].get('username'):
                data['profile']['username'] = default_username()
            if 'servers' not in data:
                data['servers'] = []
            return data
    return default_config()


def save_config(data):
    path = get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
