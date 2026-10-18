#!/usr/bin/python3
"""Conservative cache cleanup; no deletion without an interactive confirmation."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

AGE = 30 * 86400
FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def open_directory(path):
    """Reject symlinks in every component, including configured cache parents."""
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('Caminho deve ser absoluto')
    fd = os.open('/', FLAGS)
    try:
        for part in path.parts[1:]:
            next_fd = os.open(part, FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def scan_cache(path, delete=False, now=None, device=None):
    cutoff = (time.time() if now is None else now) - AGE
    result = dict(files=0, bytes=0, skipped=0, partial=False)
    deadline = time.monotonic() + 15
    visited = 0
    def walk(fd, depth=0):
        nonlocal visited
        if depth > 32:
            result['partial'] = True
            return
        with os.scandir(fd) as entries:
            for entry in entries:
                visited += 1
                if visited > 100000 or time.monotonic() > deadline:
                    result['partial'] = True
                    return
                try:
                    info = entry.stat(follow_symlinks=False)
                    if info.st_dev != device or info.st_uid != os.getuid():
                        continue
                    if stat.S_ISDIR(info.st_mode):
                        child = os.open(entry.name, FLAGS, dir_fd=fd)
                        try:
                            if os.fstat(child).st_dev == device:
                                walk(child, depth + 1)
                        finally:
                            os.close(child)
                    elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and max(info.st_mtime, info.st_atime, info.st_ctime) < cutoff:
                        if delete:
                            current = os.stat(entry.name, dir_fd=fd, follow_symlinks=False)
                            if (current.st_ino, current.st_dev, current.st_mtime_ns, current.st_ctime_ns, current.st_atime_ns, current.st_size, current.st_nlink) != (info.st_ino, info.st_dev, info.st_mtime_ns, info.st_ctime_ns, info.st_atime_ns, info.st_size, info.st_nlink):
                                result['skipped'] += 1
                                continue
                            os.unlink(entry.name, dir_fd=fd)
                        result['files'] += 1
                        result['bytes'] += info.st_blocks * 512
                except OSError:
                    result['skipped'] += 1
                if result['partial']:
                    return
    try:
        fd = open_directory(path)
        try:
            device = os.stat('/').st_dev if device is None else device
            if os.fstat(fd).st_dev == device:
                walk(fd)
        finally:
            os.close(fd)
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        result['skipped'] += 1
    return result


def cache_paths():
    base = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache')
    return [('Miniaturas antigas', base / 'thumbnails'), ('Downloads antigos do pip', base / 'pip')]


def apt_size():
    total = 0
    try:
        fd = open_directory('/var/cache/apt/archives')
        try:
            if os.fstat(fd).st_dev != os.stat('/').st_dev:
                return 0
            with os.scandir(fd) as entries:
                for entry in entries:
                    info = entry.stat(follow_symlinks=False)
                    if entry.name.endswith('.deb') and stat.S_ISREG(info.st_mode):
                        total += info.st_blocks * 512
        finally:
            os.close(fd)
    except OSError:
        pass
    return total


def size(value):
    return f'{value / 1048576:.1f} MiB'


def interactive():
    lock = open(Path('/run/user') / str(os.getuid()) / 'azclock-cleanup.lock', 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('Já existe uma limpeza aberta.')
        return
    print('Limpeza da partição do Linux (/)\n')
    print('Rotina sugerida: analisar uma vez por mês ou quando o uso passar de 90%.')
    print('Caches do usuário: somente miniaturas e downloads do pip sem acesso/alteração há mais de 30 dias, na mesma partição de /.')
    print('APT: remove os instaladores baixados; os programas instalados continuam disponíveis.')
    print('Documentos, Downloads, lixeira, navegadores, logs e /tmp ficam preservados.\n')
    reports = [(name, path, scan_cache(path)) for name, path in cache_paths()]
    for name, path, report in reports:
        print(f'{name}: {size(report["bytes"])} · {report["files"]} arquivos' + (' · análise parcial' if report['partial'] else ''))
    apt = apt_size()
    print(f'Pacotes APT: aproximadamente {size(apt)}')
    print('\n1 — Limpar caches antigos do usuário\n2 — Limpar pacotes baixados do APT (pede senha)\n3 — Executar as duas opções\nEnter — Cancelar')
    choice = input('\nOpção: ').strip()
    if choice not in ('1', '2', '3'):
        return
    if input('Digite LIMPAR para confirmar: ').strip() != 'LIMPAR':
        print('Cancelado.')
        return
    before = os.statvfs('/')
    if choice in ('1', '3'):
        for name, path, _ in reports:
            report = scan_cache(path, delete=True)
            print(f'{name}: {report["files"]} arquivos removidos · {size(report["bytes"])} · {report["skipped"]} ignorados' + (' · execução parcial; analise novamente' if report['partial'] else ''))
    if choice in ('2', '3'):
        if apt:
            status = subprocess.run(['/usr/bin/sudo', '/usr/bin/apt-get', 'clean']).returncode
            print('APT: concluído.' if status == 0 else f'APT: falhou ou foi cancelado (código {status}).')
        else:
            print('APT: nenhum pacote elegível nesta partição.')
    after = os.statvfs('/')
    print(f'\nVariação do espaço disponível em /: {size((after.f_bavail - before.f_bavail) * after.f_frsize)}')
    print('Outros programas podem alterar o espaço durante a limpeza. Clique em Atualizar no painel do SSD.')
    input('\nEnter para fechar: ')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--interactive', action='store_true')
    args = parser.parse_args()
    if args.launch:
        subprocess.Popen(['gnome-terminal', '--', '/usr/bin/python3', str(Path(__file__).resolve()), '--interactive'], start_new_session=True)
    elif args.interactive:
        if not sys.stdin.isatty():
            raise SystemExit('A limpeza exige confirmação em um terminal.')
        try:
            interactive()
        except (EOFError, KeyboardInterrupt):
            print('\nCancelado.')
    else:
        print(json.dumps({'caches': {name: scan_cache(path) for name, path in cache_paths()}, 'apt_bytes': apt_size()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
