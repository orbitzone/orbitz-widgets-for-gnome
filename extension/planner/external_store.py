"""External calendar accounts and caches; no credentials or task data."""
import contextlib,fcntl,json,os,tempfile
from pathlib import Path
PATH=Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'orbitz-widgets'/'external-calendars.json'

def read():
    try:data=json.loads(PATH.read_text())
    except FileNotFoundError:return {'accounts':[],'cache':{}}
    if not isinstance(data,dict) or not isinstance(data.get('accounts'),list) or not isinstance(data.get('cache'),dict):raise ValueError('Arquivo de calendários externos inválido; original preservado.')
    return data

def update(callback):
    PATH.parent.mkdir(parents=True,exist_ok=True)
    with open(str(PATH)+'.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);data=read();callback(data)
        fd,tmp=tempfile.mkstemp(prefix='.external-',dir=PATH.parent)
        try:
            with os.fdopen(fd,'w') as out:
                os.fchmod(out.fileno(),0o600);json.dump(data,out,ensure_ascii=False);out.flush();os.fsync(out.fileno())
            os.replace(tmp,PATH)
            fd=os.open(PATH.parent,os.O_RDONLY)
            try:os.fsync(fd)
            finally:os.close(fd)
        finally:
            with contextlib.suppress(FileNotFoundError):os.unlink(tmp)
    return data

def add_account(account):
    def add(data):
        if any(a['id']==account['id'] or (account.get('email') and a.get('email','').casefold()==account['email'].casefold()) for a in data['accounts']):raise ValueError('Esta conta já está conectada. Desconecte-a em Gerenciar conexões para conectar novamente.')
        data['accounts'].append(account)
    return update(add)

def remove_account(identity):
    def remove(data):
        account=next((a for a in data['accounts'] if a['id']==identity),None)
        if account:
            ids={c['id'] for c in account['calendars']};data['accounts'].remove(account)
            data['cache']={k:v for k,v in data['cache'].items() if not any(k.startswith(identity+'|'+i+'|') for i in ids)}
    return update(remove)

def cache_key(account_id,calendar_id,month):return '|'.join((account_id,calendar_id,month))
def put_cache(account_id,calendar,month,events,updated):
    def save(data):
        account=next((a for a in data['accounts'] if a['id']==account_id),None)
        if account and any(c['id']==calendar['id'] for c in account['calendars']):
            data['cache'][cache_key(account_id,calendar['id'],month)]={'events':events,'updated':updated}
    return update(save)

class Vault:
    """Passwords live exclusively in the desktop Secret Service."""
    def _service(self):
        import gi
        gi.require_version('Secret','1');from gi.repository import Secret
        schema=Secret.Schema.new('io.orbitz.Calendar.iCloud',Secret.SchemaFlags.NONE,{'account':Secret.SchemaAttributeType.STRING})
        return Secret,schema
    def put(self,identity,password):
        Secret,schema=self._service()
        if not Secret.password_store_sync(schema,{'account':identity},Secret.COLLECTION_DEFAULT,'Orbitz · Calendário iCloud',password,None):
            raise ValueError('Não foi possível guardar a senha no cofre do sistema.')
    def get(self,identity):
        Secret,schema=self._service();password=Secret.password_lookup_sync(schema,{'account':identity},None)
        if not password:raise ValueError('A senha do calendário não está disponível no cofre. Desbloqueie o cofre ou reconecte a conta.')
        return password
    def delete(self,identity):
        Secret,schema=self._service();Secret.password_clear_sync(schema,{'account':identity},None)
