import os
import zipfile
import tempfile
import shutil
import requests
from urllib.request import urlretrieve

DEFAULT_URL = "https://github.com/smartcmd/MinecraftConsoles/releases/download/nightly/LCEWindows64.zip"


def download_file(url, dest_path, progress_callback=None):
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total:
                        progress_callback(downloaded, total)
    except requests.RequestException:
        urlretrieve(url, dest_path)


def extract_zip(zip_path, dest_dir):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(dest_dir)


def merge_dirs(src_dir, dest_dir):
    for root, dirs, files in os.walk(src_dir):
        rel = os.path.relpath(root, src_dir)
        if rel == '.':
            target_dir = dest_dir
        else:
            target_dir = os.path.join(dest_dir, rel)
        os.makedirs(target_dir, exist_ok=True)
        for f in files:
            src_file = os.path.join(root, f)
            dst_file = os.path.join(target_dir, f)
            shutil.copy2(src_file, dst_file)


def install_from_url(url, install_name, installs_base, progress_callback=None):
    os.makedirs(installs_base, exist_ok=True)
    install_path = os.path.join(installs_base, install_name)
    os.makedirs(install_path, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, 'download.zip')
        download_file(url, zip_path, progress_callback)
        extract_path = os.path.join(tmp, 'extracted')
        os.makedirs(extract_path)
        extract_zip(zip_path, extract_path)
        contents = os.listdir(extract_path)
        if len(contents) == 1 and os.path.isdir(os.path.join(extract_path, contents[0])):
            merge_dirs(os.path.join(extract_path, contents[0]), install_path)
        else:
            merge_dirs(extract_path, install_path)
    return install_path


def update_installation(install_path, source_url, progress_callback=None):
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, 'update.zip')
        download_file(source_url, zip_path, progress_callback)
        extract_path = os.path.join(tmp, 'extracted')
        os.makedirs(extract_path)
        extract_zip(zip_path, extract_path)
        contents = os.listdir(extract_path)
        if len(contents) == 1 and os.path.isdir(os.path.join(extract_path, contents[0])):
            merge_dirs(os.path.join(extract_path, contents[0]), install_path)
        else:
            merge_dirs(extract_path, install_path)
