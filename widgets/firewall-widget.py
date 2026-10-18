#!/usr/bin/env python3
"""Incremental, bounded UFW pattern analysis. No firewall rule changes."""
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import sys
import tempfile
import time
from widget_runtime import run as bounded_run
from firewall_patterns import (
    WINDOW, MAX_SOURCES, DISCOVERY, empty, valid_state, prune, limited_add,
    ingest, date, summarize, payload,
)

CACHE = Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))/'orbitz-widgets'/'firewall-patterns-v2.json'
PREFIX = 'AZCLOCK_FIREWALL:'
BATCH = 10000
MAX_CACHE = 8388608


def load():
    try:
        fd=os.open(CACHE, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode): raise ValueError('Cache inválido')
            raw=f.read(MAX_CACHE+1)
        if len(raw)>MAX_CACHE: raise ValueError('Cache grande')
        data=json.loads(raw)
        if not valid_state(data): raise ValueError('Cache inválido')
        return data
    except (OSError, ValueError, TypeError, AttributeError): return empty()

def save(data):
    raw=json.dumps(data,ensure_ascii=False).encode()
    while len(raw)>MAX_CACHE and data['sources']:
        oldest=sorted(data['sources'],key=lambda s:data['sources'][s]['last'])[:max(1,len(data['sources'])//4)]
        for source in oldest: del data['sources'][source]
        data['limited_until']=time.time()+WINDOW
        raw=json.dumps(data,ensure_ascii=False).encode()
    fd,name=tempfile.mkstemp(prefix='firewall-patterns-',dir=CACHE.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(raw)
        os.replace(name,CACHE)
    finally:
        if os.path.exists(name): os.unlink(name)

def journal_batch(cursor):
    args=['journalctl','_TRANSPORT=kernel','--since','24 hours ago','--no-tail',r'--grep=\[UFW (BLOCK|REJECT)\]', '-o','json','--output-fields=MESSAGE,__REALTIME_TIMESTAMP,__CURSOR','--no-pager','-q']
    if cursor: args+=['--after-cursor',cursor]
    records=[]; stderr=bytearray(); pending=bytearray(); partial=False; collected_bytes=0
    with subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE) as proc:
        sel=selectors.DefaultSelector()
        for stream in (proc.stdout,proc.stderr):
            os.set_blocking(stream.fileno(),False);sel.register(stream,selectors.EVENT_READ)
        deadline=time.monotonic()+8
        try:
            while sel.get_map():
                if time.monotonic()>=deadline:
                    partial=True;break
                for key,_ in sel.select(.1):
                    chunk=os.read(key.fileobj.fileno(),8192)
                    if not chunk:sel.unregister(key.fileobj);continue
                    if key.fileobj is proc.stderr:
                        stderr.extend(chunk[:max(0,8192-len(stderr))]);continue
                    pending.extend(chunk)
                    while b'\n' in pending:
                        line,_,rest=pending.partition(b'\n');pending=bytearray(rest)
                        if len(line)>65536:raise ValueError('Registro do journal grande demais.')
                        if collected_bytes+len(line)>4194304:partial=True;break
                        collected_bytes+=len(line)
                        records.append(line)
                        if len(records)>=BATCH:partial=True;break
                    if partial:break
                    if len(pending)>65536:raise ValueError('Registro do journal grande demais.')
                if partial:break
            if partial:
                proc.terminate();proc.wait(timeout=1)
            else:
                proc.wait(timeout=1)
                if pending:records.append(bytes(pending))
                error=stderr.decode(errors='replace')
                if proc.returncode or 'not seeing messages' in error.lower() or 'permission denied' in error.lower():
                    raise RuntimeError(error[:200] or 'Sem acesso ao journal do kernel.')
        finally:
            sel.close()
            if proc.poll() is None:proc.kill();proc.wait()
    return records,partial


def collect():
    CACHE.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(CACHE.parent/'firewall-patterns.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
    with os.fdopen(fd,'r+') as lock:
        if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode):raise ValueError('Lock inválido')
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            p=payload(load());p['scope']+='\nOutra consulta está em andamento.';return p
        data=load()
        try:lines,partial=journal_batch(data['cursor'])
        except RuntimeError as e:
            if data['cursor'] and any(x in str(e).lower() for x in ('cursor','seek')):
                data=empty();lines,partial=journal_batch('')
            else:raise
        ingest(data,lines,time.time());data['partial']=partial
        save(data);return payload(data)

def inspect_target(kind,target):
    if kind=='ip':target=str(ipaddress.ip_address(target))
    elif not target.isdecimal() or not 1<=int(target)<=65535:raise ValueError('Porta inválida')
    data=load();prune(data,time.time());groups=[];samples=[]
    for source,g in data['sources'].items():
        matched=source==target or any(target in b['destinations' if kind=='ip' else 'ports'] for b in g['buckets'].values())
        if kind=='port':matched=any(target in b['ports'] for b in g['buckets'].values())
        if not matched:continue
        summary=summarize(source,g,time.time())
        if summary:groups.append(source+'\n'+summary['reason']+'\nPrimeiro: '+summary['first']+' · Último: '+summary['last'])
        for sample in g['samples']:
            f=dict(re.findall(r'\b([A-Z]+)=([^\s]*)',sample['message']))
            if (kind=='ip' and target in (f.get('SRC'),f.get('DST'))) or (kind=='port' and target==f.get('DPT')):samples.append(sample)
    text=[('IP: ' if kind=='ip' else 'Porta: ')+target,'Evidências da janela de 24 h coletada; amostras não são a lista completa.','\n\n'.join(groups[:20]) or 'Nenhum padrão destacado para esta seleção.']
    if kind=='port':
        r=bounded_run(['ss','-H','-ltnup'],timeout=3)
        listeners=[l[:512] for l in r.stdout.splitlines() if len(l.split())>=5 and l.split()[4].rsplit(':',1)[-1]==target]
        text+=['Escuta local atual:', '\n'.join(listeners[:10]) or ('Consulta indisponível.' if r.returncode else 'Nenhuma escuta visível.')]
    text+=['Amostras de bloqueios:', '\n'.join(date(x['time'])+' '+x['message'] for x in sorted(samples,key=lambda x:x['time'])[-20:]) or 'Nenhuma amostra recente disponível.']
    return dict(inspect='\n\n'.join(text),remote=kind=='ip' and ipaddress.ip_address(target).is_global)

def main():
    if '--inspect-ip' in sys.argv or '--inspect-port' in sys.argv:
        flag='--inspect-ip' if '--inspect-ip' in sys.argv else '--inspect-port'
        result=inspect_target('ip' if flag=='--inspect-ip' else 'port',sys.argv[sys.argv.index(flag)+1])
    elif '--dns' in sys.argv:
        target=str(ipaddress.ip_address(sys.argv[sys.argv.index('--dns')+1]))
        r=bounded_run(['getent','hosts',target],timeout=5)
        result={'inspect':'DNS reverso: '+target+'\n'+(r.stdout[:4096].strip() or 'Sem nome retornado.')+'\nUm nome DNS não comprova a identidade da origem.'}
    else:
        try:result=collect()
        except (OSError,RuntimeError,ValueError,subprocess.SubprocessError) as e:
            result=payload(load());result['text']='Firewall: consulta indisponível';result['scope']+='\nFalha na atualização; dados anteriores: '+str(e)[:200]
        if '--details' not in sys.argv:result={k:result[k] for k in ('text','updated')}
    print(PREFIX+json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except (OSError,subprocess.SubprocessError,RuntimeError,ValueError,IndexError) as e:
        print(str(e),file=sys.stderr);sys.exit(1)
