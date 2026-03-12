import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Leer directamente los archivos urls.py
import glob, pathlib

base = pathlib.Path('.')
for f in sorted(base.rglob('urls.py')):
    if 'venv' in str(f) or 'migrations' in str(f):
        continue
    print(f"\n{'='*50}")
    print(f"ARCHIVO: {f}")
    print('='*50)
    print(f.read_text(encoding='utf-8'))
