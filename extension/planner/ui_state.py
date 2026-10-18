"""Small durable UI preferences/drafts, separate from historical records."""
import fcntl,json,os
import atomic_json
from pathlib import Path
PATH=Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'orbitz-widgets'/'planner-ui.json'

def read():
    try:
        data=json.loads(PATH.read_text())
        if not isinstance(data,dict):raise ValueError('Arquivo de rascunhos inválido; original preservado.')
        return data
    except FileNotFoundError:return {}

def get(key,default=None):
    # A damaged draft file must never prevent access to the historical records.
    # Writes still fail explicitly, preserving the damaged file for recovery.
    try:return read().get(key,default)
    except (OSError,ValueError):return default

def set(key,value):
    PATH.parent.mkdir(parents=True,exist_ok=True)
    with open(str(PATH)+'.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);data=read()
        if value is None:data.pop(key,None)
        else:data[key]=value
        atomic_json.write(PATH, data, prefix='.planner-ui-')
