"""Bounded subprocesses and validated private caches shared by widgets."""
import json, os, selectors, signal, stat, subprocess, tempfile, time
from pathlib import Path


def run(args, capture_output=True, text=True, timeout=5, check=False, limit=262144):
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True) as proc:
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
                        raise ValueError('Saída do coletor excedeu o limite')
                    output[key.fileobj].extend(chunk)
            proc.wait(timeout=max(.001, deadline-time.monotonic()))
        except BaseException:
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            proc.wait()
            raise
        finally:
            selector.close()
        stdout, stderr = (bytes(output[s]).decode('utf-8', errors='replace') for s in (proc.stdout, proc.stderr))
        result = subprocess.CompletedProcess(args, proc.returncode, stdout, stderr)
        if check: result.check_returncode()
        return result


def cache_path(name):
    return Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))/'orbitz-widgets'/name


def load(name, age=60):
    try:
        fd=os.open(cache_path(name),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode): return None
            raw=stream.read(262145)
        if len(raw)>262144: return None
        item=json.loads(raw)
        if not isinstance(item,dict) or not isinstance(item.get('saved'),(int,float)) or not 0 <= time.time()-item['saved'] <= age: return None
        return item.get('data')
    except (OSError,ValueError,TypeError): return None


def save(name,data):
    path=cache_path(name)
    temp=None
    try:
        encoded=json.dumps({'saved':time.time(),'data':data}).encode()
        if len(encoded)>262144: return
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,temp=tempfile.mkstemp(prefix='widget-',dir=path.parent)
        with os.fdopen(fd,'wb') as stream: stream.write(encoded)
        os.replace(temp,path)
    except OSError: pass
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
