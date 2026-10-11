#!/usr/bin/env python3
import time
import shutil
from widget_runtime import load, save
from pathlib import Path

def cpu():
    fields = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
    total = sum(fields[:8])
    idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
    return total, idle

def bar(percent):
    filled = min(10, max(0, int(percent / 10 + 0.5)))
    return '█' * filled + '░' * (10 - filled)

first = cpu()
time.sleep(1)
second = cpu()
delta = second[0] - first[0]
usage = 100 * (1 - (second[1] - first[1]) / delta) if delta else 0
memory = {}
for line in Path('/proc/meminfo').read_text().splitlines():
    key, value = line.split(':', 1)
    memory[key] = int(value.split()[0])
ram = 100 * (1 - memory['MemAvailable'] / memory['MemTotal'])
print('<span font_family="monospace">')
print(f'CPU  {bar(usage)}  {usage:3.0f}%')
print()
print(f'RAM  {bar(ram)}  {ram:3.0f}%')
ssd = load('disk-usage.json', 60)
if type(ssd) not in (int, float) or not 0 <= ssd <= 100:
    disk = shutil.disk_usage(Path.home())
    ssd = disk.used / disk.total * 100
    save('disk-usage.json', ssd)
print()
print(f'SSD  {bar(ssd)}  {ssd:3.0f}%')
print('</span>')
