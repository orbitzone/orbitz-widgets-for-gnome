#!/usr/bin/env python3
import ipaddress,json,os,sys,subprocess
from urllib.parse import urlsplit
from widget_runtime import run,read_json
from pathlib import Path
MAX_ROWS=100
WEB_HTTP={80,3000,5000,8000,8080,8081,9000}
WEB_HTTPS={443,8443,9443}

def valid_url(url):
    try:
        if not isinstance(url,str) or any(ch.isspace() or ord(ch)<32 for ch in url):return False
        u=urlsplit(url)
        return u.scheme in ('http','https') and u.hostname and not u.username and not u.password and 1 <= u.port <= 65535 and not u.query and not u.fragment and len(url)<=512
    except (ValueError,TypeError):return False

def collect(details=False):
    result=run(['docker','ps','-q','--no-trunc'],timeout=6,check=True)
    ids=[line for line in result.stdout.splitlines() if line]
    if any(len(x)!=64 or any(c not in '0123456789abcdef' for c in x) for x in ids):raise ValueError('IDs inválidos')
    payload={'text':f'Docker Cotainers: {len(ids)}','items':[],'omitted':0}
    if not details:return payload
    overrides=read_json(Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'orbitz-widgets'/'docker-urls.json')
    if not isinstance(overrides,dict):overrides={}
    local=not os.environ.get('DOCKER_HOST','').startswith(('tcp:','ssh:','http:','https:'))
    context=run(['docker','context','inspect','--format','{{.Endpoints.docker.Host}}'],timeout=3,check=True).stdout.strip()
    local=local and context.startswith('unix:')
    count=0
    fmt='{"name":{{json .Name}},"running":{{json .State.Running}},"ports":{{json .NetworkSettings.Ports}},"mode":{{json .HostConfig.NetworkMode}}}'
    for offset in range(0,len(ids),50):
        result=run(['docker','inspect','--type','container','--format',fmt,*ids[offset:offset+50]],timeout=5)
        for line in result.stdout.splitlines():
            item=json.loads(line)
            if not isinstance(item,dict) or item.get('running') is not True:continue
            name=item['name'].lstrip('/')[:128];count+=1;rows=[];seen=set()
            for private,bindings in (item.get('ports') or {}).items():
                internal,protocol=private.split('/')
                if not internal.isdigit() or protocol not in ('tcp','udp','sctp'):continue
                for binding in bindings or []:
                    host=binding['HostIp'] or '0.0.0.0';port=int(binding['HostPort'])
                    if not 1<=port<=65535:continue
                    ip=ipaddress.ip_address(host)
                    target='localhost' if ip.is_unspecified and local else (f'[{ip}]' if ip.version==6 else str(ip))
                    key=(target,port,private)
                    if key in seen:continue
                    seen.add(key)
                    url=''
                    if local and protocol=='tcp' and int(internal) in WEB_HTTP|WEB_HTTPS and not ('portainer' in name.lower() and int(internal)==8000):
                        url=f'{"https" if int(internal) in WEB_HTTPS else "http"}://{target}:{port}'
                    override=overrides.get(f'{name}:{port}',overrides.get(name,''))
                    if override and valid_url(override):url=override
                    rows.append({'name':name,'ports':f'{host}:{port} → {private}','url':url})
            if not rows:rows=[{'name':name,'ports':'Rede do host' if item.get('mode')=='host' else 'Sem porta publicada no host','url':''}]
            for row in rows:
                if len(payload['items'])<MAX_ROWS:payload['items'].append(row)
                else:payload['omitted']+=1
    payload['text']=f'Docker Cotainers: {count}'
    return payload

if __name__=='__main__':
    try:payload=collect('--details' in sys.argv)
    except (OSError,ValueError,KeyError,TypeError,AttributeError,subprocess.SubprocessError):
        payload={'text':'Docker Cotainers: indisponível','items':[],'error':'Não foi possível consultar o Docker. Verifique o serviço e o acesso da sua conta.'}
    print('AZCLOCK_DOCKER:'+json.dumps(payload,ensure_ascii=False))
