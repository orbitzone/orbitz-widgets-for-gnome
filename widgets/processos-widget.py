#!/usr/bin/env python3
import html
import heapq
import os
import time
from pathlib import Path

TICKS = os.sysconf('SC_CLK_TCK')

def snapshot():
    result = {}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            text = (directory / 'stat').read_text()
            end = text.rfind(')')
            fields = text[end + 2:].split()
            name = text[text.find('(') + 1:end]
            result[int(directory.name)] = (name, int(fields[11]) + int(fields[12]), fields[19])
        except (OSError, ValueError, IndexError):
            continue
    return result

first = snapshot()
start = time.monotonic()
time.sleep(1)
second = snapshot()
elapsed = time.monotonic() - start
rows = []
for pid, (name, ticks, birth) in second.items():
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
