#!/usr/bin/env python3
"""Read-only failed system/session services; bounded calls, no journal scraping."""
from orbitz_i18n import t
import json
import re
import subprocess
import sys
from widget_runtime import run

UNIT = re.compile(r'^[A-Za-z0-9_.:@\\-]+\.service$')

def collect(details=False):
    groups = []
    for scope in ('system', 'user'):
        group = dict(scope=scope, items=[], count=0, error='')
        base = ['systemctl', '--' + scope, '--no-ask-password', '--full']
        try:
            output = run(base + ['--failed', '--type=service', '--plain', '--no-legend', '--no-pager'], timeout=2, check=True, limit=65536).stdout
            units = []
            count = 0
            for line in output.splitlines():
                fields = line.split(None, 4)
                if len(fields) < 4 or len(fields[0]) > 256 or fields[0].startswith('-') or not UNIT.fullmatch(fields[0]) or fields[2] != 'failed':
                    raise ValueError(t('widgets.servicos_widget.invalid_service_list'))
                count += 1
                if details and len(units) < 6:
                    units.append(dict(name=fields[0], description=fields[4][:256] if len(fields)>4 else fields[0], result='', status='', changed=''))
            group['count'] = count
            group['items'] = units
            if details and group['items']:
                try:
                    raw = run(base + ['show', '--no-pager', '--property=Id,Result,ExecMainStatus,StateChangeTimestamp', '--', *[i['name'] for i in group['items']]], timeout=2, check=True, limit=32768).stdout
                    records = {}
                    for block in raw.strip().split('\n\n'):
                        values = dict(line.split('=',1) for line in block.splitlines() if '=' in line)
                        records[values.get('Id')] = values
                    for item in group['items']:
                        values = records.get(item['name'], {})
                        if any(key not in values for key in ('Result', 'ExecMainStatus', 'StateChangeTimestamp')):
                            group['error'] = t('widgets.servicos_widget.list_available_details_unavailable')
                        item.update(result=values.get('Result','')[:128], status=values.get('ExecMainStatus','')[:32], changed=values.get('StateChangeTimestamp','')[:128])
                except (OSError, ValueError, subprocess.SubprocessError):
                    group['error'] = t('widgets.servicos_widget.list_available_details_unavailable')
        except (OSError, ValueError, subprocess.SubprocessError):
            group['error'] = t('widgets.servicos_widget.query_unavailable_check_systemd_and_session_permissions')
        groups.append(group)
    count = sum(g['count'] for g in groups)
    error = any(g['error'] for g in groups)
    text = t('widgets.servicos_widget.services_value0_failed', value0=count) if count else t('widgets.servicos_widget.services_incomplete_query') if error else t('widgets.servicos_widget.services_ok')
    if count and error: text += t('widgets.servicos_widget.partial')
    return dict(text=text, groups=groups)

if __name__ == '__main__':
    print('AZCLOCK_SERVICES:' + json.dumps(collect('--details' in sys.argv), ensure_ascii=False))
