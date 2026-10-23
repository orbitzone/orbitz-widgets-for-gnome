#!/usr/bin/env python3
"""Mounted block filesystems and optional read-only SMART snapshots."""
from orbitz_i18n import t
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
    result = dict(state='unavailable', temperature=None, wear=None, note=t('widgets.armazenamento_widget.install_smartmontools_smart_readings_also_require_support_and_per'))
    binary = shutil.which('smartctl')
    if not binary: return result
    try:
        response = run([binary, '-n', 'standby', '-H', '-A', '-j', device], timeout=2, limit=65536)
        data = json.loads(response.stdout)
        if response.returncode & 3: raise ValueError(t('widgets.armazenamento_widget.smart_unavailable'))
        passed = data.get('smart_status', {}).get('passed')
        if type(passed) is bool:
            result.update(state='ok' if passed else 'alert', note=t('widgets.armazenamento_widget.smart_result_reported_by_the_device_it_does_not_predict_every_fai'))
        temp = data.get('temperature', {}).get('current')
        if number(temp) and temp < 150: result['temperature'] = temp
        nvme = data.get('nvme_smart_health_information_log', {})
        wear = nvme.get('percentage_used')
        if number(wear): result['wear'] = min(wear, 1000)
        if number(nvme.get('critical_warning')) and nvme['critical_warning'] > 0:
            result.update(state='alert', note=t('widgets.armazenamento_widget.nvme_reported_a_critical_warning_review_the_device_and_your_backu'))
        if result['wear'] is not None and result['wear'] >= 100:
            result.update(state='alert', note=t('widgets.armazenamento_widget.estimated_nvme_lifetime_used_reached_100_or_more'))
    except (OSError, ValueError, TypeError, AttributeError, subprocess.SubprocessError):
        result['note'] = t('widgets.armazenamento_widget.no_smart_reading_permission_standby_device_unsupported_format_or')
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
            if not isinstance(nodes,list) or depth>12: raise ValueError(t('widgets.armazenamento_widget.invalid_inventory'))
            for node in nodes[:256]:
                if not isinstance(node,dict): raise ValueError(t('widgets.armazenamento_widget.invalid_inventory'))
                name=node.get('name',''); kind=node.get('type','')
                if not isinstance(name,str) or not re.fullmatch(r'/dev/[A-Za-z0-9_./-]+',name): continue
                if kind == 'loop': continue
                removable_here = removable or node.get('tran') == 'usb' or bool(node.get('rm')) or bool(node.get('hotplug'))
                disk = name if kind == 'disk' else parent
                if kind == 'disk': disks[name] = dict(name=name, model=str(node.get('model') or name)[:100])
                points=node.get('mountpoints') or []
                if not isinstance(points,list): raise ValueError(t('widgets.armazenamento_widget.invalid_mounts'))
                if details and (not selected or disk == '/dev/'+selected) and kind == 'part' and not any(points) and not node.get('children') and removable_here == external and number(node.get('size')) and node['size'] > 0:
                    if len(unmounted) < 12:
                        def optional_bytes(key):
                            try:
                                value = int(node.get(key))
                                return value if 0 <= value <= node['size'] else None
                            except (TypeError, ValueError): return None
                        unmounted.append(dict(device=name,disk=disk,total=node['size'],fstype=str(node.get('fstype') or t('widgets.armazenamento_widget.unidentified'))[:80],available=optional_bytes('fsavail'),used=optional_bytes('fsused')))

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
                    except OSError: content_error = t('widgets.armazenamento_widget.no_permission_to_list_contents')
                items.append(dict(files=files,content_error=content_error,more=more,device=device,disk=disk,mount=point[:512],total=total,available=available,percent=round(percent,1),inodes=round(inodes,1) if inodes is not None else None))
            except OSError:
                error=t('widgets.armazenamento_widget.some_mounts_could_not_be_queried')
        if details:
            active_disks={item['disk'] for item in items + unmounted}
            disks={name:disk for name,disk in disks.items() if name in active_disks}
            for index,disk in enumerate(disks.values()):
                disk['health']=health(disk['name']) if index<4 else dict(state='unavailable',temperature=None,wear=None,note=t('widgets.armazenamento_widget.limit_of_4_smart_queries_per_refresh'))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        error=t('widgets.armazenamento_widget.inventory_unavailable_check_lsblk_and_permissions')
    alerts=sum(i['percent']>=90 or (i['inodes'] is not None and i['inodes']>=90) for i in items)
    text=t('widgets.armazenamento_widget.storage_value0_need_attention', value0=alerts) if alerts else t('widgets.armazenamento_widget.storage_space_ok') if items and not error else t('widgets.armazenamento_widget.storage_no_reading') if not items else t('widgets.armazenamento_widget.storage_partial')
    return dict(text=text,items=items,unmounted=unmounted,disks=list(disks.values())[:16] if details else [],error=error,omitted=omitted)

def select_device(data, name, identity):
    from external_storage import device_identity
    try:
        if not identity or device_identity(name) != identity:
            raise ValueError(t('widgets.armazenamento_widget.device_removed_or_changed_refresh_the_widgets'))
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
            data.update(items=[],unmounted=[],disks=[],error=t('widgets.armazenamento_widget.invalid_external_selection'))
        else:
            data=select_device(data,argument('--device'),argument('--identity'))
    print('AZCLOCK_STORAGE:'+json.dumps(data,ensure_ascii=False))
