import os
import shutil
import requests
import tempfile


def get_char5_path(install_path):
    return os.path.join(install_path, 'common', 'res', 'mob', 'char5.png')


def install_skin_to_installation(skin_path, install_path):
    dest_dir = os.path.join(install_path, 'common', 'res', 'mob')
    dest_path = os.path.join(dest_dir, 'char5.png')
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy2(skin_path, dest_path)
    return dest_path


def install_skin_from_url_to_installation(skin_url, install_path):
    r = requests.get(skin_url, timeout=15)
    r.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(r.content)
        tmp = f.name
    try:
        return install_skin_to_installation(tmp, install_path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


_temp_skin_files = []


def get_skin_for_preview(profile, install_path):
    skin_path = profile.get('skin_path')
    skin_url = profile.get('skin_url')
    char5 = get_char5_path(install_path) if install_path else None
    if skin_path and os.path.isfile(skin_path):
        return skin_path
    if char5 and os.path.isfile(char5):
        return char5
    if skin_url:
        try:
            r = requests.get(skin_url, timeout=5)
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                f.write(r.content)
                path = f.name
                _temp_skin_files.append(path)
                return path
        except Exception:
            pass
    return None
