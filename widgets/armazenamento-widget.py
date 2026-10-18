#!/usr/bin/env python3
"""Mounted block filesystems and optional read-only SMART snapshots."""
import json
import math
import itertools
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from widget_runtime import run


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def health(device):
    result = dict(state='unavailable', temperature=None, wear=None, note='Instale smartmontools; leitura SMART também requer suporte e permissão.')
    binary = shutil.which('smartctl')
    if not binary: return result
    try:
        response = run([binary, '-n', 'standby', '-H', '-A', '-j', device], timeout=2, limit=65536)
        data = json.loads(response.stdout)
        if response.returncode & 3: raise ValueError('SMART indisponível')
        passed = data.get('smart_status', {}).get('passed')
        if type(passed) is bool:
            result.update(state='ok' if passed else 'alert', note='Resultado SMART informado pelo dispositivo; não prevê todas as falhas.')
        temp = data.get('temperature', {}).get('current')
        if number(temp) and temp < 150: result['temperature'] = temp
        nvme = data.get('nvme_smart_health_information_log', {})
        wear = nvme.get('percentage_used')
        if number(wear): result['wear'] = min(wear, 1000)
        if number(nvme.get('critical_warning')) and nvme['critical_warning'] > 0:
            result.update(state='alert', note='O NVMe registrou um aviso crítico. Revise o dispositivo e seus backups.')
        if result['wear'] is not None and result['wear'] >= 100:
            result.update(state='alert', note='Estimativa NVMe de vida útil consumida atingiu 100% ou mais.')
    except (OSError, ValueError, TypeError, AttributeError, subprocess.SubprocessError):
        result['note'] = 'SMART sem leitura: permissão, dispositivo em espera, formato ou suporte indisponível.'
    return result


def collect(details=False, external=False, selected=None):
    items, disks, seen = [], {}, set()
    unmounted = []
    error = ''
    omitted = 0
    try:
        raw = run(['lsblk', '-b', '-J', '-p', '-o', 'NAME,TYPE,SIZE,FSTYPE,FSAVAIL,FSUSED,MOUNTPOINTS,MODEL,TRAN,RM,HOTPLUG'], timeout=3, check=True, limit=131072)
        nodes = json.loads(raw.stdout)['blockdevices']
        def walk(nodes, parent='', depth=0, removable=False):
            if not isinstance(nodes,list) or depth>12: raise ValueError('Inventário inválido')
            for node in nodes[:256]:
                if not isinstance(node,dict): raise ValueError('Inventário inválido')
                name=node.get('name',''); kind=node.get('type','')
                if not isinstance(name,str) or not re.fullmatch(r'/dev/[A-Za-z0-9_./-]+',name): continue
                if kind == 'loop': continue
                removable_here = removable or node.get('tran') == 'usb' or bool(node.get('rm')) or bool(node.get('hotplug'))
                disk = name if kind == 'disk' else parent
                if kind == 'disk': disks[name] = dict(name=name, model=str(node.get('model') or name)[:100])
                points=node.get('mountpoints') or []
                if not isinstance(points,list): raise ValueError('Montagens inválidas')
                if details and (not selected or disk == '/dev/'+selected) and kind == 'part' and not any(points) and not node.get('children') and removable_here == external and number(node.get('size')) and node['size'] > 0:
                    if len(unmounted) < 12:
                        def optional_bytes(key):
                            try:
                                value = int(node.get(key))
                                return value if 0 <= value <= node['size'] else None
                            except (TypeError, ValueError): return None
                        unmounted.append(dict(device=name,disk=disk,total=node['size'],fstype=str(node.get('fstype') or 'Não identificado')[:80],available=optional_bytes('fsavail'),used=optional_bytes('fsused')))

                for point in sorted((p for p in points if isinstance(p,str) and p.startswith('/')),key=len):
                    is_external = removable_here or point.startswith(('/media/', '/run/media/', '/mnt/'))
                    if is_external == external: yield name,disk,point
                yield from walk(node.get('children') or [],disk,depth+1,removable_here)
        for device,disk,point in walk(nodes):
            if selected and disk != '/dev/'+selected: continue
            try:
                identity=os.stat(point).st_dev
                if identity in seen: continue
                seen.add(identity)
                if len(items)>=12:
                    omitted += 1; continue
                stat=os.statvfs(point)
                total=stat.f_blocks*stat.f_frsize
                if total<=0: continue
                available=max(0,stat.f_bavail)*stat.f_frsize
                used=max(0,stat.f_blocks-stat.f_bfree)*stat.f_frsize
                percent=100*used/(used+available) if used+available else 0
                inodes=100*(stat.f_files-stat.f_favail)/stat.f_files if stat.f_files else None
                files, content_error, more = [], '', False
                if external and details:
                    try:
                        with os.scandir(point) as entries:
                            entries = list(itertools.islice(entries, 31))
                        more = len(entries) > 30
                        files = sorted([('▸ ' if entry.is_dir(follow_symlinks=False) else '· ') + entry.name[:160] for entry in entries[:30]])
                    except OSError: content_error = 'Sem permissão para listar o conteúdo.'
                items.append(dict(files=files,content_error=content_error,more=more,device=device,disk=disk,mount=point[:512],total=total,available=available,percent=round(percent,1),inodes=round(inodes,1) if inodes is not None else None))
            except OSError:
                error='Algumas montagens não puderam ser consultadas.'
        if details:
            active_disks={item['disk'] for item in items + unmounted}
            disks={name:disk for name,disk in disks.items() if name in active_disks}
            for index,disk in enumerate(disks.values()):
                disk['health']=health(disk['name']) if index<4 else dict(state='unavailable',temperature=None,wear=None,note='Limite de 4 consultas SMART por atualização.')
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        error='Inventário indisponível. Verifique lsblk e permissões.'
    alerts=sum(i['percent']>=90 or (i['inodes'] is not None and i['inodes']>=90) for i in items)
    text=f'Armazenamento: {alerts} em atenção' if alerts else 'Armazenamento: espaço OK' if items and not error else 'Armazenamento: sem leitura' if not items else 'Armazenamento: parcial'
    return dict(text=text,items=items,unmounted=unmounted,disks=list(disks.values())[:16] if details else [],error=error,omitted=omitted)

def select_device(data, name, identity):
    from external_storage import device_identity
    try:
        if not identity or device_identity(name) != identity:
            raise ValueError('Dispositivo removido ou alterado. Atualize os widgets.')
        disk = '/dev/' + name
        data['items'] = [item for item in data['items'] if item['disk'] == disk]
        data['unmounted'] = [item for item in data['unmounted'] if item['disk'] == disk]
        data['disks'] = [item for item in data['disks'] if item['name'] == disk]
        data['omitted'] = 0
    except ValueError as error:
        data.update(items=[], unmounted=[], disks=[], error=str(error))
    return data


if __name__ == '__main__':
    selected = sys.argv[sys.argv.index('--device')+1] if '--device' in sys.argv and sys.argv.index('--device')+1 < len(sys.argv) else None
    data=collect('--details' in sys.argv, '--external' in sys.argv, selected)
    if '--device' in sys.argv:
        from external_storage import device_identity
        def argument(flag):
            return sys.argv[sys.argv.index(flag)+1] if flag in sys.argv and sys.argv.index(flag)+1<len(sys.argv) else ''
        if '--external' not in sys.argv:
            data.update(items=[],unmounted=[],disks=[],error='Seleção externa inválida.')
        else:
            data=select_device(data,argument('--device'),argument('--identity'))
    print('AZCLOCK_STORAGE:'+json.dumps(data,ensure_ascii=False))
