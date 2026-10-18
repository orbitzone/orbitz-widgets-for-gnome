#!/usr/bin/env python3
import time
import shutil
from widget_runtime import load, save
from pathlib import Path
from external_storage import external_usage
import subprocess
import sys
import runpy
import json

def cpu():
    fields = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
    total = sum(fields[:8])
    idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
    return total, idle

def bar(percent):
    filled = min(8, max(0, int(percent * 8 / 100 + 0.5)))
    return '█' * filled + '░' * (8 - filled)

def main():
    # Keep detail requests out of the passive sampling path used by the worker.
    if '--hardware' in sys.argv:
        runpy.run_path(str(Path(__file__).with_name('hardware-details.py')), run_name='__main__')
        return
    if '--eject' in sys.argv:
        from external_storage import eject_device
        def argument(flag):
            return sys.argv[sys.argv.index(flag)+1] if flag in sys.argv and sys.argv.index(flag)+1 < len(sys.argv) else ''
        print('AZCLOCK_EJECT:' + json.dumps(eject_device(argument('--device'), argument('--identity')), ensure_ascii=False))
        return
    if '--details' in sys.argv:
        runpy.run_path(str(Path(__file__).with_name('armazenamento-widget.py')), run_name='__main__')
        return

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
    rows = [f'  {"CPU":<4}   {bar(usage)}  {usage:3.0f}%',
            f'  {"RAM":<4}   {bar(ram)}  {ram:3.0f}%']
    ssd = load('disk-usage.json', 60)
    if type(ssd) not in (int, float) or not 0 <= ssd <= 100:
        disk = shutil.disk_usage(Path.home())
        ssd = disk.used / disk.total * 100
        save('disk-usage.json', ssd)
    rows.append(f'  {"SSD":<4}   {bar(ssd)}  {ssd:3.0f}%')
    try:
        external = external_usage()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        external = None
    if external is not None:
        rows.append(f'  {"EXT":<4}   {bar(external)}  {external:3.0f}%')
    print('<span font_family="monospace" size="7680" line_height="1.5">' + '\n'.join(rows) + '</span>')


if __name__ == '__main__':
    main()
