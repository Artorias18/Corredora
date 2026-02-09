import os

def get_file_name(path):
    return os.path.basename(path)

def get_file_extension(path):
    return os.path.splitext(path)[1].replace(".", "").lower()


import sys

def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta absoluta a un recurso.
    Funciona tanto en desarrollo como en el .exe (PyInstaller).
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller
    except AttributeError:
        base_path = os.path.abspath(".")  # desarrollo

    return os.path.join(base_path, relative_path)
