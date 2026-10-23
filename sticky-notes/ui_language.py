"""Locate the shared UI runtime in a checkout or installed Orbitz bundle."""
import os
from pathlib import Path
import sys
_roots=[Path(os.environ['ORBITZ_I18N_DIR'])] if os.environ.get('ORBITZ_I18N_DIR') else []
_roots += [Path(__file__).resolve().parents[1]/'i18n',Path.home()/'.local/share/orbitz-widgets/i18n']
for _root in _roots:
    if (_root/'ui_i18n.py').is_file():
        sys.path.insert(0,str(_root));break
import ui_i18n as ui
