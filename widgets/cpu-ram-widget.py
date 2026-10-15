#!/usr/bin/env python3
import time
import shutil
from widget_runtime import load, save
from pathlib import Path
from external_storage import external_usage
import subprocess

def cpu():
    fields = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
    total = sum(fields[:8])
    idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
    return total, idle

def bar(percent):
    filled = min(8, max(0, int(percent * 8 / 100 + 0.5)))
    return '█' * filled + '░' * (8 - filled)

import sys
if '--details' in sys.argv:
    import runpy
    runpy.run_path(str(Path(__file__).with_name('armazenamento-widget.py')), run_name='__main__')
    sys.exit(0)

first = cpu()
time.sleep(1)
second = cpu()
delta = second[0] - first[0]
usage = max(0, min(100, 100 * (1 - (second[1] - first[1]) / delta))) if delta > 0 else 0
memory = {}
for line in Path('/proc/meminfo').read_text().splitlines():
    key, value = line.split(':', 1)
    memory[key] = int(value.split()[0])
ram = 100 * (1 - memory['MemAvailable'] / memory['MemTotal'])
rows = [f'  CPU  {bar(usage)}  {usage:3.0f}%', f'  RAM  {bar(ram)}  {ram:3.0f}%']
ssd = load('disk-usage-available.json', 60)
if type(ssd) not in (int, float) or not 0 <= ssd <= 100:
    disk = shutil.disk_usage(Path.home())
    ssd = disk.used / (disk.used + disk.free) * 100 if disk.used + disk.free else 0
    save('disk-usage-available.json', ssd)
storage_alert = load('internal-storage-alert.json', 60)
if type(storage_alert) is not bool:
    try:
        import runpy
        inventory = runpy.run_path(str(Path(__file__).with_name('armazenamento-widget.py')))['collect']()
        storage_alert = any(item['percent'] >= 90 or (item['inodes'] is not None and item['inodes'] >= 90) for item in inventory['items'])
        save('internal-storage-alert.json', storage_alert)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        storage_alert = ssd >= 90
marker = '<span foreground="#ffd479">!</span> ' if storage_alert else '  '
rows.append(f'{marker}SSD  {bar(ssd)}  {ssd:3.0f}%')
try:
    external = external_usage()
except (OSError, ValueError, KeyError, subprocess.SubprocessError):
    external = None
if external is not None:
    marker = '<span foreground="#ffd479">!</span> ' if external >= 90 else '  '
    rows.append(f'{marker}EXT  {bar(external)}  {external:3.0f}%')
print('<span font_family="monospace" size="7680" line_height="1.5">' + '\n'.join(rows) + '</span>')
