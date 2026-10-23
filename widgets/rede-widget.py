#!/usr/bin/env python3
from orbitz_i18n import t
import time
import sys
import json
from pathlib import Path

def interface():
    routes = Path('/proc/net/route').read_text().splitlines()[1:]
    candidates = []
    for line in routes:
        fields = line.split()
        if len(fields) >= 8 and fields[1] == '00000000' and int(fields[3], 16) & 1:
            candidates.append((int(fields[6]), fields[0]))
    if candidates:
        return min(candidates)[1]
    try:
        for line in Path('/proc/net/ipv6_route').read_text().splitlines():
            fields = line.split()
            if len(fields) >= 10 and fields[0] == '0' * 32 and fields[1] == '00' and int(fields[8], 16) & 1 and fields[9] != 'lo':
                candidates.append((int(fields[5], 16), fields[9]))
    except OSError:
        pass
    return min(candidates)[1] if candidates else None

def counters(name):
    for line in Path('/proc/net/dev').read_text().splitlines()[2:]:
        device, values = line.split(':', 1)
        if device.strip() == name:
            fields = values.split()
            return int(fields[0]), int(fields[8])
    raise ValueError(t('widgets.rede_widget.interface_unavailable'))

def rate(value):
    value = max(0, value)
    for unit in ('B/s', 'KiB/s', 'MiB/s', 'GiB/s'):
        if value < 1024 or unit == 'GiB/s':
            return f'{value:.1f} {unit}'
        value /= 1024

def main():
    if '--details' in sys.argv:
        from network_quality import collect
        print('AZCLOCK_QUALITY:' + json.dumps(collect(), ensure_ascii=False))
        sys.exit(0)

    try:
        name = interface()
        if not name:
            print(t('widgets.rede_widget.network_disconnected'))
        else:
            first = counters(name)
            start = time.monotonic()
            time.sleep(1)
            second = counters(name)
            elapsed = time.monotonic() - start
            print(f'↓ {rate((second[0]-first[0])/elapsed)}   ↑ {rate((second[1]-first[1])/elapsed)}')
    except (OSError, ValueError, IndexError):
        print(t('widgets.rede_widget.network_unavailable'))


if __name__ == '__main__':
    main()
