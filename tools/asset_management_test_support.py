"""Resolve historical test subjects to canonical packages and explicit native modes."""
from pathlib import Path
from resolve_skill import resolve

ROOT = Path(__file__).resolve().parents[1]

def package(name):
    return ROOT / resolve(name)['path']

def script(name, filename):
    selected = resolve(name)
    mode = selected.get('mode')
    prefix = mode + '_' if mode and filename in {
        'calculate_or_transform.py', 'validate_input.py', 'validate_output.py'
    } else ''
    return ROOT / selected['path'] / 'scripts' / (prefix + filename)
