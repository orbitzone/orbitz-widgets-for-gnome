"""Presentation-only translations shared by Orbitz Python collectors.

Callers pass stable catalog IDs. ORBITZ_LOCALE is
explicit, independent of system LANG/LC_ALL. Protocols, IDs and external values
must never be passed through this helper as translation keys.
"""
import json
import os
from pathlib import Path
from functools import lru_cache


def normalize_locale(value):
    return 'en-US' if isinstance(value, str) and value.replace('_', '-').lower() == 'en-us' else 'pt-BR'


def locale():
    return normalize_locale(os.environ.get('ORBITZ_LOCALE'))


def catalog_directory():
    explicit = os.environ.get('ORBITZ_I18N_DIR')
    if explicit:
        return Path(explicit)
    local = Path(__file__).resolve().parent / 'i18n'
    return local if local.is_dir() else Path(__file__).resolve().parent.parent / 'i18n'


@lru_cache(maxsize=8)
def _read_catalog(path, stamp, size):
    try:
        with Path(path).open('rb') as stream:
            raw = stream.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            return {}
        data = json.loads(raw.decode('utf-8'))
        if not isinstance(data, dict):
            return {}
        return {key: value for key, value in data.items() if isinstance(key, str) and isinstance(value, str)}
    except (OSError, UnicodeError, ValueError, RecursionError):
        return {}


def _catalog(language):
    path = catalog_directory() / (language + '.json')
    try:
        info = path.stat()
        return _read_catalog(str(path), info.st_mtime_ns, info.st_size)
    except OSError:
        return {}


def tr(key, params=None, fallback=None):
    """Look up display text, falling back to PT-BR, then the caller's text.

    External values are interpolated only after selecting the template, so a
    process/service/user name matching a message ID is never translated.
    """
    source = fallback if fallback is not None else key
    portuguese = _catalog('pt-BR').get(key, source)
    template = _catalog('en-US').get(key, portuguese) if locale() == 'en-US' else portuguese
    if not params:
        return template
    try:
        return template.format_map(params)
    except (KeyError, IndexError, ValueError, AttributeError, TypeError):
        try:
            return portuguese.format_map(params)
        except (KeyError, IndexError, ValueError, AttributeError, TypeError):
            return portuguese


def t(key, **values):
    return tr(key, values)
