#!/usr/bin/env python3
from orbitz_i18n import t
from pathlib import Path
from widget_runtime import load, save, run as bounded_run
import json
import shutil
import os
import re
import time
import subprocess

def bar(percent):
    filled = min(10, max(0, int(percent / 10 + 0.5)))
    return '█' * filled + '░' * (10 - filled)

def size(value):
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if value < 1024 or unit == 'TiB':
            return f'{value:.1f} {unit}'
        value /= 1024

def valid_devices(devices, depth=0):
    if not isinstance(devices, list) or len(devices) > 1024 or depth > 16:
        return False
    for device in devices:
        if not isinstance(device, dict): return False
        if any(device.get(key) is not None and not isinstance(device[key], str) for key in ('name', 'label', 'tran')): return False
        if any(device.get(key) is not None and (type(device[key]) not in (bool,int) or device[key] not in (0,1)) for key in ('rm','hotplug')): return False
        points = device.get('mountpoints') or []
        if not isinstance(points, list) or any(point is not None and (not isinstance(point, str) or len(point) > 4096) for point in points): return False
        if not valid_devices(device.get('children') or [], depth+1): return False
    return True

def walk(devices, external=False):
    for device in devices:
        external_here = external or device.get('tran') == 'usb' or bool(device.get('rm')) or bool(device.get('hotplug'))
        points = device.get('mountpoints') or []
        for point in points:
            if not point:
                continue
            # Desktop-mounted volumes and removable devices; exclude system mounts.
            desktop = point.startswith(('/media/', '/run/media/', '/mnt/'))
            system = point == '/' or point.startswith(('/boot', '/snap/', '/var/', '/usr/', '/home'))
            if (external_here or desktop) and not system:
                yield device, point
        yield from walk(device.get('children') or [], external_here)

def device_identity(name):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', name): raise ValueError(t('widgets.external_storage.invalid_device'))
    try:
        root = Path('/sys/class/block') / name
        return f"{os.stat(root).st_ino}:{(root/'dev').read_text().strip()}"
    except OSError: return ''


def external_devices(refresh=False):
    signature = Path('/proc/self/mountinfo').read_text() + '\n' + ','.join(sorted(path.name for path in Path('/sys/class/block').iterdir()))
    cached = load('external-devices-inventory.json', 60)
    if not refresh and isinstance(cached, dict) and cached.get('mounts') == signature and valid_devices(cached.get('devices')):
        devices = cached['devices']
    else:
        result = bounded_run(['lsblk', '--json', '--output', 'NAME,TYPE,LABEL,TRAN,RM,HOTPLUG,MOUNTPOINTS'],
                             check=True, timeout=4)
        devices = json.loads(result.stdout)['blockdevices']
        if not valid_devices(devices): raise ValueError(t('widgets.external_storage.invalid_inventory'))
        save('external-devices-inventory.json', {'mounts': signature, 'devices': devices})
    groups, seen = {}, set()
    def visit(nodes, parent='', external=False):
        for device in nodes:
            name = device.get('name') or parent
            root = name if device.get('type') == 'disk' or not parent else parent
            external_here = external or device.get('tran') == 'usb' or bool(device.get('rm')) or bool(device.get('hotplug'))
            if external_here and device.get('type') == 'disk':
                groups.setdefault(root, dict(name=root,total=0,used=0,mounts=[],percent=None))
            for point in device.get('mountpoints') or []:
                if not point or point == '/' or point.startswith(('/boot','/snap/','/var/','/usr/','/home')): continue
                if not external_here and not point.startswith(('/media/','/run/media/','/mnt/')): continue
                group = groups.setdefault(root, dict(name=root,total=0,used=0,mounts=[],percent=None))
                try:
                    identity = Path(point).stat().st_dev
                    if identity in seen: continue
                    seen.add(identity)
                    usage = shutil.disk_usage(point)
                    group['total'] += usage.used + usage.free
                    group['used'] += usage.used
                    group['mounts'].append(point)
                except OSError: pass
            visit(device.get('children') or [],root,external_here)
    visit(devices)
    result=[]
    for name in sorted(groups):
        group=groups[name]
        group['identity']=device_identity(name)
        if group['total']: group['percent']=100*group['used']/group['total']
        result.append(group)
    return result


def external_usage():
    devices = external_devices()
    total=sum(device['total'] for device in devices)
    return 100*sum(device['used'] for device in devices)/total if total else None


def eject_device(name, identity):
    """Unmount all filesystems, verify, then ask UDisks to power off. Never force."""
    try:
        if not identity or device_identity(name) != identity: raise ValueError(t('widgets.external_storage.device_removed_or_changed_refresh_the_widgets'))
        if not any(d['name']==name and d['identity']==identity for d in external_devices(refresh=True)):
            raise ValueError(t('widgets.external_storage.external_device_not_found'))
        deadline=time.monotonic()+18
        def query(args,limit=32768):
            remaining=deadline-time.monotonic()
            if remaining<=0: raise ValueError(t('widgets.external_storage.ejection_timed_out_do_not_disconnect_yet'))
            if device_identity(name)!=identity: raise ValueError(t('widgets.external_storage.the_device_changed_during_the_operation'))
            return bounded_run(args,timeout=min(5,remaining),check=True,limit=limit)
        def mounted():
            data=json.loads(query(['lsblk','-J','-p','-o','NAME,MOUNTPOINTS','/dev/'+name]).stdout)
            result=[]
            def visit(nodes,depth=0):
                if depth>12 or not isinstance(nodes,list): raise ValueError(t('widgets.external_storage.invalid_inventory'))
                for node in nodes:
                    visit(node.get('children') or [],depth+1)
                    if '[SWAP]' in (node.get('mountpoints') or []): raise ValueError(t('widgets.external_storage.the_device_contains_active_swap_ejection_refused'))
                    points=[p for p in node.get('mountpoints') or [] if p and p.startswith('/')]
                    if any(p=='/' or p.startswith(('/boot','/usr','/var','/home')) for p in points):
                        raise ValueError(t('widgets.external_storage.the_device_contains_a_system_mount_ejection_refused'))
                    if points:
                        path=node.get('name','')
                        if not re.fullmatch(r'/dev/[A-Za-z0-9_./-]+',path): raise ValueError(t('widgets.external_storage.invalid_device'))
                        result.append(path)
            visit(data['blockdevices'])
            if len(result)>16: raise ValueError(t('widgets.external_storage.device_has_too_many_mounts_for_automatic_ejection'))
            return result
        for path in mounted(): query(['udisksctl','unmount','--block-device',path,'--no-user-interaction'])
        if mounted(): raise ValueError(t('widgets.external_storage.some_volumes_are_still_mounted_do_not_disconnect_the_device'))
        query(['udisksctl','power-off','--block-device','/dev/'+name,'--no-user-interaction'])
        return dict(ok=True,message=t('widgets.external_storage.device_ejected_safe_to_disconnect_from_usb'))
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        message=str(error) if isinstance(error,ValueError) else t('widgets.external_storage.could_not_eject_device_busy_permission_denied_or_unsupported_do_n')
        return dict(ok=False,message=message[:256])
