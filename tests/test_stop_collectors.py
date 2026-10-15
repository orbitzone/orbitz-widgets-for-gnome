import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stop_collectors', ROOT/'extension/stop-collectors.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class StopCollectorsTests(unittest.TestCase):
    def test_detached_child_is_stopped_with_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            ready = Path(folder)/'child-pid'
            program = "import subprocess,sys,time,threading; child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True);open("+repr(str(ready))+",'w').write(str(child.pid));time.sleep(30)"
            proc = subprocess.Popen([sys.executable,'-c',program], start_new_session=True)
            child = None
            try:
                deadline=time.monotonic()+3
                while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)
                self.assertTrue(ready.exists())
                child=int(ready.read_text())
                parent_birth=helper.identity(proc.pid)[0]
                helper.stop(proc.pid,parent_birth)
                proc.wait(timeout=2)
                self.assertEqual(proc.returncode,-signal.SIGKILL)
                deadline=time.monotonic()+2
                while time.monotonic()<deadline:
                    state=helper.identity(child)
                    if state is None or state[1]=='Z':break
                    time.sleep(.01)
                self.assertTrue(state is None or state[1]=='Z')
            finally:
                if proc.poll() is None:proc.kill();proc.wait()
                if child and helper.identity(child):
                    try:os.kill(child,signal.SIGKILL)
                    except ProcessLookupError:pass

    def test_children_created_by_worker_threads_are_found(self):
        with tempfile.TemporaryDirectory() as folder:
            ready=Path(folder)/'pid'
            code="import subprocess,sys,time,threading\ndef worker():\n p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)\n open("+repr(str(ready))+",'w').write(str(p.pid))\n time.sleep(30)\nthreading.Thread(target=worker).start()\ntime.sleep(30)"
            with subprocess.Popen([sys.executable,'-c',code]) as proc:
                child=None
                try:
                    deadline=time.monotonic()+3
                    while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)
                    self.assertTrue(ready.exists())
                    child=int(ready.read_text());self.assertIn(child,helper.children(proc.pid))
                    helper.stop(proc.pid,helper.identity(proc.pid)[0]);proc.wait(timeout=2)
                    state=helper.identity(child)
                    deadline=time.monotonic()+2
                    while state is not None and state[1]!='Z' and time.monotonic()<deadline:
                        time.sleep(.01);state=helper.identity(child)
                    self.assertTrue(state is None or state[1]=='Z')
                finally:
                    if proc.poll() is None:proc.kill()
                    if child and helper.identity(child):
                        try:os.kill(child,signal.SIGKILL)
                        except ProcessLookupError:pass

    def test_wrong_identity_does_not_kill(self):
        with subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']) as proc:
            try:
                helper.stop(proc.pid,'0')
                self.assertIsNone(proc.poll())
            finally:proc.kill()

    def test_rejects_system_pids(self):
        with self.assertRaises(ValueError):helper.stop(1,'0')


if __name__=='__main__':unittest.main()
