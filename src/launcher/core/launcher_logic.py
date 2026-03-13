import os
import subprocess

EXE_NAMES = ['Minecraft.Windows.exe', 'Minecraft.Client.exe']


def find_exe(install_path, saved_exe_path=None):
    if saved_exe_path and os.path.isfile(saved_exe_path):
        return saved_exe_path
    for name in EXE_NAMES:
        path = os.path.join(install_path, name)
        if os.path.isfile(path):
            return path
    for root, dirs, files in os.walk(install_path):
        for f in files:
            if f in EXE_NAMES:
                return os.path.join(root, f)
    return None


def launch_game(exe_path, username, fullscreen=True):
    args = [exe_path, '-name', username]
    if fullscreen:
        args.append('-fullscreen')
    subprocess.Popen(args, cwd=os.path.dirname(exe_path))
