import os
from pathlib import Path
from app.repositories.settings import SYSTEMS

def scan(config):
    result, warnings = {}, []
    for key, system in config['systems'].items():
        files = set()
        folders = system['folders'] or ([str(Path(config['rom_root']).expanduser() / key)] if config.get('rom_root') else [])
        for folder in folders:
            base = Path(folder).expanduser()
            if not base.is_dir():
                warnings.append(f'Carpeta no disponible: {folder}')
                continue
            def onerror(error):
                warnings.append(f'No se pudo leer: {error.filename}')
            for directory, _, names in os.walk(base, onerror=onerror, followlinks=False):
                for name in names:
                    file = Path(directory) / name
                    if file.suffix.lower() in SYSTEMS[key]:
                        files.add(str(file.resolve()))
                    if len(files) > 20000:
                        raise ValueError('Demasiados archivos. Selecciona carpetas más específicas.')
        result[key] = sorted(files)
    return {'files': result, 'warnings': warnings}

