import os
from pathlib import Path
import shutil
import subprocess

def emulator_command(system):
    name = system['emulator'].strip()
    if not name or name.startswith('-'):
        raise ValueError('Configura el emulador de esta consola.')
    if system['mode'] == 'flatpak':
        flatpak = shutil.which('flatpak')
        if not flatpak:
            raise ValueError('Flatpak no está instalado.')
        check = subprocess.run([flatpak, 'info', name], capture_output=True, timeout=10)
        if check.returncode:
            raise ValueError('La aplicación Flatpak no está instalada.')
        return [flatpak, 'run', name]
    executable = shutil.which(str(Path(name).expanduser()))
    if not executable:
        raise ValueError('No se encontró un ejecutable válido para el emulador.')
    return [executable]


def browse_folder():
    """Open a native chooser in the server user's graphical session."""
    zenity = shutil.which('zenity')
    kdialog = shutil.which('kdialog') if not zenity else None
    if zenity:
        command = [zenity, '--file-selection', '--directory', '--title=Seleccionar carpeta']
    elif kdialog:
        command = [kdialog, '--getexistingdirectory', str(Path.home()), '--title', 'Seleccionar carpeta']
    else:
        raise ValueError('Para examinar carpetas instala zenity (GNOME) o kdialog (KDE). También puedes escribir la ruta.')
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if result.returncode == 1:
        return {'path': None}
    if result.returncode != 0:
        raise ValueError('No se pudo abrir el selector. Ejecuta el servidor dentro de tu sesión gráfica.')
    path = result.stdout.rstrip('\n')
    if not path or not Path(path).is_dir():
        raise ValueError('La carpeta seleccionada no está disponible.')
    return {'path': path}


def browse_emulator():
    zenity = shutil.which('zenity')
    kdialog = shutil.which('kdialog') if not zenity else None
    title = 'Seleccionar ejecutable del emulador'
    if zenity:
        command = [zenity, '--file-selection', '--title=' + title]
    elif kdialog:
        command = [kdialog, '--getopenfilename', str(Path.home()), '--title', title]
    else:
        raise ValueError('Instala zenity (GNOME) o kdialog (KDE) para examinar archivos, o escribe la ruta.')
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if result.returncode == 1:
        return {'path': None}
    if result.returncode != 0:
        raise ValueError('No se pudo abrir el selector. Ejecuta el servidor dentro de tu sesión gráfica.')
    path = result.stdout.rstrip('\n')
    if not path or not Path(path).is_file() or not os.access(path, os.X_OK):
        raise ValueError('Selecciona un archivo ejecutable. Si es una AppImage, activa su permiso de ejecución.')
    return {'path': path}
