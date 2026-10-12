#!/usr/bin/env python3
"""Incremental, bounded UFW pattern analysis. No firewall rule changes."""
import collections
import datetime
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

CACHE = Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))/'orbitz-widgets'/'firewall-patterns-v2.json'
PREFIX = 'AZCLOCK_FIREWALL:'
WINDOW = 86400
BATCH = 10000
MAX_CACHE = 8388608
MAX_SOURCES = 512
DISCOVERY = {'137', '138', '1900', '5353', '5355'}

def empty():
    return dict(version=2, cursor='', sources={}, totals={}, partial=False, limited_until=0, updated=0)

def load():
    try:
        fd=os.open(CACHE, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as f:
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode): raise ValueError('Cache inválido')
            raw=f.read(MAX_CACHE+1)
        if len(raw)>MAX_CACHE: raise ValueError('Cache grande')
        data=json.loads(raw)
        if data.get('version')!=2 or not isinstance(data.get('sources'),dict) or not isinstance(data.get('totals'),dict): raise ValueError('Cache antigo')
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
    records=[]; stderr=bytearray(); pending=bytearray(); partial=False
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

def prune(data, now):
    cutoff=now-WINDOW
    for source in list(data['sources']):
        group=data['sources'][source]
        group['buckets']={k:v for k,v in group['buckets'].items() if v['last']>=cutoff}
        if not group['buckets']:del data['sources'][source]
    data['totals']={k:v for k,v in data['totals'].items() if int(k)*300+300>=cutoff}

def limited_add(values,value,limit):
    if value not in values and len(values)<limit: values.append(value)

def ingest(data, lines, now):
    prune(data,now)
    for line in lines:
        try:
            entry=json.loads(line)
            cursor=entry.get('__CURSOR')
            if isinstance(cursor,str) and len(cursor)<4096:data['cursor']=cursor
            msg=entry.get('MESSAGE','')
            if not isinstance(msg,str) or not re.search(r'\[UFW (?:BLOCK|REJECT)\]',msg):continue
            f=dict(re.findall(r'\b([A-Z]+)=([^\s]*)',msg))
            src=ipaddress.ip_address(f['SRC']);dst=ipaddress.ip_address(f['DST'])
            stamp=int(entry['__REALTIME_TIMESTAMP'])/1e6
            if not now-WINDOW<=stamp<=now+60:continue
            key=str(int(stamp)//300)
            total=data['totals'].setdefault(key,{'count':0,'noise':0})
            total['count']+=1
            proto={'2':'IGMP','1':'ICMP','58':'ICMPv6'}.get(f.get('PROTO','?'),f.get('PROTO','?'))[:16]
            port=f.get('DPT','—')
            if port!='—' and (not port.isdecimal() or not 1<=int(port)<=65535):continue
            noise=dst.is_multicast or str(dst)=='255.255.255.255' or (not src.is_global and proto=='UDP' and (port in DISCOVERY or f.get('SPT') in DISCOVERY)) or proto=='IGMP'
            if noise:total['noise']+=1;continue
            source=str(src)
            if source not in data['sources'] and len(data['sources'])>=MAX_SOURCES:
                victim=min(data['sources'],key=lambda s:data['sources'][s]['last'])
                del data['sources'][victim];data['limited_until']=now+WINDOW
            g=data['sources'].setdefault(source,{'buckets':{},'samples':[],'last':stamp})
            g['last']=max(g['last'],stamp)
            b=g['buckets'].setdefault(key,{'count':0,'first':stamp,'last':stamp,'ports':[],'destinations':[],'protocols':[],'interfaces':[]})
            b['count']+=1;b['first']=min(b['first'],stamp);b['last']=max(b['last'],stamp)
            for name,value,limit in [('ports',port,64),('destinations',str(dst),16),('protocols',proto,8),('interfaces',f.get('IN','')[:32],4)]:limited_add(b[name],value,limit)
            g['samples']=(g['samples']+[{'time':stamp,'message':msg[:1024]}])[-5:]
        except (ValueError,TypeError,KeyError,OverflowError,AttributeError):continue
    data['updated']=now

def date(stamp):
    return datetime.datetime.fromtimestamp(stamp).astimezone().strftime('%d/%m %H:%M:%S')

def summarize(source,g,now):
    buckets=list(g['buckets'].values())
    first=min(b['first'] for b in buckets);last=max(b['last'] for b in buckets)
    count=sum(b['count'] for b in buckets)
    def values(key):return sorted({x for b in buckets for x in b[key]})
    ports=values('ports');destinations=values('destinations');protocols=values('protocols')
    minutes=(last-first)/60;active=len(buckets)
    persistent=count>=12 and active>=3 and minutes>=10
    varied=len(ports)>=6 or len(destinations)>=3 or len(protocols)>=2
    burst=count>=30 and len(ports)>=12
    reason=[];priority=0
    if persistent and varied:
        priority=3;reason.append('Persistência com variação de caminhos: portas, destinos ou protocolos.')
    elif persistent and count>=30:
        priority=2;reason.append('Repetição persistente, mesmo sem variar o caminho.')
    elif burst:
        priority=2;reason.append('Muitas portas em uma sequência de bloqueios; possível varredura.')
    if not priority:return None
    if not ipaddress.ip_address(source).is_global:
        reason.append('Origem local/reservada: pode ser comunicação normal entre dispositivos. Revise o equipamento antes de atribuir intenção.')
        priority=min(priority,2)
    reason.append(f'{count} bloqueios · {active} intervalos de 5 min com atividade · período de {minutes:.0f} min · {len(ports)} portas · {len(destinations)} destinos · {len(protocols)} protocolos.')
    if last<now-1800:reason.append('Sem novos registros desta origem nos últimos 30 min.')
    else:reason.append('Atividade registrada nos últimos 30 min.')
    remote=ipaddress.ip_address(source).is_global
    return dict(source=source,source_remote=remote,destination=destinations[0],protocol=', '.join(protocols),ports=', '.join(ports[:24]),port_values=ports[:24],count=count,first=date(first),last=date(last),last_epoch=last,interface=', '.join(values('interfaces')),kind=('Atividade local persistente' if not remote else ('Persistência com variação' if priority==3 else 'Padrão para revisar')),priority=priority,reason='\n'.join(reason),local=not remote)

def payload(data,now=None):
    now=time.time() if now is None else now;prune(data,now)
    groups=[p for s,g in data['sources'].items() if (p:=summarize(s,g,now))]
    groups.sort(key=lambda g:(-g['priority'],-g['last_epoch'],-g['count']))
    count=sum(b['count'] for b in data['totals'].values());noise=sum(b['noise'] for b in data['totals'].values())
    scope='Últimas 24 h · atualização automática a cada 60 s · análise por origem e intervalos de 5 min'
    if data['partial']:scope+='\nColeta em andamento: próximo lote retoma do último registro; diagnóstico parcial.'
    if data.get('limited_until',0)>now:scope+='\nLimite de armazenamento atingido: algumas origens antigas foram descartadas; cobertura parcial.'
    scope+=f'\n{count} bloqueios analisados · {noise} de descoberta/multicast resumidos · {max(0,len(groups)-30)} padrões adicionais.'
    return dict(text=f"Firewall: {len(groups)} {'padrão' if len(groups)==1 else 'padrões'}"+(' · parcial' if data['partial'] or data.get('limited_until',0)>now else ''),count=count,groups=groups[:30],scope=scope,updated=date(data['updated']) if data['updated'] else 'Consulta pendente',pattern_mode=True)

def collect():
    CACHE.parent.mkdir(parents=True,exist_ok=True)
    with open(CACHE.parent/'firewall-patterns.lock','a') as lock:
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
