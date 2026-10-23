#!/usr/bin/python3
"""Inspect established TCP connections without consulting firewall data."""
from orbitz_i18n import t
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
            raise ValueError(t('widgets.conexoes_inspect.invalid_port'))
    if kind == 'dns':
        result = run(['getent', 'hosts', target], timeout=5, limit=4096)
        return dict(inspect=t('widgets.conexoes_inspect.reverse_dns') + target + '\n' + (result.stdout.strip() or t('widgets.conexoes_inspect.no_name_returned')) + t('widgets.conexoes_inspect.a_dns_name_does_not_prove_the_destination_identity'))
    if kind == 'ip':
        scope = t('widgets.conexoes_inspect.public') if ip.is_global else 'Loopback' if ip.is_loopback else 'Link-local' if ip.is_link_local else 'Multicast' if ip.is_multicast else t('widgets.conexoes_inspect.private_reserved')
        lines = [f'IP: {target}', f'IPv{ip.version} · {scope}']
        if not ip.is_global:
            lines.append(t('widgets.conexoes_inspect.whois_rdap_does_not_apply_to_this_local_or_reserved_address'))
    else:
        try:
            service = socket.getservbyport(int(target), 'tcp')
        except OSError:
            service = t('widgets.conexoes_inspect.no_name_in_the_local_registry')
        lines = [t('widgets.conexoes_inspect.destination_tcp_port_value0', value0=target), t('widgets.conexoes_inspect.registered_service_value0', value0=service), t('widgets.conexoes_inspect.the_port_number_does_not_identify_the_application_with_certainty')]
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
        lines += [t('widgets.conexoes_inspect.tcp_connections_established_now_value0', value0=len(matches)), '\n'.join(matches[:30]) or t('widgets.conexoes_inspect.no_established_connections_at_query_time')]
        if len(matches) > 30:
            lines.append(t('widgets.conexoes_inspect.value0_connections_not_shown', value0=len(matches) - 30))
    except (OSError, subprocess.SubprocessError):
        lines.append(t('widgets.conexoes_inspect.could_not_query_current_connections'))
    return dict(inspect='\n\n'.join(lines), remote=kind == 'ip' and ip.is_global)


def main():
    try:
        flag, target = sys.argv[1:]
        kind = {'--inspect-ip': 'ip', '--inspect-port': 'port', '--dns': 'dns'}[flag]
        data = inspect(kind, target)
    except (ValueError, KeyError, OSError, subprocess.SubprocessError):
        data = dict(inspect=t('widgets.conexoes_inspect.query_unavailable_or_invalid_address'), remote=False)
    print(PREFIX + json.dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    main()
