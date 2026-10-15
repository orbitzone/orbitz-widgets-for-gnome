#!/usr/bin/env python3
"""Stop a verified collector tree, restricted to the current user's processes."""
import os
from pathlib import Path
import signal
import sys
import time


def identity(pid):
    try:
        root = Path('/proc') / str(pid)
        if root.stat().st_uid != os.getuid():
            return None
        text = (root / 'stat').read_text()
        fields = text[text.rfind(')') + 2:].split()
        return fields[19], fields[0]
    except (OSError, IndexError):
        return None


def children(pid):
    found = set()
    try:
        tasks = list((Path('/proc') / str(pid) / 'task').iterdir())
    except OSError:
        return []
    for task in tasks:
        try:
            found.update(int(x) for x in (task / 'children').read_text().split())
        except (OSError, ValueError):
            continue
    return list(found)


def stop(pid, expected_birth):
    if pid <= 1 or pid == os.getpid() or not expected_birth.isdecimal():
        raise ValueError('Identidade inválida')
    current = identity(pid)
    if current is None or current[0] != expected_birth:
        return
    records = []
    seen = set()
    pending = [pid]
    try:
        while pending and len(seen) < 4096:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            stamp = identity(current)
            if stamp is None:
                continue
            birth, state = stamp
            records.append((current, birth))
            try:
                os.kill(current, signal.SIGSTOP)
            except ProcessLookupError:
                continue
            # Freeze each parent before enumerating its children, preventing forks.
            deadline = time.monotonic() + .1
            while time.monotonic() < deadline:
                stamp = identity(current)
                if stamp is None or stamp[0] != birth or stamp[1] in ('T', 't', 'Z'):
                    break
                time.sleep(.001)
            pending.extend(children(current))
        for current, birth in reversed(records):
            stamp = identity(current)
            if stamp is not None and stamp[0] == birth:
                try:
                    os.kill(current, signal.SIGKILL)
                except ProcessLookupError:
                    pass
    finally:
        # Never leave a process suspended if permission or filesystem checks fail.
        for current, birth in records:
            stamp = identity(current)
            if stamp is not None and stamp[0] == birth:
                try:
                    os.kill(current, signal.SIGCONT)
                except ProcessLookupError:
                    pass


if __name__ == '__main__':
    try:
        stop(int(sys.argv[1]), sys.argv[2])
    except (OSError, ValueError, IndexError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
