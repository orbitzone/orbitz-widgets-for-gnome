#!/usr/bin/env python3
"""Bounded package queries and explicit terminal actions for Ubuntu."""
import json,math,os,re,sys,subprocess,shutil,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from widget_runtime import run as bounded_run,load,save,read_json,launch_terminal

def run(args, **kwargs):
    return bounded_run(['/usr/bin/env', 'LC_ALL=C', *args], **kwargs)
ACTIONS=[('buscar','Buscar atualizações','sudo apt update && snap refresh --list && flatpak update --appstream'),('apt','Atualizar APT','sudo apt upgrade'),('completa','Atualização completa','sudo apt full-upgrade'),('cache','Limpar cache','sudo apt autoclean'),('dependencias','Remover sobras','sudo apt autoremove'),('snap','Atualizar Snap','sudo snap refresh'),('flatpak','Atualizar Flatpak','flatpak update'),('sequencia','Atualizar e limpar','sudo apt update && sudo apt upgrade && sudo apt autoclean')]

def actions():
    result=[{'id':i,'name':n,'command':c} for i,n,c in ACTIONS]
    config=read_json(Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'orbitz-widgets'/'update-actions.json')
    if isinstance(config,list):
        for i,item in enumerate(config[:10]):
            if isinstance(item,dict) and all(isinstance(item.get(k),str) for k in ('name','command')) and 0<len(item['name'])<=80 and 0<len(item['command'])<=2048 and '\x00' not in item['command']:
                result.append({'id':f'custom-{i}','name':item['name'],'command':item['command']})
    return result

def query(source):
    if not shutil.which({'APT':'apt','Snap':'snap','Flatpak':'flatpak'}[source]):
        return {'source':source,'items':[],'state':'Não instalado'}
    try:
        items=[]
        if source=='APT':
            output=run(['apt','list','--upgradable'],timeout=7,check=True).stdout
            for line in output.splitlines():
                m=re.match(r'^(\S+)/(\S+)\s+(\S+)\s+(\S+)\s+\[upgradable from: (.+)\]$',line)
                if m:items.append({'name':m[1]+':'+m[4],'installed':m[5],'version':m[3],'security':'security' in m[2].split(',') or '-security' in m[2]})
        elif source=='Snap':
            output=run(['snap','refresh','--list'],timeout=7,check=True).stdout
            current=run(['snap','list'],timeout=3,check=True).stdout
            versions={p[0]:p[1] for line in current.splitlines()[1:] if len(p:=line.split())>=2}
            for line in output.splitlines()[1:]:
                p=line.split()
                if len(p)>=3:items.append({'name':p[0],'installed':versions.get(p[0],'—'),'version':p[1],'security':False})
        else:
            versions={}
            for scope in ('--user','--system'):
                installed=run(['flatpak','list',scope,'--columns=ref,version'],timeout=3,check=True).stdout
                versions.update({p[0]:p[1] if len(p)>1 and p[1] else '—' for line in installed.splitlines() if (p:=line.split('\t'))})
                output=run(['flatpak','remote-ls',scope,'--updates','--cached','--columns=ref,version'],timeout=3,check=True).stdout
                for line in output.splitlines():
                    p=line.split('\t')
                    if p[0]:items.append({'name':p[0]+' ('+scope[2:]+')','installed':versions.get(p[0],'—'),'version':p[1] if len(p)>1 and p[1] else '—','security':False})
        return {'source':source,'items':items,'state':'OK','checked':time.time()}
    except (OSError,ValueError,subprocess.SubprocessError):
        previous=load('updates-'+source+'.json',86400)
        if previous is not None and (not isinstance(previous,dict) or not isinstance(previous.get('items'),list) or
                any(not isinstance(item,dict) or any(not isinstance(item.get(k),str) or len(item[k])>512 for k in ('name','installed','version')) for item in previous['items']) or
                type(previous.get('checked',0)) not in (int,float) or not math.isfinite(previous.get('checked',0))):
            previous=None
        return {'source':source,'items':previous.get('items',[]) if isinstance(previous,dict) else [],'state':'Falha na consulta; dados anteriores' if previous else 'Consulta indisponível','checked':previous.get('checked',0) if isinstance(previous,dict) else 0}

def collect():
    with ThreadPoolExecutor(max_workers=3) as pool:groups=list(pool.map(query,['APT','Snap','Flatpak']))
    items=[];notices=[];partial=False
    for g in groups:
        if g['state']=='OK':save('updates-'+g['source']+'.json',g)
        partial|=g['state'].startswith(('Falha','Consulta'))
        stamp=time.strftime('%d/%m %H:%M',time.localtime(g['checked'])) if g.get('checked') else '—'
        notices.append(f"{g['source']}: {g['state']} · consulta {stamp}")
        for item in g['items']:items.append({**item,'source':g['source']})
    timestamps=[]
    for path in Path('/var/lib/apt/lists').glob('*InRelease'):
        try:
            if path.is_file():timestamps.append(path.stat().st_mtime)
        except OSError:continue
    oldest=min(timestamps) if timestamps else 0
    index=time.strftime('%d/%m %H:%M',time.localtime(oldest)) if oldest else 'indisponível'
    if not oldest or time.time()-oldest>86400:notices.append('Índice APT antigo ou ausente; use Buscar atualizações.')
    notices.append('Flatpak usa metadados locais; Snap consulta o serviço. Segurança identificada pela origem APT.')
    reboot=Path('/var/run/reboot-required').exists()
    if reboot:
        try:notices.append('Pacotes que pediram reinício: '+Path('/var/run/reboot-required.pkgs').read_text()[:1024].strip().replace('\n',', '))
        except OSError:pass
    text=f'Atualizações: {len(items)}'+(' · parcial' if partial else '')+(' · Reiniciar' if reboot else '')
    return {'text':text,'items':items[:100],'omitted':max(0,len(items)-100),'reboot':reboot,'index_updated':index,'error':'','notices':notices,'actions':actions()}

def launch(identifier):
    action=next((a for a in actions() if a['id']==identifier),None)
    if not action:raise ValueError('Ação indisponível.')
    launch_terminal(action['name'],action['command'])

if __name__=='__main__':
    if '--action' in sys.argv:launch(sys.argv[sys.argv.index('--action')+1])
    else:
        try:payload=collect()
        except (OSError,ValueError,subprocess.SubprocessError):payload={'text':'Atualizações: indisponíveis','items':[],'omitted':0,'reboot':False,'index_updated':'indisponível','error':'Falha na consulta.','notices':[],'actions':actions()}
        print('AZCLOCK_UPDATES:'+json.dumps(payload,ensure_ascii=False))
