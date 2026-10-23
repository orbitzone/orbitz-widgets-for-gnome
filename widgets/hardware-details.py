#!/usr/bin/python3
"""Physical CPU/RAM inventory, with optional explicit firmware read."""
from orbitz_i18n import t
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from widget_runtime import run, load, save, launch_terminal

CACHE = 'physical-memory-v1.json'

def parse_dmi(text):
    modules, arrays = [], []
    for block in re.split(r'(?m)^Handle ', text):
        match = re.match(r'[^\n]*DMI type (\d+),', block)
        if not match or int(match[1]) not in (16, 17):
            continue
        fields = {}
        for line in block.splitlines():
            if ':' in line:
                key, value = line.strip().split(':', 1)
                fields[key] = value.strip()[:160]
        if int(match[1]) == 16:
            if fields.get('Use') == 'System Memory':
                arrays.append({k: fields.get(k, 'Indisponível') for k in ('Maximum Capacity', 'Number Of Devices', 'Error Correction Type')})
        else:
            keys = ('Size', 'Locator', 'Bank Locator', 'Type', 'Form Factor', 'Speed', 'Configured Memory Speed', 'Manufacturer', 'Part Number')
            modules.append({k: fields.get(k, 'Indisponível') for k in keys})
    if not modules:
        raise ValueError(t('widgets.hardware_details.firmware_missing_modules'))
    return dict(modules=modules[:64], arrays=arrays[:8], timestamp=time.strftime('%d/%m/%Y %H:%M'), boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def cpu_inventory():
    cards, note = [], t('widgets.hardware_details.model_topology_and_virtualization_features')
    try:
        response = run(['/usr/bin/env', 'LC_ALL=C', 'lscpu', '--json'], timeout=3, check=True)
        values = {row['field'].rstrip(':'): str(row['data']) for row in json.loads(response.stdout)['lscpu']}
        def value(key): return values.get(key, t('widgets.hardware_details.unavailable'))
        cards.append(dict(title=t('widgets.hardware_details.processor'), lines=[value('Model name'), t('widgets.hardware_details.architecture')+value('Architecture'), t('widgets.hardware_details.manufacturer')+value('Vendor ID')]))
        sockets = values.get('Socket(s)')
        cores = values.get('Core(s) per socket')
        physical = str(int(sockets)*int(cores)) if sockets and cores and sockets.isdecimal() and cores.isdecimal() else t('widgets.hardware_details.unavailable')
        cards.append(dict(title=t('widgets.hardware_details.topology'), lines=[t('widgets.hardware_details.physical_cores')+physical, t('widgets.hardware_details.logical_processors')+value('CPU(s)'), t('widgets.hardware_details.threads_per_core')+value('Thread(s) per core'), 'Sockets: '+value('Socket(s)')]))
        flags = values.get('Flags', '').split()
        supported = 'vmx' in flags or 'svm' in flags
        kvm = Path('/dev/kvm')
        status = t('widgets.hardware_details.available_to_your_account') if kvm.exists() and os.access(kvm, os.R_OK|os.W_OK) else t('widgets.hardware_details.device_present_restricted_access') if kvm.exists() else t('widgets.hardware_details.device_dev_kvm_unavailable')
        cards.append(dict(title=t('widgets.hardware_details.virtualization'), lines=[t('widgets.hardware_details.reported_extension')+values.get('Virtualization', t('widgets.hardware_details.yes') if supported else t('widgets.hardware_details.not_reported')), 'KVM: '+status, t('widgets.hardware_details.the_presence_of_the_extension_does_not_confirm_firmware_configura')]))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        cards.append(dict(title=t('widgets.hardware_details.processor'), lines=[t('widgets.hardware_details.inventory_unavailable_check_access_to_lscpu')]))
    return dict(mode='cpu', title=t('widgets.hardware_details.cpu_physical_configuration'), note=note, cards=cards, firmware_action=False)


def firmware_value(record, key):
    # Historical caches use this marker for missing fields, never for identity.
    value = record.get(key)
    return t('widgets.hardware_details.unavailable') if value is None or value == 'Indisponível' else value


def ram_inventory():
    memory = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        memory[key] = int(value.split()[0])*1024
    cards = [dict(title=t('widgets.hardware_details.memory_recognized_by_linux'), lines=[t('widgets.hardware_details.total_usable_value0_1f_gib', value0=memory['MemTotal'] / 1073741824), t('widgets.hardware_details.the_usable_total_may_be_smaller_than_the_installed_physical_capac')])]
    cached = load(CACHE, 365*86400)
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    valid = isinstance(cached, dict) and cached.get('boot') == boot and isinstance(cached.get('modules'), list) and isinstance(cached.get('arrays'), list)
    if valid:
        modules = cached['modules']
        empty = sum(m.get('Size') == 'No Module Installed' for m in modules)
        populated = sum(bool(re.fullmatch(r'\d+\s+(?:MB|GB|TB)', m.get('Size', ''))) for m in modules)
        unknown = len(modules)-empty-populated
        cards.append(dict(title=t('widgets.hardware_details.slots_reported_by_firmware'), lines=[t('widgets.hardware_details.populated_value0_empty_value1_inconclusive_value2', value0=populated, value1=empty, value2=unknown), t('widgets.hardware_details.empty_slots_do_not_guarantee_physical_access_or_expandability'), t('widgets.hardware_details.reading')+str(cached.get('timestamp', t('widgets.hardware_details.unavailable')))]))
        for array in cached['arrays']:
            cards.append(dict(title=t('widgets.hardware_details.limits_reported_by_firmware'), lines=[t('widgets.hardware_details.maximum_capacity')+firmware_value(array, 'Maximum Capacity'), t('widgets.hardware_details.devices')+firmware_value(array, 'Number Of Devices'), t('widgets.hardware_details.error_correction')+firmware_value(array, 'Error Correction Type'), t('widgets.hardware_details.confirm_the_limit_and_compatibility_in_the_equipment_manual')]))
        for index, module in enumerate(modules):
            lines = [t('widgets.hardware_details.capacity')+firmware_value(module, 'Size')]
            if module.get('Size') != 'No Module Installed':
                for key,label in [('Type',t('widgets.hardware_details.type')),('Form Factor',t('widgets.hardware_details.form_factor')),('Speed',t('widgets.hardware_details.rated_speed')),('Configured Memory Speed',t('widgets.hardware_details.configured_speed')),('Manufacturer',t('widgets.hardware_details.manufacturer_b79530')),('Part Number',t('widgets.hardware_details.model'))]:
                    lines.append(label+': '+firmware_value(module, key))
            cards.append(dict(title=module.get('Locator') or t('widgets.hardware_details.module_value0', value0=index + 1), lines=lines))
    else:
        cards.append(dict(title=t('widgets.hardware_details.modules_and_expansion'), lines=[t('widgets.hardware_details.ddr_type_speeds_modules_slots_and_limits_unavailable_without_read'), t('widgets.hardware_details.use_read_ram_modules_to_authorize_the_terminal_read_this_does_not')]))
    return dict(mode='ram', title=t('widgets.hardware_details.ram_modules_and_expansion'), note=t('widgets.hardware_details.physical_inventory_reported_by_firmware_reading_valid_for_this_bo'), cards=cards, firmware_action=True)


def main():
    if '--import-firmware' in sys.argv:
        raw = sys.stdin.read(131073)
        if len(raw)>131072: raise ValueError(t('widgets.hardware_details.inventory_exceeded_the_limit'))
        data = parse_dmi(raw)
        save(CACHE, data)
        if load(CACHE,60) != data: raise OSError(t('widgets.hardware_details.could_not_save_the_reading'))
        print(t('widgets.hardware_details.reading_saved_click_refresh_in_the_ram_dialog'))
    elif '--read-firmware' in sys.argv:
        command = 'set -o pipefail; LC_ALL=C sudo /usr/sbin/dmidecode --type 16,17 | /usr/bin/python3 '+shlex.quote(str(Path(__file__).resolve()))+' --import-firmware'
        launch_terminal(t('widgets.hardware_details.ram_firmware_reading'), command, t('widgets.hardware_details.runs_only_dmidecode_as_administrator_saves_module_data_without_se'))
    else:
        mode = sys.argv[sys.argv.index('--hardware')+1]
        if mode not in ('cpu','ram'): raise ValueError(t('widgets.hardware_details.invalid_selection'))
        print('AZCLOCK_HARDWARE:'+json.dumps(cpu_inventory() if mode=='cpu' else ram_inventory(), ensure_ascii=False))

if __name__ == '__main__':
    main()
