#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

def read(path):
    try:
        value = int(path.read_text().strip()) / 1000
        return value if -20 <= value <= 150 else None
    except (OSError, ValueError):
        return None

cpu = None
cores = []
gpu = None
for device in Path('/sys/class/hwmon').glob('hwmon*'):
    try:
        driver = (device / 'name').read_text().strip().lower()
    except OSError:
        continue
    for sensor in device.glob('temp*_input'):
        value = read(sensor)
        if value is None:
            continue
        label_path = sensor.with_name(sensor.name.replace('_input', '_label'))
        try:
            label = label_path.read_text().strip().lower()
        except OSError:
            label = ''
        if driver == 'coretemp':
            if 'package' in label:
                cpu = value
            elif 'core' in label:
                cores.append(value)
        if driver == 'amdgpu' and (gpu is None or label == 'edge'):
            gpu = value
if gpu is None:
    try:
        result = subprocess.run(['sensors', '-j'], capture_output=True, text=True, check=True, timeout=3)
        data = json.loads(result.stdout)
        for chip, entries in data.items():
            if chip.startswith('applesmc'):
                sensor = entries.get('TG0D', {})
                for key, value in sensor.items():
                    if key.endswith('_input') and isinstance(value, (int, float)) and 0 <= value <= 150:
                        gpu = value
                        break
    except (OSError, ValueError, subprocess.SubprocessError):
        pass

if cpu is None and cores:
    cpu = sum(cores) / len(cores)

def display(value):
    return f'{value:.0f}°C' if value is not None else 'N/D'

print(f'<span font_family="monospace">CPU: {display(cpu)}\nGPU: {display(gpu)}</span>')
