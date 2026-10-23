"""Bounded subprocesses and validated private caches shared by widgets."""
from orbitz_i18n import t
import json, math, os, selectors, shlex, shutil, signal, stat, subprocess, tempfile, time
from pathlib import Path


def run(args, capture_output=True, text=True, timeout=5, check=False, limit=262144):
    if not math.isfinite(timeout) or timeout <= 0 or limit < 1:
        raise ValueError(t('widgets.widget_runtime.invalid_subprocess_limits'))
    # A native watchdog survives abrupt collector cancellation and bounds orphan lifetime.
    guarded = ['/usr/bin/timeout', '--signal=KILL', str(timeout) + 's', *args]
    with subprocess.Popen(guarded, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True) as proc:
        selector = selectors.DefaultSelector()
        output = {proc.stdout: bytearray(), proc.stderr: bytearray()}
        for stream in output:
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        deadline = time.monotonic() + timeout
        size = 0
        try:
            while selector.get_map():
                left = deadline - time.monotonic()
                if left <= 0:
                    raise subprocess.TimeoutExpired(args, timeout)
                for key, _ in selector.select(min(left, .2)):
                    chunk = os.read(key.fileobj.fileno(), 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    size += len(chunk)
                    if size > limit:
                        raise ValueError(t('widgets.widget_runtime.collector_output_exceeded_the_limit'))
                    output[key.fileobj].extend(chunk)
            proc.wait(timeout=max(.001, deadline-time.monotonic()))
        except BaseException:
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
            raise
        finally:
            selector.close()
        if proc.returncode in (-signal.SIGKILL, 124):
            raise subprocess.TimeoutExpired(args, timeout)
        stdout, stderr = (bytes(output[s]).decode('utf-8', errors='replace') for s in (proc.stdout, proc.stderr))
        result = subprocess.CompletedProcess(args, proc.returncode, stdout, stderr)
        if check: result.check_returncode()
        return result


def cache_path(name):
    if not isinstance(name,str) or Path(name).name != name or name in ('', '.', '..'):
        raise ValueError(t('widgets.widget_runtime.invalid_cache_name'))
    return Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))/'orbitz-widgets'/name


def load(name, age=60):
    try:
        fd=os.open(cache_path(name),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode): return None
            raw=stream.read(262145)
        if len(raw)>262144: return None
        item=json.loads(raw)
        if not isinstance(item,dict) or type(item.get('saved')) not in (int,float) or not math.isfinite(item['saved']) or not 0 <= time.time()-item['saved'] <= age: return None
        return item.get('data')
    except (OSError,ValueError,TypeError): return None


def save(name,data):
    path=cache_path(name)
    temp=None
    try:
        encoded=json.dumps({'saved':time.time(),'data':data},allow_nan=False).encode()
        if len(encoded)>262144: return
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,temp=tempfile.mkstemp(prefix='widget-',dir=path.parent)
        with os.fdopen(fd,'wb') as stream: stream.write(encoded)
        os.replace(temp,path)
    except (OSError,ValueError,TypeError): pass
    finally:
        if temp and os.path.exists(temp): os.unlink(temp)


def read_json(path):
    try:
        fd=os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode): return None
            data=stream.read(262145)
        return json.loads(data) if len(data)<=262144 else None
    except (OSError,ValueError,TypeError): return None


def launch_terminal_command(command):
    """Run an argv command in Tilix without passing it through an implicit shell."""
    if not isinstance(command, (list, tuple)) or not command or any(not isinstance(arg, str) or '\x00' in arg for arg in command):
        raise ValueError(t('widgets.widget_runtime.invalid_terminal_command'))
    terminal = shutil.which('tilix')
    if not terminal:
        raise FileNotFoundError(t('widgets.widget_runtime.tilix_is_not_installed_install_tilix_to_run_interactive_actions'))
    # Inherit DESKTOP_STARTUP_ID from the GNOME launch context. A new window
    # keeps each confirmation visible even when Tilix already has a session.
    subprocess.Popen([terminal, '--action=app-new-window', '-e', shlex.join(command)], start_new_session=True)


def launch_terminal(name, command, effect=''):
    """Display command as data and require successful input before execution."""
    if not isinstance(command,str) or not command or '\x00' in command:
        raise ValueError(t('widgets.widget_runtime.invalid_command'))
    message='\n'.join(part for part in (name, effect, command) if part)
    script=('printf "%s\\n" '+shlex.quote(message)+
            '; printf "%s" '+shlex.quote(t('widgets.widget_runtime.confirm_execution'))+
            '; read -r reply || exit 0; '+command+
            '; result=$?; printf "%s%s%s" '+shlex.quote(t('widgets.widget_runtime.exit_code'))+
            ' "$result" '+shlex.quote(t('widgets.widget_runtime.close_terminal'))+'; read -r reply || true')
    launch_terminal_command(['bash', '-c', script])
