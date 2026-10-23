#!/usr/bin/env python3
from orbitz_i18n import t
import html
import heapq
import os
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from widget_runtime import run as bounded_run, launch_terminal
from pressure_metrics import snapshot as pressure_snapshot

PAGE_SIZE = os.sysconf('SC_PAGE_SIZE')
TICKS = os.sysconf('SC_CLK_TCK')

def snapshot():
    result = {}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            with (directory / 'stat').open() as stream:
                text = stream.read(8192)
            end = text.rfind(')')
            fields = text[end + 2:].split()
            if end < 0:
                continue
            name = ''.join(c if c.isprintable() else ' ' for c in text[text.find('(') + 1:end])[:80]
            result[int(directory.name)] = (name, int(fields[11]) + int(fields[12]), fields[19], max(0,int(fields[21])) * PAGE_SIZE)
        except (OSError, ValueError, IndexError):
            continue
    return result


def query(args):
    try:
        return bounded_run(args,timeout=3,check=True,limit=65536).stdout.strip()
    except (OSError, ValueError, subprocess.SubprocessError):
        return ''

def available_actions():
    result = []
    def add(identifier, name, command, effect):
        result.append(dict(id=identifier, name=name, command=command, effect=effect))
    if shutil.which('gnome-system-monitor'):
        add('monitor', t('widgets.processos_widget.view_processes'), 'gnome-system-monitor', t('widgets.processos_widget.opens_the_monitor_to_review_process_cpu_and_memory_usage'))
    elif shutil.which('top'):
        add('monitor', t('widgets.processos_widget.view_processes'), 'top', t('widgets.processos_widget.opens_the_interactive_process_list_press_q_to_exit'))
    if shutil.which('gnome-session-properties'):
        add('startup', t('widgets.processos_widget.startup'), 'gnome-session-properties', t('widgets.processos_widget.opens_startup_applications_review_what_needs_to_start_with_your_s'))
    elif shutil.which('xdg-open'):
        folder = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config'))) / 'autostart'
        add('startup', t('widgets.processos_widget.startup'), 'xdg-open ' + shlex.quote(str(folder)), t('widgets.processos_widget.opens_the_startup_shortcuts_folder_for_your_session'))
    profiles = query(['powerprofilesctl', 'list']) if shutil.which('powerprofilesctl') else ''
    for identifier, title, effect in [
        ('balanced', t('widgets.processos_widget.balanced'), t('widgets.processos_widget.selects_the_balanced_power_profile')),
        ('performance', t('widgets.processos_widget.performance'), t('widgets.processos_widget.selects_the_performance_profile_may_increase_power_use_heat_and_n'))]:
        if re.search(r'^\s*\*?\s*' + identifier + r':', profiles, re.M):
            add(identifier, title, 'powerprofilesctl set ' + identifier, effect)
    return result

def cpu_totals():
    values = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:9]))
    return sum(values), values[3] + values[4]

def details():
    first = snapshot(); before = cpu_totals(); started = time.monotonic()
    time.sleep(0.6)
    second = snapshot(); after = cpu_totals(); elapsed = time.monotonic() - started
    delta = after[0] - before[0]
    cpu = max(0, min(100, 100 * (1 - (after[1] - before[1]) / delta))) if delta else 0
    memory = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        parts = line.split(); memory[parts[0].rstrip(':')] = int(parts[1]) * 1024
    total = memory.get('MemTotal', 0); free = memory.get('MemAvailable', 0)
    swap = memory.get('SwapTotal', 0) - memory.get('SwapFree', 0)
    temperatures = []
    for zone in Path('/sys/class/thermal').glob('thermal_zone*'):
        try:
            kind = (zone/'type').read_text().strip()
            if any(x in kind.lower() for x in ('cpu', 'pkg', 'x86', 'soc')):
                value = int((zone/'temp').read_text()) / 1000
                if 0 < value < 150: temperatures.append(value)
        except (OSError, ValueError): pass
    rows = []
    for pid, (name, ticks, birth, rss) in second.items():
        if pid == os.getpid() or pid not in first or first[pid][2] != birth: continue
        rows.append(dict(pid=pid, name=name[:80], cpu=round(max(0, ticks-first[pid][1])/TICKS/elapsed*100, 1), memory=round(rss/1048576)))
    notices = []
    if cpu >= 85: notices.append(t('widgets.processos_widget.cpu_busy_in_this_sample_review_the_busiest_processes_before_chang'))
    if total and free/total < 0.15: notices.append(t('widgets.processos_widget.low_available_memory_review_the_largest_consumers_and_close_appli'))
    if swap: notices.append(t('widgets.processos_widget.swap_usage_alone_does_not_indicate_slowness_check_available_memor'))
    disk = shutil.disk_usage(Path.home())
    if disk.free/disk.total < 0.1: notices.append(t('widgets.processos_widget.less_than_10_free_space_on_the_home_partition_review_large_files'))
    temperature = max(temperatures) if temperatures else None
    if temperature and temperature >= 85: notices.append(t('widgets.processos_widget.high_temperature_in_this_sample_check_ventilation_and_reduce_heav'))
    if not notices: notices.append(t('widgets.processos_widget.no_alerts_in_this_sample'))
    profile = query(['powerprofilesctl', 'get']) if shutil.which('powerprofilesctl') else ''
    summary = t('widgets.processos_widget.cpu_value0_0f_available_ram_value1_1f_value2_1f_gib_swap_value3_1', value0=cpu, value1=free / 1073741824, value2=total / 1073741824, value3=swap / 1073741824)
    summary += t('widgets.processos_widget.temperature_value0_0f_c', value0=temperature) if temperature else t('widgets.processos_widget.temperature_unavailable')
    summary += t('widgets.processos_widget.free_disk_space_value0_1f_gib', value0=disk.free / 1073741824)
    if profile: summary += t('widgets.processos_widget.profile') + profile
    return dict(pressure=pressure_snapshot(), summary=summary, notices=notices, cpu_rows=heapq.nsmallest(7,rows,key=lambda r:(-r['cpu'],r['pid'])), memory_rows=heapq.nsmallest(7,rows,key=lambda r:(-r['memory'],r['pid'])), actions=available_actions())

def launch(identifier):
    action = next((a for a in available_actions() if a['id'] == identifier), None)
    if not action: raise ValueError(t('widgets.processos_widget.action_unavailable'))
    if identifier == 'startup':
        (Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config'))) / 'autostart').mkdir(parents=True, exist_ok=True)
    launch_terminal(action['name'], action['command'], action['effect'])

def main():
    if '--details' in sys.argv:
        print('AZCLOCK_PROCESSES:' + json.dumps(details(), ensure_ascii=False))
        sys.exit(0)
    if '--action' in sys.argv:
        launch(sys.argv[sys.argv.index('--action')+1])
        sys.exit(0)

    first = snapshot()
    start = time.monotonic()
    time.sleep(1)
    second = snapshot()
    elapsed = time.monotonic() - start
    rows = []
    for pid, (name, ticks, birth, rss) in second.items():
        if pid == os.getpid() or pid not in first or first[pid][2] != birth:
            continue
        cpu = max(0, ticks - first[pid][1]) / TICKS / elapsed * 100
        rows.append((cpu, pid, name))
    rows = heapq.nsmallest(7, rows, key=lambda row: (-row[0], row[1]))
    # All lines need equal width: GNOME may center each line independently.
    formatted_rows = [(name[:18], f'{cpu:.1f}%') for cpu, _pid, name in rows]
    cpu_width = max([6] + [len(cpu) for _name, cpu in formatted_rows])
    lines = [f'{"PROCESSO":18} {"CPU":>{cpu_width}}']
    lines.extend(f'{name:18} {cpu:>{cpu_width}}' for name, cpu in formatted_rows)
    print('<span font_family="monospace">' + html.escape('\n'.join(lines)) + '</span>')
    pressure = pressure_snapshot()
    color = '#ff6b6b' if any(i['level'] == 'high' for i in pressure['items']) else '#ffd479' if any(i['level'] == 'attention' for i in pressure['items']) else '#c8c8c8'
    print()  # Separate the pressure summary from the process list.
    print(f"<span foreground=\"{color}\">{html.escape(pressure['text'])}</span>")


if __name__ == '__main__':
    main()
