#!/usr/bin/python3
import os
from pathlib import Path
script=Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'orbitz-postits/app/postits.py'
env=dict(os.environ,GDK_BACKEND='x11')
os.execve('/usr/bin/python3',['/usr/bin/python3',str(script)],env)
