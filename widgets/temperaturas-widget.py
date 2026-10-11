#!/usr/bin/env python3
import json,re,subprocess
from pathlib import Path
from widget_runtime import load,save,run

def read(path):
    try:
        value=int(Path(path).read_text().strip())/1000
        return value if -20<=value<=150 else None
    except (OSError,ValueError):return None

pattern=re.compile(r'^/sys/class/hwmon/hwmon\d+/temp\d+_input$')
entries=load('sensors-paths.json',60)
if not isinstance(entries,list) or len(entries)>256 or any(not isinstance(e,dict) or not isinstance(e.get('path'),str) or not pattern.fullmatch(e['path']) or e.get('driver') not in ('coretemp','amdgpu','applesmc') or not isinstance(e.get('label'),str) for e in entries) or any(not Path(e['path']).exists() for e in entries):
    entries=[]
    for device in Path('/sys/class/hwmon').glob('hwmon*'):
        try:driver=(device/'name').read_text().strip().lower()
        except OSError:continue
        if driver not in ('coretemp','amdgpu','applesmc'):continue
        for path in device.glob('temp*_input'):
            try:label=path.with_name(path.name.replace('_input','_label')).read_text().strip().lower()
            except OSError:label=''
            entries.append({'path':str(path),'driver':driver,'label':label[:64]})
    save('sensors-paths.json',entries)
cpu=gpu=None;cores=[]
for entry in entries:
    value=read(entry['path'])
    if value is None:continue
    driver,label=entry['driver'],entry['label']
    if driver=='coretemp':
        if 'package' in label:cpu=value
        elif 'core' in label:cores.append(value)
    if driver=='amdgpu' and (gpu is None or label=='edge'):gpu=value
    if driver=='applesmc' and label=='tg0d':gpu=value
if gpu is None and load('gpu-absent.json',60) is not True:
    try:
        data=json.loads(run(['sensors','-j'],timeout=3,check=True).stdout)
        if not isinstance(data,dict):raise ValueError('Sensores inválidos')
        for chip,values in data.items():
            if chip.startswith('applesmc') and isinstance(values,dict):
                sensor=values.get('TG0D',{})
                if not isinstance(sensor,dict):continue
                for key,value in sensor.items():
                    if key.endswith('_input') and type(value) in (int,float) and 0<=value<=150:gpu=value
        if gpu is None:save('gpu-absent.json',True)
    except (OSError,ValueError,subprocess.SubprocessError):save('gpu-absent.json',True)
if cpu is None and cores:cpu=sum(cores)/len(cores)
def display(value):return f'{value:.0f}°C' if value is not None else 'N/D'
print(f'<span font_family="monospace">CPU: {display(cpu)}\nGPU: {display(gpu)}</span>')
