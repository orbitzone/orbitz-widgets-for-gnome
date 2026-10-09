#!/usr/bin/env python3
import html
import json
import shutil
import subprocess

def bar(percent):
    filled = min(10, max(0, int(percent / 10 + 0.5)))
    return '█' * filled + '░' * (10 - filled)

def size(value):
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if value < 1024 or unit == 'TiB':
            return f'{value:.1f} {unit}'
        value /= 1024

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

try:
    result = subprocess.run(
        ['lsblk', '--json', '--output', 'NAME,LABEL,TRAN,RM,HOTPLUG,MOUNTPOINTS'],
        capture_output=True, text=True, check=True, timeout=4)
    volumes = []
    seen = set()
    for device, point in walk(json.loads(result.stdout)['blockdevices']):
        if point in seen:
            continue
        seen.add(point)
        try:
            usage = shutil.disk_usage(point)
            if not usage.total:
                continue
            name = device.get('label') or point.rstrip('/').split('/')[-1] or device['name']
            percent = usage.used / usage.total * 100
            volumes.append(f'{html.escape(name)}  {bar(percent)} {percent:3.0f}%\n{usage.free / (1024 ** 3):.1f} GiB Livres')
        except OSError:
            continue
    if volumes:
        print('<span font_family="monospace">' + '\n\n'.join(volumes) + '</span>')
    else:
        print('\u200b')
except (OSError, ValueError, KeyError, subprocess.SubprocessError):
    print('Volumes indisponíveis')
