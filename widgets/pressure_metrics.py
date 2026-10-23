"""Small, read-only PSI snapshot. Thresholds are UI heuristics, not diagnoses."""
from orbitz_i18n import t
import math
from pathlib import Path

RESOURCES = {'cpu': 'CPU', 'memory': 'widgets.pressure_metrics.memory', 'io': 'widgets.pressure_metrics.disk_i_o'}
SUGGESTIONS = {
    'cpu': 'widgets.pressure_metrics.review_the_busiest_cpu_processes_and_reduce_concurrent_tasks',
    'memory': 'widgets.pressure_metrics.review_ram_usage_and_close_unnecessary_applications_do_not_clear',
    'io': 'widgets.pressure_metrics.check_copying_downloads_and_tasks_accessing_storage',
}


def parse_pressure(text):
    result = {}
    for line in text.splitlines():
        fields = line.split()
        if not fields or fields[0] not in ('some', 'full'):
            continue
        values = dict(field.split('=', 1) for field in fields[1:] if '=' in field)
        averages = [float(values[key]) for key in ('avg10', 'avg60', 'avg300')]
        if not all(math.isfinite(value) and 0 <= value <= 100 for value in averages):
            raise ValueError(t('widgets.pressure_metrics.invalid_psi'))
        if fields[0] in result:
            raise ValueError(t('widgets.pressure_metrics.duplicate_psi_sample'))
        result[fields[0]] = averages
    if 'some' not in result:
        raise ValueError(t('widgets.pressure_metrics.missing_psi_sample'))
    return result


def snapshot(root=Path('/proc/pressure')):
    items = []
    for resource, name in RESOURCES.items():
        name = t(name) if resource != 'cpu' else name
        try:
            with (root / resource).open() as stream:
                parsed = parse_pressure(stream.read(4096))
            averages = parsed['some']
            # CPU full is deliberately ignored: its system-level semantics vary.
            full = parsed.get('full') if resource != 'cpu' else None
            level = 'high' if averages[0] >= 20 else 'attention' if averages[0] >= 5 else 'normal'
            items.append(dict(resource=resource, name=name, averages=averages, full=full,
                              level=level, suggestion=t(SUGGESTIONS[resource])))
        except (OSError, ValueError, KeyError):
            items.append(dict(resource=resource, name=name, averages=None, full=None,
                              level='unavailable', suggestion=t('widgets.pressure_metrics.psi_unavailable_on_this_system_or_no_read_permission')))
    active = [item for item in items if item['level'] in ('attention', 'high')]
    missing = any(item['level'] == 'unavailable' for item in items)
    if active:
        text = t('widgets.pressure_metrics.bottleneck') + ' + '.join(item['name'] for item in active)
    elif missing:
        text = t('widgets.pressure_metrics.bottlenecks_partial_reading') if any(item['averages'] is not None for item in items) else t('widgets.pressure_metrics.bottlenecks_unavailable')
    else:
        text = t('widgets.pressure_metrics.no_significant_pressure')
    return dict(text=text, items=items)
