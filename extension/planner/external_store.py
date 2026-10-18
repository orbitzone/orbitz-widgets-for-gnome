"""External calendar accounts and caches; no credentials or task data."""
import fcntl,json,os
import atomic_json
from credential_vault import Vault  # Existing callers use external_store.Vault.
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
        atomic_json.write(PATH, data, prefix='.external-')
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
