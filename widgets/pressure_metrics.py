"""Small, read-only PSI snapshot. Thresholds are UI heuristics, not diagnoses."""
import math
from pathlib import Path

RESOURCES = {'cpu': 'CPU', 'memory': 'Memória', 'io': 'Disco / E/S'}
SUGGESTIONS = {
    'cpu': 'Revise os processos que mais usam CPU e reduza tarefas simultâneas.',
    'memory': 'Revise o consumo de RAM e feche aplicativos dispensáveis. Não limpe caches automaticamente.',
    'io': 'Verifique cópias, downloads e tarefas que acessam o armazenamento.',
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
            raise ValueError('PSI inválido')
        if fields[0] in result:
            raise ValueError('Amostra PSI duplicada')
        result[fields[0]] = averages
    if 'some' not in result:
        raise ValueError('PSI sem amostra')
    return result


def snapshot(root=Path('/proc/pressure')):
    items = []
    for resource, name in RESOURCES.items():
        try:
            with (root / resource).open() as stream:
                parsed = parse_pressure(stream.read(4096))
            averages = parsed['some']
            # CPU full is deliberately ignored: its system-level semantics vary.
            full = parsed.get('full') if resource != 'cpu' else None
            level = 'high' if averages[0] >= 20 else 'attention' if averages[0] >= 5 else 'normal'
            items.append(dict(resource=resource, name=name, averages=averages, full=full,
                              level=level, suggestion=SUGGESTIONS[resource]))
        except (OSError, ValueError, KeyError):
            items.append(dict(resource=resource, name=name, averages=None, full=None,
                              level='unavailable', suggestion='PSI indisponível neste sistema ou sem permissão de leitura.'))
    active = [item for item in items if item['level'] in ('attention', 'high')]
    missing = any(item['level'] == 'unavailable' for item in items)
    if active:
        text = 'Gargalo: ' + ' + '.join(item['name'] for item in active)
    elif missing:
        text = 'Gargalos: leitura parcial' if any(item['averages'] is not None for item in items) else 'Gargalos: indisponível'
    else:
        text = 'Sem pressão relevante'
    return dict(text=text, items=items)
