"""Small durable UI preferences/drafts, separate from historical records."""
import contextlib,fcntl,json,os,tempfile
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
        fd,name=tempfile.mkstemp(prefix='.planner-ui-',dir=PATH.parent)
        try:
            with os.fdopen(fd,'w') as stream:
                os.fchmod(stream.fileno(),0o600);json.dump(data,stream,ensure_ascii=False);stream.flush();os.fsync(stream.fileno())
            os.replace(name,PATH)
            directory=os.open(PATH.parent,os.O_RDONLY)
            try:os.fsync(directory)
            finally:os.close(directory)
        finally:
            with contextlib.suppress(FileNotFoundError):os.unlink(name)
