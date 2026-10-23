#!/usr/bin/python3
"""Conservative cache cleanup; no deletion without an interactive confirmation."""
from orbitz_i18n import t
import argparse
import fcntl
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from widget_runtime import launch_terminal_command

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
        print(t('widgets.limpeza_linux.a_cleanup_is_already_open'))
        return
    print(t('widgets.limpeza_linux.linux_partition_cleanup'))
    print(t('widgets.limpeza_linux.suggested_routine_analyze_monthly_or_when_usage_exceeds_90'))
    print(t('widgets.limpeza_linux.user_caches_only_thumbnails_and_pip_downloads_not_accessed_change'))
    print(t('widgets.limpeza_linux.apt_removes_downloaded_installers_installed_programs_remain_avail'))
    print(t('widgets.limpeza_linux.documents_downloads_trash_browsers_logs_and_tmp_are_preserved'))
    # cache_paths names are legacy JSON keys; localize their terminal labels only.
    labels = {'Miniaturas antigas': t('widgets.limpeza_linux.old_thumbnails'),
              'Downloads antigos do pip': t('widgets.limpeza_linux.old_pip_downloads')}
    reports = [(labels[name], path, scan_cache(path)) for name, path in cache_paths()]
    for name, path, report in reports:
        print(t('widgets.limpeza_linux.value0_value1_value2_files', value0=name, value1=size(report['bytes']), value2=report['files']) + (t('widgets.limpeza_linux.partial_analysis') if report['partial'] else ''))
    apt = apt_size()
    print(t('widgets.limpeza_linux.apt_packages_approximately_value0', value0=size(apt)))
    print(t('widgets.limpeza_linux.1_clean_old_user_caches_2_clean_downloaded_apt_packages_asks_for'))
    choice = input(t('widgets.limpeza_linux.option')).strip()
    if choice not in ('1', '2', '3'):
        return
    if input(t('widgets.limpeza_linux.type_limpar_to_confirm')).strip() != 'LIMPAR':
        print(t('widgets.limpeza_linux.cancelled'))
        return
    before = os.statvfs('/')
    if choice in ('1', '3'):
        for name, path, _ in reports:
            report = scan_cache(path, delete=True)
            print(t('widgets.limpeza_linux.value0_value1_files_removed_value2_value3_skipped', value0=name, value1=report['files'], value2=size(report['bytes']), value3=report['skipped']) + (t('widgets.limpeza_linux.partial_execution_analyze_again') if report['partial'] else ''))
    if choice in ('2', '3'):
        if apt:
            status = subprocess.run(['/usr/bin/sudo', '/usr/bin/apt-get', 'clean']).returncode
            print(t('widgets.limpeza_linux.apt_completed') if status == 0 else t('widgets.limpeza_linux.apt_failed_or_cancelled_code_value0', value0=status))
        else:
            print(t('widgets.limpeza_linux.apt_no_eligible_packages_on_this_partition'))
    after = os.statvfs('/')
    print(t('widgets.limpeza_linux.change_in_available_space_on_value0', value0=size((after.f_bavail - before.f_bavail) * after.f_frsize)))
    print(t('widgets.limpeza_linux.other_programs_may_change_disk_space_during_cleanup_click_refresh'))
    input(t('widgets.limpeza_linux.enter_to_close'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--interactive', action='store_true')
    args = parser.parse_args()
    if args.launch:
        launch_terminal_command(['/usr/bin/python3', str(Path(__file__).resolve()), '--interactive'])
    elif args.interactive:
        if not sys.stdin.isatty():
            raise SystemExit(t('widgets.limpeza_linux.cleanup_requires_confirmation_in_a_terminal'))
        try:
            interactive()
        except (EOFError, KeyboardInterrupt):
            print(t('widgets.limpeza_linux.cancelled_92aa83'))
    else:
        print(json.dumps({'caches': {name: scan_cache(path) for name, path in cache_paths()}, 'apt_bytes': apt_size()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
