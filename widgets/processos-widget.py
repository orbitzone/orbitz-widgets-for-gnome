#!/usr/bin/env python3
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
        add('monitor', 'Ver processos', 'gnome-system-monitor', 'Abre o monitor para revisar CPU e memória dos processos.')
    elif shutil.which('top'):
        add('monitor', 'Ver processos', 'top', 'Abre a lista interativa de processos. Pressione q para sair.')
    if shutil.which('gnome-session-properties'):
        add('startup', 'Inicialização', 'gnome-session-properties', 'Abre os aplicativos da inicialização; revise o que precisa iniciar com a sessão.')
    elif shutil.which('xdg-open'):
        folder = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config'))) / 'autostart'
        add('startup', 'Inicialização', 'xdg-open ' + shlex.quote(str(folder)), 'Abre a pasta de atalhos da inicialização da sua sessão.')
    profiles = query(['powerprofilesctl', 'list']) if shutil.which('powerprofilesctl') else ''
    for identifier, title, effect in [
        ('balanced', 'Equilibrado', 'Seleciona o perfil equilibrado de energia.'),
        ('performance', 'Desempenho', 'Seleciona o perfil de desempenho; pode aumentar consumo, calor e ruído.')]:
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
    if cpu >= 85: notices.append('CPU ocupada nesta amostra. Revise os processos com maior uso antes de alterar o perfil de energia.')
    if total and free/total < 0.15: notices.append('Pouca memória disponível. Revise os aplicativos com maior consumo e feche os que não precisa.')
    if swap: notices.append('Swap em uso, por si só, não indica lentidão. Observe a memória disponível e a espera por memória.')
    disk = shutil.disk_usage(Path.home())
    if disk.free/disk.total < 0.1: notices.append('Menos de 10% de espaço livre na partição da pasta pessoal. Revise arquivos grandes para liberar espaço.')
    temperature = max(temperatures) if temperatures else None
    if temperature and temperature >= 85: notices.append('Temperatura elevada nesta amostra. Verifique a ventilação e reduza tarefas pesadas.')
    if not notices: notices.append('Nenhum alerta nos indicadores desta amostra.')
    profile = query(['powerprofilesctl', 'get']) if shutil.which('powerprofilesctl') else ''
    summary = f'CPU {cpu:.0f}% · RAM disponível {free/1073741824:.1f} / {total/1073741824:.1f} GiB · Swap {swap/1073741824:.1f} GiB'
    summary += f"\nTemperatura {temperature:.0f} °C" if temperature else '\nTemperatura indisponível'
    summary += f' · Disco livre {disk.free/1073741824:.1f} GiB'
    if profile: summary += ' · Perfil ' + profile
    return dict(pressure=pressure_snapshot(), summary=summary, notices=notices, cpu_rows=heapq.nsmallest(7,rows,key=lambda r:(-r['cpu'],r['pid'])), memory_rows=heapq.nsmallest(7,rows,key=lambda r:(-r['memory'],r['pid'])), actions=available_actions())

def launch(identifier):
    action = next((a for a in available_actions() if a['id'] == identifier), None)
    if not action: raise ValueError('Ação indisponível.')
    if identifier == 'startup':
        (Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config'))) / 'autostart').mkdir(parents=True, exist_ok=True)
    launch_terminal(action['name'], action['command'], action['effect'])

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
print('<span font_family="monospace">', end='')
print('PROCESSO             CPU')
for index, (cpu, pid, name) in enumerate(rows[:7]):
    print(html.escape(f'{name[:18]:18} {cpu:5.1f}%'), end='\n' if index < len(rows[:7]) - 1 else '')
print('</span>')
pressure = pressure_snapshot()
color = '#ff6b6b' if any(i['level'] == 'high' for i in pressure['items']) else '#ffd479' if any(i['level'] == 'attention' for i in pressure['items']) else '#c8c8c8'
print(f"<span foreground=\"{color}\">{html.escape(pressure['text'])}</span>")
