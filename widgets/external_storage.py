#!/usr/bin/env python3
from pathlib import Path
from widget_runtime import load, save
import json
import shutil
import subprocess
from widget_runtime import run as bounded_run

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
        yield from walk(device.get('children', []), external_here)

def external_usage():
    signature = Path('/proc/self/mountinfo').read_text()
    cached = load('volumes-inventory.json', 60)
    if isinstance(cached, dict) and cached.get('mounts') == signature and valid_devices(cached.get('devices')):
        devices = cached['devices']
    else:
        result = bounded_run(
        ['lsblk', '--json', '--output', 'NAME,LABEL,TRAN,RM,HOTPLUG,MOUNTPOINTS'],
            capture_output=True, text=True, check=True, timeout=4)
        devices = json.loads(result.stdout)['blockdevices']
        if not valid_devices(devices):
            raise ValueError('Inventário inválido')
        save('volumes-inventory.json', {'mounts': signature, 'devices': devices})
    total = used = 0
    seen = set()
    for device, point in walk(devices):
        try:
            identity = Path(point).stat().st_dev
            if identity in seen:
                continue
            seen.add(identity)
            usage = shutil.disk_usage(point)
            total += usage.total
            used += usage.used
        except OSError:
            continue
    return 100 * used / total if total else None
