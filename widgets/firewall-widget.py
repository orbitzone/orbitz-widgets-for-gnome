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
from widget_runtime import run as bounded_run
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
            if not isinstance(item, dict):
                continue
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
            g = groups.setdefault(key, {'source': source, 'source_remote': not (source_ip.is_private or source_ip.is_loopback or source_ip.is_link_local), 'destination': str(dest), 'protocol': proto, 'ports': set(), 'count': 0, 'first': stamp, 'last': stamp, 'interface': fields.get('IN', '')[:32], 'kind': 'Descoberta / multicast' if dest.is_multicast else ('Rede local' if source_ip.is_private else 'Origem externa')})
            g['ports'].add(port)
            g['count'] += 1
            g['last'] = stamp
            count += 1
        except (ValueError, TypeError, KeyError, OverflowError, OSError):
            continue
    ordered = sorted(groups.values(), key=lambda g: -g['count'])
    for g in ordered:
        g['port_values'] = sorted(g['ports'])[:30]
        g['ports'] = ', '.join(g['port_values'])[:160]
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
        return {'text': f"Eventos bloqueados: {data['count']}", 'updated': str(data.get('updated', 'Atualização manual pendente'))[:80]}
    except (OSError, ValueError, TypeError):
        return {'text': 'Eventos bloqueados: —'}

def read_logs():
    result = bounded_run(['journalctl', '-k', '--since', '24 hours ago', '-n', '2000', r'--grep=\[UFW (BLOCK|REJECT)\]', '-o', 'json', '--no-pager', '-q'], capture_output=True, text=True, timeout=10, limit=2097152)
    if result.returncode != 0 or 'not seeing messages' in result.stderr.lower() or 'permission denied' in result.stderr.lower():
        raise RuntimeError('Sem acesso aos logs do kernel.')
    return result.stdout.splitlines()

def inspect_target(kind, target):
    if kind == 'ip':
        target = str(ipaddress.ip_address(target))
    elif not target.isdecimal() or not 1 <= int(target) <= 65535:
        raise ValueError('Porta inválida')
    matches = []
    for line in read_logs():
        try:
            entry = json.loads(line)
            if not isinstance(entry, dict):
                continue
            message = entry.get('MESSAGE', '')
            fields = dict(re.findall(r'\b([A-Z]+)=([^\s]*)', message))
            if (kind == 'ip' and target in (fields.get('SRC'), fields.get('DST'))) or (kind == 'port' and fields.get('DPT') == target):
                # Reuse the validated parser before accepting the record.
                if parse([line])['count']:
                    matches.append((entry, fields))
        except (ValueError, TypeError):
            continue
    counts = collections.Counter(f.get('SRC', '?') for _, f in matches)
    def values(key):
        return ', '.join(sorted({f.get(key, '—') for _, f in matches})[:40])
    def date(entry):
        return datetime.datetime.fromtimestamp(int(entry['__REALTIME_TIMESTAMP']) / 1e6).astimezone().strftime('%d/%m %H:%M:%S')
    remote = False
    title = 'IP: ' + target if kind == 'ip' else 'Porta: ' + target
    text = [title, f'{len(matches)} registros na amostra das últimas 24 h']
    if kind == 'ip':
        address = ipaddress.ip_address(target)
        remote = address.is_global and not address.is_multicast
        category = 'Multicast' if address.is_multicast else ('Loopback' if address.is_loopback else ('Link-local' if address.is_link_local else ('IP público' if remote else 'IP local / reservado')))
        text.append('Tipo: ' + category)
    if matches:
        text.extend(['Primeiro: ' + date(matches[0][0]), 'Último: ' + date(matches[-1][0]), 'Origens: ' + ', '.join(f'{ip} ({n})' for ip, n in counts.most_common(30)), 'Destinos: ' + values('DST'), 'Protocolos: ' + values('PROTO'), 'Portas destino: ' + values('DPT'), 'Portas origem: ' + values('SPT'), 'Interfaces: ' + values('IN')])
    if kind == 'port':
        services = {'22': 'SSH', '53': 'DNS', '80': 'HTTP', '443': 'HTTPS', '3000': 'Servidor de desenvolvimento (uso frequente)', '5432': 'PostgreSQL', '3306': 'MySQL', '6379': 'Redis', '9443': 'HTTPS / Portainer (uso frequente)'}
        text.append('Serviço usual: ' + services.get(target, 'Não identificado') + ' — a porta não comprova o serviço.')
        result = bounded_run(['ss', '-H', '-ltnup'], capture_output=True, text=True, timeout=3)
        listeners = []
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 5 and fields[4].rsplit(':', 1)[-1] == target:
                listeners.append(line[:1024])
        text.extend(['Escuta local atual (processo apenas quando permitido):', ('Falha ao consultar sockets locais.' if result.returncode != 0 else ('\n'.join(listeners[:20]) or 'Nenhuma escuta visível nesta porta.'))])
    text.extend(['', 'Registros originais — últimos 50 da seleção:', '\n'.join(date(e) + ' ' + e['MESSAGE'][:1024] for e, _ in matches[-50:]) or 'Nenhum registro na amostra.'])
    return {'inspect': '\n'.join(text), 'remote': remote}

def main():
    if '--inspect-ip' in sys.argv or '--inspect-port' in sys.argv:
        flag = '--inspect-ip' if '--inspect-ip' in sys.argv else '--inspect-port'
        data = inspect_target('ip' if flag == '--inspect-ip' else 'port', sys.argv[sys.argv.index(flag) + 1])
    elif '--dns' in sys.argv:
        target = str(ipaddress.ip_address(sys.argv[sys.argv.index('--dns') + 1]))
        result = bounded_run(['getent', 'hosts', target], capture_output=True, text=True, timeout=5)
        data = {'inspect': 'DNS reverso: ' + target + '\n' + (result.stdout[:4096].strip() or 'Sem nome retornado pelo resolvedor.') + '\nUm nome DNS não comprova a identidade da origem.'}
    elif '--details' not in sys.argv:
        data = cached()
    else:
        data = parse(read_logs())
        try:
            save(data)
        except OSError:
            pass
    print(PREFIX + json.dumps(data, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError, IndexError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
