#!/usr/bin/env python3
"""Contadores TCP; atividade de rede não implica invasão."""
import sys
import time
import math
import os
import tempfile
import stat
from pathlib import Path
import json
import ipaddress
import subprocess
from widget_runtime import run as bounded_run

_PSL = None

def display_hostname(name):
    import ctypes
    global _PSL
    if not name:
        return ''
    try:
        if _PSL is False:
            return name.rstrip('.')
        if _PSL is None:
            _PSL = ctypes.CDLL('libpsl.so.5')
            _PSL.psl_builtin.restype = ctypes.c_void_p
            _PSL.psl_registrable_domain.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            _PSL.psl_registrable_domain.restype = ctypes.c_char_p
        domain = _PSL.psl_registrable_domain(_PSL.psl_builtin(), name.rstrip('.').encode())
        return domain.decode() if domain else name.rstrip('.')
    except (OSError, AttributeError):
        _PSL = False
        return name.rstrip('.')

def sockets(state):
    result = bounded_run(['ss', '-Htn', 'state', state], capture_output=True,
                            text=True, timeout=4, check=True)
    return [line.split() for line in result.stdout.splitlines() if line.strip()]

def address(endpoint):
    host, port = endpoint.rsplit(':', 1)
    return host.strip('[]'), port

def hostnames(ips):
    from concurrent.futures import ThreadPoolExecutor
    cache_path = Path(__file__).resolve().parent.parent / 'work' / 'network-hostnames.json'
    cache = {}
    try:
        fd = os.open(cache_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError('Cache inválido')
            raw = stream.read(262145)
        if len(raw) > 262144:
            raise ValueError('Cache grande')
        data = json.loads(raw)
        if isinstance(data, dict):
            for ip, entry in list(data.items())[:4096]:
                if (isinstance(entry, dict) and isinstance(entry.get('name'), str) and
                        len(entry['name']) <= 253 and isinstance(entry.get('time'), (int, float)) and
                        not isinstance(entry['time'], bool) and math.isfinite(entry['time']) and
                        0 <= time.time() - entry['time'] <= 86400):
                    cache[ip] = entry
    except (OSError, ValueError, TypeError):
        pass
    now = time.time()
    pending = [ip for ip in sorted(ips) if now - cache.get(ip, {}).get('time', 0) > 3600][:16]
    def resolve(ip):
        try:
            result = bounded_run(['getent', 'hosts', ip], capture_output=True, text=True, timeout=0.5)
            fields = result.stdout.split()
            return ip, fields[1][:253] if result.returncode == 0 and len(fields) > 1 else ''
        except (OSError, subprocess.SubprocessError):
            return ip, ''
    with ThreadPoolExecutor(max_workers=4) as pool:
        for ip, name in pool.map(resolve, pending):
            cache[ip] = {'name': name, 'time': now}
    if pending:
        name = None
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            encoded = json.dumps(cache)
            while len(encoded.encode()) > 262144 and cache:
                oldest = min(cache, key=lambda ip: cache[ip]['time'])
                del cache[oldest]
                encoded = json.dumps(cache)
            fd, name = tempfile.mkstemp(prefix='network-', dir=cache_path.parent)
            with os.fdopen(fd, 'w') as stream:
                stream.write(encoded)
            os.replace(name, cache_path)
        except OSError:
            pass
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
    return {ip: cache.get(ip, {}).get('name', '') for ip in ips}

try:
    external = 0
    peers = []
    for fields in sockets('established'):
        if len(fields) < 4:
            continue
        host, port = address(fields[3])
        host = host.split('%', 1)[0]
        try:
            ip = ipaddress.ip_address(host)
            if ip.version == 6 and ip.ipv4_mapped:
                ip = ip.ipv4_mapped
            if not ip.is_loopback and not ip.is_unspecified:
                external += 1
                peers.append((str(ip), port))
        except ValueError:
            continue
    ports = set()
    for fields in sockets('listening'):
        if len(fields) < 3:
            continue
        host, port = address(fields[2])
        try:
            ip = ipaddress.ip_address(host.split('%', 1)[0])
            if ip.version == 6 and ip.ipv4_mapped:
                ip = ip.ipv4_mapped
            if ip.is_loopback:
                continue
        except ValueError:
            if host != '*':
                continue
        ports.add(port)
    if '--summary' in sys.argv:
        text = f'Conexões externas: {external}\nEscutando portas: {len(ports)}'
        print('AZCLOCK_NETWORK:' + json.dumps({'text': text}, ensure_ascii=False))
        sys.exit(0)
    ordered = sorted(ports, key=int)
    details = '\n'.join(f'{port}/TCP' for port in ordered)
    tooltip = details or 'Nenhuma porta escutando'
    visible_peers = sorted(peers)[:200]
    resolved = hostnames({ip for ip, port in visible_peers})
    connection_items = []
    for ip, port in visible_peers:
        name = resolved.get(ip)
        connection_items.append({'hostname': name or '', 'display': display_hostname(name), 'ip': ip, 'port': port})
    text = f'Conexões externas: {external}\nEscutando portas: {len(ports)}'
    print('AZCLOCK_NETWORK:' + json.dumps({'text': text, 'tooltip': tooltip, 'connection_items': connection_items, 'omitted': max(0, len(peers) - 200)}, ensure_ascii=False))
except (OSError, ValueError, subprocess.SubprocessError):
    print('Leitura indisponível')
