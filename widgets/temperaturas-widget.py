#!/usr/bin/env python3
from orbitz_i18n import t
import json,re,subprocess,sys
from pathlib import Path
from widget_runtime import load,save,run

def read(path):
    try:
        value=int(Path(path).read_text().strip())/1000
        return value if -20<=value<=150 else None
    except (OSError,ValueError):return None

# References: VirtualSMC/Docs/SMCSensorKeys.txt and exelban/stats SensorsList.
# SMC locations can vary by model; unknown keys receive an explicit fallback.
SMC_DESCRIPTIONS = {
    'TA0V': 'widgets.temperaturas_widget.estimated_ambient_temperature_near_the_equipment',
    'TC0E': 'widgets.temperaturas_widget.estimated_internal_processor_temperature',
    'TC0F': 'widgets.temperaturas_widget.internal_processor_temperature_with_filtered_reading',
    'TC0P': 'widgets.temperaturas_widget.temperature_near_the_processor',
    'TCGC': 'widgets.temperaturas_widget.temperature_of_the_integrated_processor_graphics',
    'TCXC': 'widgets.temperaturas_widget.processor_temperature_reading_via_the_peci_interface',
    'TG0D': 'widgets.temperaturas_widget.internal_gpu_temperature',
    'TG0P': 'widgets.temperaturas_widget.temperature_near_the_gpu',
    'TGDD': 'widgets.temperaturas_widget.dedicated_amd_gpu_temperature',
    'TM0P': 'widgets.temperaturas_widget.temperature_near_ram',
    'TPCD': 'widgets.temperaturas_widget.motherboard_controller_chipset_temperature',
    'TTLD': 'widgets.temperaturas_widget.left_thunderbolt_controller_temperature',
    'TTRD': 'widgets.temperaturas_widget.right_thunderbolt_controller_temperature',
    'TW0P': 'widgets.temperaturas_widget.temperature_near_the_wi_fi_module',
    'Ts0P': 'widgets.temperaturas_widget.temperature_near_the_palm_rest_or_trackpad_depending_on_the_model',
    'Ts1P': 'widgets.temperaturas_widget.another_sensor_near_the_palm_rest_location_varies_by_model',
    'Ts0S': 'widgets.temperaturas_widget.estimated_bottom_enclosure_surface_temperature',
    'Ts1S': 'widgets.temperaturas_widget.estimated_top_enclosure_surface_temperature',
}

def describe(group, name):
    code=name.split(' · ')[-1]
    if group.startswith('applesmc'):
        if code in SMC_DESCRIPTIONS:return t(SMC_DESCRIPTIONS[code])
        if re.fullmatch(r'TC[0-9]C',code):return t('widgets.temperaturas_widget.temperature_of_a_processor_core_identified_by')+code+'.'
        if re.fullmatch(r'TH0[A-Ca-c]',code):return t('widgets.temperaturas_widget.ssd_storage_temperature_sensor_point')+code[-1].upper()+'.'
        if re.fullmatch(r'Th[0-9]H',code):return t('widgets.temperaturas_widget.heatsink_assembly_temperature')
        return t('widgets.temperaturas_widget.apple_smc_sensor')+code+t('widgets.temperaturas_widget.exact_component_or_location_not_identified_for_this_model')
    if group.startswith('coretemp'):
        return t('widgets.temperaturas_widget.processor_package_temperature') if 'Package' in name else t('widgets.temperaturas_widget.temperature_of_the_processor_core_indicated_in_the_name')
    if group.startswith('nvme'):return t('widgets.temperaturas_widget.nvme_ssd_temperature_composite_is_the_combined_reading_reported_b')
    if group.startswith(('amdgpu','NVIDIA')):return t('widgets.temperaturas_widget.gpu_temperature_the_point_is_identified_by_the_driver')
    return t('widgets.temperaturas_widget.temperature_sensor_exposed_by')+group+t('widgets.temperaturas_widget.the_system_does_not_provide_a_more_specific_description')

def details():
    import math, shutil
    items=[]; covered=set()
    try:
        sensors=json.loads(run(['sensors','-j'],timeout=3,check=True).stdout)
        if isinstance(sensors,dict):
            for chip,groups in sensors.items():
                if not isinstance(groups,dict):continue
                found=False
                for label,values in groups.items():
                    if not isinstance(values,dict):continue
                    for key,value in values.items():
                        if not re.fullmatch(r'temp\d+_input',key):continue
                        valid=type(value) in (int,float) and math.isfinite(value) and -20<=value<=250
                        found=True
                        if not valid:continue
                        title=label
                        if chip.startswith('applesmc'):
                            if label.startswith('TG'):title='GPU · '+label
                            elif label.startswith('TC'):title='CPU · '+label
                        items.append(dict(group=chip[:128],name=title[:100],value=value))
                        found=True
                if found:covered.add(chip.split('-')[0])
    except (OSError,ValueError,subprocess.SubprocessError):pass
    for device in sorted(Path('/sys/class/hwmon').glob('hwmon*')):
        try: driver=(device/'name').read_text().strip()
        except OSError: continue
        if driver in covered:continue
        for path in sorted(device.glob('temp*_input')):
            try: value=int(path.read_text().strip())/1000
            except (OSError,ValueError): value=None
            if value is not None and (not math.isfinite(value) or not -20<=value<=250): value=None
            if value is None:continue
            try: label=path.with_name(path.name.replace('_input','_label')).read_text().strip()
            except OSError: label=path.name.replace('_input','')
            items.append(dict(group=driver+' · '+device.name,name=label[:100],value=value))
    for zone in sorted(Path('/sys/class/thermal').glob('thermal_zone*')):
        try:
            label=(zone/'type').read_text().strip(); value=int((zone/'temp').read_text().strip())/1000
        except (OSError,ValueError): continue
        if label=='x86_pkg_temp' and 'coretemp' in covered:continue
        if -20<=value<=250: items.append(dict(group=t('widgets.temperaturas_widget.system')+zone.name,name=label[:100],value=value))
    if shutil.which('nvidia-smi'):
        try:
            output=run(['nvidia-smi','--query-gpu=name,temperature.gpu','--format=csv,noheader,nounits'],timeout=3,check=True).stdout
            for line in output.splitlines():
                name,value=line.rsplit(',',1); value=float(value)
                if math.isfinite(value) and -273.15<=value<=250:items.append(dict(group='NVIDIA',name=name.strip()[:100],value=value))
        except (OSError,ValueError,subprocess.SubprocessError):pass
    items=[item for item in items if type(item['value']) in (int,float) and math.isfinite(item['value']) and -20<=item['value']<=250]
    for item in items:
        if item['name']=='CPU · TCGC':item['name']='GPU · TCGC'
        item['description']=describe(item['group'],item['name'])
    return dict(items=items[:256],omitted=max(0,len(items)-256))

def display(value):
    if value is None:return t('widgets.temperaturas_widget.n_a')
    text=f'{value:.0f}°C'
    return f'<span foreground="#ff5c5c">{text}</span>' if value>80 else text


def main():
    if '--details' in sys.argv:
        print('AZCLOCK_TEMPERATURES:'+json.dumps(details(),ensure_ascii=False))
        sys.exit(0)

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
            if not isinstance(data,dict):raise ValueError(t('widgets.temperaturas_widget.invalid_sensors'))
            for chip,values in data.items():
                if chip.startswith('applesmc') and isinstance(values,dict):
                    sensor=values.get('TG0D',{})
                    if not isinstance(sensor,dict):continue
                    for key,value in sensor.items():
                        if key.endswith('_input') and type(value) in (int,float) and 0<=value<=150:gpu=value
            if gpu is None:save('gpu-absent.json',True)
        except (OSError,ValueError,subprocess.SubprocessError):save('gpu-absent.json',True)
    if cpu is None and cores:cpu=sum(cores)/len(cores)
    print(f'<span font_family="monospace">CPU: {display(cpu)}\nGPU: {display(gpu)}</span>')


if __name__ == '__main__':
    main()
