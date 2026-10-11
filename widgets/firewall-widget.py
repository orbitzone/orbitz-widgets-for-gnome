#!/usr/bin/env python3
"""UFW snapshot: logs are read only on --details, never with sudo."""
import collections
import datetime
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

CACHE = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'orbitz-widgets' / 'firewall.json'
PREFIX = 'AZCLOCK_FIREWALL:'

def parse(lines):
    groups = {}
    count = 0
    for line in lines:
        try:
            item = json.loads(line)
            message = item.get('MESSAGE', '')
            if not isinstance(message, str) or not re.search(r'\[UFW (?:BLOCK|REJECT)\]', message):
                continue
            fields = dict(re.findall(r'\b([A-Z]+)=([^\s]*)', message))
            source = str(ipaddress.ip_address(fields['SRC']))
            dest = ipaddress.ip_address(fields['DST'])
            source_ip = ipaddress.ip_address(source)
            stamp = datetime.datetime.fromtimestamp(int(item['__REALTIME_TIMESTAMP']) / 1e6).astimezone().strftime('%d/%m %H:%M:%S')
            proto = fields.get('PROTO', '?')[:16]
            proto = {'2': 'IGMP', '1': 'ICMP', '58': 'ICMPv6'}.get(proto, proto)
            port = fields.get('DPT', '—')[:8]
            key = (source, str(dest), proto)
            g = groups.setdefault(key, {'source': source, 'source_remote': not (source_ip.is_private or source_ip.is_loopback or source_ip.is_link_local), 'destination': str(dest), 'protocol': proto, 'ports': set(), 'count': 0, 'last': stamp, 'interface': fields.get('IN', '')[:32], 'kind': 'Descoberta / multicast' if dest.is_multicast else ('Rede local' if source_ip.is_private else 'Origem externa')})
            g['ports'].add(port)
            g['count'] += 1
            g['last'] = stamp
            count += 1
        except (ValueError, TypeError, KeyError, OverflowError, OSError):
            continue
    ordered = sorted(groups.values(), key=lambda g: -g['count'])
    for g in ordered:
        g['ports'] = ', '.join(sorted(g['ports']))[:160]
    return {'text': f'Eventos bloqueados: {count}', 'count': count, 'groups': ordered[:50], 'scope': 'Últimas 24 h · até 2000 bloqueios registrados · máximo 50 grupos', 'updated': datetime.datetime.now().astimezone().strftime('%d/%m %H:%M')}

def save(data):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='firewall-', dir=CACHE.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f)
        os.replace(name, CACHE)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def cached():
    try:
        fd = os.open(CACHE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as f:
            import stat
            if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
                raise ValueError()
            raw = f.read(262145)
        if len(raw) > 262144:
            raise ValueError()
        data = json.loads(raw)
        if not isinstance(data, dict) or type(data.get('count')) is not int or data['count'] < 0:
            raise ValueError()
        return {'text': f"Eventos bloqueados: {data['count']}"}
    except (OSError, ValueError, TypeError):
        return {'text': 'Eventos bloqueados: —'}

def main():
    if '--details' not in sys.argv:
        data = cached()
    else:
        result = subprocess.run(['journalctl', '-k', '--since', '24 hours ago', '-n', '2000', r'--grep=\[UFW (BLOCK|REJECT)\]', '-o', 'json', '--no-pager', '-q'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0 or 'not seeing messages' in result.stderr.lower() or 'permission denied' in result.stderr.lower():
            raise RuntimeError('Sem acesso aos logs do kernel. Configure uma fonte de logs com acesso de leitura.')
        data = parse(result.stdout.splitlines())
        try:
            save(data)
        except OSError:
            pass
    print(PREFIX + json.dumps(data, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
