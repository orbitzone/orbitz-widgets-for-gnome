#!/usr/bin/python3
"""Inspect established TCP connections without consulting firewall data."""
import ipaddress
import json
import socket
import subprocess
import sys
from widget_runtime import run

PREFIX = 'AZCLOCK_CONNECTION_INSPECT:'


def endpoint(value):
    host, port = value.rsplit(':', 1)
    return str(ipaddress.ip_address(host.strip('[]').split('%')[0])), port


def inspect(kind, target):
    if kind in ('ip', 'dns'):
        ip = ipaddress.ip_address(target)
        target = str(ip)
    else:
        if not target.isdecimal() or not 1 <= int(target) <= 65535:
            raise ValueError('Porta inválida')
    if kind == 'dns':
        result = run(['getent', 'hosts', target], timeout=5, limit=4096)
        return dict(inspect='DNS reverso: ' + target + '\n' + (result.stdout.strip() or 'Sem nome retornado.') + '\nUm nome DNS não comprova a identidade do destino.')
    if kind == 'ip':
        scope = 'Público' if ip.is_global else 'Loopback' if ip.is_loopback else 'Link-local' if ip.is_link_local else 'Multicast' if ip.is_multicast else 'Privado / reservado'
        lines = [f'IP: {target}', f'IPv{ip.version} · {scope}']
        if not ip.is_global:
            lines.append('WHOIS/RDAP não se aplica a este endereço local ou reservado.')
    else:
        try:
            service = socket.getservbyport(int(target), 'tcp')
        except OSError:
            service = 'Sem nome no cadastro local'
        lines = [f'Porta TCP de destino: {target}', f'Serviço cadastrado: {service}', 'O número da porta não identifica o aplicativo com certeza.']
    try:
        result = run(['ss', '-Htn', 'state', 'established'], timeout=4, check=True, limit=131072)
        matches = []
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) < 4:
                continue
            try:
                peer, port = endpoint(fields[-1])
                local, local_port = endpoint(fields[-2])
            except ValueError:
                continue
            if (kind == 'ip' and peer == target) or (kind == 'port' and port == target):
                matches.append(f'[{local}]:{local_port} → [{peer}]:{port}')
        lines += [f'Conexões TCP estabelecidas agora: {len(matches)}', '\n'.join(matches[:30]) or 'Nenhuma conexão estabelecida no momento da consulta.']
        if len(matches) > 30:
            lines.append(f'+ {len(matches) - 30} conexões não exibidas.')
    except (OSError, subprocess.SubprocessError):
        lines.append('Não foi possível consultar as conexões atuais.')
    return dict(inspect='\n\n'.join(lines), remote=kind == 'ip' and ip.is_global)


def main():
    try:
        flag, target = sys.argv[1:]
        kind = {'--inspect-ip': 'ip', '--inspect-port': 'port', '--dns': 'dns'}[flag]
        data = inspect(kind, target)
    except (ValueError, KeyError, OSError, subprocess.SubprocessError):
        data = dict(inspect='Consulta indisponível ou endereço inválido.', remote=False)
    print(PREFIX + json.dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    main()
