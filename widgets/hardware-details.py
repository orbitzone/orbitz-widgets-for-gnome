#!/usr/bin/python3
"""Physical CPU/RAM inventory, with optional explicit firmware read."""
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
        raise ValueError('O firmware não forneceu dados dos módulos de RAM.')
    return dict(modules=modules[:64], arrays=arrays[:8], timestamp=time.strftime('%d/%m/%Y %H:%M'), boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def cpu_inventory():
    cards, note = [], 'Modelo, topologia e recursos de virtualização.'
    try:
        response = run(['/usr/bin/env', 'LC_ALL=C', 'lscpu', '--json'], timeout=3, check=True)
        values = {row['field'].rstrip(':'): str(row['data']) for row in json.loads(response.stdout)['lscpu']}
        def value(key): return values.get(key, 'Indisponível')
        cards.append(dict(title='Processador', lines=[value('Model name'), 'Arquitetura: '+value('Architecture'), 'Fabricante: '+value('Vendor ID')]))
        sockets = values.get('Socket(s)')
        cores = values.get('Core(s) per socket')
        physical = str(int(sockets)*int(cores)) if sockets and cores and sockets.isdecimal() and cores.isdecimal() else 'Indisponível'
        cards.append(dict(title='Topologia', lines=['Núcleos físicos: '+physical, 'Processadores lógicos: '+value('CPU(s)'), 'Threads por núcleo: '+value('Thread(s) per core'), 'Sockets: '+value('Socket(s)')]))
        flags = values.get('Flags', '').split()
        supported = 'vmx' in flags or 'svm' in flags
        kvm = Path('/dev/kvm')
        status = 'Disponível para sua conta' if kvm.exists() and os.access(kvm, os.R_OK|os.W_OK) else 'Dispositivo presente; acesso restrito' if kvm.exists() else 'Dispositivo /dev/kvm indisponível'
        cards.append(dict(title='Virtualização', lines=['Extensão anunciada: '+values.get('Virtualization', 'Sim' if supported else 'Não informada'), 'KVM: '+status, 'A presença da extensão não confirma a configuração do firmware.']))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        cards.append(dict(title='Processador', lines=['Inventário indisponível. Verifique o acesso ao lscpu.']))
    return dict(mode='cpu', title='CPU · configuração física', note=note, cards=cards, firmware_action=False)


def ram_inventory():
    memory = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        memory[key] = int(value.split()[0])*1024
    cards = [dict(title='Memória reconhecida pelo Linux', lines=[f'Total utilizável: {memory["MemTotal"]/1073741824:.1f} GiB', 'O total utilizável pode ser menor que a capacidade física instalada.'])]
    cached = load(CACHE, 365*86400)
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    valid = isinstance(cached, dict) and cached.get('boot') == boot and isinstance(cached.get('modules'), list) and isinstance(cached.get('arrays'), list)
    if valid:
        modules = cached['modules']
        empty = sum(m.get('Size') == 'No Module Installed' for m in modules)
        populated = sum(bool(re.fullmatch(r'\d+\s+(?:MB|GB|TB)', m.get('Size', ''))) for m in modules)
        unknown = len(modules)-empty-populated
        cards.append(dict(title='Slots informados pelo firmware', lines=[f'Com módulo: {populated} · vazios: {empty} · sem leitura conclusiva: {unknown}', 'Slots vazios não garantem acesso físico ou possibilidade de expansão.', 'Leitura: '+str(cached.get('timestamp', 'Indisponível'))]))
        for array in cached['arrays']:
            cards.append(dict(title='Limites declarados pelo firmware', lines=['Capacidade máxima: '+array.get('Maximum Capacity','Indisponível'), 'Dispositivos: '+array.get('Number Of Devices','Indisponível'), 'Correção de erros: '+array.get('Error Correction Type','Indisponível'), 'Confirme o limite e a compatibilidade no manual do equipamento.']))
        for index, module in enumerate(modules):
            lines = ['Capacidade: '+module.get('Size','Indisponível')]
            if module.get('Size') != 'No Module Installed':
                for key,label in [('Type','Tipo'),('Form Factor','Formato'),('Speed','Velocidade declarada'),('Configured Memory Speed','Velocidade configurada'),('Manufacturer','Fabricante'),('Part Number','Modelo')]:
                    lines.append(label+': '+module.get(key,'Indisponível'))
            cards.append(dict(title=module.get('Locator') or f'Módulo {index+1}', lines=lines))
    else:
        cards.append(dict(title='Módulos e expansão', lines=['Tipo DDR, velocidades, módulos, slots e limites: indisponíveis sem leitura do firmware.', 'Use “Ler módulos de RAM” para autorizar a leitura no terminal. Não altera a configuração.']))
    return dict(mode='ram', title='RAM · módulos e expansão', note='Inventário físico informado pelo firmware · leitura válida para esta inicialização.', cards=cards, firmware_action=True)


def main():
    if '--import-firmware' in sys.argv:
        raw = sys.stdin.read(131073)
        if len(raw)>131072: raise ValueError('Inventário excedeu o limite')
        data = parse_dmi(raw)
        save(CACHE, data)
        if load(CACHE,60) != data: raise OSError('Não foi possível salvar a leitura')
        print('Leitura salva. Clique em Atualizar na modal da RAM.')
    elif '--read-firmware' in sys.argv:
        command = 'set -o pipefail; LC_ALL=C sudo /usr/sbin/dmidecode --type 16,17 | /usr/bin/python3 '+shlex.quote(str(Path(__file__).resolve()))+' --import-firmware'
        launch_terminal('RAM · leitura do firmware', command, 'Executa somente dmidecode como administrador. Salva os dados dos módulos sem números de série. Depois clique em Atualizar na modal.')
    else:
        mode = sys.argv[sys.argv.index('--hardware')+1]
        if mode not in ('cpu','ram'): raise ValueError('Seleção inválida')
        print('AZCLOCK_HARDWARE:'+json.dumps(cpu_inventory() if mode=='cpu' else ram_inventory(), ensure_ascii=False))

if __name__ == '__main__':
    main()
