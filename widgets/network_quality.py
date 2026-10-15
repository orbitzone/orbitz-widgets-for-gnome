"""On-demand, bounded ICMP probes; never runs with the passive traffic sample."""
import ipaddress
import json
import math
import re
import subprocess
from widget_runtime import run


def gateway():
    routes = json.loads(run(['ip', '-j', '-4', 'route', 'show', 'default'], timeout=1, check=True, limit=16384).stdout)
    routes = sorted((r for r in routes if r.get('gateway')), key=lambda r: int(r.get('metric', 0)))
    return str(ipaddress.IPv4Address(routes[0]['gateway'])) if routes else None


def parse_ping(text):
    loss = re.search(r'(\d+(?:\.\d+)?)% packet loss', text)
    timing = re.search(r'=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)\s*ms', text)
    if not loss: raise ValueError('Resposta ICMP inválida')
    lost = float(loss[1])
    latency, jitter = (float(timing[2]), float(timing[4])) if timing else (None, None)
    if not math.isfinite(lost) or not 0 <= lost <= 100: raise ValueError('Perda inválida')
    if lost < 100 and latency is None: raise ValueError('Latência ausente')
    if any(v is not None and (not math.isfinite(v) or v < 0) for v in (latency, jitter)): raise ValueError('Tempo inválido')
    return lost, latency, jitter


def probe(name, target):
    item = dict(name=name, target=target or '', loss=None, latency=None, jitter=None, error='')
    if not target:
        item['error'] = 'Gateway IPv4 não disponível (por exemplo, VPN ou rede IPv6).'
        return item
    try:
        target = str(ipaddress.ip_address(target))
        result = run(['/usr/bin/env', 'LC_ALL=C', 'ping', '-n', '-c', '5', '-i', '0.2', '-W', '1', '-w', '3', target], timeout=4, limit=8192)
        if result.returncode not in (0, 1): raise ValueError('ICMP indisponível')
        item['loss'], item['latency'], item['jitter'] = parse_ping(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        item['error'] = 'Sem leitura ICMP. Verifique ping, permissões e conectividade.'
    return item


def collect():
    try: local = gateway()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError): local = None
    return dict(items=[probe('Roteador', local), probe('Internet', '1.1.1.1')])
